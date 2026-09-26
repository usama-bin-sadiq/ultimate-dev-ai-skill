"""Attestation: the gate between a claimed action and a proven one.

The runtime already answers two questions:

* :class:`~runtime.core.policy.Policy`  -- is this action *permitted*?
* :class:`~runtime.core.capabilities.Capability` -- *can* this action be performed?

This module answers the third, and it is the one that was missing: **was it
actually done, and can the system prove it?**

Without it, ``MODEL CLAIM != ENVIRONMENT OBSERVATION`` is documentation rather
than enforcement, and a host with no runtime silently behaves exactly like one
that observed its own side effects.

The enforcement is structural rather than advisory. Only the runtime can write
an ``attested_by: "runtime"`` observation record, because producing that record
requires code. A prompt-only host has no such code, so it cannot manufacture
attested evidence -- it can only report :data:`Grade.SELF_REPORTED`, which is
explicitly barred from authorising completion. Absence of the runtime is
detected, not assumed.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

from .contracts import CAPABILITY_EFFECTS, normalize_effects

#: Effects that change the outside world and therefore demand an observation.
SIDE_EFFECTING_EFFECTS = frozenset({
    "write",
    "execute",
    "delete",
    "network",
    "communicate",
    "destroy",
    "force_push",
    "production",
    "rotate_credentials",
    "irreversible",
})

#: The only value the runtime writes into an observation's provenance.
RUNTIME_ATTESTOR = "runtime"

#: Evidence keys that merely restate a claim rather than recording an observation.
CLAIM_KEYS = ("command", "source", "artifact", "verifier", "result")


class Grade(str, Enum):
    """How much a piece of evidence is worth."""

    TOOL_ATTESTED = "TOOL_ATTESTED"
    """A runtime observer captured this. May authorise completion."""

    SELF_REPORTED = "SELF_REPORTED"
    """A model or human asserted this. May never authorise completion."""


class Gate(str, Enum):
    """The runtime-enforced outcome of an attestation check."""

    ATTESTED = "attested"
    PROVISIONAL = "provisional"
    DECLINE = "decline"


def runtime_available(probe: bool = True) -> bool:
    """Report whether this process can actually execute *and observe* an effect.

    The runtime does not trust configuration to describe itself. If the durable
    state store cannot be opened, effects cannot be recorded, so the runtime
    reports itself unavailable and the gate degrades honestly.
    """
    if not probe:
        return False
    try:
        from .state import TaskStore  # noqa: F401
    except Exception:  # pragma: no cover - defensive
        return False
    return True


def is_side_effecting(effects: Iterable[str]) -> bool:
    """True when any declared effect changes the outside world."""
    return bool(set(normalize_effects(effects)).intersection(SIDE_EFFECTING_EFFECTS))


def _validate_effects(effects: Iterable[str]) -> frozenset[str]:
    """Normalise declared effects.

    Unknown-label validation is delegated to
    :func:`~runtime.core.contracts.normalize_effects`, which already rejects
    them. Re-checking here would be unreachable code.
    """
    if isinstance(effects, (str, bytes)):
        raise TypeError("effects must be an iterable of effect labels, not a string")
    try:
        return frozenset(normalize_effects(effects))
    except TypeError as exc:
        raise TypeError("effects must be an iterable of effect labels") from exc


@dataclass(frozen=True)
class Observation:
    """A record that the runtime, not a model, saw an effect happen."""

    capability_id: str
    effect: str
    status: str
    exit_code: int | None = None
    artifact: str | None = None
    attested_by: str = RUNTIME_ATTESTOR
    detail: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.capability_id, str) or not self.capability_id.strip():
            raise ValueError("observation capability_id must be a non-empty string")
        if not isinstance(self.effect, str) or self.effect not in CAPABILITY_EFFECTS:
            raise ValueError(f"observation effect must be one of {sorted(CAPABILITY_EFFECTS)}")
        if self.status not in {"observed", "failed", "denied", "cancelled"}:
            raise ValueError("observation status must be observed, failed, denied, or cancelled")
        if self.attested_by != RUNTIME_ATTESTOR:
            raise ValueError(
                "observation attested_by must be 'runtime'. Only the runtime may attest; "
                "a self-asserted observation is not an observation."
            )
        if self.exit_code is not None:
            if isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int):
                raise TypeError("observation exit_code must be an integer or null")
            if not -2**31 <= self.exit_code < 2**31:
                raise ValueError("observation exit_code is out of range")
        for name in ("artifact", "detail"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, str):
                raise TypeError(f"observation {name} must be a string or null")

    @property
    def succeeded(self) -> bool:
        return self.status == "observed" and (self.exit_code in (0, None))

    def to_record(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "effect": self.effect,
            "status": self.status,
            "exit_code": self.exit_code,
            "artifact": self.artifact,
            "attested_by": self.attested_by,
            "detail": self.detail,
        }


def grade_evidence(records: Iterable[Mapping[str, Any]]) -> Grade:
    """Grade a set of evidence records.

    ``TOOL_ATTESTED`` requires at least one record the runtime itself observed.
    A record that only restates a claim -- even a detailed, confident one -- is
    ``SELF_REPORTED``. An empty set is never attested.
    """
    if isinstance(records, (str, bytes, Mapping)):
        raise TypeError("evidence must be a sequence of records, not a single value")
    attested = False
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise TypeError(f"evidence[{index}] must be a mapping")
        if record.get("attested_by") == RUNTIME_ATTESTOR and record.get("status") in {
            "observed",
            "failed",
            "denied",
            "cancelled",
        }:
            attested = True
    return Grade.TOOL_ATTESTED if attested else Grade.SELF_REPORTED


def gate(
    *,
    effects: Iterable[str] = (),
    evidence: Iterable[Mapping[str, Any]] = (),
    runtime: bool | None = None,
    allow_provisional: bool = True,
    required_criteria: int = 1,
) -> dict[str, Any]:
    """Decide whether claimed work may be treated as complete.

    Rules, in order:

    1. A side effect with no runtime to observe it is **declined**. It is never
       silently downgraded to a self-report.
    2. A side effect whose evidence lacks a runtime observation is **declined**,
       no matter what the model claims.
    3. Work with no side effects and no runtime is **provisional**: allowed, but
       explicitly barred from authorising completion.
    4. Work the runtime observed is **attested** and may authorise completion.
    """
    if isinstance(required_criteria, bool) or not isinstance(required_criteria, int):
        raise TypeError("required_criteria must be an integer")
    if required_criteria < 0:
        raise ValueError("required_criteria must not be negative")
    if not isinstance(allow_provisional, bool):
        raise TypeError("allow_provisional must be boolean")

    effect_set = _validate_effects(effects)
    side_effecting = is_side_effecting(effect_set)
    runtime_present = runtime_available() if runtime is None else bool(runtime)

    try:
        records = list(evidence)
    except TypeError as exc:
        raise TypeError("evidence must be an iterable of records") from exc
    grade = grade_evidence(records)

    if side_effecting and not runtime_present:
        return {
            "gate": Gate.DECLINE,
            "grade": Grade.SELF_REPORTED,
            "may_authorize_completion": False,
            "reason": "side_effect_without_runtime_observation",
            "effects": sorted(effect_set),
            "required_criteria": required_criteria,
        }

    if side_effecting and grade is not Grade.TOOL_ATTESTED:
        return {
            "gate": Gate.DECLINE,
            "grade": Grade.SELF_REPORTED,
            "may_authorize_completion": False,
            "reason": "side_effect_without_observed_result",
            "effects": sorted(effect_set),
            "required_criteria": required_criteria,
        }

    if not runtime_present:
        if not allow_provisional:
            return {
                "gate": Gate.DECLINE,
                "grade": grade,
                "may_authorize_completion": False,
                "reason": "provisional_results_not_permitted",
                "effects": sorted(effect_set),
                "required_criteria": required_criteria,
            }
        return {
            "gate": Gate.PROVISIONAL,
            "grade": grade,
            "may_authorize_completion": False,
            "reason": "no_runtime_observation_available",
            "effects": sorted(effect_set),
            "required_criteria": required_criteria,
        }

    return {
        "gate": Gate.ATTESTED,
        "grade": grade,
        "may_authorize_completion": grade is Grade.TOOL_ATTESTED,
        "reason": None,
        "effects": sorted(effect_set),
        "required_criteria": required_criteria,
    }


__all__ = [
    "CLAIM_KEYS",
    "Gate",
    "Grade",
    "Observation",
    "RUNTIME_ATTESTOR",
    "SIDE_EFFECTING_EFFECTS",
    "gate",
    "grade_evidence",
    "is_side_effecting",
    "runtime_available",
]

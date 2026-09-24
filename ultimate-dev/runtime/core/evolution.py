"""Governed self-evolution candidates for the dependency-free runtime.

This module is deliberately a *store*, not a publisher.  A proposal can be
staged and evaluated in project-local memory, but the only publication
primitive writes a receipt under ``.memory``.  It never copies a proposal to
``skills/``, ``agents/``, a manifest, or any other canonical project file.

The lifecycle is intentionally small and fail-closed::

    staged -> evaluating -> evaluated -> approved -> published
       |            |            |          |
       +------------+------------+-----------+-> rejected/expired
                                                |
                                                +-> rolled_back

Evaluation functions are injected by the host.  A missing evaluator, an
exception, a malformed result, or a failed security/regression check prevents
approval.  Approval is a separate explicit admission operation and is bound to
the candidate version and evaluation fingerprint.  This keeps a model or a
future host publisher from turning an unverified proposal into global state.
"""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
import os
import re
import tempfile
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

try:  # POSIX hosts get a small cross-process mutation lock.
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None


SCHEMA_VERSION = "1.0"
STORAGE_RELATIVE = Path(".memory") / "ultimate-dev" / "evolution"
MAX_JSON_BYTES = 2_000_000
MAX_HISTORY = 250
MAX_TRIALS = 100

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_TERMINAL_STATUSES = frozenset({"rejected", "expired", "rolled_back"})

# The store writes below its memory root only.  These values are useful in
# receipts and make the safety boundary explicit to callers and reviewers.
CANONICAL_WRITE_POLICY = "forbidden"
PUBLICATION_MODE = "memory_receipt_only"

# Public status vocabulary for hosts that render lifecycle state.
STAGED = "staged"
EVALUATING = "evaluating"
EVALUATED = "evaluated"
APPROVED = "approved"
ADMITTED = "admitted"
PUBLISHED = "published"
REJECTED = "rejected"
EXPIRED = "expired"
ROLLED_BACK = "rolled_back"
STATUS_STAGED = STAGED
STATUS_EVALUATING = EVALUATING
STATUS_EVALUATED = EVALUATED
STATUS_APPROVED = APPROVED
STATUS_ADMITTED = ADMITTED
STATUS_PUBLISHED = PUBLISHED
STATUS_REJECTED = REJECTED
STATUS_EXPIRED = EXPIRED
STATUS_ROLLED_BACK = ROLLED_BACK


class EvolutionError(RuntimeError):
    """Base class for governed evolution failures."""


class EvolutionContractError(EvolutionError, ValueError):
    """Raised when a proposal or lifecycle request is malformed."""


class CandidateNotFound(EvolutionError, KeyError):
    """Raised when a candidate identifier is not present in the store."""


class InvalidCandidateTransition(EvolutionError, ValueError):
    """Raised when a caller attempts an unsafe state transition."""


class AdmissionRequired(EvolutionError, PermissionError):
    """Raised when publication is attempted without explicit admission."""


class CandidateExpired(InvalidCandidateTransition):
    """Raised when an expired candidate is used for a new action."""


# Short aliases make the module convenient for callers that use the vocabulary
# from the runtime's other contract modules.
ContractError = EvolutionContractError
InvalidTransition = InvalidCandidateTransition
ApprovalRequired = AdmissionRequired
SelfEvolutionError = EvolutionError


class CandidateRecord(dict):
    """A JSON-compatible candidate record with attribute access.

    Returning a dict subclass keeps this store compatible with the existing
    runtime APIs while allowing callers to use either ``candidate["status"]``
    or ``candidate.status``.
    """

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:  # pragma: no cover - normal attribute behavior
            raise AttributeError(name) from exc

    @property
    def id(self) -> str:
        return self["candidate_id"]

    @property
    def proposal_id(self) -> str:
        return self["candidate_id"]

    @property
    def name(self) -> Any:
        proposal = self.get("proposal")
        metadata = proposal.get("metadata", {}) if isinstance(proposal, Mapping) else {}
        return metadata.get("name", self.get("name")) if isinstance(metadata, Mapping) else self.get("name")

    @property
    def evaluations(self) -> Any:
        return self.get("evaluation")

    def as_dict(self) -> dict[str, Any]:
        return _json_clone(dict(self), "candidate")


# Public names for callers that prefer an explicit model name.
EvolutionCandidate = CandidateRecord
Candidate = CandidateRecord


@dataclass(frozen=True)
class EvaluatorSet:
    """Explicit injected evaluator bundle for hosts that prefer an object."""

    deterministic: Any
    repeated: Any
    security: Any
    trials: int | None = None


def _json_clone(value: Any, label: str = "value") -> Any:
    """Return a detached JSON value, rejecting non-finite/non-serializable data."""
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise EvolutionContractError(f"{label} must be JSON serializable: {exc}") from exc
    if len(encoded.encode("utf-8")) > MAX_JSON_BYTES:
        raise EvolutionContractError(f"{label} exceeds the maximum persisted size")
    return json.loads(encoded)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _validate_identifier(value: Any, label: str = "candidate_id") -> str:
    if isinstance(value, Mapping):
        value = value.get("candidate_id") or value.get("id")
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value):
        raise EvolutionContractError(f"{label} must match {_IDENTIFIER_RE.pattern}")
    if value in {".", ".."}:
        raise EvolutionContractError(f"{label} is not a valid path component")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvolutionContractError(f"{label} must be a non-empty string")
    return value


def _parse_timestamp(value: Any, label: str = "timestamp") -> str:
    """Normalize a datetime, epoch value, or ISO-8601 string to UTC text."""
    if isinstance(value, datetime):
        moment = value
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            moment = datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError) as exc:
            raise EvolutionContractError(f"{label} is not a valid timestamp") from exc
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            raise EvolutionContractError(f"{label} must be a non-empty timestamp")
        if raw.endswith(("Z", "z")):
            raw = raw[:-1] + "+00:00"
        try:
            moment = datetime.fromisoformat(raw)
        except ValueError as exc:
            raise EvolutionContractError(f"{label} is not a valid ISO-8601 timestamp") from exc
    else:
        raise EvolutionContractError(f"{label} must be a datetime, epoch, or ISO-8601 string")
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _timestamp_value(value: str) -> float:
    raw = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(raw).timestamp()


def _utc_now() -> str:
    return _parse_timestamp(datetime.now(timezone.utc))


def _safe_relative_target(value: Any, label: str) -> str | None:
    """Validate a *metadata* target without ever resolving or writing it."""
    if value is None:
        return None
    if isinstance(value, os.PathLike):
        value = os.fspath(value)
    target = _text(value, label)
    path = Path(target)
    if target in {".", ""} or path.is_absolute() or "\\" in target or ".." in path.parts:
        raise EvolutionContractError(f"{label} must be a contained relative path")
    return target


def _mapping_or_text(value: Any, label: str, *, allow_text: bool = True) -> Any:
    if isinstance(value, Mapping):
        _json_clone(dict(value), label)
        return dict(value)
    if isinstance(value, (list, tuple)) and value:
        _json_clone(list(value), label)
        return list(value)
    if allow_text and isinstance(value, str) and value.strip():
        return value
    raise EvolutionContractError(
        f"{label} must be a non-empty object, array, or string"
        if allow_text
        else f"{label} must be a non-empty object or array"
    )


def _normalize_evidence(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        raw_items: list[Any] = [value]
    elif isinstance(value, (list, tuple)):
        raw_items = list(value)
    elif isinstance(value, str) and value.strip():
        raw_items = [value]
    else:
        raise EvolutionContractError("evidence must be a non-empty array or object")
    if not raw_items:
        raise EvolutionContractError("evidence must contain at least one item")
    if len(raw_items) > 100:
        raise EvolutionContractError("evidence contains too many items")
    result: list[dict[str, Any]] = []
    provenance_keys = {
        "source",
        "command",
        "artifact",
        "verifier",
        "result",
        "url",
        "hash",
        "description",
        "value",
        "commands",
        "tests",
        "regression",
        "metrics",
        "trace",
    }
    for index, item in enumerate(raw_items):
        if isinstance(item, str):
            item = {"value": item}
        if not isinstance(item, Mapping):
            raise EvolutionContractError(f"evidence[{index}] must be an object")
        normalized = _json_clone(dict(item), f"evidence[{index}]")
        if not normalized or not provenance_keys.intersection(normalized):
            raise EvolutionContractError(
                f"evidence[{index}] must identify its source, command, artifact, verifier, or result"
            )
        result.append(normalized)
    return result


def _normalize_metadata_target(metadata: Mapping[str, Any]) -> None:
    """Reject obvious path escapes in optional target metadata.

    Canonical target paths are allowed as *declarative* metadata.  The store
    never opens them.  Escaping paths are rejected so a later publisher cannot
    accidentally receive an unsafe rollback plan.
    """
    for key in ("target", "target_path", "canonical_target", "canonical_path", "path"):
        if key in metadata:
            _safe_relative_target(metadata[key], f"proposal.{key}")


def _validate_embedded_targets(value: Any, label: str = "proposal") -> None:
    """Apply target containment checks to nested diff/rollback metadata."""
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).lower() in {"target", "target_path", "canonical_target", "canonical_path", "path"}:
                _safe_relative_target(child, f"{label}.{key}")
            else:
                _validate_embedded_targets(child, f"{label}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_embedded_targets(child, f"{label}[{index}]")


def _find_target(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key in ("canonical_target", "target", "target_path", "canonical_path", "path"):
            if key in value:
                return _safe_relative_target(value[key], f"proposal.{key}")
        for child in value.values():
            found = _find_target(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_target(child)
            if found is not None:
                return found
    return None


def _safe_result(value: Any) -> Any:
    """Keep evaluator output JSON-safe without allowing an exception to escape."""
    try:
        return _json_clone(value)
    except EvolutionContractError:
        text = repr(value)
        return {"unserializable": text[:1000]}


def _result_is_json_safe(value: Any) -> bool:
    try:
        _json_clone(value)
    except EvolutionContractError:
        return False
    return True


def _passed_value(value: Any) -> bool:
    """Interpret only explicit evaluator success values as a pass."""
    if isinstance(value, bool):
        return value
    if isinstance(value, Mapping):
        for key in ("passed", "pass", "ok", "success", "safe", "approved"):
            if key in value:
                return _passed_value(value[key])
        status = value.get("status")
        if isinstance(status, str):
            return status.lower() in {"pass", "passed", "success", "succeeded", "ok", "safe", "approved", "admitted"}
        result = value.get("result")
        if result is not None and key_is_result(result):
            return _passed_value(result)
        return False
    for name in ("passed", "ok", "success", "safe", "approved"):
        if hasattr(value, name):
            return _passed_value(getattr(value, name))
    status = getattr(value, "status", None)
    if isinstance(status, str):
        return status.lower() in {"pass", "passed", "success", "succeeded", "ok", "safe"}
    return False


def key_is_result(value: Any) -> bool:
    """Avoid treating arbitrary result text as a boolean success claim."""
    return isinstance(value, (bool, Mapping)) or hasattr(value, "passed") or hasattr(value, "ok")


class EvolutionStore:
    """Durable, governed candidate lifecycle backed by project-local memory.

    Parameters
    ----------
    project_root:
        Project directory.  All writes are contained below
        ``<project_root>/.memory/ultimate-dev/evolution``.
    evaluators:
        Optional mapping containing ``deterministic``, ``repeated``, and
        ``security`` callables.  The three evaluator families are required by
        :meth:`evaluate`; staging itself does not run them.
    clock:
        Optional zero-argument clock returning a datetime, epoch, or ISO
        string.  It makes expiry and audit tests deterministic.
    """

    _EVALUATOR_NAMES = {
        "deterministic": "deterministic",
        "deterministic_evaluator": "deterministic",
        "det": "deterministic",
        "functional": "deterministic",
        "repeated": "repeated",
        "repeated_evaluator": "repeated",
        "repeat": "repeated",
        "regression": "regression",
        "regression_evaluator": "regression",
        "security": "security",
        "security_evaluator": "security",
        "sandbox": "security",
    }

    _ALLOWED_TRANSITIONS = {
        "staged": {"evaluating", "rejected", "expired"},
        "evaluating": {"evaluated", "rejected", "expired"},
        "evaluated": {"evaluating", "approved", "rejected", "expired"},
        "approved": {"published", "rejected", "expired", "rolled_back"},
        "published": {"rolled_back"},
        "rejected": {"staged", "expired"},
        "expired": set(),
        "rolled_back": {"staged"},
    }

    def __init__(
        self,
        project_root: str | Path,
        evaluators: Mapping[str, Any] | None = None,
        *,
        deterministic: Any = None,
        repeated: Any = None,
        security: Any = None,
        regression: Any = None,
        deterministic_evaluator: Any = None,
        repeated_evaluator: Any = None,
        security_evaluator: Any = None,
        regression_evaluator: Any = None,
        clock: Callable[[], Any] | None = None,
        now: Callable[[], Any] | None = None,
        default_ttl_seconds: float | None = None,
        ttl: float | None = None,
    ) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.root = self.project_root
        self.base = (self.project_root / STORAGE_RELATIVE).resolve()
        self._assert_contained(self.base)
        self.base.mkdir(parents=True, exist_ok=True)
        self.candidates_dir = self.base / "candidates"
        self.events_dir = self.base / "events"
        self.publications_dir = self.base / "publications"
        self.rollbacks_dir = self.base / "rollbacks"
        self.index_path = self.base / "index.json"
        self.events_path = self.events_dir / "events.jsonl"
        self.lock_path = self.base / ".lock"
        self.memory_root = self.base
        self.evolution_dir = self.base
        self.state_dir = self.candidates_dir
        for directory in (self.candidates_dir, self.events_dir, self.publications_dir, self.rollbacks_dir):
            self._assert_contained(directory)
            directory.mkdir(parents=True, exist_ok=True)
        self._clock = clock or now or _utc_now
        if default_ttl_seconds is not None and ttl is not None:
            raise EvolutionContractError("use default_ttl_seconds or ttl, not both")
        if default_ttl_seconds is None:
            default_ttl_seconds = ttl
        if default_ttl_seconds is not None:
            if isinstance(default_ttl_seconds, bool) or not isinstance(default_ttl_seconds, (int, float)):
                raise EvolutionContractError("default_ttl_seconds must be a number")
            if default_ttl_seconds <= 0:
                raise EvolutionContractError("default_ttl_seconds must be positive")
        self.default_ttl_seconds = default_ttl_seconds
        configured: dict[str, Any] = {}
        if evaluators is not None:
            if isinstance(evaluators, EvaluatorSet):
                configured.update(
                    {
                        "deterministic": evaluators.deterministic,
                        "repeated": evaluators.repeated,
                        "security": evaluators.security,
                    }
                )
                if evaluators.trials is not None:
                    configured["repeated_trials"] = evaluators.trials
            elif isinstance(evaluators, Mapping):
                for key, value in evaluators.items():
                    normalized_key = str(key).lower()
                    mapped = self._EVALUATOR_NAMES.get(normalized_key)
                    if mapped:
                        configured[mapped] = value
                    elif normalized_key in {
                        "trials",
                        "repetitions",
                        "trial_count",
                        "repeat_count",
                        "run_count",
                        "runs",
                    }:
                        configured["repeated_trials"] = value
            elif isinstance(evaluators, (list, tuple)) and len(evaluators) == 3:
                configured.update(
                    {
                        "deterministic": evaluators[0],
                        "repeated": evaluators[1],
                        "security": evaluators[2],
                    }
                )
            else:
                raise EvolutionContractError("evaluators must be an object or EvaluatorSet")
        for key, value in {
            "deterministic": deterministic,
            "deterministic_evaluator": deterministic_evaluator,
            "repeated": repeated,
            "repeated_evaluator": repeated_evaluator,
            "security": security,
            "security_evaluator": security_evaluator,
            "regression": regression,
            "regression_evaluator": regression_evaluator,
        }.items():
            if value is not None:
                configured["regression" if key.startswith("regression") else key.removesuffix("_evaluator")] = value
        self.evaluators = configured
        with self._lock():
            if not self.index_path.exists():
                self._write_json_unlocked(
                    self.index_path,
                    {
                        "schema_version": SCHEMA_VERSION,
                        "candidates": {},
                        "updated_at": self._now_text(),
                    },
                )

    def _assert_contained(self, path: Path) -> None:
        resolved = path.resolve()
        root = self.project_root.resolve()
        if resolved != root and root not in resolved.parents:
            raise EvolutionContractError(f"evolution storage escapes project root: {path}")
        if path.is_symlink():
            raise EvolutionContractError(f"evolution storage paths must not be symlinks: {path}")

    def _now(self) -> str:
        try:
            return _parse_timestamp(self._clock())
        except EvolutionContractError:
            raise
        except Exception as exc:  # a host clock is an external boundary
            raise EvolutionContractError(f"clock returned an invalid value: {exc}") from exc

    def _now_text(self) -> str:
        return self._now()

    @contextmanager
    def _lock(self) -> Iterator[None]:
        self._assert_contained(self.lock_path)
        with open(self.lock_path, "a+", encoding="utf-8") as lock_file:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _write_json_unlocked(self, path: Path, value: Any) -> None:
        self._assert_contained(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _write_event_unlocked(self, event: Mapping[str, Any]) -> None:
        self._assert_contained(self.events_path)
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        encoded = _canonical_json(dict(event)) + "\n"
        with open(self.events_path, "a", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())

    def _read_json_unlocked(self, path: Path, label: str) -> dict[str, Any]:
        self._assert_contained(path)
        try:
            with open(path, encoding="utf-8") as handle:
                value = json.load(handle)
        except FileNotFoundError as exc:
            raise CandidateNotFound(f"{label} does not exist: {path.name}") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise EvolutionContractError(f"unable to read {label}: {exc}") from exc
        if not isinstance(value, dict):
            raise EvolutionContractError(f"{label} must contain an object")
        return value

    def _load_index_unlocked(self) -> dict[str, Any]:
        if not self.index_path.exists():
            return {"schema_version": SCHEMA_VERSION, "candidates": {}, "updated_at": self._now_text()}
        value = self._read_json_unlocked(self.index_path, "evolution index")
        if not isinstance(value.get("candidates"), dict):
            raise EvolutionContractError("evolution index candidates must be an object")
        return value

    def _save_index_unlocked(self) -> None:
        self._write_json_unlocked(
            self.index_path,
            {
                "schema_version": SCHEMA_VERSION,
                "candidates": self._load_index_unlocked().get("candidates", {}),
                "updated_at": self._now_text(),
            },
        )

    def candidate_path(self, candidate_id: str) -> Path:
        candidate_id = _validate_identifier(candidate_id)
        path = (self.candidates_dir / f"{candidate_id}.json").resolve()
        self._assert_contained(path)
        return path

    def _load_candidate_unlocked(self, candidate_id: str) -> CandidateRecord:
        candidate_id = _validate_identifier(candidate_id)
        value = self._read_json_unlocked(self.candidate_path(candidate_id), f"candidate {candidate_id}")
        if value.get("candidate_id") != candidate_id:
            raise EvolutionContractError(f"candidate {candidate_id} has an identity mismatch")
        if value.get("status") not in self._ALLOWED_TRANSITIONS:
            raise EvolutionContractError(f"candidate {candidate_id} has an invalid status")
        proposal = value.get("proposal")
        if not isinstance(proposal, Mapping):
            raise EvolutionContractError(f"candidate {candidate_id} has no proposal payload")
        if value.get("proposal_fingerprint") != _fingerprint(dict(proposal)):
            raise EvolutionContractError(f"candidate {candidate_id} proposal fingerprint does not match")
        for field in ("source", "evidence", "diff", "rollback", "metadata"):
            if field in value and value[field] != proposal.get(field):
                raise EvolutionContractError(f"candidate {candidate_id} {field} does not match proposal")
        return CandidateRecord(value)

    def _persist_candidate_unlocked(self, record: CandidateRecord, *, index: bool = True) -> None:
        candidate_id = _validate_identifier(record.get("candidate_id"))
        self._write_json_unlocked(self.candidate_path(candidate_id), dict(record))
        if index:
            index_value = self._load_index_unlocked()
            candidates = index_value.setdefault("candidates", {})
            candidates[candidate_id] = {
                "status": record.get("status"),
                "version": record.get("version"),
                "active": record.get("active", False),
                "published_version": record.get("published_version"),
                "updated_at": record.get("updated_at"),
                "path": str(self.candidate_path(candidate_id).relative_to(self.base)),
            }
            index_value["schema_version"] = SCHEMA_VERSION
            index_value["updated_at"] = self._now_text()
            self._write_json_unlocked(self.index_path, index_value)

    def _event_unlocked(
        self,
        record: CandidateRecord,
        event_type: str,
        *,
        reason: str | None = None,
        actor: str | None = None,
        **details: Any,
    ) -> dict[str, Any]:
        event = {
            "event_id": f"event-{uuid.uuid4().hex}",
            "at": self._now_text(),
            "candidate_id": record["candidate_id"],
            "version": record.get("version"),
            "type": event_type,
            "from": record.get("previous_status"),
            "to": record.get("status"),
            "proposal_fingerprint": record.get("proposal_fingerprint"),
            "state_revision": int(record.get("revision", 0)) + 1,
        }
        if reason is not None:
            event["reason"] = reason
        if actor is not None:
            event["actor"] = actor
        if details:
            event["details"] = _json_clone(details, "event details")
        record.setdefault("history", []).append(_json_clone(event, "history event"))
        record["history"] = record["history"][-MAX_HISTORY:]
        record["revision"] = int(record.get("revision", 0)) + 1
        self._write_event_unlocked(event)
        return event

    def _transition_unlocked(
        self,
        record: CandidateRecord,
        new_status: str,
        *,
        reason: str,
        actor: str | None = None,
        clear_approval: bool = False,
        clear_evaluation: bool = False,
        **details: Any,
    ) -> None:
        current = record.get("status")
        if new_status == current:
            return
        if new_status not in self._ALLOWED_TRANSITIONS.get(current, set()):
            raise InvalidCandidateTransition(f"invalid candidate transition {current} -> {new_status}")
        record["previous_status"] = current
        record["status"] = new_status
        record["state"] = new_status
        record["updated_at"] = self._now_text()
        record["last_transition_reason"] = reason
        if clear_approval:
            record["admission"] = None
            record["approval"] = None
            record["admission_state"] = None
            record["admitted"] = False
            record["approved"] = False
            record["status_aliases"] = []
            record["approved_by"] = None
            record["approved_at"] = None
        if clear_evaluation:
            record["evaluation"] = None
        for key, value in details.items():
            record[key] = _json_clone(value, key) if isinstance(value, (Mapping, list)) else value
        self._event_unlocked(record, "transition", reason=reason, actor=actor, **details)

    def _expire_if_due_unlocked(self, record: CandidateRecord, *, at: str | None = None) -> bool:
        status = record.get("status")
        expires_at = record.get("expires_at")
        if not expires_at or status in _TERMINAL_STATUSES or status in {"evaluating", "published"}:
            return False
        moment = at or self._now_text()
        if _timestamp_value(moment) < _timestamp_value(expires_at):
            return False
        self._transition_unlocked(
            record,
            "expired",
            reason="ttl_expired",
            clear_approval=True,
            expiration={"expired_at": moment, "scheduled_at": expires_at, "reason": "ttl_expired"},
        )
        self._persist_candidate_unlocked(record)
        return True

    def _proposal_payload(
        self,
        proposal: Mapping[str, Any] | None,
        *,
        source: Any = None,
        evidence: Any = None,
        diff: Any = None,
        rollback: Any = None,
        extra: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = dict(proposal or {})
        for key, value in {
            "source": source,
            "evidence": evidence,
            "diff": diff,
            "rollback": rollback,
        }.items():
            if value is not None:
                data[key] = value
        if extra:
            for key, value in extra.items():
                data[key] = value
        aliases = {
            "source": ("source_metadata", "provenance"),
            "evidence": ("evidence_refs", "evidence_records"),
            "diff": ("patch", "change", "changes"),
            "rollback": ("rollback_plan", "rollback_metadata"),
        }
        for canonical, names in aliases.items():
            if canonical not in data:
                for name in names:
                    if name in data:
                        data[canonical] = data[name]
                        break
        missing = [key for key in ("source", "evidence", "diff", "rollback") if key not in data]
        if missing:
            raise EvolutionContractError(f"proposal is missing required metadata: {', '.join(missing)}")
        normalized_source = _mapping_or_text(data["source"], "proposal.source")
        normalized_diff = _mapping_or_text(data["diff"], "proposal.diff")
        normalized_rollback = _mapping_or_text(data["rollback"], "proposal.rollback")
        if isinstance(normalized_rollback, str):
            normalized_rollback = {"description": normalized_rollback}
        if isinstance(normalized_rollback, Mapping) and not normalized_rollback:
            raise EvolutionContractError("proposal.rollback must not be empty")
        if isinstance(normalized_diff, Mapping) and not normalized_diff:
            raise EvolutionContractError("proposal.diff must not be empty")
        if isinstance(normalized_source, Mapping) and not normalized_source:
            raise EvolutionContractError("proposal.source must not be empty")
        _validate_embedded_targets(normalized_diff, "proposal.diff")
        _validate_embedded_targets(normalized_rollback, "proposal.rollback")
        normalized = {
            "source": _json_clone(normalized_source, "proposal.source"),
            "evidence": _normalize_evidence(data["evidence"]),
            "diff": _json_clone(normalized_diff, "proposal.diff"),
            "rollback": _json_clone(normalized_rollback, "proposal.rollback"),
        }
        reserved = {"source", "evidence", "diff", "rollback"}
        metadata = {key: value for key, value in data.items() if key not in reserved}
        _normalize_metadata_target(metadata)
        _validate_embedded_targets(metadata, "proposal.metadata")
        normalized["metadata"] = _json_clone(metadata, "proposal.metadata")
        return normalized

    def stage(
        self,
        proposal: Mapping[str, Any] | None = None,
        *,
        source: Any = None,
        evidence: Any = None,
        diff: Any = None,
        rollback: Any = None,
        candidate_id: str | None = None,
        proposal_id: str | None = None,
        ttl_seconds: float | None = None,
        ttl: float | None = None,
        expires_at: Any = None,
        expires_in: float | None = None,
        version: int | None = None,
        parent_id: str | None = None,
        parent: str | None = None,
        parent_candidate_id: str | None = None,
        actor: str | None = None,
        **extra: Any,
    ) -> CandidateRecord:
        """Stage a proposal without touching canonical skill/agent files."""
        if ttl_seconds is not None and ttl is not None:
            raise EvolutionContractError("use ttl_seconds or ttl, not both")
        if ttl_seconds is not None and expires_at is not None:
            raise EvolutionContractError("use ttl_seconds or expires_at, not both")
        if ttl_seconds is None:
            ttl_seconds = ttl
        if ttl_seconds is None:
            ttl_seconds = expires_in
        if ttl_seconds is None:
            ttl_seconds = self.default_ttl_seconds
        if ttl_seconds is not None:
            if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, (int, float)):
                raise EvolutionContractError("ttl_seconds must be a number")
            if ttl_seconds <= 0:
                raise EvolutionContractError("ttl_seconds must be positive")
        if proposal is not None and not isinstance(proposal, Mapping):
            if isinstance(proposal, str) and proposal.strip() and all(
                value is not None for value in (source, evidence, diff, rollback)
            ):
                # Convenient form: stage("candidate-name", source=..., ...)
                extra = {"name": proposal, **extra}
                proposal = None
            else:
                raise EvolutionContractError("proposal must be an object")
        payload = self._proposal_payload(
            proposal,
            source=source,
            evidence=evidence,
            diff=diff,
            rollback=rollback,
            extra=extra,
        )
        metadata = payload["metadata"]
        if proposal_id is not None:
            if candidate_id is not None and proposal_id != candidate_id:
                raise EvolutionContractError("candidate_id and proposal_id disagree")
            candidate_id = proposal_id
        requested_id = candidate_id or metadata.pop("id", None) or metadata.pop("candidate_id", None)
        # ``id``/``candidate_id`` are not retained as arbitrary metadata once
        # consumed as identity; all other proposal metadata remains durable.
        candidate_id = _validate_identifier(requested_id or f"candidate-{uuid.uuid4().hex[:16]}")
        parent_aliases = [value for value in (parent_id, parent, parent_candidate_id) if value is not None]
        if len(set(parent_aliases)) > 1:
            raise EvolutionContractError("parent_id aliases disagree")
        if parent_aliases:
            parent_id = _validate_identifier(parent_aliases[0], "parent_id")
        if version is not None:
            if isinstance(version, bool) or not isinstance(version, int) or version < 1:
                raise EvolutionContractError("version must be a positive integer")
        now = self._now_text()
        if expires_at is not None:
            normalized_expiry = _parse_timestamp(expires_at, "expires_at")
        elif ttl_seconds is not None:
            normalized_expiry = _parse_timestamp(_timestamp_value(now) + float(ttl_seconds), "expires_at")
        else:
            normalized_expiry = None
        if normalized_expiry is not None and _timestamp_value(normalized_expiry) <= _timestamp_value(now):
            raise EvolutionContractError("expires_at must be in the future")
        payload["metadata"].pop("id", None)
        payload["metadata"].pop("candidate_id", None)
        proposal_fingerprint = _fingerprint(payload)
        with self._lock():
            if self.candidate_path(candidate_id).exists():
                raise EvolutionContractError(f"candidate already exists: {candidate_id}")
            if parent_id is not None:
                parent = self._load_candidate_unlocked(parent_id)
                self._expire_if_due_unlocked(parent)
                next_version = int(parent.get("version", 1)) + 1
                if version is not None and version != next_version:
                    raise EvolutionContractError("version does not follow parent candidate version")
                version = next_version
                lineage_id = parent.get("lineage_id", parent_id)
            else:
                version = version or 1
                lineage_id = candidate_id
            record = CandidateRecord(
                {
                    "schema_version": SCHEMA_VERSION,
                    "candidate_id": candidate_id,
                    "id": candidate_id,
                    "proposal_id": candidate_id,
                    "name": payload["metadata"].get("name"),
                    "lineage_id": lineage_id,
                    "parent_candidate_id": parent_id,
                    "parent_id": parent_id,
                    "version": version,
                    "status": "staged",
                    "state": "staged",
                    "phase": "proposed",
                    "created_at": now,
                    "updated_at": now,
                    "expires_at": normalized_expiry,
                    "revision": 0,
                    "proposal": payload,
                    # Top-level copies make audit consumers pleasantly small
                    # while the normalized proposal remains authoritative.
                    "source": payload["source"],
                    "evidence": payload["evidence"],
                    "evidence_refs": payload["evidence"],
                    "diff": payload["diff"],
                    "rollback": payload["rollback"],
                    "rollback_plan": payload["rollback"],
                    "metadata": payload["metadata"],
                    "source_fingerprint": _fingerprint(payload["source"]),
                    "evidence_fingerprint": _fingerprint(payload["evidence"]),
                    "diff_fingerprint": _fingerprint(payload["diff"]),
                    "rollback_fingerprint": _fingerprint(payload["rollback"]),
                    "proposal_fingerprint": proposal_fingerprint,
                    "evaluation": None,
                    "admission": None,
                    "approval": None,
                    "admission_state": None,
                    "admitted": False,
                    "approved": False,
                    "status_aliases": [],
                    "publication": None,
                    "global_published": False,
                    "published_version": None,
                    "active": False,
                    "active_version": None,
                    "version_history": [],
                    "rollback_history": [],
                    "children": [],
                    "history": [],
                    "protected_regression_failure": False,
                    "canonical_write_policy": CANONICAL_WRITE_POLICY,
                    "canonical_write_performed": False,
                    "created_by": actor,
                    "failure": None,
                }
            )
            if actor is not None:
                _text(actor, "actor")
            self._persist_candidate_unlocked(record)
            self._event_unlocked(
                record,
                "staged",
                reason="proposal_staged",
                actor=actor,
                version=version,
                parent_candidate_id=parent_id,
            )
            self._persist_candidate_unlocked(record)
            return record

    # Friendly aliases used by workflow adapters.
    stage_proposal = stage
    stage_candidate = stage

    def stage_id(self, *args: Any, **kwargs: Any) -> str:
        return self.stage(*args, **kwargs)["candidate_id"]

    def transition(
        self,
        candidate_id: str,
        new_status: str,
        *,
        actor: str | None = None,
        reason: str = "manual_transition",
        explicit: bool = True,
        approver: str | None = None,
        approved_by: str | None = None,
    ) -> CandidateRecord:
        """Apply a governed lifecycle action without exposing a raw state setter.

        ``evaluating`` and ``evaluated`` are intentionally not directly
        settable: they can only be reached through :meth:`evaluate`, which runs
        all required evaluator families.
        """
        if not isinstance(new_status, str):
            raise EvolutionContractError("new_status must be a string")
        normalized = new_status.strip().lower().replace("-", "_")
        if normalized in {"admitted", "approved"}:
            return self.admit(candidate_id, actor=actor or approver or approved_by, explicit=explicit, reason=reason)
        if normalized == "published":
            return self.publish(candidate_id, actor=actor or approver or approved_by, explicit=explicit, reason=reason)
        if normalized == "rejected":
            return self.reject(candidate_id, reason=reason, actor=actor)
        if normalized == "expired":
            return self.expire(candidate_id, reason=reason, actor=actor)
        if normalized == "rolled_back":
            return self.rollback(candidate_id, reason=reason, actor=actor, explicit=explicit)
        if normalized == "staged":
            record = self.get_candidate(candidate_id)
            if record.status != "staged":
                raise InvalidCandidateTransition("only evaluation/revision operations may restage a candidate")
            return record
        raise InvalidCandidateTransition(f"transition to {new_status} is not directly available")

    def get_candidate(
        self,
        candidate_id: str,
        *,
        now: Any = None,
        at: Any = None,
    ) -> CandidateRecord:
        with self._lock():
            record = self._load_candidate_unlocked(candidate_id)
            moment = (
                _parse_timestamp(now if now is not None else at, "now")
                if (now is not None or at is not None)
                else None
            )
            if self._expire_if_due_unlocked(record, at=moment):
                record = self._load_candidate_unlocked(candidate_id)
            return record

    get = get_candidate
    load = get_candidate

    def list_candidates(self, status: str | None = None) -> list[CandidateRecord]:
        with self._lock():
            result: list[CandidateRecord] = []
            for path in sorted(self.candidates_dir.glob("*.json")):
                candidate_id = path.stem
                record = self._load_candidate_unlocked(candidate_id)
                if self._expire_if_due_unlocked(record):
                    record = self._load_candidate_unlocked(candidate_id)
                if status is None or record.get("status") == status:
                    result.append(record)
            return result

    list = list_candidates

    def _resolve_evaluators(
        self,
        evaluators: Mapping[str, Any] | None,
        deterministic: Any,
        repeated: Any,
        security: Any,
        regression: Any,
    ) -> tuple[Any, Any, Any, int | None]:
        configured = dict(self.evaluators)
        if evaluators is not None:
            if isinstance(evaluators, EvaluatorSet):
                configured.update(
                    {
                        "deterministic": evaluators.deterministic,
                        "repeated": evaluators.repeated,
                        "security": evaluators.security,
                    }
                )
                if evaluators.trials is not None:
                    configured["repeated_trials"] = evaluators.trials
            elif isinstance(evaluators, Mapping):
                for key, value in evaluators.items():
                    normalized_key = str(key).lower()
                    mapped = self._EVALUATOR_NAMES.get(normalized_key)
                    if mapped:
                        configured[mapped] = value
                    elif normalized_key in {
                        "trials",
                        "repetitions",
                        "trial_count",
                        "repeat_count",
                        "run_count",
                        "runs",
                    }:
                        configured["repeated_trials"] = value
            elif isinstance(evaluators, (list, tuple)) and len(evaluators) == 3:
                configured.update(
                    {
                        "deterministic": evaluators[0],
                        "repeated": evaluators[1],
                        "security": evaluators[2],
                    }
                )
            else:
                raise EvolutionContractError("evaluators must be an object or a three-item sequence")
        if deterministic is not None:
            configured["deterministic"] = deterministic
        if repeated is not None:
            configured["repeated"] = repeated
        if security is not None:
            configured["security"] = security
        if regression is not None:
            configured["regression"] = regression
        regression_value = configured.pop("regression", None)
        if configured.get("security") is None and regression_value is not None:
            configured["security"] = regression_value
        elif regression_value is not None:
            configured["security"] = [configured["security"], regression_value]
        repeated_trials: int | None = configured.pop("repeated_trials", None)
        repeated_value = configured.get("repeated")
        if isinstance(repeated_value, Mapping):
            suite_trials = repeated_value.get("trials", repeated_value.get("repetitions"))
            if suite_trials is not None:
                repeated_trials = suite_trials
            if "evaluator" in repeated_value:
                repeated_value = repeated_value["evaluator"]
                configured["repeated"] = repeated_value
        for name in ("deterministic", "repeated", "security"):
            if configured.get(name) is None:
                raise EvolutionContractError(f"{name} evaluator is required")
        if repeated_trials is not None:
            if isinstance(repeated_trials, bool) or not isinstance(repeated_trials, int):
                raise EvolutionContractError("repeated trials must be an integer")
        return configured["deterministic"], repeated_value, configured["security"], repeated_trials

    def _evaluator_callable(self, evaluator: Any) -> Callable[..., Any]:
        if callable(evaluator):
            return evaluator
        for method_name in ("evaluate", "run", "check"):
            method = getattr(evaluator, method_name, None)
            if callable(method):
                return method
        return lambda _candidate: evaluator

    def _invoke_evaluator(
        self,
        evaluator: Any,
        record: CandidateRecord,
        *,
        trial_index: int | None = None,
        trials: int | None = None,
    ) -> Any:
        target = self._evaluator_callable(evaluator)
        proposal = copy.deepcopy(record.get("proposal", {}))
        candidate = copy.deepcopy(dict(record))
        context = {
            "candidate_id": record["candidate_id"],
            "version": record.get("version"),
            "proposal": copy.deepcopy(proposal),
            "trial_index": trial_index,
            "trial": trial_index,
            "run": trial_index,
            "repetition": trial_index,
            "attempt": trial_index,
            "trials": trials,
        }
        names = {
            "candidate": candidate,
            "record": candidate,
            "state": candidate,
            "proposal": proposal,
            "payload": proposal,
            "context": context,
            "ctx": context,
            "candidate_id": record["candidate_id"],
            "id": record["candidate_id"],
            "version": record.get("version"),
            "trial_index": trial_index,
            "trial": trial_index,
            "index": trial_index,
            "run": trial_index,
            "iteration": trial_index,
            "iteration_index": trial_index,
            "repeat_index": trial_index,
            "repetition": trial_index,
            "n": trial_index,
            "attempt": trial_index,
            "seed": trial_index,
            "trials": trials,
        }
        try:
            signature = inspect.signature(target)
        except (TypeError, ValueError):
            return target(candidate)
        parameters = list(signature.parameters.values())
        has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in parameters)
        args: list[Any] = []
        kwargs: dict[str, Any] = {}
        for parameter in parameters:
            if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            if parameter.name in names:
                value = names[parameter.name]
            elif parameter.default is inspect.Parameter.empty:
                value = candidate
            else:
                continue
            if parameter.kind == inspect.Parameter.POSITIONAL_ONLY:
                args.append(value)
            else:
                kwargs[parameter.name] = value
        # A bare ``*args`` evaluator has no useful parameter names; passing the
        # candidate is the least surprising contract.
        if not parameters:
            return target()
        if all(
            parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            for parameter in parameters
        ):
            if any(parameter.kind == inspect.Parameter.VAR_POSITIONAL for parameter in parameters):
                return target(candidate)
            return target(candidate=candidate, proposal=proposal, context=context, candidate_id=record["candidate_id"])
        if has_var_kw:
            for name in ("candidate", "proposal", "context", "candidate_id", "trial_index", "trials"):
                if name not in kwargs and name in names:
                    kwargs[name] = copy.deepcopy(names[name])
        return target(*args, **kwargs)

    def _run_check(
        self,
        name: str,
        evaluator: Any,
        record: CandidateRecord,
        *,
        trials: int | None = None,
    ) -> dict[str, Any]:
        if name == "repeated":
            count = trials or 3
            if isinstance(count, bool) or not isinstance(count, int) or count < 1 or count > MAX_TRIALS:
                raise EvolutionContractError(f"repeated trials must be between 1 and {MAX_TRIALS}")
            runs: list[dict[str, Any]] = []
            suite = evaluator if isinstance(evaluator, (list, tuple)) else [evaluator]
            if not suite:
                suite = [evaluator]
            for index in range(count):
                trial_results: list[dict[str, Any]] = []
                for member in suite:
                    try:
                        raw = self._invoke_evaluator(member, record, trial_index=index, trials=count)
                        if inspect.isawaitable(raw):
                            close = getattr(raw, "close", None)
                            if callable(close):
                                close()
                            raise EvolutionContractError("asynchronous evaluators require a host adapter")
                        trial_results.append(
                            {
                                "passed": _passed_value(raw) and _result_is_json_safe(raw),
                                "result": _safe_result(raw),
                            }
                        )
                    except Exception as exc:  # evaluator boundary
                        trial_results.append(
                            {
                                "passed": False,
                                "error": {"type": type(exc).__name__, "message": str(exc)[:500]},
                            }
                        )
                runs.append(
                    {
                        "trial": index,
                        "passed": bool(trial_results) and all(item["passed"] for item in trial_results),
                        "checks": trial_results,
                    }
                )
            return {
                "name": name,
                "passed": bool(runs) and all(run["passed"] for run in runs),
                "trials": count,
                "runs": runs,
                "stable": len({run["passed"] for run in runs}) <= 1,
            }
        suite = evaluator if isinstance(evaluator, (list, tuple)) else [evaluator]
        if not suite:
            suite = [evaluator]
        results: list[dict[str, Any]] = []
        for member in suite:
            try:
                raw = self._invoke_evaluator(member, record, trials=1)
                if inspect.isawaitable(raw):
                    close = getattr(raw, "close", None)
                    if callable(close):
                        close()
                    raise EvolutionContractError("asynchronous evaluators require a host adapter")
                results.append(
                    {
                        "passed": _passed_value(raw) and _result_is_json_safe(raw),
                        "result": _safe_result(raw),
                    }
                )
            except Exception as exc:  # evaluator boundary
                results.append(
                    {
                        "passed": False,
                        "error": {"type": type(exc).__name__, "message": str(exc)[:500]},
                    }
                )
        passed = bool(results) and all(item["passed"] for item in results)
        result: dict[str, Any] = {"name": name, "passed": passed}
        if len(results) == 1 and "result" in results[0]:
            result["result"] = results[0]["result"]
        else:
            result["checks"] = results
        return result

    def evaluate(
        self,
        candidate_id: str,
        evaluators: Mapping[str, Any] | None = None,
        *,
        deterministic: Any = None,
        repeated: Any = None,
        security: Any = None,
        regression: Any = None,
        trials: int | None = None,
        repetitions: int | None = None,
        trial_count: int | None = None,
        repeat_count: int | None = None,
        run_count: int | None = None,
        runs: int | None = None,
        deterministic_evaluator: Any = None,
        repeated_evaluator: Any = None,
        security_evaluator: Any = None,
        protected_regression: Any = None,
    ) -> CandidateRecord:
        """Run deterministic, repeated, and security evaluators.

        Every evaluator is attempted even when an earlier one fails, so the
        persisted audit trail explains all observed failures rather than only
        the first one.  A failed security/regression check is terminal until a
        new version is staged.
        """
        selected_trials = trials if trials is not None else repetitions
        if selected_trials is None:
            selected_trials = trial_count
        if selected_trials is None:
            selected_trials = repeat_count
        if selected_trials is None:
            selected_trials = run_count
        if selected_trials is None:
            selected_trials = runs
        if deterministic_evaluator is not None:
            deterministic = deterministic_evaluator
        if repeated_evaluator is not None:
            repeated = repeated_evaluator
        if security_evaluator is not None:
            security = security_evaluator
        if protected_regression is not None:
            regression = protected_regression
        with self._lock():
            record = self._load_candidate_unlocked(candidate_id)
            self._expire_if_due_unlocked(record)
            record = self._load_candidate_unlocked(candidate_id)
            if record.get("status") == "expired":
                raise CandidateExpired("candidate has expired")
            if record.get("status") in _TERMINAL_STATUSES or record.get("status") in {"approved", "published"}:
                raise InvalidCandidateTransition(f"candidate cannot be evaluated from {record.get('status')}")
            if record.get("status") not in {"staged", "evaluated"}:
                raise InvalidCandidateTransition(f"candidate cannot be evaluated from {record.get('status')}")
            # Resolve evaluators only after state validation.  An expired or
            # already terminal candidate must not be mutated merely because a
            # caller supplied an incomplete evaluator configuration.
            det, rep, sec, suite_trials = self._resolve_evaluators(
                evaluators,
                deterministic,
                repeated,
                security,
                regression,
            )
            if selected_trials is not None:
                if isinstance(selected_trials, bool) or not isinstance(selected_trials, int):
                    raise EvolutionContractError("trials must be an integer")
                suite_trials = selected_trials
            self._transition_unlocked(record, "evaluating", reason="evaluation_started")
            self._persist_candidate_unlocked(record)
            evaluating_record = copy.deepcopy(record)
            evaluation_revision = int(record.get("revision", 0))

        # Evaluators are injected host code and may inspect the store.  Run
        # them outside the mutation lock, then bind the result back only if no
        # other actor changed the candidate while the suite was running.
        checks = [
            self._run_check("deterministic", det, evaluating_record),
            self._run_check("repeated", rep, evaluating_record, trials=suite_trials or 3),
            self._run_check("security", sec, evaluating_record),
        ]
        passed = all(check["passed"] is True for check in checks)
        protected_failure = checks[2]["passed"] is not True
        with self._lock():
            current = self._load_candidate_unlocked(candidate_id)
            if current.get("status") != "evaluating" or int(current.get("revision", 0)) != evaluation_revision:
                raise InvalidCandidateTransition("candidate changed while evaluators were running")
            evaluation = {
                "status": "passed" if passed else "failed",
                "passed": passed,
                "checks": checks,
                "results": {check["name"]: check for check in checks},
                "deterministic": checks[0],
                "repeated": checks[1],
                "security": checks[2],
                "protected_regression": {
                    "passed": not protected_failure,
                    "failure": protected_failure,
                },
                "evaluated_at": self._now_text(),
            }
            evaluation["fingerprint"] = _fingerprint(
                {
                    "candidate_id": current["candidate_id"],
                    "version": current.get("version"),
                    "proposal_fingerprint": current.get("proposal_fingerprint"),
                    "checks": checks,
                }
            )
            current["evaluation"] = evaluation
            current["protected_regression_failure"] = protected_failure
            if passed:
                self._transition_unlocked(
                    current,
                    "evaluated",
                    reason="evaluators_passed",
                    evaluation=evaluation,
                    failure=None,
                )
            else:
                failure_codes = ["protected_regression_failure"] if protected_failure else ["evaluation_failed"]
                if protected_failure:
                    failure_codes.append("security_failed")
                failure = {
                    "code": failure_codes[0],
                    "codes": failure_codes,
                    "message": "one or more required evaluators failed",
                    "at": self._now_text(),
                }
                current["failure"] = failure
                self._transition_unlocked(
                    current,
                    "rejected",
                    reason=failure["code"],
                    clear_approval=True,
                    evaluation=evaluation,
                    failure=failure,
                )
            self._persist_candidate_unlocked(current)
            return current

    evaluate_candidate = evaluate
    run_evaluators = evaluate

    def _verify_evaluation_unlocked(self, record: CandidateRecord) -> None:
        evaluation = record.get("evaluation")
        if (
            record.get("status") not in {"evaluated", "approved", "published"}
            or not isinstance(evaluation, Mapping)
            or evaluation.get("passed") is not True
        ):
            failure = record.get("failure") or {}
            raise AdmissionRequired(
                "candidate requires a passing deterministic, repeated, and security evaluation"
                + (f": {failure.get('code')}" if failure.get("code") else "")
            )
        checks = evaluation.get("checks", [])
        if (
            not isinstance(checks, list)
            or len(checks) != 3
            or {
                item.get("name")
                for item in checks
                if isinstance(item, Mapping)
            }
            != {"deterministic", "repeated", "security"}
        ):
            raise AdmissionRequired("evaluation does not contain all required evaluator families")
        if any(item.get("passed") is not True for item in checks if isinstance(item, Mapping)):
            raise AdmissionRequired("one or more required evaluators did not pass")
        expected = _fingerprint(
            {
                "candidate_id": record["candidate_id"],
                "version": record.get("version"),
                "proposal_fingerprint": record.get("proposal_fingerprint"),
                "checks": checks,
            }
        )
        if evaluation.get("fingerprint") != expected:
            raise AdmissionRequired("evaluation evidence fingerprint does not match the candidate")

    def admit(
        self,
        candidate_id: str,
        actor: str | None = None,
        approved_by: str | None = None,
        explicit: bool = True,
        approved: bool | None = None,
        approval: bool | Mapping[str, Any] | None = None,
        *,
        reason: str | None = None,
        admission_id: str | None = None,
        scope: str = "global",
        approver: str | None = None,
        confirmation: bool | None = None,
        confirmed: bool | None = None,
        version: int | None = None,
    ) -> CandidateRecord:
        """Explicitly admit a fully evaluated candidate for publication.

        This method does not publish anything.  It creates a durable approval
        bound to the proposal and evaluation fingerprints; a later publisher
        must still call :meth:`publish` (or ``publish_global``).
        """
        if isinstance(actor, bool) and approved is None:
            approved = actor
            actor = None
        if isinstance(approved_by, bool) and approved is None:
            approved = approved_by
            approved_by = None
        if isinstance(actor, Mapping) and approval is None:
            approval = actor
            actor = None
        if isinstance(approved_by, Mapping) and approval is None:
            approval = approved_by
            approved_by = None
        if isinstance(approval, Mapping):
            approval_data = dict(approval)
            actor = actor or approved_by or approver or approval_data.get("actor") or approval_data.get("approved_by")
            if "explicit" in approval_data:
                explicit = approval_data["explicit"]
            if "approved" in approval_data:
                approved = approval_data["approved"]
            reason = reason or approval_data.get("reason")
        elif approval is not None:
            approved = approval
        if confirmation is not None:
            explicit = confirmation
        if confirmed is not None:
            explicit = confirmed
        actor = actor or approved_by or approver
        if explicit is not True:
            raise AdmissionRequired("explicit admission is required")
        if approved is not None and approved is not True:
            raise AdmissionRequired("candidate approval must be explicitly true")
        if not isinstance(actor, str) or not actor.strip():
            raise AdmissionRequired("an explicit approver is required")
        actor = _text(actor, "explicit approver")
        if reason is not None:
            _text(reason, "admission reason")
        if scope != "global":
            raise EvolutionContractError("evolution admission currently supports global scope only")
        with self._lock():
            record = self._load_candidate_unlocked(candidate_id)
            self._expire_if_due_unlocked(record)
            record = self._load_candidate_unlocked(candidate_id)
            if record.get("status") == "expired":
                raise CandidateExpired("candidate has expired")
            if version is not None and version != record.get("version"):
                raise AdmissionRequired("admission is bound to a different candidate version")
            self._verify_evaluation_unlocked(record)
            admission_id = _validate_identifier(
                admission_id or f"admission-{uuid.uuid4().hex[:16]}",
                "admission_id",
            )
            admission = {
                "admission_id": admission_id,
                "candidate_id": record["candidate_id"],
                "version": record.get("version"),
                "scope": "global",
                "status": "admitted",
                "decision": "admit",
                "approved_by": actor,
                "explicit": True,
                "approved": True,
                "reason": reason,
                "at": self._now_text(),
                "proposal_fingerprint": record.get("proposal_fingerprint"),
                "source_fingerprint": record.get("source_fingerprint"),
                "evidence_fingerprint": record.get("evidence_fingerprint"),
                "diff_fingerprint": record.get("diff_fingerprint"),
                "rollback_fingerprint": record.get("rollback_fingerprint"),
                "evaluation_fingerprint": record.get("evaluation", {}).get("fingerprint"),
            }
            if record.get("status") == "approved":
                existing = record.get("admission") or {}
                if (
                    existing.get("approved_by") == actor
                    and existing.get("proposal_fingerprint") == record.get("proposal_fingerprint")
                    and existing.get("evaluation_fingerprint") == record.get("evaluation", {}).get("fingerprint")
                ):
                    return record
                raise AdmissionRequired("candidate already has a different admission")
            self._transition_unlocked(
                record,
                "approved",
                reason="explicit_admission",
                actor=actor,
                admission=admission,
                approval=admission,
                admission_state="admitted",
                admitted=True,
                approved=True,
                status_aliases=["approved", "admitted"],
                approved_by=actor,
                approved_at=admission["at"],
                failure=None,
            )
            self._persist_candidate_unlocked(record)
            return record

    admit_candidate = admit
    approve_candidate = admit

    def approve(
        self,
        candidate_id: str,
        approved_by: str | None = None,
        approved: bool | None = None,
        *,
        actor: str | None = None,
        approver: str | None = None,
        explicit: bool = True,
        confirmation: bool | None = None,
        confirmed: bool | None = None,
        **kwargs: Any,
    ) -> CandidateRecord:
        effective_explicit = explicit
        if confirmation is not None:
            effective_explicit = confirmation
        elif confirmed is not None:
            effective_explicit = confirmed
        return self.admit(
            candidate_id,
            actor=actor or approved_by or approver,
            approved_by=approved_by or approver,
            approved=approved,
            explicit=effective_explicit,
            **kwargs,
        )

    def _verify_admission_unlocked(self, record: CandidateRecord, *, actor: str | None = None) -> dict[str, Any]:
        if record.get("status") not in {"approved", "published"}:
            raise AdmissionRequired("candidate has not been explicitly admitted")
        admission = record.get("admission")
        if (
            not isinstance(admission, Mapping)
            or admission.get("explicit") is not True
            or admission.get("approved") is not True
        ):
            raise AdmissionRequired("candidate admission record is missing or invalid")
        if (
            admission.get("candidate_id") != record.get("candidate_id")
            or admission.get("version") != record.get("version")
        ):
            raise AdmissionRequired("candidate admission is bound to another version")
        if admission.get("proposal_fingerprint") != record.get("proposal_fingerprint"):
            raise AdmissionRequired("candidate proposal changed after admission")
        for fingerprint_key in (
            "source_fingerprint",
            "evidence_fingerprint",
            "diff_fingerprint",
            "rollback_fingerprint",
        ):
            if admission.get(fingerprint_key) != record.get(fingerprint_key):
                raise AdmissionRequired("candidate metadata changed after admission")
        if admission.get("evaluation_fingerprint") != record.get("evaluation", {}).get("fingerprint"):
            raise AdmissionRequired("candidate evaluation changed after admission")
        # Admission and publication may be performed by separate host roles;
        # both identities are recorded, but neither can replace the other's
        # signed decision.
        return dict(admission)

    def publish(
        self,
        candidate_id: str,
        actor: str | None = None,
        *,
        approved_by: str | None = None,
        explicit: bool = True,
        confirmed: bool | None = None,
        scope: str = "global",
        target: Any = None,
        publication_id: str | None = None,
        reason: str | None = None,
        approved: bool | None = None,
        approval: Mapping[str, Any] | None = None,
        admission: Mapping[str, Any] | None = None,
        admission_id: str | None = None,
        approver: str | None = None,
        global_publication: bool | None = None,
        confirmation: bool | None = None,
        version: int | None = None,
    ) -> CandidateRecord:
        """Create a memory-only global publication receipt.

        This method intentionally has no publisher callback and performs no
        canonical filesystem mutation.  The receipt is the hand-off artifact
        for a separately governed host publisher.
        """
        if confirmed is False or confirmation is False:
            raise AdmissionRequired("publication confirmation is required")
        if explicit is not True:
            raise AdmissionRequired("explicit publication is required")
        if approved is False:
            raise AdmissionRequired("publication approval must be explicitly true")
        if global_publication is False:
            raise AdmissionRequired("global publication cannot be disabled")
        if scope != "global":
            raise EvolutionContractError("only global publication is supported by this store")
        if reason is not None:
            _text(reason, "publication reason")
        if approval is None and admission is not None:
            approval = admission
        if approval is not None and admission is not None and approval != admission:
            raise AdmissionRequired("approval and admission records disagree")
        if isinstance(actor, bool) and approved is None:
            approved = actor
            actor = None
        if isinstance(approved_by, bool) and approved is None:
            approved = approved_by
            approved_by = None
        if isinstance(actor, Mapping) and approval is None:
            approval = actor
            actor = None
        if isinstance(approved_by, Mapping) and approval is None:
            approval = approved_by
            approved_by = None
        actor = actor or approved_by or approver
        if isinstance(approval, Mapping):
            supplied = dict(approval)
            if supplied.get("explicit") is not True or supplied.get("approved") is not True:
                raise AdmissionRequired("supplied publication approval is not explicit")
        elif approval is not None:
            raise AdmissionRequired("publication approval must be an admission object")
        target_value = _safe_relative_target(target, "publication target")
        with self._lock():
            record = self._load_candidate_unlocked(candidate_id)
            self._expire_if_due_unlocked(record)
            record = self._load_candidate_unlocked(candidate_id)
            if record.get("status") == "expired":
                raise CandidateExpired("candidate has expired")
            if version is not None and version != record.get("version"):
                raise AdmissionRequired("publication is bound to a different candidate version")
            if record.get("status") == "published":
                existing = record.get("publication") or {}
                existing_receipt = self.publications_dir / f"{existing.get('publication_id', '')}.json"
                if record.get("version") == existing.get("version") and existing_receipt.is_file():
                    return record
                if record.get("version") == existing.get("version"):
                    raise EvolutionContractError("publication receipt is missing or invalid")
                raise AdmissionRequired("a different version is already published")
            admission = self._verify_admission_unlocked(record, actor=actor)
            if admission_id is not None and admission_id != admission.get("admission_id"):
                raise AdmissionRequired("publication is bound to a different admission")
            if isinstance(approval, Mapping):
                supplied = dict(approval)
                for key in ("admission_id", "proposal_fingerprint", "evaluation_fingerprint"):
                    if supplied.get(key) is not None and supplied.get(key) != admission.get(key):
                        raise AdmissionRequired("supplied publication approval is stale")
            publication_id = _validate_identifier(
                publication_id or f"publication-{uuid.uuid4().hex[:16]}",
                "publication_id",
            )
            metadata = record.get("proposal", {}).get("metadata", {})
            declared_target = target_value
            if declared_target is None:
                target_sources = (metadata, record.get("diff"), record.get("rollback"))
                for source_value in target_sources:
                    declared_target = _find_target(source_value)
                    if declared_target is not None:
                        break
            receipt_path = self.publications_dir / f"{publication_id}.json"
            if receipt_path.exists():
                raise EvolutionContractError(f"publication receipt already exists: {publication_id}")
            publication = {
                "publication_id": publication_id,
                "candidate_id": record["candidate_id"],
                "version": record.get("version"),
                "scope": "global",
                "status": "published",
                "admission_id": admission.get("admission_id"),
                "approved_by": admission.get("approved_by"),
                "published_by": actor,
                "proposal_fingerprint": record.get("proposal_fingerprint"),
                "source_fingerprint": record.get("source_fingerprint"),
                "evidence_fingerprint": record.get("evidence_fingerprint"),
                "diff_fingerprint": record.get("diff_fingerprint"),
                "rollback_fingerprint": record.get("rollback_fingerprint"),
                "evaluation_fingerprint": record.get("evaluation", {}).get("fingerprint"),
                "canonical_target": declared_target,
                "staged_artifact": f"candidates/{record['candidate_id']}.json",
                "canonical_write": False,
                "publication_mode": PUBLICATION_MODE,
                "reason": reason,
                "published_at": self._now_text(),
            }
            self._write_json_unlocked(
                self.publications_dir / f"{publication_id}.json",
                publication,
            )
            version_entry = {
                "version": record.get("version"),
                "status": "published",
                "publication_id": publication_id,
                "admission_id": admission.get("admission_id"),
                "at": publication["published_at"],
            }
            history = list(record.get("version_history", []))
            history.append(version_entry)
            self._transition_unlocked(
                record,
                "published",
                reason="global_publication_receipt_created",
                actor=actor,
                publication=publication,
                published_version=record.get("version"),
                global_published=True,
                active=True,
                active_version=record.get("version"),
                version_history=history,
            )
            record["canonical_write_performed"] = False
            self._persist_candidate_unlocked(record)
            return record

    publish_candidate = publish

    def publish_global(self, candidate_id: str, actor: str | None = None, **kwargs: Any) -> CandidateRecord:
        kwargs["scope"] = "global"
        return self.publish(candidate_id, actor=actor, **kwargs)

    publish_globally = publish_global
    admit_for_publication = admit

    def reject(
        self,
        candidate_id: str,
        reason: str = "manual_rejection",
        actor: str | None = None,
    ) -> CandidateRecord:
        reason = _text(reason, "rejection reason")
        if actor is not None:
            _text(actor, "actor")
        with self._lock():
            record = self._load_candidate_unlocked(candidate_id)
            self._expire_if_due_unlocked(record)
            record = self._load_candidate_unlocked(candidate_id)
            if record.get("status") in _TERMINAL_STATUSES:
                if record.get("status") == "rejected":
                    return record
                if record.get("status") == "expired":
                    raise CandidateExpired("candidate has expired")
                raise InvalidCandidateTransition(f"candidate cannot be rejected from {record.get('status')}")
            if record.get("status") == "published":
                raise InvalidCandidateTransition("published candidates must be rolled back before rejection")
            failure = {"code": "rejected", "message": reason, "at": self._now_text()}
            record["failure"] = failure
            self._transition_unlocked(
                record,
                "rejected",
                reason=reason,
                actor=actor,
                clear_approval=True,
                failure=failure,
            )
            self._persist_candidate_unlocked(record)
            return record

    reject_candidate = reject

    def expire(
        self,
        candidate_id: str,
        reason: str = "ttl_expired",
        at: Any = None,
        *,
        now: Any = None,
        actor: str | None = None,
    ) -> CandidateRecord:
        reason = _text(reason, "expiration reason")
        moment = _parse_timestamp(at if at is not None else now if now is not None else self._now_text(), "at")
        with self._lock():
            record = self._load_candidate_unlocked(candidate_id)
            if record.get("status") == "expired":
                return record
            if record.get("status") == "rolled_back":
                raise InvalidCandidateTransition("rolled-back candidates cannot expire")
            self._transition_unlocked(
                record,
                "expired",
                reason=reason,
                actor=actor,
                clear_approval=True,
                expiration={"expired_at": moment, "scheduled_at": record.get("expires_at"), "reason": reason},
            )
            self._persist_candidate_unlocked(record)
            return record

    expire_candidate = expire

    def expire_due(self, *, now: Any = None, at: Any = None) -> list[CandidateRecord]:
        """Expire all candidates whose TTL has elapsed and return their records."""
        moment = (
            _parse_timestamp(now if now is not None else at, "now")
            if (now is not None or at is not None)
            else None
        )
        with self._lock():
            result: list[CandidateRecord] = []
            for path in sorted(self.candidates_dir.glob("*.json")):
                record = self._load_candidate_unlocked(path.stem)
                if self._expire_if_due_unlocked(record, at=moment):
                    result.append(self._load_candidate_unlocked(path.stem))
            return result

    def rollback(
        self,
        candidate_id: str,
        target_version: int | None = None,
        *,
        rollback_to: int | None = None,
        reason: str = "manual_rollback",
        actor: str | None = None,
        explicit: bool = True,
        version: int | None = None,
        to_version: int | None = None,
        to: int | None = None,
        target_candidate_id: str | None = None,
    ) -> CandidateRecord:
        """Withdraw a candidate/publication without restoring canonical files."""
        if explicit is not True:
            raise AdmissionRequired("explicit rollback is required")
        if target_version is None:
            target_version = rollback_to
        if target_version is None:
            target_version = version
        if target_version is None:
            target_version = to_version
        if target_version is None:
            target_version = to
        reason = _text(reason, "rollback reason")
        if actor is not None:
            _text(actor, "actor")
        if target_version is not None:
            if isinstance(target_version, bool) or not isinstance(target_version, int) or target_version < 0:
                raise EvolutionContractError("target_version must be a non-negative integer")
        with self._lock():
            record = self._load_candidate_unlocked(candidate_id)
            self._expire_if_due_unlocked(record)
            record = self._load_candidate_unlocked(candidate_id)
            if record.get("status") == "rolled_back":
                return record
            if record.get("status") == "expired":
                raise CandidateExpired("candidate has expired")
            if record.get("status") == "rejected":
                raise InvalidCandidateTransition(f"candidate cannot roll back from {record.get('status')}")
            current_version = int(record.get("version", 1))
            target_record: CandidateRecord | None = None
            explicit_target = target_candidate_id is not None
            if target_candidate_id is not None:
                target_candidate_id = _validate_identifier(target_candidate_id, "target_candidate_id")
                target_record = self._load_candidate_unlocked(target_candidate_id)
                if target_record.get("lineage_id") != record.get("lineage_id"):
                    raise EvolutionContractError("rollback target belongs to another lineage")
                if target_version is not None and target_version != target_record.get("version"):
                    raise EvolutionContractError("rollback target version and candidate disagree")
                target_version = int(target_record.get("version", 0))
            if target_version is None:
                prior = [
                    item.get("version")
                    for item in record.get("version_history", [])
                    if (
                        isinstance(item, Mapping)
                        and isinstance(item.get("version"), int)
                        and item["version"] < current_version
                    )
                ]
                target_version = max(prior) if prior else (current_version - 1 if current_version > 1 else 0)
            if target_version >= current_version:
                raise EvolutionContractError("rollback target must be older than the current version")
            if not explicit_target:
                target_candidate_id = None
                for path in sorted(self.candidates_dir.glob("*.json")):
                    if path.stem == candidate_id:
                        continue
                    try:
                        candidate = self._load_candidate_unlocked(path.stem)
                    except EvolutionContractError:
                        continue
                    if (
                        candidate.get("lineage_id") == record.get("lineage_id")
                        and candidate.get("version") == target_version
                    ):
                        target_candidate_id = candidate["candidate_id"]
                        target_record = candidate
                        break
            rollback_id = f"rollback-{uuid.uuid4().hex[:16]}"
            receipt = {
                "rollback_id": rollback_id,
                "candidate_id": record["candidate_id"],
                "from_version": current_version,
                "from_publication_id": (record.get("publication") or {}).get("publication_id"),
                "target_version": target_version,
                "restored_version": target_version,
                "target_candidate_id": target_candidate_id,
                "proposal_fingerprint": record.get("proposal_fingerprint"),
                "rollback": copy.deepcopy(record.get("rollback")),
                "reason": reason,
                "actor": actor,
                "at": self._now_text(),
                "canonical_write": False,
                "publication_mode": PUBLICATION_MODE,
            }
            self._write_json_unlocked(self.rollbacks_dir / f"{rollback_id}.json", receipt)
            history = list(record.get("rollback_history", []))
            history.append(receipt)
            version_history = list(record.get("version_history", []))
            version_history.append(
                {
                    "version": current_version,
                    "status": "rolled_back",
                    "rollback_id": rollback_id,
                    "target_version": target_version,
                    "at": receipt["at"],
                }
            )
            self._transition_unlocked(
                record,
                "rolled_back",
                reason=reason,
                actor=actor,
                clear_approval=True,
                rollback_receipt=receipt,
                rollback_history=history,
                version_history=version_history,
                active_version=target_version,
                active=False,
                global_published=False,
                rolled_back_from_version=current_version,
                canonical_write_performed=False,
            )
            self._persist_candidate_unlocked(record)
            if target_record is not None:
                target_record["active"] = True
                target_record["active_version"] = target_version
                target_record["updated_at"] = self._now_text()
                self._persist_candidate_unlocked(target_record)
            return record

    rollback_candidate = rollback

    def create_version(
        self,
        candidate_id: str,
        proposal: Mapping[str, Any] | None = None,
        *,
        candidate_id_new: str | None = None,
        version: int | None = None,
        actor: str | None = None,
        **changes: Any,
    ) -> CandidateRecord:
        """Create a staged child candidate at the next immutable version."""
        # Do not call ``stage`` while holding this store's POSIX lock: flock is
        # not guaranteed to be re-entrant across separate open file handles.
        changes = dict(changes)
        nested_changes = changes.pop("changes", None)
        if nested_changes is not None:
            if not isinstance(nested_changes, Mapping):
                raise EvolutionContractError("changes must be an object")
            changes.update(nested_changes)
        with self._lock():
            parent = self._load_candidate_unlocked(candidate_id)
            self._expire_if_due_unlocked(parent)
            parent = self._load_candidate_unlocked(candidate_id)
            if proposal is None:
                proposal_data = copy.deepcopy(parent.get("proposal", {}))
            else:
                if not isinstance(proposal, Mapping):
                    raise EvolutionContractError("proposal must be an object")
                proposal_data = copy.deepcopy(dict(proposal))
            if changes:
                proposal_data.update(copy.deepcopy(changes))
            parent_version = int(parent.get("version", 1))

        source = proposal_data.get("source")
        evidence = proposal_data.get("evidence")
        diff = proposal_data.get("diff")
        rollback = proposal_data.get("rollback")
        metadata = proposal_data.get("metadata", {})
        if not isinstance(metadata, Mapping):
            metadata = {}
        metadata = dict(metadata)
        for key, value in proposal_data.items():
            if key not in {"source", "evidence", "diff", "rollback", "metadata"}:
                metadata[key] = value
        # ``proposal`` includes normalized metadata; preserve it when no
        # explicit top-level changes were supplied.
        stage_proposal = {
            "source": source,
            "evidence": evidence,
            "diff": diff,
            "rollback": rollback,
            **{str(k): v for k, v in metadata.items() if k not in {"source", "evidence", "diff", "rollback"}},
        }
        stage_proposal.update({k: v for k, v in changes.items() if k in {"source", "evidence", "diff", "rollback"}})
        if version is not None and version != parent_version + 1:
            raise EvolutionContractError("child version must immediately follow its parent")
        child = self.stage(
            stage_proposal,
            candidate_id=candidate_id_new,
            parent_id=candidate_id,
            version=parent_version + 1,
            actor=actor,
        )
        with self._lock():
            parent = self._load_candidate_unlocked(candidate_id)
            children = list(parent.get("children", []))
            if child["candidate_id"] not in children:
                children.append(child["candidate_id"])
                parent["children"] = children
                self._event_unlocked(
                    parent,
                    "version_staged",
                    reason="child_version_staged",
                    actor=actor,
                    child_candidate_id=child["candidate_id"],
                    child_version=child.get("version"),
                )
            self._persist_candidate_unlocked(parent)
        return child

    new_version = create_version
    revise = create_version
    version_candidate = create_version

    def version(self, candidate_id: str) -> int:
        return int(self.get_candidate(candidate_id).get("version", 1))

    current_version = version

    def lineage(self, candidate_id: str) -> list[CandidateRecord]:
        """Return all persisted versions in a candidate's lineage, oldest first."""
        root = self.get_candidate(candidate_id)
        with self._lock():
            records: list[CandidateRecord] = []
            for path in self.candidates_dir.glob("*.json"):
                candidate = self._load_candidate_unlocked(path.stem)
                if candidate.get("lineage_id") == root.get("lineage_id"):
                    records.append(candidate)
            records.sort(key=lambda item: (int(item.get("version", 1)), item.get("candidate_id", "")))
            return records

    def publication_receipt(self, candidate_id: str) -> dict[str, Any]:
        receipts = self.publications(candidate_id)
        if not receipts:
            raise CandidateNotFound(f"no publication receipt for candidate: {candidate_id}")
        return receipts[-1]

    get_publication = publication_receipt

    def publications(self, candidate_id: str | None = None) -> list[dict[str, Any]]:
        if candidate_id is not None:
            candidate_id = _validate_identifier(candidate_id)
        with self._lock():
            paths = sorted(self.publications_dir.glob("*.json"))
            result: list[dict[str, Any]] = []
            for path in paths:
                value = self._read_json_unlocked(path, "publication receipt")
                if candidate_id is None or value.get("candidate_id") == candidate_id:
                    result.append(value)
            result.sort(
                key=lambda item: (
                    str(item.get("published_at", "")),
                    str(item.get("publication_id", "")),
                )
            )
            return result

    def rollbacks(self, candidate_id: str | None = None) -> list[dict[str, Any]]:
        if candidate_id is not None:
            candidate_id = _validate_identifier(candidate_id)
        with self._lock():
            result: list[dict[str, Any]] = []
            for path in sorted(self.rollbacks_dir.glob("*.json")):
                value = self._read_json_unlocked(path, "rollback receipt")
                if candidate_id is None or value.get("candidate_id") == candidate_id:
                    result.append(value)
            result.sort(
                key=lambda item: (
                    str(item.get("at", "")),
                    str(item.get("rollback_id", "")),
                )
            )
            return result

    def events(self, candidate_id: str | None = None) -> list[dict[str, Any]]:
        if candidate_id is not None:
            candidate_id = _validate_identifier(candidate_id)
        if not self.events_path.exists():
            return []
        result: list[dict[str, Any]] = []
        with open(self.events_path, encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict) and (candidate_id is None or value.get("candidate_id") == candidate_id):
                    result.append(value)
        return result

    audit_log = events

    def can_publish(self, candidate_id: str) -> bool:
        try:
            with self._lock():
                record = self._load_candidate_unlocked(candidate_id)
                self._expire_if_due_unlocked(record)
                record = self._load_candidate_unlocked(candidate_id)
                self._verify_evaluation_unlocked(record)
                self._verify_admission_unlocked(record)
                if record.get("status") == "published":
                    publication = record.get("publication") or {}
                    receipt = self.publications_dir / f"{publication.get('publication_id', '')}.json"
                    if not receipt.is_file():
                        return False
                return True
        except (EvolutionError, OSError, ValueError):
            return False


# Compatibility/factory names for hosts that call this component a manager or
# lifecycle rather than a store.
EvolutionManager = EvolutionStore
GovernedEvolution = EvolutionStore
SelfEvolutionStore = EvolutionStore
CandidateLifecycle = EvolutionStore
EvolutionLifecycle = EvolutionStore


def create_store(project_root: str | Path, **kwargs: Any) -> EvolutionStore:
    """Construct an :class:`EvolutionStore` without importing host services."""
    return EvolutionStore(project_root, **kwargs)


__all__ = [
    "ADMITTED",
    "APPROVED",
    "AdmissionRequired",
    "ApprovalRequired",
    "CANONICAL_WRITE_POLICY",
    "Candidate",
    "CandidateExpired",
    "CandidateLifecycle",
    "CandidateNotFound",
    "CandidateRecord",
    "ContractError",
    "EVALUATED",
    "EVALUATING",
    "EXPIRED",
    "EvaluatorSet",
    "EvolutionCandidate",
    "EvolutionContractError",
    "EvolutionError",
    "EvolutionLifecycle",
    "EvolutionManager",
    "EvolutionStore",
    "GovernedEvolution",
    "InvalidCandidateTransition",
    "InvalidTransition",
    "PUBLISHED",
    "PUBLICATION_MODE",
    "REJECTED",
    "ROLLED_BACK",
    "SCHEMA_VERSION",
    "STAGED",
    "SelfEvolutionError",
    "STATUS_ADMITTED",
    "STATUS_APPROVED",
    "STATUS_EVALUATED",
    "STATUS_EVALUATING",
    "STATUS_EXPIRED",
    "STATUS_PUBLISHED",
    "STATUS_REJECTED",
    "STATUS_ROLLED_BACK",
    "STATUS_STAGED",
    "SelfEvolutionStore",
    "create_store",
]

"""Deterministic, dependency-free task and new-question routing.

This module is a small host-side guardrail.  It classifies an incoming message
into one of a deliberately finite set of actions:

``continuation``
    Keep working on the currently active task.
``clarification``
    Ask the host/user for a disambiguating answer; do not execute the task.
``new_task``
    Allocate a new task identity, linked to the active task when there is one.
``abandon``
    Explicitly stop the active task without creating a child task.
``unknown``
    The text is not sufficiently grounded to choose safely.  This is a
    fail-closed result, not a guess and not permission to execute.

The classifier is intentionally conservative and lexical.  It never imports a
model adapter, provider, browser, shell, or network client.  A host can supply
structured ``explicit_decision``/``signals`` when it has a stronger, auditable
intent signal, but an absent or conflicting signal never becomes a continuation
or a new task by default.

The module is independent of :mod:`runtime.core.engine` and
:mod:`runtime.core.state`.  Persistence is supplied through a small JSON store
or through ``load_hook``/``save_hook`` callbacks, which lets a Runtime host wire
the result into its own durable state without importing a provider or requiring
this module to own the task database.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import json
import os
import re
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol, Sequence

from .redaction import redact_sensitive


try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None


ROUTER_SCHEMA_VERSION = "1.0"
ROUTER_VERSION = "1.0"
DEFAULT_MIN_CONFIDENCE = 0.72
DEFAULT_MAX_TEXT_CHARS = 100_000
MAX_METADATA_CHARS = 64_000
DEFAULT_ROUTE_FILENAME = Path(".memory") / "ultimate-dev" / "task-routes.json"
DEFAULT_MAX_ROUTE_RECORDS = 10_000
DEFAULT_MAX_ROUTE_BYTES = 8 * 1024 * 1024
DEFAULT_ROUTE_TTL_SECONDS = 30 * 24 * 60 * 60

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)
_WHITESPACE_RE = re.compile(r"\s+", re.UNICODE)
_DIGEST_RE = re.compile(r"^[a-f0-9]{64}$")

# Common words carry little task identity.  Keeping the list small makes the
# overlap calculation predictable and avoids pretending to be a semantic model.
_STOP_WORDS = frozenset(
    {
        "a",
        "about",
        "after",
        "again",
        "all",
        "also",
        "an",
        "and",
        "any",
        "are",
        "as",
        "at",
        "be",
        "been",
        "before",
        "being",
        "but",
        "by",
        "can",
        "could",
        "do",
        "does",
        "for",
        "from",
        "get",
        "had",
        "has",
        "have",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "just",
        "me",
        "more",
        "my",
        "need",
        "of",
        "on",
        "or",
        "our",
        "please",
        "should",
        "so",
        "some",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "these",
        "this",
        "those",
        "task",
        "tasks",
        "work",
        "request",
        "project",
        "item",
        "question",
        "feature",
        "change",
        "to",
        "too",
        "us",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "will",
        "with",
        "would",
        "you",
        "your",
    }
)

# Explicit intent markers have higher authority than generic action verbs.
_CLARIFICATION_PATTERNS = (
    re.compile(r"\b(?:can|could|would)\s+you\s+(?:please\s+)?(?:clarify|explain|confirm|specify)\b", re.I),
    re.compile(r"\bwhat\s+do\s+you\s+mean\b", re.I),
    re.compile(r"\bwhat\s+did\s+you\s+mean\b", re.I),
    re.compile(r"\bwhat\s+you\s+mean\b", re.I),
    re.compile(r"\bwhat\s+(?:does|do|did)\s+(?:this|that|it)\s+mean\b", re.I),
    re.compile(r"\bwhat\s+exactly\b", re.I),
    re.compile(r"\b(?:please\s+)?clarify\b", re.I),
    re.compile(r"\b(?:need|request|want)\s+(?:a\s+)?clarification\b", re.I),
    re.compile(r"\b(?:i|we)\s+(?:am|are)\s+(?:not\s+sure|unsure)\b", re.I),
    re.compile(r"\b(?:this|that|it)\s+(?:is|seems)\s+(?:unclear|ambiguous)\b", re.I),
    re.compile(r"\bwhich\s+(?:one|option|approach|version)\b", re.I),
    re.compile(r"\bdo\s+you\s+want\s+me\s+to\b", re.I),
    re.compile(r"\bshould\s+i\b", re.I),
    re.compile(r"\bcan\s+you\s+be\s+more\s+specific\b", re.I),
)

_ABANDON_PATTERNS = (
    re.compile(r"\b(?:cancel|stop|abandon|discard|forget|end|halt|quit)\s+(?:this|the\s+current|that)\s+(?:task|work|job|request|question|plan|item|change)\b", re.I),
    re.compile(r"\bstop\s+working\s+on\s+(?:this|the\s+current|that)\b", re.I),
    re.compile(r"\b(?:cancel|abandon|discard)\s+(?:it|this\s+work|this\s+request)\b", re.I),
    re.compile(r"\bi\s+(?:want\s+to\s+)?abandon\s+(?:this|it)\b", re.I),
)

_NEW_TASK_PATTERNS = (
    re.compile(r"\b(?:new|another|separate|different|unrelated|second|next)\s+(?:task|question|request|feature|item|project|piece\s+of\s+work)\b", re.I),
    re.compile(r"\bstart\s+(?:a|an|the)?\s*(?:new|another|different|separate)\s+(?:task|question|request|project|piece\s+of\s+work)\b", re.I),
    re.compile(r"\b(?:switch|move)\s+to\s+(?:a|an|the)?\s*(?:new|another|different|separate)\s+(?:task|question|request|project)\b", re.I),
    re.compile(r"\bactually\s*,?\s+(?:i|we)\s+(?:need|want|have)\s+(?:to\s+)?(?:build|create|implement|add|update|fix|write|design|research|compare|review|test|document)\b", re.I),
    re.compile(r"\bby\s+the\s+way\s*,?\s*(?:i|we)\s+(?:need|want|have)\s+(?:to\s+)?(?:build|create|implement|add|update|fix|write|design|research|compare|review|test|document)\b", re.I),
)

_CONTINUATION_PATTERNS = (
    re.compile(r"\b(?:continue|resume|proceed|carry\s+on|keep\s+going|go\s+ahead)\b", re.I),
    re.compile(r"\b(?:next\s+step|and\s+then|in\s+addition|as\s+well\s+as|also)\b", re.I),
    re.compile(r"\b(?:make|change|update|fix)\s+(?:it|this|that)\b", re.I),
    re.compile(r"\b(?:it|this|that)\s+(?:should|must|needs?)\b", re.I),
    re.compile(r"\bwhat\s+about\s+(?:the\s+)?[A-Za-z0-9_-]+", re.I),
)

# These verbs are useful only as supporting evidence.  An action verb without
# a grounded task identity is not sufficient to invent a route.
_ACTION_RE = re.compile(
    r"\b(?:add|build|create|implement|fix|update|write|design|refactor|test|debug|"
    r"investigate|research|compare|review|deploy|document|migrate|optimize|install|"
    r"generate|remove|delete|explain|plan|analy[sz]e|benchmark|profile)\b",
    re.I,
)
_HEDGE_RE = re.compile(r"\b(?:maybe|perhaps|possibly|not\s+sure|unsure|somehow)\b", re.I)


class TaskRouterError(ValueError):
    """Base error for invalid router configuration or metadata."""


class RoutePersistenceError(TaskRouterError):
    """Raised by a persistence implementation when its backing store is unusable."""


class RouteDecision(str, Enum):
    """The finite set of safe routing outcomes."""

    CONTINUATION = "continuation"
    CLARIFICATION = "clarification"
    NEW_TASK = "new_task"
    ABANDON = "abandon"
    UNKNOWN = "unknown"

    # Friendly aliases make the enum pleasant to use without changing the
    # canonical wire values.
    CONTINUE = "continuation"
    CLARIFY = "clarification"
    NEW = "new_task"
    NEW_QUESTION = "new_task"
    CANCEL = "abandon"
    STOP = "abandon"
    AMBIGUOUS = "unknown"


# Names used by different Runtime generations; keeping aliases here avoids
# forcing an integration to wrap a trivial enum spelling change.
RoutingDecision = RouteDecision
RouteAction = RouteDecision
RouteDecisionType = RouteDecision
ROUTE_ACTIONS = {
    "continue": RouteDecision.CONTINUATION,
    "clarify": RouteDecision.CLARIFICATION,
    "new_task": RouteDecision.NEW_TASK,
    "abandon": RouteDecision.ABANDON,
    "unknown": RouteDecision.UNKNOWN,
}


@dataclass(frozen=True)
class TaskContext:
    """The minimum durable identity and text needed for safe routing."""

    task_id: str
    goal: str = ""
    summary: str = ""
    description: str = ""
    keywords: tuple[str, ...] = ()
    parent_task_id: str | None = None
    status: str | None = None

    def __post_init__(self) -> None:
        task_id = _validate_identifier(self.task_id, "task_id")
        parent = self.parent_task_id
        if parent is not None:
            parent = _validate_identifier(parent, "parent_task_id")
            if parent == task_id:
                raise TaskRouterError("a task cannot be its own parent")
        object.__setattr__(self, "task_id", task_id)
        object.__setattr__(self, "parent_task_id", parent)
        object.__setattr__(self, "goal", _optional_text(self.goal, "goal"))
        object.__setattr__(self, "summary", _optional_text(self.summary, "summary"))
        object.__setattr__(self, "description", _optional_text(self.description, "description"))
        if self.status is not None:
            if not isinstance(self.status, str) or not self.status.strip() or len(self.status) > 64:
                raise TaskRouterError("status must be a bounded string")
            object.__setattr__(self, "status", self.status.strip().lower())
        if isinstance(self.keywords, str):
            values = tuple(item for item in re.split(r"[,\n]+", self.keywords) if item.strip())
        else:
            try:
                values = tuple(str(item).strip() for item in self.keywords if str(item).strip())
            except TypeError as exc:
                raise TaskRouterError("keywords must be a string or iterable of strings") from exc
        object.__setattr__(self, "keywords", tuple(dict.fromkeys(values)))

    @property
    def text(self) -> str:
        return " ".join(part for part in (self.goal, self.summary, self.description) if part).strip()

    @property
    def parent_id(self) -> str | None:
        return self.parent_task_id

    @property
    def descriptor(self) -> dict[str, Any]:
        """A bounded, JSON-safe identity used for route-cache keys."""

        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "summary": self.summary,
            "description": self.description,
            "keywords": list(self.keywords),
            "parent_task_id": self.parent_task_id,
            "status": self.status,
        }

    @classmethod
    def from_value(cls, value: Any) -> "TaskContext":
        """Coerce a Runtime state, mapping, ID, or context object into a context."""

        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls(task_id=value)
        if isinstance(value, Mapping):
            nested = value.get("contract") if isinstance(value.get("contract"), Mapping) else {}
            task_id = value.get("task_id", value.get("id", nested.get("task_id")))
            if task_id is None:
                raise TaskRouterError("current task context requires task_id")
            goal = value.get("goal", value.get("title", value.get("name", nested.get("goal", ""))))
            summary = value.get("summary", nested.get("summary", ""))
            description = value.get(
                "description",
                value.get("text", value.get("objective", nested.get("description", nested.get("objective", "")))),
            )
            keywords = value.get("keywords", nested.get("keywords", ()))
            parent = value.get(
                "parent_task_id",
                value.get("parent_id", value.get("parent", nested.get("parent_task_id", nested.get("parent_id", nested.get("parent"))))),
            )
            status = value.get("status", nested.get("status"))
            return cls(
                task_id=task_id,
                goal=goal,
                summary=summary,
                description=description,
                keywords=keywords,
                parent_task_id=parent,
                status=status,
            )
        task_id = getattr(value, "task_id", getattr(value, "id", None))
        if task_id is not None:
            return cls(
                task_id=task_id,
                goal=getattr(value, "goal", getattr(value, "title", getattr(value, "name", ""))),
                summary=getattr(value, "summary", ""),
                description=getattr(value, "description", getattr(value, "text", getattr(value, "objective", ""))),
                keywords=getattr(value, "keywords", ()),
                parent_task_id=getattr(value, "parent_task_id", getattr(value, "parent_id", getattr(value, "parent", None))),
                status=getattr(value, "status", None),
            )
        raise TaskRouterError("current task context must be a mapping, ID, or context object")


@dataclass(frozen=True)
class RouteMetadata:
    """Serializable result of one routing decision.

    ``task_id`` is the route target, not merely the message ID.  For an
    ``unknown`` result it is intentionally ``None`` so a caller cannot
    accidentally execute against the old task.  ``current_task_id`` remains as
    provenance so the host can ask the user which task was meant.
    """

    decision: RouteDecision
    task_id: str | None = None
    parent_task_id: str | None = None
    confidence: float = 0.0
    reason: str = ""
    current_task_id: str | None = None
    unknown: bool = False
    ambiguous: bool = False
    requires_clarification: bool = False
    fail_closed: bool = True
    candidate_decision: RouteDecision | None = None
    candidate_confidence: float | None = None
    input_digest: str | None = None
    evidence: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: str | None = None
    persisted: bool = False

    def __post_init__(self) -> None:
        decision = _coerce_decision(self.decision)
        object.__setattr__(self, "decision", decision)
        if self.candidate_decision is not None:
            object.__setattr__(self, "candidate_decision", _coerce_decision(self.candidate_decision))
        if self.task_id is not None:
            object.__setattr__(self, "task_id", _validate_identifier(self.task_id, "task_id"))
        if self.parent_task_id is not None:
            object.__setattr__(self, "parent_task_id", _validate_identifier(self.parent_task_id, "parent_task_id"))
        if self.current_task_id is not None:
            object.__setattr__(self, "current_task_id", _validate_identifier(self.current_task_id, "current_task_id"))
        if self.task_id is not None and self.task_id == self.parent_task_id:
            raise TaskRouterError("a route target cannot be its own parent")
        if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
            raise TaskRouterError("route confidence must be a number")
        confidence = float(self.confidence)
        if not 0.0 <= confidence <= 1.0:
            raise TaskRouterError("route confidence must be between 0 and 1")
        object.__setattr__(self, "confidence", confidence)
        if self.candidate_confidence is not None:
            if isinstance(self.candidate_confidence, bool) or not isinstance(self.candidate_confidence, (int, float)):
                raise TaskRouterError("candidate confidence must be a number")
            candidate_confidence = float(self.candidate_confidence)
            if not 0.0 <= candidate_confidence <= 1.0:
                raise TaskRouterError("candidate confidence must be between 0 and 1")
            object.__setattr__(self, "candidate_confidence", candidate_confidence)
        if self.input_digest is not None and not _DIGEST_RE.fullmatch(str(self.input_digest)):
            raise TaskRouterError("input_digest must be a lowercase SHA-256 digest")
        if not isinstance(self.reason, str):
            raise TaskRouterError("route reason must be a string")
        if decision is RouteDecision.UNKNOWN:
            if self.task_id is not None or self.parent_task_id is not None or self.confidence != 0.0:
                raise TaskRouterError("unknown route cannot contain a target or confidence")
            object.__setattr__(self, "unknown", True)
            object.__setattr__(self, "ambiguous", True)
            object.__setattr__(self, "requires_clarification", True)
            object.__setattr__(self, "fail_closed", True)
        elif self.unknown:
            raise TaskRouterError("only unknown routes may set unknown=true")
        try:
            object.__setattr__(
                self,
                "evidence",
                tuple(str(redact_sensitive(item)) for item in self.evidence),
            )
            copied_metadata = redact_sensitive(copy.deepcopy(dict(self.metadata)))
            if not isinstance(copied_metadata, Mapping):
                raise TaskRouterError("route metadata must be JSON-shaped")
            if len(_canonical_json(copied_metadata)) > MAX_METADATA_CHARS:
                raise TaskRouterError("route metadata exceeds the maximum size")
        except (TypeError, ValueError, AttributeError) as exc:
            raise TaskRouterError("route metadata must be JSON-shaped") from exc
        object.__setattr__(self, "metadata", MappingProxyType(copied_metadata))

    @property
    def action(self) -> str:
        """Short action spelling for hosts that use an action field."""

        return {
            RouteDecision.CONTINUATION: "continue",
            RouteDecision.CLARIFICATION: "clarify",
            RouteDecision.NEW_TASK: "new_task",
            RouteDecision.ABANDON: "abandon",
            RouteDecision.UNKNOWN: "unknown",
        }[self.decision]

    @property
    def route(self) -> str:
        return self.decision.value

    @property
    def route_decision(self) -> RouteDecision:
        return self.decision

    @property
    def kind(self) -> str:
        return self.decision.value

    @property
    def is_unknown(self) -> bool:
        return self.decision is RouteDecision.UNKNOWN or self.unknown

    @property
    def is_ambiguous(self) -> bool:
        return self.ambiguous or self.is_unknown

    @property
    def needs_clarification(self) -> bool:
        return self.requires_clarification

    @property
    def new_task_id(self) -> str | None:
        return self.task_id if self.decision is RouteDecision.NEW_TASK else None

    @property
    def target_task_id(self) -> str | None:
        return self.task_id

    @property
    def parent_id(self) -> str | None:
        return self.parent_task_id

    @property
    def safe_to_execute(self) -> bool:
        return self.decision is RouteDecision.CONTINUATION and not self.fail_closed

    def to_dict(self) -> dict[str, Any]:
        """Return a defensive, canonical-JSON-compatible representation."""

        return {
            "schema_version": ROUTER_SCHEMA_VERSION,
            "router_version": ROUTER_VERSION,
            "decision": self.decision.value,
            "action": self.action,
            "route": self.route,
            "task_id": self.task_id,
            "parent_task_id": self.parent_task_id,
            "current_task_id": self.current_task_id,
            "confidence": self.confidence,
            "reason": self.reason,
            "unknown": self.is_unknown,
            "ambiguous": self.ambiguous,
            "requires_clarification": self.requires_clarification,
            "fail_closed": self.fail_closed,
            "candidate_decision": self.candidate_decision.value if self.candidate_decision else None,
            "candidate_confidence": self.candidate_confidence,
            "input_digest": self.input_digest,
            "evidence": list(self.evidence),
            "metadata": copy.deepcopy(dict(self.metadata)),
            "created_at": self.created_at,
            "persisted": self.persisted,
        }

    as_dict = to_dict
    projection_dict = to_dict

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RouteMetadata":
        """Validate persisted metadata; malformed records fail closed upstream."""

        if not isinstance(value, Mapping):
            raise TaskRouterError("route metadata must be an object")
        if value.get("schema_version", ROUTER_SCHEMA_VERSION) != ROUTER_SCHEMA_VERSION:
            raise TaskRouterError("unsupported route metadata schema")
        if value.get("router_version", ROUTER_VERSION) != ROUTER_VERSION:
            raise TaskRouterError("unsupported router metadata version")
        if "decision" not in value:
            raise TaskRouterError("route metadata is missing decision")
        decision = _coerce_decision(value["decision"])
        return cls(
            decision=decision,
            task_id=value.get("task_id"),
            parent_task_id=value.get("parent_task_id", value.get("parent_id")),
            confidence=value.get("confidence", 0.0),
            reason=value.get("reason", ""),
            current_task_id=value.get("current_task_id", value.get("active_task_id")),
            unknown=bool(value.get("unknown", decision is RouteDecision.UNKNOWN)),
            ambiguous=bool(value.get("ambiguous", decision is RouteDecision.UNKNOWN)),
            requires_clarification=bool(
                value.get(
                    "requires_clarification",
                    value.get("needs_clarification", decision in {RouteDecision.CLARIFICATION, RouteDecision.UNKNOWN}),
                )
            ),
            fail_closed=bool(value.get("fail_closed", True)),
            candidate_decision=(
                _coerce_decision(value["candidate_decision"]) if value.get("candidate_decision") else None
            ),
            candidate_confidence=value.get("candidate_confidence"),
            input_digest=value.get("input_digest"),
            evidence=tuple(value.get("evidence", ())),
            metadata=value.get("metadata", {}),
            created_at=value.get("created_at"),
            persisted=bool(value.get("persisted", True)),
        )

    def __getitem__(self, key: str) -> Any:
        # A small mapping façade keeps the result convenient for Runtime hosts
        # that historically consume routing dictionaries.
        aliases = {
            "parent_id": "parent_task_id",
            "active_task_id": "current_task_id",
            "new_task_id": "new_task_id",
            "target_task_id": "target_task_id",
            "route": "route",
            "route_decision": "route_decision",
            "kind": "kind",
            "action": "action",
            "is_unknown": "is_unknown",
            "is_ambiguous": "is_ambiguous",
            "needs_clarification": "needs_clarification",
            "safe_to_execute": "safe_to_execute",
        }
        if key in {
            "new_task_id",
            "target_task_id",
            "route",
            "route_decision",
            "kind",
            "action",
            "is_unknown",
            "is_ambiguous",
            "needs_clarification",
            "safe_to_execute",
        }:
            return getattr(self, key)
        return self.to_dict()[aliases.get(key, key)]

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self):
        return self.to_dict().keys()

    def items(self):
        return self.to_dict().items()


# Result aliases keep the data object discoverable under the terminology used
# by different Runtime hosts without duplicating its implementation.
RouteResult = RouteMetadata
TaskRoute = RouteMetadata
TaskRoutingDecision = RouteMetadata


class RoutePersistence(Protocol):
    """Minimal persistence contract accepted by :class:`TaskRouter`."""

    def load(self, key: str) -> Mapping[str, Any] | None:
        ...

    def save(self, key: str, metadata: Mapping[str, Any]) -> None:
        ...


class InMemoryRouteStore:
    """Thread-safe store useful for tests and hosts that provide their own I/O."""

    def __init__(self, records: dict[str, Any] | None = None) -> None:
        self._records: dict[str, Any] = records if records is not None else {}
        self._lock = threading.RLock()

    def load(self, key: str) -> Mapping[str, Any] | None:
        with self._lock:
            value = self._records.get(str(key))
            return copy.deepcopy(value) if value is not None else None

    def save(self, key: str, metadata: Mapping[str, Any]) -> None:
        if not isinstance(metadata, Mapping):
            raise RoutePersistenceError("route metadata must be an object")
        _canonical_json(dict(metadata))
        with self._lock:
            self._records[str(key)] = copy.deepcopy(dict(metadata))

    get = load
    put = save


class RouteMetadataStore(InMemoryRouteStore):
    """Atomic JSON-backed route metadata store.

    The store is deliberately separate from ``TaskStore``.  A Runtime can pass
    this object directly, or replace it with a host adapter that stores route
    metadata in the Runtime's own task state/evidence files.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        clock: Callable[[], Any] | None = None,
        max_records: int = DEFAULT_MAX_ROUTE_RECORDS,
        max_bytes: int = DEFAULT_MAX_ROUTE_BYTES,
        ttl_seconds: float = DEFAULT_ROUTE_TTL_SECONDS,
    ) -> None:
        super().__init__()
        self.path = Path(path)
        self._clock = clock
        self._file_lock = threading.RLock()
        for name, value, minimum in (("max_records", max_records, 1), ("max_bytes", max_bytes, 1024)):
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise RoutePersistenceError(f"{name} is outside its bounded range")
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, (int, float)) or ttl_seconds <= 0:
            raise RoutePersistenceError("ttl_seconds must be a positive finite number")
        self.max_records = max_records
        self.max_bytes = max_bytes
        self.ttl_seconds = float(ttl_seconds)

    @contextlib.contextmanager
    def _process_file_lock(self):
        lock_path = self.path.with_name(self.path.name + ".lock")
        if lock_path.is_symlink() or self.path.is_symlink():
            raise RoutePersistenceError("route metadata paths must not be symlinks")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        if fcntl is not None:
            with open(lock_path, "a+", encoding="utf-8") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return
        # A bounded O_EXCL fallback still coordinates processes on hosts
        # without fcntl; failure to acquire fails closed rather than silently
        # allowing lost updates.
        deadline = time.monotonic() + 10.0
        while True:
            try:
                descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(descriptor)
                break
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise RoutePersistenceError("timed out acquiring route metadata lock")
                time.sleep(0.01)
        try:
            yield
        finally:
            with contextlib.suppress(FileNotFoundError):
                lock_path.unlink()

    def _read_document(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": ROUTER_SCHEMA_VERSION, "routes": {}}
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise RoutePersistenceError("route metadata store is unreadable") from exc
        if not isinstance(value, dict) or value.get("schema_version") != ROUTER_SCHEMA_VERSION:
            raise RoutePersistenceError("route metadata store has an unsupported schema")
        routes = value.get("routes")
        if not isinstance(routes, dict):
            raise RoutePersistenceError("route metadata store has no routes object")
        if len(routes) > self.max_records:
            raise RoutePersistenceError("route metadata store exceeds its record quota")
        try:
            if self.path.stat().st_size > self.max_bytes:
                raise RoutePersistenceError("route metadata store exceeds its byte quota")
        except FileNotFoundError:
            return {"schema_version": ROUTER_SCHEMA_VERSION, "routes": {}}
        return value

    def load(self, key: str) -> Mapping[str, Any] | None:
        with self._file_lock, self._process_file_lock():
            value = self._read_document().get("routes", {}).get(str(key))
            return copy.deepcopy(value) if isinstance(value, Mapping) else None

    def _write_document(self, document: Mapping[str, Any]) -> None:
        if self.path.is_symlink():
            raise RoutePersistenceError("route metadata path must not be a symlink")
        encoded = json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
        if len(encoded.encode("utf-8")) > self.max_bytes:
            raise RoutePersistenceError("route metadata store exceeds its byte quota")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=".task-routes-", dir=self.path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _prune_routes(self, routes: dict[str, Any]) -> None:
        now = time.time()
        expired: list[str] = []
        for key, value in routes.items():
            if not isinstance(value, Mapping):
                expired.append(key)
                continue
            created_at = value.get("created_at")
            if isinstance(created_at, str):
                try:
                    age = now - float(created_at)
                except ValueError:
                    try:
                        from datetime import datetime
                        age = now - datetime.fromisoformat(created_at.replace("Z", "+00:00")).timestamp()
                    except (TypeError, ValueError, OverflowError):
                        expired.append(key)
                        continue
                if age > self.ttl_seconds:
                    expired.append(key)
        for key in expired:
            routes.pop(key, None)
        overflow = len(routes) - self.max_records
        if overflow > 0:
            for key in list(routes)[:overflow]:
                routes.pop(key, None)

    def save(self, key: str, metadata: Mapping[str, Any]) -> None:
        if not isinstance(metadata, Mapping):
            raise RoutePersistenceError("route metadata must be an object")
        encoded = _canonical_json(dict(metadata))
        if len(encoded.encode("utf-8")) > self.max_bytes:
            raise RoutePersistenceError("route metadata payload exceeds its byte quota")
        with self._file_lock, self._process_file_lock():
            document = self._read_document()
            routes = document.setdefault("routes", {})
            self._prune_routes(routes)
            routes[str(key)] = copy.deepcopy(dict(metadata))
            while len(routes) > self.max_records:
                routes.pop(next(iter(routes)))
            self._write_document(document)
            if self.path.stat().st_size > self.max_bytes:
                raise RoutePersistenceError("route metadata store exceeds its byte quota")

    def delete(self, key: str) -> bool:
        with self._file_lock, self._process_file_lock():
            document = self._read_document()
            routes = document.get("routes", {})
            if str(key) not in routes:
                return False
            del routes[str(key)]
            self._write_document(document)
            return True

    get = load
    put = save


# Compatibility names for hosts that call the persistence object a file store.
JsonRouteStore = RouteMetadataStore
FileRouteStore = RouteMetadataStore
TaskRouteStore = RouteMetadataStore


class _HookStore:
    def __init__(self, load_hook: Callable[[str], Mapping[str, Any] | None] | None, save_hook: Callable[[str, Mapping[str, Any]], Any] | None) -> None:
        self.load_hook = load_hook
        self.save_hook = save_hook

    def load(self, key: str) -> Mapping[str, Any] | None:
        if self.load_hook is None:
            return None
        value = self.load_hook(key)
        if value is None or isinstance(value, Mapping):
            return value
        raise RoutePersistenceError("load_hook must return an object or null")

    def save(self, key: str, metadata: Mapping[str, Any]) -> None:
        if self.save_hook is None:
            raise RoutePersistenceError("save_hook is required for durable routing")
        self.save_hook(key, metadata)


@dataclass
class _Signals:
    clarification: bool = False
    abandon: bool = False
    new_task: bool = False
    continuation: bool = False
    action: bool = False
    question: bool = False
    hedged: bool = False
    overlap: float = 0.0
    reasons: list[str] = field(default_factory=list)

    def add(self, value: str) -> None:
        if value not in self.reasons:
            self.reasons.append(value)


class TaskRouter:
    """Deterministic task/new-question guardrail with durable metadata hooks.

    Parameters are intentionally permissive at the host boundary, but the
    resulting route is strict:

    * ``project_root`` enables a default JSON store below ``.memory``.
    * ``storage_path``/``persistence_path`` selects an explicit JSON file.
    * ``persistence`` may be any object implementing ``load``/``save``.
    * ``load_hook`` and ``save_hook`` provide callback integration without a
      Runtime or provider dependency.
    * ``id_factory`` and ``clock`` make task IDs/timestamps testable.

    A route is only returned as executable when it is an unambiguous
    ``continuation``.  Clarification, abandon, and unknown outcomes never grant
    execution capability.
    """

    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        storage_path: str | Path | None = None,
        persistence_path: str | Path | None = None,
        persistence: Any = None,
        store: Any = None,
        route_store: Any = None,
        load_hook: Callable[[str], Mapping[str, Any] | None] | None = None,
        save_hook: Callable[[str, Mapping[str, Any]], Any] | None = None,
        id_factory: Callable[[], str] | None = None,
        clock: Callable[[], Any] | None = None,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
        max_text_chars: int = DEFAULT_MAX_TEXT_CHARS,
        confidence_threshold: float | None = None,
        threshold: float | None = None,
    ) -> None:
        if confidence_threshold is not None and threshold is not None:
            raise TaskRouterError("provide only one of confidence_threshold and threshold")
        if confidence_threshold is not None:
            min_confidence = confidence_threshold
        elif threshold is not None:
            min_confidence = threshold
        if isinstance(min_confidence, bool) or not isinstance(min_confidence, (int, float)):
            raise TaskRouterError("min_confidence must be a number")
        if not 0.0 <= float(min_confidence) <= 1.0:
            raise TaskRouterError("min_confidence must be between 0 and 1")
        if isinstance(max_text_chars, bool) or not isinstance(max_text_chars, int) or max_text_chars < 1:
            raise TaskRouterError("max_text_chars must be a positive integer")
        if sum(value is not None for value in (storage_path, persistence_path)) > 1:
            raise TaskRouterError("provide only one of storage_path and persistence_path")
        supplied_stores = [value for value in (persistence, store, route_store) if value is not None]
        if len(supplied_stores) > 1:
            raise TaskRouterError("provide only one persistence object")
        if supplied_stores and (storage_path is not None or persistence_path is not None):
            raise TaskRouterError("persistence object and storage_path are mutually exclusive")
        if load_hook is not None and not callable(load_hook):
            raise TaskRouterError("load_hook must be callable")
        if save_hook is not None and not callable(save_hook):
            raise TaskRouterError("save_hook must be callable")
        if id_factory is not None and not callable(id_factory):
            raise TaskRouterError("id_factory must be callable")
        if clock is not None and not callable(clock):
            raise TaskRouterError("clock must be callable")

        selected_store: Any
        durable = True
        if supplied_stores:
            selected_store = supplied_stores[0]
            if isinstance(selected_store, (str, Path)):
                selected_store = RouteMetadataStore(selected_store, clock=clock)
            elif isinstance(selected_store, Mapping):
                if not isinstance(selected_store, dict):
                    raise TaskRouterError("mapping persistence must be a mutable dictionary")
                selected_store = InMemoryRouteStore(selected_store)
        elif load_hook is not None or save_hook is not None:
            selected_store = _HookStore(load_hook, save_hook)
        else:
            selected_path = storage_path if storage_path is not None else persistence_path
            if selected_path is not None:
                selected_store = RouteMetadataStore(selected_path, clock=clock)
            elif project_root is not None:
                selected_store = RouteMetadataStore(Path(project_root) / DEFAULT_ROUTE_FILENAME, clock=clock)
            else:
                selected_store = InMemoryRouteStore()
                durable = False

        if not hasattr(selected_store, "load") or not callable(selected_store.load) or not hasattr(selected_store, "save") or not callable(selected_store.save):
            raise TaskRouterError("persistence must provide callable load(key) and save(key, metadata) methods")
        self.store = selected_store
        self.persistence = selected_store
        self.persistence_enabled = durable
        self.project_root = Path(project_root).resolve() if project_root is not None else None
        self.storage_path = getattr(selected_store, "path", None)
        self.id_factory = id_factory
        self.clock = clock
        self.min_confidence = float(min_confidence)
        self.max_text_chars = max_text_chars

    @staticmethod
    def _now(clock: Callable[[], Any] | None) -> str:
        try:
            value = clock() if clock is not None else time.time()
        except Exception:
            return "unknown"
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(value)))
        isoformat = getattr(value, "isoformat", None)
        if callable(isoformat):
            result = isoformat()
            return str(result).replace("+00:00", "Z")
        return str(value)

    def _normalize_text(self, text: Any) -> tuple[str | None, str | None]:
        if not isinstance(text, str):
            return None, "message must be a string"
        if len(text) > self.max_text_chars:
            return None, "message exceeds the configured size limit"
        normalized = _WHITESPACE_RE.sub(" ", text.strip()).lower()
        if not normalized:
            return None, "message is empty"
        return normalized, None

    @staticmethod
    def _tokens(text: str) -> frozenset[str]:
        return frozenset(token for token in _WORD_RE.findall(text.lower()) if token not in _STOP_WORDS and len(token) > 1)

    @staticmethod
    def _overlap(incoming: str, context: TaskContext) -> float:
        left = TaskRouter._tokens(incoming)
        right = TaskRouter._tokens(context.text + " " + " ".join(context.keywords))
        if not left or not right:
            return 0.0
        shared = len(left.intersection(right))
        if not shared:
            return 0.0
        coverage = shared / len(left)
        context_coverage = shared / len(right)
        jaccard = shared / len(left.union(right))
        return min(1.0, 0.55 * coverage + 0.25 * context_coverage + 0.20 * jaccard)

    @staticmethod
    def _signals(text: str, context: TaskContext | None) -> _Signals:
        signals = _Signals(
            clarification=any(pattern.search(text) for pattern in _CLARIFICATION_PATTERNS),
            abandon=any(pattern.search(text) for pattern in _ABANDON_PATTERNS),
            new_task=any(pattern.search(text) for pattern in _NEW_TASK_PATTERNS),
            continuation=any(pattern.search(text) for pattern in _CONTINUATION_PATTERNS),
            action=bool(_ACTION_RE.search(text)),
            question="?" in text,
            hedged=bool(_HEDGE_RE.search(text)),
        )
        if signals.clarification:
            signals.add("explicit_clarification")
        if signals.abandon:
            signals.add("explicit_abandon")
        if signals.new_task:
            signals.add("explicit_new_task")
        if signals.continuation:
            signals.add("explicit_continuation")
        if signals.action:
            signals.add("action_verb")
        if signals.hedged:
            signals.add("hedged_language")
        if context is not None:
            signals.overlap = TaskRouter._overlap(text, context)
            if signals.overlap > 0.0:
                signals.add("task_overlap")
            if signals.question and signals.overlap >= 0.35:
                signals.add("anchored_question")
        return signals

    def _route_key(
        self,
        normalized_text: str,
        context: TaskContext | None,
        explicit_decision: RouteDecision | None,
        explicit_task_id: str | None,
    ) -> str:
        return _digest(
            {
                "router_version": ROUTER_VERSION,
                "text": normalized_text,
                "context": (
                    {"task_id": context.task_id, "parent_task_id": context.parent_task_id, "status": context.status}
                    if context is not None
                    else None
                ),
                "explicit_decision": explicit_decision.value if explicit_decision else None,
                "explicit_task_id": explicit_task_id,
                "min_confidence": self.min_confidence,
            }
        )

    @staticmethod
    def _parent_for(
        context: TaskContext | None,
        *,
        requested_parent: str | None = None,
        for_new_task: bool = False,
    ) -> str | None:
        if requested_parent is not None:
            return _validate_identifier(requested_parent, "parent_task_id")
        if context is None:
            return None
        return context.task_id if for_new_task else context.parent_task_id

    def _new_id(self, context: TaskContext | None) -> str:
        try:
            value = self.id_factory() if self.id_factory is not None else f"task-{uuid.uuid4().hex[:12]}"
        except Exception as exc:
            raise TaskRouterError("new task_id factory failed") from exc
        task_id = _validate_identifier(value, "new task_id")
        if context is not None and task_id == context.task_id:
            raise TaskRouterError("new task_id must differ from the active task_id")
        return task_id

    def _result(
        self,
        *,
        decision: RouteDecision,
        context: TaskContext | None,
        task_id: str | None,
        parent_task_id: str | None,
        confidence: float,
        reason: str,
        input_digest: str,
        evidence: Sequence[str] = (),
        metadata: Mapping[str, Any] | None = None,
        candidate_decision: RouteDecision | None = None,
        candidate_confidence: float | None = None,
        ambiguous: bool = False,
        persisted: bool = False,
    ) -> RouteMetadata:
        requires_clarification = decision in {RouteDecision.CLARIFICATION, RouteDecision.UNKNOWN}
        # Known clarification and unknown outcomes are intentionally blocking.
        fail_closed = decision in {
            RouteDecision.CLARIFICATION,
            RouteDecision.UNKNOWN,
            RouteDecision.ABANDON,
        }
        values = {
            "router_version": ROUTER_VERSION,
            "source": "deterministic_task_router",
        }
        if metadata:
            values.update(copy.deepcopy(dict(metadata)))
        values["router_version"] = ROUTER_VERSION
        values["source"] = "deterministic_task_router"
        return RouteMetadata(
            decision=decision,
            task_id=task_id,
            parent_task_id=parent_task_id,
            confidence=confidence,
            reason=reason,
            current_task_id=context.task_id if context is not None else None,
            unknown=decision is RouteDecision.UNKNOWN,
            ambiguous=ambiguous or decision is RouteDecision.UNKNOWN,
            requires_clarification=requires_clarification,
            fail_closed=fail_closed,
            candidate_decision=candidate_decision,
            candidate_confidence=candidate_confidence,
            input_digest=input_digest,
            evidence=tuple(evidence),
            metadata=values,
            created_at=self._now(self.clock),
            persisted=persisted,
        )

    def _unknown(
        self,
        *,
        context: TaskContext | None,
        input_digest: str,
        reason: str,
        candidate_decision: RouteDecision | None = None,
        candidate_confidence: float | None = None,
        evidence: Sequence[str] = (),
    ) -> RouteMetadata:
        return self._result(
            decision=RouteDecision.UNKNOWN,
            context=context,
            task_id=None,
            parent_task_id=None,
            confidence=0.0,
            reason=reason,
            input_digest=input_digest,
            evidence=evidence,
            candidate_decision=candidate_decision,
            candidate_confidence=candidate_confidence,
            ambiguous=True,
        )

    @staticmethod
    def _coerce_explicit_decision(value: Any) -> RouteDecision | None:
        if value is None:
            return None
        if isinstance(value, RouteDecision):
            return value
        if not isinstance(value, str):
            raise TaskRouterError("explicit_decision must be a decision name")
        normalized = value.strip().lower().replace("-", "_")
        aliases = {
            "continue": RouteDecision.CONTINUATION,
            "continuation": RouteDecision.CONTINUATION,
            "clarify": RouteDecision.CLARIFICATION,
            "clarification": RouteDecision.CLARIFICATION,
            "new": RouteDecision.NEW_TASK,
            "new_task": RouteDecision.NEW_TASK,
            "new_question": RouteDecision.NEW_TASK,
            "cancel": RouteDecision.ABANDON,
            "stop": RouteDecision.ABANDON,
            "abandon": RouteDecision.ABANDON,
            "unknown": RouteDecision.UNKNOWN,
        }
        if normalized not in aliases:
            raise TaskRouterError(f"unknown explicit routing decision: {value!r}")
        return aliases[normalized]

    def _resolve_context(
        self,
        current_task: Any,
        active_task: Any,
        current_task_id: str | None,
        active_task_id: str | None,
        task_id: str | None,
    ) -> TaskContext | None:
        supplied = [value for value in (current_task, active_task) if value is not None]
        if current_task_id is not None and active_task_id is not None and current_task_id != active_task_id:
            raise TaskRouterError("current_task_id and active_task_id disagree")
        if task_id is not None:
            task_id = _validate_identifier(task_id, "task_id")
            if current_task_id is not None and task_id != current_task_id:
                raise TaskRouterError("task_id and current_task_id disagree")
            if active_task_id is not None and task_id != active_task_id:
                raise TaskRouterError("task_id and active_task_id disagree")
            current_task_id = task_id
            active_task_id = task_id
        if current_task_id is None:
            current_task_id = active_task_id
        if active_task_id is None:
            active_task_id = current_task_id
        if len(supplied) > 1:
            left = TaskContext.from_value(supplied[0])
            right = TaskContext.from_value(supplied[1])
            if left.descriptor != right.descriptor:
                raise TaskRouterError("current_task and active_task contexts disagree")
            context = left
        elif supplied:
            context = TaskContext.from_value(supplied[0])
        elif current_task_id is None:
            context = None
        else:
            context = TaskContext(task_id=current_task_id)
        if context is not None:
            if current_task_id is not None and context.task_id != current_task_id:
                raise TaskRouterError("current task context and task ID disagree")
            if active_task_id is not None and context.task_id != active_task_id:
                raise TaskRouterError("active task context and task ID disagree")
        return context

    def _validate_restored(
        self,
        result: RouteMetadata,
        *,
        context: TaskContext | None,
        input_digest: str,
        parent_task_id: str | None = None,
    ) -> RouteMetadata:
        """Revalidate a persisted route before it can influence a host."""

        if result.input_digest != input_digest:
            raise RoutePersistenceError("persisted route digest does not match input")
        if result.decision is RouteDecision.UNKNOWN:
            if result.task_id is not None or result.parent_task_id is not None or result.confidence != 0.0:
                raise RoutePersistenceError("unknown persisted route contains a target or confidence")
            if not result.fail_closed or not result.unknown or not result.ambiguous:
                raise RoutePersistenceError("unknown persisted route is not fail-closed")
            return result
        if result.unknown or result.confidence < self.min_confidence:
            raise RoutePersistenceError("persisted route confidence is not safe")
        if result.decision is RouteDecision.CONTINUATION:
            if context is None or result.task_id != context.task_id:
                raise RoutePersistenceError("persisted continuation is not bound to the active task")
            expected_parent = parent_task_id if parent_task_id is not None else (context.parent_task_id if context else None)
            if result.parent_task_id != expected_parent:
                raise RoutePersistenceError("persisted continuation parent does not match context")
            if result.current_task_id != context.task_id:
                raise RoutePersistenceError("persisted continuation current task does not match context")
            if not result.safe_to_execute:
                raise RoutePersistenceError("persisted continuation is fail-closed")
            return result
        if result.decision in {RouteDecision.CLARIFICATION, RouteDecision.ABANDON}:
            if context is not None and result.task_id != context.task_id:
                raise RoutePersistenceError("persisted terminal route is not bound to the active task")
            if not result.requires_clarification or not result.fail_closed:
                raise RoutePersistenceError("persisted blocking route is not fail-closed")
            return result
        if result.decision is RouteDecision.NEW_TASK:
            if result.task_id is None:
                raise RoutePersistenceError("persisted new-task route has no task ID")
            if context is not None:
                expected_parent = parent_task_id if parent_task_id is not None else context.task_id
                if result.parent_task_id != expected_parent or result.current_task_id != context.task_id:
                    raise RoutePersistenceError("persisted new-task parent does not match context")
            elif result.current_task_id is not None:
                raise RoutePersistenceError("root new-task route unexpectedly has a current task")
            return result
        raise RoutePersistenceError("unsupported persisted route decision")

    def _persist_unknown(
        self,
        key: str | None,
        persist: bool,
        *,
        context: TaskContext | None,
        input_digest: str,
        reason: str,
        candidate_decision: RouteDecision | None = None,
        candidate_confidence: float | None = None,
        evidence: Sequence[str] = (),
    ) -> RouteMetadata:
        result = self._unknown(
            context=context,
            input_digest=input_digest,
            reason=reason,
            candidate_decision=candidate_decision,
            candidate_confidence=candidate_confidence,
            evidence=evidence,
        )
        if not persist or not self.persistence_enabled or key is None:
            return result
        return self._persist_or_unknown(key, result, context)

    def _persist_or_unknown(
        self,
        key: str,
        result: RouteMetadata,
        context: TaskContext | None,
    ) -> RouteMetadata:
        if not self.persistence_enabled:
            return result
        try:
            existing = self.store.load(key)
            if existing is not None:
                # Validate before trusting a restart-time record.  Invalid
                # records become an explicit unknown result below.
                restored = RouteMetadata.from_dict(existing)
                restored = self._validate_restored(
                    restored,
                    context=context,
                    input_digest=result.input_digest or "",
                    parent_task_id=result.parent_task_id if result.decision is RouteDecision.NEW_TASK else None,
                )
                return _with_persisted(restored, True)
            to_store = _with_persisted(result, True)
            self.store.save(key, to_store.to_dict())
            # A store may not return the record, but a successful save is the
            # persistence contract.  Marking the returned object keeps the
            # route metadata honest without retaining mutable input.
            return to_store
        except Exception as exc:
            return self._unknown(
                context=context,
                input_digest=result.input_digest or "",
                reason="route metadata persistence unavailable; routing failed closed",
                evidence=("persistence_failure", type(exc).__name__),
            )

    def route(
        self,
        text: str,
        current_task: Any = None,
        *,
        active_task: Any = None,
        current_task_id: str | None = None,
        active_task_id: str | None = None,
        task_id: str | None = None,
        parent_task_id: str | None = None,
        new_task_id: str | None = None,
        explicit_decision: Any = None,
        decision: Any = None,
        signals: Mapping[str, Any] | Sequence[str] | None = None,
        persist: bool = True,
        metadata: Mapping[str, Any] | None = None,
    ) -> RouteMetadata:
        """Classify ``text`` without making any model, provider, or network call.

        Invalid or ambiguous input is returned as ``RouteDecision.UNKNOWN``.
        Known routes are persisted when a durable store is configured; a
        persistence failure is also converted to unknown so a host cannot
        execute a route whose identity was not durably recorded.
        """

        key: str | None = None
        if explicit_decision is not None and decision is not None:
            try:
                if _coerce_explicit_decision(explicit_decision) is not _coerce_explicit_decision(decision):
                    return self._persist_unknown(
                        key,
                        persist,
                        context=None,
                        input_digest=_digest(text),
                        reason="conflicting explicit routing decisions",
                    )
            except TaskRouterError as exc:
                return self._persist_unknown(
                    key,
                    persist,
                    context=None,
                    input_digest=_digest(text),
                    reason=str(exc),
                )
        explicit_value = explicit_decision if explicit_decision is not None else decision
        try:
            forced = self._coerce_explicit_decision(explicit_value)
        except TaskRouterError as exc:
            return self._persist_unknown(
                key,
                persist,
                context=None,
                input_digest=_digest(text),
                reason=str(exc),
            )

        try:
            context = self._resolve_context(
                current_task,
                active_task,
                current_task_id,
                active_task_id,
                task_id,
            )
        except TaskRouterError as exc:
            # The digest of arbitrary non-string input is not relied upon for
            # execution; it is only a best-effort audit value.
            return self._persist_unknown(
                key,
                persist,
                context=None,
                input_digest=_digest(text),
                reason=str(exc),
            )

        try:
            if parent_task_id is not None:
                parent_task_id = _validate_identifier(parent_task_id, "parent_task_id")
            if metadata is not None:
                encoded_metadata = _canonical_json(dict(metadata))
                if len(encoded_metadata) > MAX_METADATA_CHARS:
                    raise TaskRouterError("route metadata exceeds the maximum size")
        except (TaskRouterError, TypeError, ValueError) as exc:
            return self._persist_unknown(
                key,
                persist,
                context=context,
                input_digest=_digest(text),
                reason=str(exc),
            )

        normalized, normalization_error = self._normalize_text(text)
        input_digest = _digest(text)
        if normalization_error is not None or normalized is None:
            return self._persist_unknown(
                key,
                persist,
                context=context,
                input_digest=input_digest,
                reason=normalization_error or "message cannot be routed",
            )
        if len(normalized) > self.max_text_chars:
            return self._persist_unknown(
                key,
                persist,
                context=context,
                input_digest=input_digest,
                reason="message exceeds the configured size limit",
            )

        try:
            supplied_signals = _validate_host_signals(signals) if signals is not None else {}
        except TaskRouterError as exc:
            return self._persist_unknown(
                key,
                persist,
                context=context,
                input_digest=input_digest,
                reason=str(exc),
            )

        key = self._route_key(normalized, context, forced, new_task_id)
        if self.persistence_enabled:
            try:
                existing = self.store.load(key)
                if existing is not None and not supplied_signals:
                    restored = RouteMetadata.from_dict(existing)
                    restored = self._validate_restored(
                        restored,
                        context=context,
                        input_digest=input_digest,
                        parent_task_id=parent_task_id,
                    )
                    return _with_persisted(restored, True)
            except Exception as exc:
                return self._unknown(
                    context=context,
                    input_digest=input_digest,
                    reason="route metadata persistence unavailable; routing failed closed",
                    evidence=("persistence_failure", type(exc).__name__),
                )

        if context is not None and context.status in {"completed", "abandoned", "cancelled", "failed"}:
            if forced in {RouteDecision.CONTINUATION, RouteDecision.ABANDON, RouteDecision.UNKNOWN}:
                return self._persist_unknown(
                    key,
                    persist,
                    context=context,
                    input_digest=input_digest,
                    reason="active task is terminal and cannot accept this route",
                    candidate_decision=forced,
                    candidate_confidence=1.0 if forced is not None else None,
                    evidence=("terminal_task",),
                )
            if forced is RouteDecision.CLARIFICATION:
                result = self._result(
                    decision=RouteDecision.CLARIFICATION,
                    context=context,
                    task_id=context.task_id,
                    parent_task_id=self._parent_for(context, requested_parent=parent_task_id),
                    confidence=1.0,
                    reason="active task is terminal; clarification is required",
                    input_digest=input_digest,
                    evidence=("terminal_task", "explicit_decision"),
                    metadata=metadata,
                )
                return self._persist_or_unknown(key, result, context) if persist else result
            try:
                target = _validate_identifier(new_task_id, "new_task_id") if new_task_id is not None else self._new_id(context)
            except TaskRouterError as exc:
                return self._persist_unknown(
                    key,
                    persist,
                    context=context,
                    input_digest=input_digest,
                    reason=str(exc),
                    evidence=("terminal_task",),
                )
            result = self._result(
                decision=RouteDecision.NEW_TASK,
                context=context,
                task_id=target,
                parent_task_id=self._parent_for(context, requested_parent=parent_task_id, for_new_task=True),
                confidence=0.99,
                reason="active task is terminal; a new task must be created",
                input_digest=input_digest,
                evidence=("terminal_task",),
                metadata=metadata,
            )
            return self._persist_or_unknown(key, result, context) if persist else result

        lexical = self._signals(normalized, context)
        lexical = _merge_host_signals(lexical, supplied_signals)

        if lexical.hedged and not lexical.clarification:
            return self._persist_unknown(
                key,
                persist,
                context=context,
                input_digest=input_digest,
                reason="hedged language does not establish a safe route",
                evidence=lexical.reasons,
            )

        if forced is not None:
            forced_name = {
                RouteDecision.CONTINUATION: "continuation",
                RouteDecision.CLARIFICATION: "clarification",
                RouteDecision.NEW_TASK: "new_task",
                RouteDecision.ABANDON: "abandon",
                RouteDecision.UNKNOWN: "unknown",
            }[forced]
            positive_signals = [name for name, value in supplied_signals.items() if value]
            if any(name != forced_name for name in positive_signals) or len(positive_signals) > 1:
                return self._persist_unknown(
                    key,
                    persist,
                    context=context,
                    input_digest=input_digest,
                    reason="explicit decision and host signals conflict",
                    candidate_decision=forced,
                    candidate_confidence=1.0,
                    evidence=tuple(positive_signals),
                )
            result = self._route_forced(forced, context, input_digest, parent_task_id, new_task_id, metadata)
            return self._persist_or_unknown(key, result, context) if persist else result

        if lexical.clarification and lexical.abandon:
            return self._persist_unknown(key, persist,
                context=context,
                input_digest=input_digest,
                reason="clarification and abandon signals conflict",
                candidate_decision=RouteDecision.CLARIFICATION,
                candidate_confidence=0.5,
                evidence=lexical.reasons,
            )
        if lexical.abandon and lexical.new_task:
            return self._persist_unknown(key, persist,
                context=context,
                input_digest=input_digest,
                reason="abandon and new-task signals conflict",
                candidate_decision=RouteDecision.NEW_TASK,
                candidate_confidence=0.5,
                evidence=lexical.reasons,
            )
        if lexical.clarification and lexical.new_task:
            return self._persist_unknown(key, persist,
                context=context,
                input_digest=input_digest,
                reason="clarification and new-task signals conflict",
                candidate_decision=RouteDecision.CLARIFICATION,
                candidate_confidence=0.5,
                evidence=lexical.reasons,
            )
        if lexical.continuation and lexical.new_task and lexical.overlap < 0.35:
            return self._persist_unknown(key, persist,
                context=context,
                input_digest=input_digest,
                reason="continuation and new-task signals conflict",
                candidate_decision=RouteDecision.NEW_TASK,
                candidate_confidence=0.5,
                evidence=lexical.reasons,
            )

        # An explicit abandon is a terminal decision.  It never creates a
        # replacement task implicitly, even if the message contains an action
        # verb such as "remove".
        if lexical.abandon:
            if context is None:
                return self._persist_unknown(key, persist,
                    context=None,
                    input_digest=input_digest,
                    reason="abandon requires an active task",
                    candidate_decision=RouteDecision.ABANDON,
                    candidate_confidence=0.99,
                    evidence=lexical.reasons,
                )
            result = self._result(
                decision=RouteDecision.ABANDON,
                context=context,
                task_id=context.task_id,
                parent_task_id=self._parent_for(context, requested_parent=parent_task_id),
                confidence=0.99,
                reason="explicit abandon signal",
                input_digest=input_digest,
                evidence=lexical.reasons,
                metadata=metadata,
            )
            return self._persist_or_unknown(key, result, context) if persist else result

        if lexical.clarification:
            result = self._result(
                decision=RouteDecision.CLARIFICATION,
                context=context,
                task_id=context.task_id if context is not None else None,
                parent_task_id=self._parent_for(context, requested_parent=parent_task_id),
                confidence=0.98,
                reason="explicit clarification signal",
                input_digest=input_digest,
                evidence=lexical.reasons,
                metadata=metadata,
            )
            return self._persist_or_unknown(key, result, context) if persist else result

        # Explicit new-task language is the strongest non-terminal signal.
        if lexical.new_task:
            if context is None:
                confidence = 0.96
            else:
                confidence = 0.97
            try:
                target = _validate_identifier(new_task_id, "new_task_id") if new_task_id is not None else self._new_id(context)
            except TaskRouterError as exc:
                return self._persist_unknown(
                    key,
                    persist,
                    context=context, input_digest=input_digest, reason=str(exc), evidence=lexical.reasons)
            result = self._result(
                decision=RouteDecision.NEW_TASK,
                context=context,
                task_id=target,
                parent_task_id=self._parent_for(context, requested_parent=parent_task_id, for_new_task=True),
                confidence=confidence,
                reason="explicit new-task signal",
                input_digest=input_digest,
                evidence=lexical.reasons,
                metadata=metadata,
            )
            return self._persist_or_unknown(key, result, context) if persist else result

        if context is not None:
            # A continuation needs either an explicit anchor or meaningful
            # lexical overlap.  Generic action verbs are not enough to keep
            # mutating an existing task.
            if lexical.continuation or (lexical.overlap >= 0.20 and lexical.action):
                confidence = min(0.99, 0.68 + 0.30 * max(lexical.overlap, 0.0))
                if lexical.continuation and lexical.overlap < 0.20:
                    confidence = 0.91
                if confidence >= self.min_confidence:
                    result = self._result(
                        decision=RouteDecision.CONTINUATION,
                        context=context,
                        task_id=context.task_id,
                        parent_task_id=self._parent_for(context, requested_parent=parent_task_id),
                        confidence=confidence,
                        reason="same-task anchor or lexical overlap",
                        input_digest=input_digest,
                        evidence=lexical.reasons,
                        metadata=metadata,
                    )
                    return self._persist_or_unknown(key, result, context) if persist else result
                return self._persist_unknown(key, persist,
                    context=context,
                    input_digest=input_digest,
                    reason="same-task signal is below the confidence threshold",
                    candidate_decision=RouteDecision.CONTINUATION,
                    candidate_confidence=confidence,
                    evidence=lexical.reasons,
                )

            # A new-task marker is required once an active task exists.  This
            # prevents an unrelated imperative from silently hijacking the
            # active task.
            if lexical.action and lexical.overlap < 0.18 and "action_verb" in lexical.reasons:
                return self._persist_unknown(key, persist,
                    context=context,
                    input_digest=input_digest,
                    reason="message has an action but no grounded task identity",
                    candidate_decision=RouteDecision.NEW_TASK,
                    candidate_confidence=0.45,
                    evidence=lexical.reasons,
                )
            return self._persist_unknown(key, persist,
                context=context,
                input_digest=input_digest,
                reason="message is not clearly related to the active task",
                evidence=lexical.reasons,
            )

        # Without an active task, only a clear imperative or an explicit new
        # task marker can create work.  A vague question is intentionally not
        # enough to create state.
        if lexical.action and len(self._tokens(normalized)) >= 2 and normalized.split()[0] in {
            "add", "build", "create", "implement", "fix", "update", "write", "design",
            "refactor", "test", "debug", "investigate", "research", "compare", "review",
            "deploy", "document", "migrate", "optimize", "install", "generate", "remove",
            "delete", "plan", "analyze", "analyse", "benchmark", "profile",
        }:
            try:
                target = _validate_identifier(new_task_id, "new_task_id") if new_task_id is not None else self._new_id(None)
            except TaskRouterError as exc:
                return self._persist_unknown(
                    key,
                    persist,
                    context=None, input_digest=input_digest, reason=str(exc), evidence=lexical.reasons)
            result = self._result(
                decision=RouteDecision.NEW_TASK,
                context=None,
                task_id=target,
                parent_task_id=self._parent_for(None, requested_parent=parent_task_id),
                confidence=0.90,
                reason="clear new-task imperative without an active task",
                input_digest=input_digest,
                evidence=lexical.reasons,
                metadata=metadata,
            )
            return self._persist_or_unknown(key, result, context) if persist else result

        return self._persist_unknown(key, persist,
            context=None,
            input_digest=input_digest,
            reason="no active task and message is not a clear task request",
            evidence=lexical.reasons,
        )

    def _route_forced(
        self,
        forced: RouteDecision,
        context: TaskContext | None,
        input_digest: str,
        parent_task_id: str | None,
        new_task_id: str | None,
        metadata: Mapping[str, Any] | None,
    ) -> RouteMetadata:
        if forced is RouteDecision.UNKNOWN:
            return self._unknown(context=context, input_digest=input_digest, reason="caller explicitly marked routing unknown")
        if forced is RouteDecision.CONTINUATION:
            if context is None:
                return self._unknown(context=None, input_digest=input_digest, reason="continuation requires an active task")
            return self._result(
                decision=forced,
                context=context,
                task_id=context.task_id,
                parent_task_id=self._parent_for(context, requested_parent=parent_task_id),
                confidence=1.0,
                reason="caller supplied an explicit continuation decision",
                input_digest=input_digest,
                evidence=("explicit_decision",),
                metadata=metadata,
            )
        if forced is RouteDecision.CLARIFICATION:
            return self._result(
                decision=forced,
                context=context,
                task_id=context.task_id if context is not None else None,
                parent_task_id=self._parent_for(context, requested_parent=parent_task_id),
                confidence=1.0,
                reason="caller supplied an explicit clarification decision",
                input_digest=input_digest,
                evidence=("explicit_decision",),
                metadata=metadata,
            )
        if forced is RouteDecision.ABANDON:
            if context is None:
                return self._unknown(context=None, input_digest=input_digest, reason="abandon requires an active task")
            return self._result(
                decision=forced,
                context=context,
                task_id=context.task_id,
                parent_task_id=self._parent_for(context, requested_parent=parent_task_id),
                confidence=1.0,
                reason="caller supplied an explicit abandon decision",
                input_digest=input_digest,
                evidence=("explicit_decision",),
                metadata=metadata,
            )
        try:
            target = _validate_identifier(new_task_id, "new_task_id") if new_task_id is not None else self._new_id(context)
        except TaskRouterError as exc:
            return self._unknown(context=context, input_digest=input_digest, reason=str(exc), evidence=("explicit_decision",))
        return self._result(
            decision=RouteDecision.NEW_TASK,
            context=context,
            task_id=target,
            parent_task_id=self._parent_for(context, requested_parent=parent_task_id, for_new_task=True),
            confidence=1.0,
            reason="caller supplied an explicit new-task decision",
            input_digest=input_digest,
            evidence=("explicit_decision",),
            metadata=metadata,
        )

    # Common host spellings.  They intentionally delegate to the same strict
    # implementation rather than creating a second classification path.
    decide = route
    route_question = route
    route_message = route

    def load_metadata(self, text: str, current_task: Any = None, **kwargs: Any) -> RouteMetadata | None:
        """Load a previously persisted route without classifying new input."""

        normalized, error = self._normalize_text(text)
        if error or normalized is None:
            return None
        try:
            context = self._resolve_context(
                current_task,
                kwargs.pop("active_task", None),
                kwargs.pop("current_task_id", None),
                kwargs.pop("active_task_id", None),
                kwargs.pop("task_id", None),
            )
        except TaskRouterError:
            return None
        try:
            explicit = self._coerce_explicit_decision(
                kwargs.pop("explicit_decision", None) or kwargs.pop("decision", None)
            )
        except TaskRouterError:
            return None
        key = self._route_key(normalized, context, explicit, kwargs.get("new_task_id"))
        if not self.persistence_enabled:
            return None
        try:
            value = self.store.load(key)
            if value is None:
                return None
            result = RouteMetadata.from_dict(value)
            result = self._validate_restored(
                result,
                context=context,
                input_digest=_digest(text),
                parent_task_id=kwargs.get("parent_task_id"),
            )
            return _with_persisted(result, True)
        except Exception:
            return None

    def clear_metadata(self, text: str, current_task: Any = None, **kwargs: Any) -> bool:
        """Remove one cached route when a host has a deliberate delete hook."""

        normalized, error = self._normalize_text(text)
        if error or normalized is None:
            return False
        try:
            context = self._resolve_context(
                current_task,
                kwargs.pop("active_task", None),
                kwargs.pop("current_task_id", None),
                kwargs.pop("active_task_id", None),
                kwargs.pop("task_id", None),
            )
        except TaskRouterError:
            return False
        key = self._route_key(normalized, context, None, kwargs.get("new_task_id"))
        deleter = getattr(self.store, "delete", None)
        if not callable(deleter):
            return False
        try:
            deleter(key)
            return True
        except Exception:
            return False


def create_task_router(*args: Any, **kwargs: Any) -> TaskRouter:
    """Factory kept for hosts that use constructor factories elsewhere."""

    return TaskRouter(*args, **kwargs)


def route_question(text: str, current_task: Any = None, **kwargs: Any) -> RouteMetadata:
    """One-shot convenience wrapper for hosts without a long-lived router."""

    router_keys = {
        "project_root",
        "storage_path",
        "persistence_path",
        "persistence",
        "store",
        "route_store",
        "load_hook",
        "save_hook",
        "id_factory",
        "clock",
        "min_confidence",
        "max_text_chars",
        "confidence_threshold",
        "threshold",
    }
    router_kwargs = {key: kwargs.pop(key) for key in tuple(kwargs) if key in router_keys}
    return TaskRouter(**router_kwargs).route(text, current_task, **kwargs)


# Short aliases for callers that use a noun rather than a factory name.
Router = TaskRouter
TaskRouteRouter = TaskRouter


def _with_persisted(value: RouteMetadata, persisted: bool) -> RouteMetadata:
    if value.persisted == persisted:
        return value
    # ``replace`` keeps the metadata immutable and avoids exposing the store's
    # mutable dictionaries to callers.
    from dataclasses import replace

    return replace(value, persisted=persisted)


def _coerce_decision(value: Any) -> RouteDecision:
    if isinstance(value, RouteDecision):
        return value
    if not isinstance(value, str):
        raise TaskRouterError("decision must be a RouteDecision or string")
    normalized = value.strip().lower().replace("-", "_")
    if normalized == "continue":
        normalized = "continuation"
    elif normalized == "clarify":
        normalized = "clarification"
    elif normalized in {"new", "new_question"}:
        normalized = "new_task"
    elif normalized in {"cancel", "stop"}:
        normalized = "abandon"
    try:
        return RouteDecision(normalized)
    except ValueError as exc:
        raise TaskRouterError(f"unknown routing decision: {value!r}") from exc


def _validate_identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value):
        raise TaskRouterError(f"{label} must match {_IDENTIFIER_RE.pattern}")
    if value in {".", ".."}:
        raise TaskRouterError(f"{label} is not a valid identifier")
    return value


def _optional_text(value: Any, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise TaskRouterError(f"{label} must be a string")
    if len(value) > DEFAULT_MAX_TEXT_CHARS:
        raise TaskRouterError(f"{label} exceeds the maximum supported length")
    return value.strip()


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise TaskRouterError("value is not canonical JSON") from exc


def _digest(value: Any) -> str:
    try:
        encoded = _canonical_json(value).encode("utf-8")
    except TaskRouterError:
        # Routing is a safety boundary: malformed non-JSON input must produce
        # an auditable unknown result rather than escaping as an exception.
        # The fallback is only a digest input; it is never executed or
        # persisted as task text.
        encoded = f"{type(value).__module__}.{type(value).__qualname__}:{value!r}".encode("utf-8", errors="replace")
    return hashlib.sha256(encoded).hexdigest()


def _validate_host_signals(signals: Mapping[str, Any] | Sequence[str]) -> dict[str, bool]:
    if isinstance(signals, Mapping):
        values = dict(signals)
    else:
        try:
            values = {(item.value if isinstance(item, RouteDecision) else str(item)): True for item in signals}
        except TypeError as exc:
            raise TaskRouterError("signals must be a mapping or iterable") from exc
    aliases = {
        "clarify": "clarification",
        "continue": "continuation",
        "new": "new_task",
        "new-task": "new_task",
        "cancel": "abandon",
        "stop": "abandon",
    }
    normalized_values: dict[str, bool] = {}
    for key, value in values.items():
        raw_key = key.value if isinstance(key, RouteDecision) else str(key).lower()
        normalized_key = aliases.get(raw_key, raw_key)
        if normalized_key in normalized_values and normalized_values[normalized_key] != value:
            raise TaskRouterError(f"conflicting aliases for routing signal {normalized_key!r}")
        normalized_values[normalized_key] = value
    allowed = {"clarification", "abandon", "new_task", "continuation"}
    unknown = set(normalized_values) - allowed
    if unknown:
        raise TaskRouterError(f"unsupported routing signal(s): {sorted(unknown)}")
    result: dict[str, bool] = {}
    for key, value in normalized_values.items():
        if not isinstance(value, bool):
            raise TaskRouterError(f"routing signal {key!r} must be boolean")
        result[key] = value
    return result


def _merge_host_signals(signals: _Signals, supplied: Mapping[str, bool]) -> _Signals:
    for key, value in supplied.items():
        setattr(signals, key, getattr(signals, key) or value)
        if value:
            signals.add(f"host_{key}")
    # Host signals cannot invent a context overlap; they can only make an
    # already explicit intent more authoritative.
    return signals


__all__ = [
    "DEFAULT_MAX_TEXT_CHARS",
    "DEFAULT_MIN_CONFIDENCE",
    "MAX_METADATA_CHARS",
    "DEFAULT_ROUTE_FILENAME",
    "ROUTER_SCHEMA_VERSION",
    "ROUTER_VERSION",
    "FileRouteStore",
    "InMemoryRouteStore",
    "JsonRouteStore",
    "RouteAction",
    "RouteDecision",
    "RouteDecisionType",
    "RouteMetadata",
    "RouteMetadataStore",
    "RouteResult",
    "ROUTE_ACTIONS",
    "RoutePersistence",
    "RoutePersistenceError",
    "Router",
    "RoutingDecision",
    "TaskContext",
    "TaskRoute",
    "TaskRouteRouter",
    "TaskRouteStore",
    "TaskRoutingDecision",
    "TaskRouter",
    "TaskRouterError",
    "create_task_router",
    "route_question",
]

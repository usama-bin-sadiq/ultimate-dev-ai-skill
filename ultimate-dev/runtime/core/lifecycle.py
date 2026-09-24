"""Bounded task lifecycle and host-resource cleanup primitives.

This module is deliberately independent of :mod:`runtime.core.engine` and
:mod:`runtime.core.state`.  The host injects a task-store boundary and this
module only uses the small, durable operations that boundary exposes:

* ``load(task_id)``
* ``update_internal(task_id, **changes)`` (or ``update_if_status``)
* ``append_event(task_id, event)``
* ``checkpoint(task_id)`` (when available)

The controller adds three explicit, non-terminal/task-terminal lifecycle
states to the Runtime vocabulary:

``paused``
    A cooperative suspension.  A pause is checkpointed and graceful host
    cleanup is attempted before the state is changed.
``interrupted``
    A hard interruption.  The state is made durable even when an external
    host cannot be torn down; in-flight operations are handed to the stale
    operation hook and are never implicitly replayed.
``abandoned``
    A terminal, explicit user/host decision.  Cleanup must succeed before the
    task is marked abandoned.

``resume`` restores the safe prior status recorded by the controller.  An
interrupted execution/verification phase resumes through ``recovering`` so a
host must reconcile uncertain side effects before continuing.  No method in
this module deletes task state, checkpoints, verification records, or evidence.
Host cleanup is deliberately separate from evidence cleanup.

The module is synchronous and uses only the Python standard library.  A host
that owns an async browser or process must provide a small synchronous bridge
around its async close/abort implementation.
"""
from __future__ import annotations

import asyncio
import copy
import inspect
import json
import math
import queue
import re
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping, Protocol, Sequence


LIFECYCLE_SCHEMA_VERSION = "1.0"

# The existing Runtime status vocabulary is deliberately accepted here.  The
# additional short aliases make the controller useful to small host adapters
# without coupling it to one spelling of a state machine.
ACTIVE_STATUSES = frozenset({
    "created",
    "ready",
    "planning",
    "planned",
    "executing",
    "observing",
    "verifying",
    "recovering",
    "replanned",
    # A failed Runtime task is recoverable in the existing engine.
    "failed",
    "blocked",
    "running",
    "in_progress",
    "pending",
    "started",
    "working",
    "paused",
    "interrupted",
})

TERMINAL_STATUSES = frozenset({
    "completed",
    "abandoned",
    "cancelled",
    "canceled",
    "done",
    "succeeded",
    "archived",
})

LIFECYCLE_STATES = frozenset({"paused", "interrupted", "abandoned"})

# Explicit transitions owned by this controller.  The underlying Runtime keeps
# its own execution transition table; these entries are deliberately separate
# so a host cannot bypass pause/abandon cleanup through a generic update.
LIFECYCLE_TRANSITIONS = {
    status: frozenset({"paused", "interrupted", "abandoned"})
    for status in ACTIVE_STATUSES
    if status not in {"paused", "interrupted"}
}
LIFECYCLE_TRANSITIONS.update({
    "paused": frozenset({"interrupted", "abandoned"}),
    "interrupted": frozenset({"abandoned"}),
    "completed": frozenset(),
    "abandoned": frozenset(),
})
ALLOWED_TRANSITIONS = LIFECYCLE_TRANSITIONS
TRANSITIONS = LIFECYCLE_TRANSITIONS

# Statuses that may be restored by a cooperative pause.  Unknown statuses are
# rejected rather than silently treated as runnable.
RESUMABLE_STATUSES = frozenset({
    "created",
    "ready",
    "planning",
    "planned",
    "executing",
    "observing",
    "verifying",
    "recovering",
    "replanned",
    "failed",
    "blocked",
    "running",
    "in_progress",
    "pending",
    "started",
    "working",
})

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_MAX_REASON_CHARS = 4_096
_MAX_HOOK_HISTORY = 32
_MAX_CLEANUP_RESOURCES = 10_000


class LifecycleError(RuntimeError):
    """Base class for lifecycle controller failures."""


class LifecycleContractError(LifecycleError, ValueError):
    """The controller received an invalid store, hook, or lifecycle request."""


class InvalidLifecycleTransition(LifecycleContractError):
    """A requested lifecycle transition is not safe for the current state."""


# Short aliases are useful to hosts that use the vocabulary from Runtime or
# Evolution without importing those modules.
ContractError = LifecycleContractError
InvalidTransition = InvalidLifecycleTransition
LifecycleTransitionError = InvalidLifecycleTransition


class LifecyclePersistenceError(LifecycleError):
    """A durable store operation failed."""


class ConcurrentLifecycleError(LifecyclePersistenceError):
    """Another writer changed the task while a lifecycle action was running."""


class LifecycleHookError(LifecycleError):
    """A host checkpoint/event/stale-operation hook failed."""


HookError = LifecycleHookError


class StaleOperationError(LifecycleHookError):
    """A stale operation could not be safely reconciled."""


class ResourceCleanupError(LifecycleError):
    """One or more host resources could not be closed or aborted."""

    def __init__(self, message: str, *, results: Sequence[Mapping[str, Any]] = ()) -> None:
        super().__init__(message)
        self.results = [dict(item) for item in results]


CleanupError = ResourceCleanupError


class ResourceContractError(LifecycleContractError):
    """An injected resource does not satisfy the cleanup contract."""


class ResourceRegistrationError(ResourceContractError):
    """A resource identifier is already bound to another object."""


class ResourceNotFound(ResourceContractError):
    """A requested cleanup resource is not registered."""


class EvidencePreservationError(LifecycleContractError):
    """A caller attempted to disable the safe evidence-preserving default."""


# A descriptive alias for hosts that want to catch the preservation contract
# explicitly.
EvidencePreservationRequired = EvidencePreservationError


class TaskStoreProtocol(Protocol):
    """Minimal injected persistence boundary used by ``LifecycleController``."""

    def load(self, task_id: str) -> Mapping[str, Any]: ...

    def update_internal(self, task_id: str, **changes: Any) -> Mapping[str, Any]: ...

    def append_event(self, task_id: str, event: Mapping[str, Any]) -> Any: ...


class ResourceCleanupContract(Protocol):
    """Host resource contract for lifecycle cleanup.

    Implementations should make their own methods safe to call after a
    partially completed process death.  ``close`` and ``abort`` are the
    canonical names; ``shutdown`` and ``cleanup`` are accepted host fallbacks.
    ``ResourceCleanupManager`` additionally prevents duplicate successful calls
    in one controller and persists successful terminal markers when a task
    store is available.
    """

    def close(self) -> Any: ...

    def abort(self) -> Any: ...


# A few descriptive aliases make the contract easy to discover.
HostResource = ResourceCleanupContract
CleanupContract = ResourceCleanupContract


@dataclass
class _ResourceEntry:
    resource_id: str
    resource: Any
    task_id: str | None
    state: str = "open"
    action: str | None = None
    result_type: str | None = None
    error_type: str | None = None
    error: str | None = None
    updated_at: str | None = None


def _await_cleanup_result(value: Any, timeout_seconds: float) -> Any:
    if not inspect.isawaitable(value):
        return value
    if not inspect.iscoroutine(value):
        close = getattr(value, "close", None)
        if callable(close):
            close()
        raise ResourceContractError("async cleanup returned a non-coroutine awaitable")
    result_queue: queue.Queue[tuple[bool, Any]] = queue.Queue(maxsize=1)

    def runner() -> None:
        try:
            result_queue.put((True, asyncio.run(value)))
        except BaseException as exc:
            result_queue.put((False, exc))

    worker = threading.Thread(target=runner, name="ultimate-resource-cleanup", daemon=True)
    worker.start()
    try:
        ok, result = result_queue.get(timeout=timeout_seconds)
    except queue.Empty as exc:
        raise ResourceContractError("async resource cleanup exceeded its deadline") from exc
    if ok:
        return result
    raise result


class ResourceCleanupManager:
    """Register host resources and perform bounded, idempotent cleanup.

    ``close`` and ``abort`` are separate actions.  Once either action has
    completed successfully, a later call for the same resource is a no-op.
    A failed action remains retryable; the host is expected to make its own
    operation safe to retry because a callback can fail after performing an
    external side effect.

    The manager does not own or remove task evidence.  A task-aware
    ``LifecycleController`` records only compact terminal cleanup markers in
    task metadata and can therefore avoid repeating cleanup after a restart.
    """

    def __init__(self, resources: Any = None, *, async_timeout_seconds: float = 30.0) -> None:
        if isinstance(async_timeout_seconds, bool) or not isinstance(async_timeout_seconds, (int, float)) or not math.isfinite(float(async_timeout_seconds)) or async_timeout_seconds <= 0:
            raise ResourceContractError("async_timeout_seconds must be positive")
        self._entries: dict[tuple[str | None, str], _ResourceEntry] = {}
        self._persisted_markers: dict[tuple[str | None, str], tuple[str, str]] = {}
        self._next_id = 1
        self._lock = threading.RLock()
        self.async_timeout_seconds = float(async_timeout_seconds)
        if resources is not None:
            self.register_many(resources)

    @staticmethod
    def _resource_id_from_object(resource: Any, index: int) -> str:
        for attribute in ("resource_id", "id", "name"):
            value = getattr(resource, attribute, None)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return f"resource-{index}"

    @staticmethod
    def _validate_id(value: Any, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ResourceContractError(f"{label} must be a non-empty string")
        value = value.strip()
        if not _IDENTIFIER_RE.fullmatch(value):
            raise ResourceContractError(f"{label} contains an unsafe identifier")
        return value

    @staticmethod
    def _validate_task_id(value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ResourceContractError("resource task_id must be a non-empty string")
        return value.strip()

    def register(
        self,
        resource: Any,
        resource_id: str | None = None,
        *,
        task_id: str | None = None,
        replace: bool = False,
    ) -> str:
        """Register a resource and return its stable identifier.

        For compatibility with small host adapters, ``register("browser",
        browser_object)`` is accepted as well as the documented
        ``register(browser_object, "browser")`` form.
        """
        # Accept the common reversed positional spelling without making the
        # public contract ambiguous.
        if isinstance(resource, str) and resource_id is not None and not isinstance(resource_id, str):
            resource, resource_id = resource_id, resource
        if resource is None:
            raise ResourceContractError("resource must not be None")
        task = self._validate_task_id(task_id)
        with self._lock:
            if len(self._entries) >= _MAX_CLEANUP_RESOURCES and (task, resource_id) not in self._entries:
                raise ResourceContractError("too many cleanup resources")
            index = self._next_id
            candidate = resource_id or self._resource_id_from_object(resource, index)
            identifier = self._validate_id(candidate, "resource_id")
            key = (task, identifier)
            existing = self._entries.get(key)
            if existing is not None:
                if existing.resource is resource:
                    return identifier
                if not replace:
                    raise ResourceRegistrationError(f"resource_id is already registered: {identifier}")
                existing.resource = resource
                existing.state = "open"
                existing.action = None
                existing.result_type = None
                existing.error_type = None
                existing.error = None
                existing.updated_at = None
                self._next_id += 1
                return identifier
            close = getattr(resource, "close", None)
            abort = getattr(resource, "abort", None)
            shutdown = getattr(resource, "shutdown", None)
            cleanup = getattr(resource, "cleanup", None)
            if not any(callable(method) for method in (close, abort, shutdown, cleanup)):
                raise ResourceContractError("resource must provide close(), abort(), shutdown(), or cleanup()")
            entry = _ResourceEntry(identifier, resource, task)
            marker = self._persisted_markers.get(key)
            if marker is not None:
                entry.action, marker_state = marker
                entry.state = "closed" if marker_state in {"closed", "close"} else "aborted"
            self._entries[key] = entry
            self._next_id += 1
            return identifier

    def add(
        self,
        resource: Any,
        resource_id: str | None = None,
        *,
        task_id: str | None = None,
        replace: bool = False,
    ) -> str:
        """Alias for :meth:`register`."""
        return self.register(resource, resource_id, task_id=task_id, replace=replace)

    def register_resource(
        self,
        resource: Any,
        resource_id: str | None = None,
        *,
        task_id: str | None = None,
        replace: bool = False,
    ) -> str:
        """Explicitly named registration alias with task binding support."""
        return self.register(resource, resource_id, task_id=task_id, replace=replace)

    def register_for_task(
        self,
        task_id: str,
        resource: Any,
        resource_id: str | None = None,
        *,
        replace: bool = False,
    ) -> str:
        return self.register(resource, resource_id, task_id=task_id, replace=replace)

    bind_resource = register_for_task

    def register_many(self, resources: Any, *, task_id: str | None = None) -> list[str]:
        """Register a resource, mapping, iterable, or ``(id, resource)`` pairs."""
        if resources is None:
            return []
        if isinstance(resources, ResourceCleanupManager):
            return resources.register_many(resources._entries_for_task(task_id), task_id=task_id)
        if isinstance(resources, Mapping):
            result: list[str] = []
            for key, value in resources.items():
                if not isinstance(key, str):
                    raise ResourceContractError("resource mapping keys must be strings")
                result.append(self.register(value, key, task_id=task_id))
            return result
        if isinstance(resources, (str, bytes)):
            raise ResourceContractError("a resource cannot be a string")
        if isinstance(resources, tuple) and len(resources) == 2 and isinstance(resources[0], str):
            return [self.register(resources[1], resources[0], task_id=task_id)]
        if any(callable(getattr(resources, name, None)) for name in ("close", "abort", "shutdown", "cleanup")):
            return [self.register(resources, task_id=task_id)]
        try:
            values = list(resources)
        except TypeError as exc:
            raise ResourceContractError("resources must be a resource, mapping, or iterable") from exc
        result = []
        for value in values:
            if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str):
                result.append(self.register(value[1], value[0], task_id=task_id))
            else:
                result.append(self.register(value, task_id=task_id))
        return result

    def _entries_for_task(self, task_id: str | None = None) -> list[tuple[str, Any]]:
        task = self._validate_task_id(task_id)
        with self._lock:
            return [
                (entry.resource_id, entry.resource)
                for (entry_task, _), entry in self._entries.items()
                if entry_task == task
            ]

    def _select(
        self,
        resource_id: str | None,
        task_id: str | None,
        *,
        include_global: bool = True,
    ) -> list[_ResourceEntry]:
        task = self._validate_task_id(task_id)
        with self._lock:
            if resource_id is not None:
                identifier = self._validate_id(resource_id, "resource_id")
                exact = self._entries.get((task, identifier))
                if exact is not None:
                    return [exact]
                # A globally registered resource is safe to use for a task.
                return [self._entries[(None, identifier)]] if (None, identifier) in self._entries else []
            candidates = [
                entry
                for (entry_task, _), entry in self._entries.items()
                if task is None or entry_task == task or (include_global and task is not None and entry_task is None)
            ]
            if task is not None:
                candidates.sort(key=lambda entry: 0 if entry.task_id == task else 1)
            selected: list[_ResourceEntry] = []
            seen_resources: set[int] = set()
            for entry in candidates:
                identity = id(entry.resource)
                if identity in seen_resources:
                    continue
                seen_resources.add(identity)
                selected.append(entry)
            return selected

    @staticmethod
    def _method_for(entry: _ResourceEntry, action: str) -> tuple[Callable[[], Any], str]:
        preferred = getattr(entry.resource, action, None)
        if callable(preferred):
            return preferred, action
        # close-only browser adapters are common.  For hard interruption, use
        # the same graceful primitive as a safe fallback, but record the
        # requested action separately so the host can still report uncertainty.
        fallback_names = (
            ("close", "shutdown", "cleanup")
            if action == "abort"
            else ("abort", "shutdown", "cleanup")
        )
        for fallback_name in fallback_names:
            fallback = getattr(entry.resource, fallback_name, None)
            if callable(fallback):
                return fallback, fallback_name
        raise ResourceContractError(f"resource {entry.resource_id!r} has no {action}() method")

    def mark_terminal(
        self,
        resource_id: str,
        action: str,
        *,
        task_id: str | None = None,
    ) -> None:
        """Restore a durable cleanup marker after controller restart."""
        normalized = self._normalize_action(action)
        entries = self._select(resource_id, task_id)
        if not entries:
            raise ResourceNotFound(resource_id)
        with self._lock:
            entry = entries[0]
            entry.state = "closed" if normalized == "close" else "aborted"
            entry.action = normalized
            entry.updated_at = _utc_now()

    def restore(self, markers: Mapping[str, Any], *, task_id: str | None = None) -> None:
        """Apply persisted ``{resource_id: marker}`` cleanup records.

        Markers are retained even when a host registers its resource after a
        restart.  Existing entries are marked terminal immediately.
        """
        if not isinstance(markers, Mapping):
            raise ResourceContractError("cleanup markers must be an object")
        task = self._validate_task_id(task_id)
        with self._lock:
            for raw_id, marker in markers.items():
                if not isinstance(raw_id, str):
                    continue
                resource_id = self._validate_id(raw_id, "resource_id")
                if isinstance(marker, str):
                    action, state = marker, marker
                elif isinstance(marker, Mapping):
                    action = marker.get("action")
                    state = marker.get("status", marker.get("state"))
                else:
                    continue
                if state in {"closed", "close"}:
                    normalized_action = "close"
                    terminal_state = "closed"
                elif state in {"aborted", "abort"}:
                    normalized_action = "abort"
                    terminal_state = "aborted"
                else:
                    continue
                if action not in {None, "close", "abort", "closed", "aborted", "cancel", "cancelled"}:
                    continue
                keys = {(task, resource_id)}
                if task is not None:
                    keys.add((None, resource_id))
                for key in keys:
                    if key not in self._persisted_markers and len(self._persisted_markers) >= _MAX_CLEANUP_RESOURCES:
                        raise ResourceContractError("too many persisted cleanup markers")
                    self._persisted_markers[key] = (normalized_action, terminal_state)
                    entry = self._entries.get(key)
                    if entry is not None:
                        entry.state = terminal_state
                        entry.action = normalized_action
                        entry.updated_at = _utc_now()

    @staticmethod
    def _normalize_action(action: Any) -> str:
        if action in {"close", "closed"}:
            return "close"
        if action in {"abort", "aborted", "cancel", "cancelled"}:
            return "abort"
        raise ResourceContractError("cleanup action must be 'close' or 'abort'")

    @staticmethod
    def _call_resource_method(method: Callable[..., Any], entry: _ResourceEntry, action: str) -> Any:
        """Call a host cleanup method with either its zero-arg or context form."""
        try:
            signature = inspect.signature(method)
        except (TypeError, ValueError):
            return method()
        parameters = list(signature.parameters.values())
        required = [
            item
            for item in parameters
            if item.default is inspect.Parameter.empty
            and item.kind in {
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            }
        ]
        if not required:
            return method()
        context = {
            "task_id": entry.task_id,
            "resource_id": entry.resource_id,
            "action": action,
        }
        if any(item.name in {"task_id", "task"} for item in required):
            return method(task_id=entry.task_id)
        if len(required) == 1:
            return method(context)
        return method(**context)

    def _perform(self, entry: _ResourceEntry, action: str) -> dict[str, Any]:
        requested_action = action
        if entry.state in {"closed", "aborted"}:
            return {
                "resource_id": entry.resource_id,
                "action": requested_action,
                "status": entry.state,
                "changed": False,
                "already_done": True,
            }
        method, method_name = self._method_for(entry, action)
        try:
            result = self._call_resource_method(method, entry, requested_action)
            if inspect.isawaitable(result):
                result = _await_cleanup_result(result, self.async_timeout_seconds)
        except Exception as exc:  # host boundary: report, do not erase evidence
            entry.state = "failed"
            entry.action = requested_action
            entry.error_type = type(exc).__name__
            entry.error = str(exc)[:_MAX_REASON_CHARS]
            entry.updated_at = _utc_now()
            raise ResourceCleanupError(
                f"resource {entry.resource_id!r} {requested_action} failed: {type(exc).__name__}",
                results=(),
            ) from exc
        entry.state = "closed" if requested_action == "close" else "aborted"
        entry.action = requested_action
        entry.result_type = type(result).__name__
        entry.error_type = None
        entry.error = None
        entry.updated_at = _utc_now()
        return {
            "resource_id": entry.resource_id,
            "action": requested_action,
            "method": method_name,
            "status": entry.state,
            "changed": True,
            "already_done": False,
        }

    def cleanup(
        self,
        action: str = "close",
        *,
        task_id: str | None = None,
        resource_id: str | None = None,
        preserve_evidence: bool = True,
        mode: str | None = None,
        include_global: bool = True,
    ) -> dict[str, Any]:
        """Close or abort one/all registered resources.

        The operation attempts every selected resource even when one fails, then
        raises :class:`ResourceCleanupError` with a compact per-resource report.
        """
        if preserve_evidence is not True:
            raise EvidencePreservationError("cleanup always preserves task evidence")
        if mode is not None:
            if action != "close" and action != mode:
                raise ResourceContractError("provide only one of action or mode")
            action = mode
        normalized = self._normalize_action(action)
        entries = self._select(resource_id, task_id, include_global=include_global)
        if resource_id is not None and not entries:
            raise ResourceNotFound(resource_id)
        results: list[dict[str, Any]] = []
        failures: list[tuple[str, Exception]] = []
        with self._lock:
            for entry in entries:
                try:
                    results.append(self._perform(entry, normalized))
                except ResourceCleanupError as exc:
                    results.append({
                        "resource_id": entry.resource_id,
                        "action": normalized,
                        "status": "failed",
                        "changed": False,
                        "already_done": False,
                        "error_type": entry.error_type,
                        "error": entry.error,
                    })
                    failures.append((entry.resource_id, exc))
        report = {
            "success": not failures,
            "action": normalized,
            "resources": results,
            "changed": sum(1 for item in results if item.get("changed")),
            "already_done": sum(1 for item in results if item.get("already_done")),
            "evidence_preserved": True,
        }
        if failures:
            raise ResourceCleanupError(
                f"{len(failures)} cleanup resource(s) failed",
                results=results,
            )
        return report

    def close(
        self,
        resource_id: str | None = None,
        *,
        task_id: str | None = None,
        preserve_evidence: bool = True,
    ) -> dict[str, Any]:
        resource_id, task_id = self._resolve_cleanup_target(resource_id, task_id)
        return self.cleanup(
            action="close",
            task_id=task_id,
            resource_id=resource_id,
            preserve_evidence=preserve_evidence,
        )

    def abort(
        self,
        resource_id: str | None = None,
        *,
        task_id: str | None = None,
        preserve_evidence: bool = True,
    ) -> dict[str, Any]:
        resource_id, task_id = self._resolve_cleanup_target(resource_id, task_id)
        return self.cleanup(
            action="abort",
            task_id=task_id,
            resource_id=resource_id,
            preserve_evidence=preserve_evidence,
        )

    def _resolve_cleanup_target(
        self,
        resource_id: str | None,
        task_id: str | None,
    ) -> tuple[str | None, str | None]:
        if resource_id is None or task_id is not None:
            return resource_id, task_id
        # ``close("task-id")`` is a convenient task-scoped spelling when no
        # resource has that identifier.  Explicit resource_id/task_id pairs
        # remain unambiguous.
        with self._lock:
            if (None, resource_id) in self._entries:
                return resource_id, None
            if any(entry.task_id == resource_id for entry in self._entries.values()):
                return None, resource_id
        return resource_id, None

    def close_all(self, *, task_id: str | None = None, preserve_evidence: bool = True) -> dict[str, Any]:
        return self.close(task_id=task_id, preserve_evidence=preserve_evidence)

    def abort_all(self, *, task_id: str | None = None, preserve_evidence: bool = True) -> dict[str, Any]:
        return self.abort(task_id=task_id, preserve_evidence=preserve_evidence)

    def status(self, *, task_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {
                    "resource_id": entry.resource_id,
                    "task_id": entry.task_id,
                    "state": entry.state,
                    "action": entry.action,
                    "error_type": entry.error_type,
                    "error": entry.error,
                    "updated_at": entry.updated_at,
                }
                for entry in self._select(None, task_id)
            ]

    def __enter__(self) -> "ResourceCleanupManager":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if exc_type is None:
            self.close_all()
        else:
            self.abort_all()
        return False

    def reset_for_testing(self, *, task_id: str | None = None) -> None:
        """Forget in-memory resource state without touching task evidence.

        This is intentionally explicit and exists for hosts that create a
        fresh resource object after a process restart.  It does not unregister
        the object or call a host callback.
        """
        task = self._validate_task_id(task_id)
        with self._lock:
            for key, entry in list(self._entries.items()):
                if task is None or key[0] in {task, None}:
                    entry.state = "open"
                    entry.action = None
                    entry.error_type = None
                    entry.error = None
                    entry.updated_at = None


# Compatibility names for hosts that call the registry a contract/registry.
HostResourceCleanup = ResourceCleanupManager
CleanupManager = ResourceCleanupManager
ResourceRegistry = ResourceCleanupManager


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _normalise_timestamp(value: Any) -> str:
    if value is None:
        return _utc_now()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(value)))
        except (OverflowError, OSError, ValueError) as exc:
            raise LifecycleContractError("clock returned an invalid timestamp") from exc
    if hasattr(value, "isoformat"):
        try:
            return str(value.isoformat()).replace("+00:00", "Z")
        except Exception as exc:  # pragma: no cover - defensive host boundary
            raise LifecycleContractError("clock returned an invalid timestamp") from exc
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise LifecycleContractError("clock must return a timestamp-like value")


def _validate_task_id(task_id: Any) -> str:
    if not isinstance(task_id, str) or not task_id.strip():
        raise LifecycleContractError("task_id must be a non-empty string")
    task_id = task_id.strip()
    if not _IDENTIFIER_RE.fullmatch(task_id) or task_id in {".", ".."}:
        raise LifecycleContractError("task_id contains an unsafe identifier")
    return task_id


def _validate_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise LifecycleContractError(f"{label} must be boolean")
    return value


def _validate_reason(reason: Any) -> str | None:
    if reason is None:
        return None
    if not isinstance(reason, str):
        raise LifecycleContractError("lifecycle reason must be a string")
    reason = reason.strip()
    if not reason:
        return None
    if len(reason) > _MAX_REASON_CHARS:
        raise LifecycleContractError(f"lifecycle reason exceeds {_MAX_REASON_CHARS} characters")
    return reason


def _json_safe(value: Any, label: str = "value") -> Any:
    try:
        return json.loads(json.dumps(value, allow_nan=False, ensure_ascii=False))
    except (TypeError, ValueError, OverflowError) as exc:
        raise LifecycleContractError(f"{label} must be JSON serializable") from exc


def _copy_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise LifecyclePersistenceError(f"{label} must be an object")
    return copy.deepcopy(dict(value))


class LifecycleState(str, Enum):
    """Public names for the controller-owned lifecycle states."""

    PAUSED = "paused"
    INTERRUPTED = "interrupted"
    ABANDONED = "abandoned"


PAUSED = LifecycleState.PAUSED.value
INTERRUPTED = LifecycleState.INTERRUPTED.value
ABANDONED = LifecycleState.ABANDONED.value
TaskLifecycleState = LifecycleState
LifecycleStatus = LifecycleState


class CleanupAction(str, Enum):
    CLOSE = "close"
    ABORT = "abort"


CleanupMode = CleanupAction


class LifecycleController:
    """Coordinate explicit task lifecycle actions over an injected store.

    Parameters
    ----------
    task_store:
        Object implementing the small persistence boundary described by
        :class:`TaskStoreProtocol`.  ``store=`` is accepted as a keyword alias.
    checkpoint_hook, event_hook:
        Optional synchronous host callbacks.  They are called with the
        checkpoint/event payload plus ``task_id`` and ``state`` when accepted
        by their signature.  Hook failures are surfaced and never silently
        treated as successful durability.
    stale_operation_handler:
        Optional callback for operations that are active after a hard
        interruption or whose lease is expired.  With no callback, the
        controller conservatively marks eligible operations ``uncertain``.
    resources:
        Optional :class:`ResourceCleanupManager`, a resource, a mapping of
        named resources, or an iterable of resources.
    """

    def __init__(
        self,
        task_store: Any = None,
        *,
        store: Any = None,
        checkpoint_hook: Any = None,
        event_hook: Any = None,
        stale_operation_handler: Any = None,
        resources: Any = None,
        resource_manager: Any = None,
        host: Any = None,
        hooks: Mapping[str, Any] | None = None,
        on_checkpoint: Any = None,
        on_event: Any = None,
        checkpoint_callback: Any = None,
        event_callback: Any = None,
        checkpoint: Any = None,
        event: Any = None,
        stale_handler: Any = None,
        on_stale_operation: Any = None,
        resource_cleanup: Any = None,
        host_cleanup: Any = None,
        stale_operation_policy: Any = None,
        stale_operation: Any = None,
        clock: Callable[[], Any] | None = None,
        preserve_evidence: bool = True,
        require_checkpoint: bool = False,
        include_global_resources: bool = True,
    ) -> None:
        if task_store is not None and store is not None and task_store is not store:
            raise LifecycleContractError("task_store and store refer to different objects")
        selected_store = task_store if task_store is not None else store
        if selected_store is None:
            raise LifecycleContractError("an injected task store is required")
        if not callable(getattr(selected_store, "load", None)) and callable(getattr(getattr(selected_store, "store", None), "load", None)):
            selected_store = selected_store.store
        if not callable(getattr(selected_store, "load", None)):
            raise LifecycleContractError("task store must provide load(task_id)")
        if not callable(getattr(selected_store, "update_internal", None)) and not callable(
            getattr(selected_store, "update_if_status", None)
        ):
            raise LifecycleContractError("task store must provide update_internal() or update_if_status()")
        self.store = selected_store
        self.task_store = selected_store
        # Accept the common callback spellings without duplicating lifecycle
        # behavior.  An explicitly supplied canonical name wins only when no
        # alias was provided.
        if checkpoint_hook is None:
            checkpoint_hook = on_checkpoint
        if checkpoint_hook is None:
            checkpoint_hook = checkpoint_callback
        if checkpoint_hook is None:
            checkpoint_hook = checkpoint
        if event_hook is None:
            event_hook = on_event
        if event_hook is None:
            event_hook = event_callback
        if event_hook is None:
            event_hook = event
        if stale_operation_handler is None:
            stale_operation_handler = stale_handler
        if stale_operation_handler is None:
            stale_operation_handler = on_stale_operation
        if stale_operation_handler is None:
            stale_operation_handler = stale_operation_policy
        if stale_operation_handler is None:
            stale_operation_handler = stale_operation
        if resources is None:
            resources = resource_cleanup
        if resources is None:
            resources = host_cleanup
        self._clock = clock or _utc_now
        if not callable(self._clock):
            raise LifecycleContractError("clock must be callable")
        if not isinstance(preserve_evidence, bool):
            raise LifecycleContractError("preserve_evidence must be boolean")
        self.preserve_evidence = preserve_evidence
        self.require_checkpoint = _validate_bool(require_checkpoint, "require_checkpoint")
        self.include_global_resources = _validate_bool(include_global_resources, "include_global_resources")

        if isinstance(hooks, Mapping):
            checkpoint_hook = hooks.get(
                "checkpoint",
                hooks.get("checkpoint_hook", hooks.get("on_checkpoint", checkpoint_hook)),
            )
            event_hook = hooks.get(
                "event",
                hooks.get("event_hook", hooks.get("on_event", event_hook)),
            )
            stale_operation_handler = hooks.get(
                "stale_operation",
                hooks.get(
                    "stale_operation_handler",
                    hooks.get("on_stale_operation", stale_operation_handler),
                ),
            )
        self.checkpoint_hook = self._coerce_hook(
            checkpoint_hook,
            ("checkpoint", "checkpoint_hook", "save_checkpoint", "on_checkpoint"),
            "checkpoint_hook",
        )
        self.event_hook = self._coerce_hook(
            event_hook,
            ("event", "event_hook", "append_event", "emit", "on_event"),
            "event_hook",
        )
        self.stale_operation_handler = self._coerce_hook(
            stale_operation_handler,
            ("handle", "recover", "stale_operation_handler", "on_stale_operation", "stale_operation"),
            "stale_operation_handler",
        )

        if resource_manager is not None and resources is not None:
            raise LifecycleContractError("use resource_manager or resources, not both")
        selected_resources = resource_manager if resource_manager is not None else resources
        if isinstance(selected_resources, ResourceCleanupManager):
            self.resource_manager = selected_resources
        else:
            self.resource_manager = ResourceCleanupManager()
            if selected_resources is not None:
                self.resource_manager.register_many(selected_resources)
        if host is not None:
            self.resource_manager.register(host, "host")
        self.resources = self.resource_manager

    @staticmethod
    def _coerce_hook(value: Any, method_names: Sequence[str], label: str) -> Any:
        if value is None:
            return None
        if callable(value):
            return value
        for name in method_names:
            candidate = getattr(value, name, None)
            if callable(candidate):
                return candidate
        raise LifecycleContractError(f"{label} must be callable or expose a supported method")

    def _now(self) -> str:
        return _normalise_timestamp(self._clock())

    def _load(self, task_id: str) -> dict[str, Any]:
        task = _validate_task_id(task_id)
        try:
            value = self.store.load(task)
        except Exception as exc:
            raise LifecyclePersistenceError(f"unable to load task {task!r}: {type(exc).__name__}") from exc
        return _copy_mapping(value, f"task {task!r} state")

    @staticmethod
    def _state_status(state: Mapping[str, Any]) -> str:
        status = state.get("status")
        if not isinstance(status, str) or not status.strip():
            raise LifecycleContractError("task state status must be a non-empty string")
        return status.strip()

    @staticmethod
    def _lifecycle_metadata(state: Mapping[str, Any]) -> dict[str, Any]:
        value = state.get("lifecycle", {})
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise LifecycleContractError("task lifecycle metadata must be an object")
        return copy.deepcopy(dict(value))

    def _invoke_hook(
        self,
        hook: Any,
        label: str,
        *,
        task_id: str,
        state: Mapping[str, Any] | None = None,
        event: Mapping[str, Any] | None = None,
        checkpoint: Any = None,
        operation: Mapping[str, Any] | None = None,
        reason: str | None = None,
    ) -> Any:
        if hook is None:
            return None
        copied_state = copy.deepcopy(dict(state)) if isinstance(state, Mapping) else state
        copied_event = copy.deepcopy(dict(event)) if isinstance(event, Mapping) else event
        copied_operation = copy.deepcopy(dict(operation)) if isinstance(operation, Mapping) else operation
        event_type = copied_event.get("type") if isinstance(copied_event, Mapping) else None
        event_action = copied_event.get("action") if isinstance(copied_event, Mapping) else None
        values: dict[str, Any] = {
            "task_id": task_id,
            "state": copied_state,
            "context": copied_state,
            "ctx": copied_state,
            "event": copied_event,
            "payload": copied_event,
            "record": copied_event,
            "event_type": event_type,
            "kind": event_type,
            "action": event_action if event_action is not None else reason,
            "checkpoint": checkpoint,
            "checkpoint_path": checkpoint,
            "path": checkpoint,
            "operation": copied_operation,
            "op": copied_operation,
            "operation_id": copied_operation.get("operation_id") if isinstance(copied_operation, Mapping) else None,
            "reason": reason,
        }
        if "checkpoint" in label:
            ordered = [checkpoint, task_id, state, reason, event]
        elif "stale" in label:
            ordered = [operation, task_id, reason, state, event]
        else:
            ordered = [event, task_id, state, reason, checkpoint]
        ordered = [value for value in ordered if value is not None]
        try:
            signature = inspect.signature(hook)
        except (TypeError, ValueError):
            signature = None
        try:
            if signature is None:
                # A few extension callables do not expose a signature.  The
                # keyword form is the documented form; only fall back to a
                # single positional form when the keyword form is rejected by
                # the callable boundary itself.
                try:
                    return hook(**{key: value for key, value in values.items() if value is not None})
                except TypeError:
                    if not ordered:
                        return hook()
                    return hook(*ordered)
            parameters = list(signature.parameters.values())
            has_var_kw = any(item.kind == inspect.Parameter.VAR_KEYWORD for item in parameters)
            has_var_args = any(item.kind == inspect.Parameter.VAR_POSITIONAL for item in parameters)
            if has_var_kw:
                return hook(**{key: value for key, value in values.items() if value is not None})
            named = {
                item.name: values[item.name]
                for item in parameters
                if item.name in values and values[item.name] is not None
            }
            required = [
                item
                for item in parameters
                if item.default is inspect.Parameter.empty
                and item.kind in {
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                }
            ]
            positional_only = [item for item in parameters if item.kind == inspect.Parameter.POSITIONAL_ONLY]
            missing = [item for item in required if item.name not in named]
            if not missing and not positional_only and not has_var_args:
                return hook(**named)
            positional_parameters = [
                item
                for item in parameters
                if item.kind in {
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                }
            ]
            args: list[Any] = []
            used_candidates: set[int] = set()
            for index, item in enumerate(positional_parameters):
                if item.name in values and values[item.name] is not None:
                    value = values[item.name]
                    args.append(value)
                    for candidate_index, candidate in enumerate(ordered):
                        if candidate_index not in used_candidates and candidate is value:
                            used_candidates.add(candidate_index)
                            break
                    continue
                candidate_index = next(
                    (candidate for candidate, value in enumerate(ordered) if value is not None and candidate not in used_candidates),
                    None,
                )
                if candidate_index is not None:
                    args.append(ordered[candidate_index])
                    used_candidates.add(candidate_index)
                elif item.default is not inspect.Parameter.empty:
                    break
                else:
                    raise LifecycleHookError(f"{label} has an unsupported required parameter: {item.name}")
            # Keyword-only parameters cannot be supplied positionally; retain
            # only those values when invoking the callback.
            keyword_only = {
                item.name: named[item.name]
                for item in parameters
                if item.kind == inspect.Parameter.KEYWORD_ONLY and item.name in named
            }
            if has_var_args:
                for candidate_index, value in enumerate(ordered):
                    if value is not None and candidate_index not in used_candidates:
                        args.append(value)
            return hook(*args, **keyword_only)
        except LifecycleHookError:
            raise
        except Exception as exc:
            raise LifecycleHookError(f"{label} failed: {type(exc).__name__}") from exc

    def _checkpoint(self, task_id: str, state: Mapping[str, Any], *, action: str) -> Any:
        checkpoint = None
        method = getattr(self.store, "checkpoint", None)
        if callable(method):
            try:
                try:
                    signature = inspect.signature(method)
                    positional = [
                        item for item in signature.parameters.values()
                        if item.kind in {
                            inspect.Parameter.POSITIONAL_ONLY,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        }
                    ]
                    has_varargs = any(item.kind == inspect.Parameter.VAR_POSITIONAL for item in signature.parameters.values())
                except (TypeError, ValueError):
                    positional = []
                    has_varargs = False
                checkpoint = method(task_id, state) if len(positional) >= 2 or has_varargs else method(task_id)
            except Exception as exc:
                raise LifecyclePersistenceError(f"checkpoint failed: {type(exc).__name__}") from exc
        if self.require_checkpoint and checkpoint is None and self.checkpoint_hook is None:
            raise LifecyclePersistenceError("durable checkpointing is required but unavailable")
        if self.checkpoint_hook is not None:
            self._invoke_hook(
                self.checkpoint_hook,
                "checkpoint hook",
                task_id=task_id,
                state=state,
                checkpoint=checkpoint,
                reason=action,
            )
        return checkpoint

    def _append_event(
        self,
        task_id: str,
        event: Mapping[str, Any],
        *,
        state: Mapping[str, Any] | None = None,
        failure: bool = False,
    ) -> Any:
        if not isinstance(event, Mapping):
            raise LifecycleContractError("lifecycle event must be an object")
        payload = _json_safe(dict(event), "lifecycle event")
        method = getattr(self.store, "append_event", None)
        result = None
        if callable(method):
            try:
                try:
                    signature = inspect.signature(method)
                    parameters = list(signature.parameters.values())
                    event_kw = next((item for item in parameters if item.name in {"event", "payload", "record"} and item.kind == inspect.Parameter.KEYWORD_ONLY), None)
                except (TypeError, ValueError):
                    event_kw = None
                result = method(task_id, event=payload) if event_kw is not None else method(task_id, payload)
            except Exception as exc:
                raise LifecyclePersistenceError(f"event persistence failed: {type(exc).__name__}") from exc
        elif self.event_hook is None:
            raise LifecyclePersistenceError("task store must provide append_event() or an event hook")
        if self.event_hook is not None:
            self._invoke_hook(
                self.event_hook,
                "event hook",
                task_id=task_id,
                state=state,
                event=payload,
                reason=payload.get("reason") if isinstance(payload, Mapping) else None,
            )
        return result

    def _update(self, task_id: str, changes: Mapping[str, Any], *, expected_status: str | None = None) -> dict[str, Any]:
        values = _json_safe(dict(changes), "lifecycle state changes")
        method = getattr(self.store, "update_if_status", None)
        if callable(method) and expected_status is not None:
            try:
                signature = inspect.signature(method)
                accepts_internal = "_internal" in signature.parameters or any(
                    item.kind == inspect.Parameter.VAR_KEYWORD for item in signature.parameters.values()
                )
            except (TypeError, ValueError):
                accepts_internal = True
            try:
                if accepts_internal:
                    result = method(task_id, expected_status, values, _internal=True)
                else:
                    result = method(task_id, expected_status, values)
            except TypeError as exc:
                # A small fake store may expose a simpler three-argument
                # method.  Do not retry when the method itself raised a
                # TypeError unless its signature explicitly lacks _internal.
                if accepts_internal:
                    raise LifecyclePersistenceError("conditional state update failed") from exc
                try:
                    result = method(task_id, expected_status, values)
                except Exception as retry_exc:
                    raise LifecyclePersistenceError("conditional state update failed") from retry_exc
            except Exception as exc:
                raise LifecyclePersistenceError("conditional state update failed") from exc
            if result is False:
                raise ConcurrentLifecycleError("task state changed concurrently; retry the lifecycle action")
            if result is True or result is None:
                try:
                    current = self._load(task_id)
                except LifecyclePersistenceError:
                    current = None
                if current is not None and current.get("status") != expected_status:
                    raise ConcurrentLifecycleError("task state changed concurrently; retry the lifecycle action")
                return current or {"status": expected_status, **values}
            updated = _copy_mapping(result, "updated task state")
            if "status" in values and updated.get("status") != values["status"]:
                raise LifecyclePersistenceError("task store did not apply the requested status")
            return updated
        method = getattr(self.store, "update_internal", None)
        if not callable(method):
            raise LifecyclePersistenceError("task store cannot persist lifecycle state")
        try:
            try:
                signature = inspect.signature(method)
                accepts_kwargs = any(item.kind == inspect.Parameter.VAR_KEYWORD for item in signature.parameters.values())
            except (TypeError, ValueError):
                accepts_kwargs = True
            result = method(task_id, **values) if accepts_kwargs else method(task_id, values)
        except Exception as exc:
            raise LifecyclePersistenceError(f"state persistence failed: {type(exc).__name__}") from exc
        if result is True:
            return self._load(task_id)
        if result is False:
            raise LifecyclePersistenceError("task state update was rejected")
        if result is None:
            updated = self._load(task_id)
        else:
            updated = _copy_mapping(result, "updated task state")
        if "status" in values and updated.get("status") != values["status"]:
            raise LifecyclePersistenceError("task store did not apply the requested status")
        return updated

    def _update_metadata(self, task_id: str, metadata: Mapping[str, Any], *, expected_status: str | None = None) -> dict[str, Any]:
        return self._update(task_id, {"lifecycle": dict(metadata)}, expected_status=expected_status)

    @staticmethod
    def _target_for_resume(source: str, metadata: Mapping[str, Any], explicit: str | None) -> str:
        if explicit is not None:
            target = explicit
        else:
            target = metadata.get("resume_status") or metadata.get("previous_status")
        if not isinstance(target, str) or not target.strip():
            target = "ready"
        target = target.strip()
        if target in TERMINAL_STATUSES or target in {"paused", "interrupted"}:
            raise InvalidLifecycleTransition(f"cannot resume task to unsafe status {target!r}")
        if target not in RESUMABLE_STATUSES:
            raise InvalidLifecycleTransition(f"cannot resume task to unknown status {target!r}")
        # A hard interruption can leave an external side effect in flight.
        # Never silently return to an executing/verifying phase; require the
        # host to reconcile it through ``recovering`` first.
        if (source == "interrupted" or metadata.get("recovery_required") is True) and target in {
            "executing",
            "observing",
            "verifying",
            "running",
            "in_progress",
            "working",
        }:
            return "recovering"
        if source == "interrupted" and target == "failed":
            return "recovering"
        if source == "paused" and target == "failed":
            return "recovering"
        return target

    @staticmethod
    def _append_history(metadata: dict[str, Any], entry: Mapping[str, Any]) -> None:
        history = metadata.setdefault("history", [])
        if not isinstance(history, list):
            history = []
            metadata["history"] = history
        history.append(dict(entry))
        if len(history) > _MAX_HOOK_HISTORY:
            del history[:-_MAX_HOOK_HISTORY]

    def state(self, task_id: str) -> dict[str, Any]:
        """Return a detached lifecycle snapshot for a task."""
        return self._load(task_id)

    def checkpoint(self, task_id: str, *, action: str = "manual") -> Any:
        """Create a durable checkpoint without changing task status."""
        task = _validate_task_id(task_id)
        state = self._load(task)
        return self._checkpoint(task, state, action=_validate_reason(action) or "manual")

    def emit_event(self, task_id: str, event: Mapping[str, Any]) -> Any:
        """Append a bounded lifecycle event through the injected boundary."""
        task = _validate_task_id(task_id)
        state = self._load(task)
        return self._append_event(task, event, state=state)

    def register_resource(
        self,
        task_id: str,
        resource: Any,
        resource_id: str | None = None,
    ) -> str:
        """Register a host resource for a specific task."""
        return self.resource_manager.register(resource, resource_id, task_id=_validate_task_id(task_id))

    def _transition_state(
        self,
        task_id: str,
        target: str,
        *,
        action: str,
        reason: str | None,
        resume_status: str | None = None,
        extra: Mapping[str, Any] | None = None,
        checkpoint: bool = True,
    ) -> dict[str, Any]:
        state = self._load(task_id)
        current = self._state_status(state)
        if target not in LIFECYCLE_STATES | RESUMABLE_STATUSES:
            raise InvalidLifecycleTransition(f"unsupported lifecycle target: {target!r}")
        if current in TERMINAL_STATUSES:
            raise InvalidLifecycleTransition(f"task is terminal ({current}) and cannot transition to {target}")
        if current not in ACTIVE_STATUSES:
            raise InvalidLifecycleTransition(f"unknown current task status: {current!r}")
        if target == "paused" and current == "paused":
            raise InvalidLifecycleTransition("task is already paused")
        if target == "interrupted" and current == "interrupted":
            raise InvalidLifecycleTransition("task is already interrupted")
        # ``abandoned`` is intentionally routed through this same atomic
        # status/metadata update after its caller has completed cleanup.
        metadata = self._lifecycle_metadata(state)
        now = self._now()
        previous_resume = metadata.get("resume_status")
        if target == "paused":
            metadata.update({
                "schema_version": LIFECYCLE_SCHEMA_VERSION,
                "status": "paused",
                "state": "paused",
                "previous_status": current,
                "resume_status": current,
                "paused_at": now,
                "last_action": "pause",
                "reason": reason,
                "evidence_preserved": True,
            })
            metadata.pop("interrupted_at", None)
            metadata.pop("hard_interruption", None)
            metadata.pop("recovery_required", None)
        elif target == "interrupted":
            metadata.update({
                "schema_version": LIFECYCLE_SCHEMA_VERSION,
                "status": "interrupted",
                "previous_status": current,
                "resume_status": previous_resume if current == "paused" and isinstance(previous_resume, str) else current,
                "interrupted_from": current,
                "interrupted_at": now,
                "last_action": "interrupt",
                "reason": reason,
                "hard_interruption": True,
                "evidence_preserved": True,
            })
            metadata.pop("paused_at", None)
        elif target == "abandoned":
            metadata.update({
                "schema_version": LIFECYCLE_SCHEMA_VERSION,
                "status": "abandoned",
                "state": "abandoned",
                "previous_status": current,
                "abandoned_at": now,
                "last_action": "abandon",
                "reason": reason,
                "terminal": True,
                "evidence_preserved": True,
            })
        else:
            source = current
            target = self._target_for_resume(source, metadata, resume_status)
            metadata.update({
                "schema_version": LIFECYCLE_SCHEMA_VERSION,
                "status": target,
                "state": target,
                "resumed_at": now,
                "resumed_from": source,
                "last_action": "resume",
                "reason": reason,
                "evidence_preserved": True,
            })
            metadata["resume_status"] = target
            metadata.pop("paused_at", None)
            metadata.pop("interrupted_at", None)
            metadata.pop("hard_interruption", None)
            metadata["terminal"] = False
        if extra:
            metadata.update(copy.deepcopy(dict(extra)))
        for pending_key in ("pending_action", "pending_target", "cleanup_pending", "pending_reason"):
            metadata.pop(pending_key, None)
        self._append_history(metadata, {
            "action": action,
            "from": current,
            "to": target,
            "at": now,
            "reason": reason,
        })
        if checkpoint:
            self._checkpoint(task_id, state, action=action)
        updated = self._update(
            task_id,
            {"status": target, "lifecycle": metadata},
            expected_status=current,
        )
        event = {
            "type": "lifecycle_transition",
            "action": action,
            "event": action,
            "from": current,
            "to": target,
            "status": target,
            "previous_status": current,
            "lifecycle_state": target,
            "reason": reason,
            "evidence_preserved": True,
        }
        self._append_event(task_id, event, state=updated)
        return updated

    def _record_failure_event(self, task_id: str, action: str, error: BaseException, *, state: Mapping[str, Any] | None = None) -> None:
        try:
            event = {
                "type": "lifecycle_failure",
                "action": action,
                "error_type": type(error).__name__,
                "error": f"{type(error).__name__} during {action}",
                "evidence_preserved": True,
            }
            results = getattr(error, "results", ())
            if results:
                event["resources"] = [
                    {
                        "resource_id": item.get("resource_id"),
                        "status": item.get("status"),
                        "error_type": item.get("error_type"),
                    }
                    for item in results
                    if isinstance(item, Mapping)
                ]
            self._append_event(
                task_id,
                event,
                state=state,
                failure=True,
            )
        except Exception:
            # The original failure is more useful to the caller.  Durable
            # state/evidence are never deleted as a fallback.
            pass

    def _operations(self, task_id: str) -> list[Mapping[str, Any]]:
        method = getattr(self.store, "list_operations", None)
        if not callable(method):
            return []
        try:
            values = method(task_id)
        except Exception as exc:
            raise StaleOperationError(f"unable to list operations: {type(exc).__name__}") from exc
        if values is None:
            return []
        if isinstance(values, (str, bytes, Mapping)):
            raise StaleOperationError("task store list_operations() must return a sequence")
        try:
            values = list(values)
        except TypeError as exc:
            raise StaleOperationError("task store list_operations() must return a sequence") from exc
        result: list[Mapping[str, Any]] = []
        for value in values:
            if not isinstance(value, Mapping):
                raise StaleOperationError("task store returned a malformed operation record")
            result.append(value)
        return result

    @staticmethod
    def _operation_expired(operation: Mapping[str, Any], cutoff: float) -> bool:
        lease = operation.get("lease_expires_at_epoch")
        return isinstance(lease, (int, float)) and not isinstance(lease, bool) and float(lease) <= cutoff

    def _persist_uncertain_operation(
        self,
        task_id: str,
        operation_id: str,
        *,
        reason: str,
    ) -> None:
        method = getattr(self.store, "update_operation", None)
        if not callable(method):
            return
        timestamp = self._now()
        def mark(operation: dict[str, Any]) -> dict[str, Any]:
            if operation.get("status") not in {"pending", "running"}:
                return operation
            operation["status"] = "uncertain"
            if "result" in operation:
                operation["previous_result"] = operation["result"]
            operation["result"] = {
                "success": False,
                "code": "operation_interrupted",
                "error": reason,
                "uncertain": True,
            }
            operation["updated_at"] = timestamp
            operation["recovered_at"] = timestamp
            operation["recovery_reason"] = reason
            operation["lease_expires_at_epoch"] = None
            return operation
        try:
            method(task_id, operation_id, mark)
        except FileNotFoundError:
            return
        except Exception as exc:
            raise StaleOperationError(f"unable to mark operation {operation_id!r} uncertain") from exc

    def recover_stale_operations(
        self,
        task_id: str,
        *,
        now: float | None = None,
        force: bool = False,
        reason: str = "stale operation",
    ) -> int:
        """Reconcile pending/running operations without replaying side effects.

        Only operations with an expired lease are selected unless ``force`` is
        true.  The default durable result is ``uncertain``.  A custom handler
        may return an updated operation mapping; otherwise the conservative
        fallback is persisted when the store supports ``update_operation``.
        """
        task = _validate_task_id(task_id)
        task_state = self._load(task)
        reason = _validate_reason(reason) or "stale operation"
        if now is None:
            cutoff = time.time()
        else:
            try:
                cutoff = float(now.timestamp()) if hasattr(now, "timestamp") else float(now)
            except (TypeError, ValueError, AttributeError, OverflowError, OSError) as exc:
                raise LifecycleContractError("now must be a finite epoch number") from exc
            if cutoff != cutoff or cutoff in {float("inf"), float("-inf")}:
                raise LifecycleContractError("now must be a finite epoch number")
        list_operations = getattr(self.store, "list_operations", None)
        if not callable(list_operations):
            recovery = getattr(self.store, "recover_stale_operations", None)
            if callable(recovery):
                try:
                    return int(recovery(task) or 0)
                except Exception as exc:
                    raise StaleOperationError("stale-operation recovery failed") from exc
            return 0
        try:
            operations = self._operations(task)
        except StaleOperationError:
            # Some Runtime-like injected boundaries expose recovery directly
            # but not list_operations.  Use it as a best-effort hook.
            recovery = getattr(self.store, "recover_stale_operations", None)
            if not callable(recovery):
                raise
            try:
                return int(recovery(task) or 0)
            except Exception as exc:
                raise StaleOperationError("stale-operation recovery failed") from exc
        handled = 0
        for operation in operations:
            status = operation.get("status")
            operation_task = operation.get("task_id")
            if operation_task not in {None, task}:
                raise StaleOperationError("stale operation belongs to a different task")
            if status not in {"pending", "running"}:
                continue
            if not force and not self._operation_expired(operation, cutoff):
                continue
            operation_id = operation.get("operation_id")
            if not isinstance(operation_id, str) or not operation_id or not _IDENTIFIER_RE.fullmatch(operation_id):
                raise StaleOperationError("stale operation has an invalid operation_id")
            if self.stale_operation_handler is not None:
                try:
                    result = self._invoke_hook(
                        self.stale_operation_handler,
                        "stale-operation hook",
                        task_id=task,
                        state=task_state,
                        operation=operation,
                        reason=reason,
                    )
                except LifecycleHookError:
                    raise
                if isinstance(result, Mapping):
                    candidate = dict(result)
                    candidate_status = candidate.get("status")
                    if candidate_status in {"cancelled", "aborted", "succeeded", "failed", "uncertain"}:
                        method = getattr(self.store, "update_operation", None)
                        if callable(method):
                            try:
                                def apply_candidate(old, value=candidate):
                                    merged = dict(old)
                                    merged.update(value)
                                    merged.setdefault("operation_id", operation_id)
                                    merged.setdefault("task_id", task)
                                    return merged
                                method(task, operation_id, apply_candidate)
                            except Exception as exc:
                                raise StaleOperationError(f"unable to persist stale operation {operation_id!r}") from exc
                        # A hook may have persisted a terminal result itself.
                        if candidate_status != "uncertain":
                            self._append_event(task, {
                                "type": "stale_operation_handled",
                                "operation_id": operation_id,
                                "status": candidate_status,
                                "reason": reason,
                                "handler": "injected",
                            })
                            handled += 1
                            continue
            loader = getattr(self.store, "load_operation", None)
            if callable(loader) and self.stale_operation_handler is not None:
                try:
                    current_operation = loader(task, operation_id)
                except Exception as exc:
                    raise StaleOperationError(f"unable to verify stale operation {operation_id!r}") from exc
                if isinstance(current_operation, Mapping) and current_operation.get("status") not in {"pending", "running"}:
                    current_status = current_operation.get("status")
                    self._append_event(task, {
                        "type": "stale_operation_handled",
                        "operation_id": operation_id,
                        "status": current_status,
                        "reason": reason,
                        "handler": "injected",
                    })
                    handled += 1
                    continue
            update_operation = getattr(self.store, "update_operation", None)
            if not callable(update_operation) and self.stale_operation_handler is None:
                raise StaleOperationError(
                    "stale operations require an injected handler or update_operation()"
                )
            self._persist_uncertain_operation(task, operation_id, reason=reason)
            self._append_event(task, {
                "type": "stale_operation_handled",
                "operation_id": operation_id,
                "status": "uncertain",
                "reason": reason,
                "handler": "default" if self.stale_operation_handler is None else "fallback",
            })
            handled += 1
        return handled

    # Common alternate spelling used by host recovery code.
    handle_stale_operations = recover_stale_operations
    recover_operations = recover_stale_operations

    def _cleanup_for_task(
        self,
        task_id: str,
        *,
        action: str,
        preserve_evidence: bool,
        reason: str | None,
        resources: Any = None,
        emit_event: bool = True,
    ) -> dict[str, Any]:
        task = _validate_task_id(task_id)
        if preserve_evidence is not True:
            raise EvidencePreservationError("lifecycle cleanup preserves evidence by default; deletion is not supported")
        if not self.preserve_evidence:
            raise EvidencePreservationError("controller was configured without evidence preservation")
        preserve_evidence = _validate_bool(preserve_evidence, "preserve_evidence")
        if preserve_evidence is not True:
            raise EvidencePreservationError("lifecycle cleanup preserves evidence by default; deletion is not supported")
        # Rehydrate terminal cleanup markers before invoking a host method.
        # This makes idempotency survive a fresh controller/resource-manager
        # instance, not merely repeated calls on one Python object.
        state_before = self._load(task)
        metadata_before = self._lifecycle_metadata(state_before)
        persisted_markers = metadata_before.get("cleanup", {})
        if isinstance(persisted_markers, Mapping):
            self.resource_manager.restore(persisted_markers, task_id=task)
        if resources is not None:
            self.resource_manager.register_many(resources, task_id=task)
        try:
            report = self.resource_manager.cleanup(
                action=action,
                task_id=task,
                preserve_evidence=True,
                include_global=self.include_global_resources,
            )
        except ResourceCleanupError as exc:
            self._record_failure_event(task, f"cleanup_{action}", exc)
            raise
        state = self._load(task)
        metadata = self._lifecycle_metadata(state)
        markers = metadata.setdefault("cleanup", {})
        if not isinstance(markers, Mapping):
            markers = {}
            metadata["cleanup"] = markers
        mutable_markers = copy.deepcopy(dict(markers))
        for item in report.get("resources", []):
            if not isinstance(item, Mapping):
                continue
            resource_id = item.get("resource_id")
            status = item.get("status")
            if not isinstance(resource_id, str) or status not in {"closed", "aborted", "failed"}:
                continue
            mutable_markers[resource_id] = {
                "action": item.get("action"),
                "status": status,
                "at": self._now(),
                "evidence_preserved": True,
            }
        metadata["cleanup"] = mutable_markers
        metadata["last_cleanup"] = {
            "action": action,
            "at": self._now(),
            "evidence_preserved": True,
        }
        updated = self._update_metadata(task, metadata, expected_status=self._state_status(state))
        if emit_event:
            self._append_event(task, {
                "type": "lifecycle_cleanup",
                "action": action,
                "reason": reason,
                "resources": [
                    {
                        "resource_id": item.get("resource_id"),
                        "status": item.get("status"),
                        "changed": bool(item.get("changed")),
                        "already_done": bool(item.get("already_done")),
                    }
                    for item in report.get("resources", [])
                    if isinstance(item, Mapping)
                ],
                "evidence_preserved": True,
            }, state=updated)
        # Return the task-shaped result, with a compact cleanup report attached
        # for hosts that need to display resource status without another call.
        result = copy.deepcopy(updated)
        result["cleanup"] = copy.deepcopy(report)
        return result

    def cleanup(
        self,
        task_id: str,
        action: str = "close",
        *,
        preserve_evidence: bool = True,
        reason: str | None = None,
        resources: Any = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
        """Close or abort host resources without changing task status.

        The default is deliberately non-destructive: task state, checkpoints,
        and evidence remain in place.  ``preserve_evidence=False`` is rejected
        rather than silently deleting anything.
        """
        reason = _validate_reason(reason)
        if mode is not None:
            if action != "close" and action != mode:
                raise LifecycleContractError("provide only one of action or mode")
            action = mode
        normalized = self.resource_manager._normalize_action(action)
        return self._cleanup_for_task(
            task_id,
            action=normalized,
            preserve_evidence=preserve_evidence,
            reason=reason,
            resources=resources,
        )

    def close(self, task_id: str, **kwargs: Any) -> dict[str, Any]:
        """Alias for graceful resource cleanup."""
        kwargs["action"] = "close"
        return self.cleanup(task_id, **kwargs)

    def abort(self, task_id: str, **kwargs: Any) -> dict[str, Any]:
        """Alias for hard resource cleanup."""
        kwargs["action"] = "abort"
        return self.cleanup(task_id, **kwargs)

    close_resources = close
    abort_resources = abort
    cleanup_resources = cleanup
    cleanup_host = cleanup
    close_host = close
    abort_host = abort

    def _record_pending_action(
        self,
        task_id: str,
        *,
        current_status: str,
        action: str,
        target: str,
        reason: str | None,
    ) -> dict[str, Any]:
        metadata = self._lifecycle_metadata(self._load(task_id))
        metadata.update({
            "pending_action": action,
            "pending_target": target,
            "pending_reason": reason,
            "cleanup_pending": True,
            "intent_recorded_at": self._now(),
            "evidence_preserved": True,
        })
        updated = self._update_metadata(task_id, metadata, expected_status=current_status)
        # Persist the intent directly in the task store before invoking an
        # external event sink. A sink outage must not erase the recovery
        # marker that tells a restarted host what cleanup was in progress.
        append = getattr(self.store, "append_event", None)
        if callable(append):
            try:
                append(
                    task_id,
                    {
                        "type": "lifecycle_intent",
                        "action": "intent",
                        "intent": action,
                        "target": target,
                        "reason": reason,
                        "cleanup_pending": True,
                        "evidence_preserved": True,
                    },
                )
            except Exception as exc:
                raise LifecyclePersistenceError("lifecycle intent persistence failed") from exc
        return updated

    def recover_pending_lifecycle(self, task_id: str) -> dict[str, Any] | None:
        """Finish a pause/abandon that crashed after intent or cleanup began."""
        task = _validate_task_id(task_id)
        state = self._load(task)
        metadata = self._lifecycle_metadata(state)
        action = metadata.get("pending_action")
        target = metadata.get("pending_target")
        if action not in {"pause", "abandon"} or target not in {"paused", "abandoned"}:
            return None
        reason = metadata.get("pending_reason") if isinstance(metadata.get("pending_reason"), str) else None
        current = self._state_status(state)
        if current in TERMINAL_STATUSES:
            return state
        if action == "pause":
            self._cleanup_for_task(
                task,
                action="close",
                preserve_evidence=True,
                reason=reason or "recovering pending pause",
                emit_event=False,
            )
            return self._transition_state(task, "paused", action="pause", reason=reason, checkpoint=False)
        self.recover_stale_operations(task, force=True, reason=reason or "recovering pending abandonment")
        self._cleanup_for_task(
            task,
            action="abort",
            preserve_evidence=True,
            reason=reason or "recovering pending abandonment",
            emit_event=False,
        )
        return self._transition_state(task, "abandoned", action="abandon", reason=reason, checkpoint=False)

    def pause(
        self,
        task_id: str,
        reason: str | None = None,
        *,
        close_resources: bool = True,
        preserve_evidence: bool = True,
        checkpoint: bool = True,
    ) -> dict[str, Any]:
        """Cooperatively pause a task and checkpoint before the transition."""
        task = _validate_task_id(task_id)
        reason = _validate_reason(reason)
        close_resources = _validate_bool(close_resources, "close_resources")
        preserve_evidence = _validate_bool(preserve_evidence, "preserve_evidence")
        checkpoint = _validate_bool(checkpoint, "checkpoint")
        state = self._load(task)
        current = self._state_status(state)
        if current == "paused":
            raise InvalidLifecycleTransition("task is already paused")
        if current == "interrupted":
            raise InvalidLifecycleTransition("an interrupted task must be resumed or abandoned")
        if current in TERMINAL_STATUSES or current not in ACTIVE_STATUSES:
            raise InvalidLifecycleTransition(f"cannot pause task in status {current!r}")
        pending = self._lifecycle_metadata(state).get("pending_action")
        if pending in {"pause", "abandon"}:
            recovered = self.recover_pending_lifecycle(task)
            if recovered is not None:
                if self._state_status(recovered) == "paused":
                    raise InvalidLifecycleTransition("task is already paused")
                state = self._load(task)
                current = self._state_status(state)
        self._record_pending_action(
            task,
            current_status=current,
            action="pause",
            target="paused",
            reason=reason,
        )
        # Checkpoint before touching a host resource.  A failed checkpoint or
        # cleanup therefore cannot leave a half-committed cooperative pause.
        if checkpoint:
            self._checkpoint(task, state, action="pause")
        if close_resources:
            self._cleanup_for_task(
                task,
                action="close",
                preserve_evidence=preserve_evidence,
                reason=reason or "cooperative pause",
                emit_event=False,
            )
        return self._transition_state(task, "paused", action="pause", reason=reason, checkpoint=False)

    def interrupt(
        self,
        task_id: str,
        reason: str = "hard interruption",
        *,
        abort_resources: bool = True,
        preserve_evidence: bool = True,
        force_stale: bool = True,
        checkpoint: bool = True,
    ) -> dict[str, Any]:
        """Durably mark a hard interruption and reconcile in-flight work.

        The interrupted state is persisted before host abort is attempted.  A
        cleanup failure therefore never rewrites the task as if the hard
        interruption had been safely handled; the exception carries the
        already-durable state to the caller for retry/reporting.
        """
        task = _validate_task_id(task_id)
        reason = _validate_reason(reason) or "hard interruption"
        abort_resources = _validate_bool(abort_resources, "abort_resources")
        preserve_evidence = _validate_bool(preserve_evidence, "preserve_evidence")
        force_stale = _validate_bool(force_stale, "force_stale")
        checkpoint = _validate_bool(checkpoint, "checkpoint")
        state = self._load(task)
        current = self._state_status(state)
        if current == "interrupted":
            raise InvalidLifecycleTransition("task is already interrupted")
        if current in TERMINAL_STATUSES or current not in ACTIVE_STATUSES:
            raise InvalidLifecycleTransition(f"cannot interrupt task in status {current!r}")
        # Checkpoint the last known good state before changing the status.
        if checkpoint:
            self._checkpoint(task, state, action="interrupt")
        metadata = self._lifecycle_metadata(state)
        now = self._now()
        previous_resume = metadata.get("resume_status")
        metadata.update({
            "schema_version": LIFECYCLE_SCHEMA_VERSION,
            "status": "interrupted",
            "state": "interrupted",
            "previous_status": current,
            "resume_status": previous_resume if current == "paused" and isinstance(previous_resume, str) else current,
            "interrupted_from": current,
            "interrupted_at": now,
            "last_action": "interrupt",
            "reason": reason,
            "hard_interruption": True,
            "recovery_required": True,
            "evidence_preserved": True,
        })
        metadata.pop("paused_at", None)
        self._append_history(metadata, {
            "action": "interrupt",
            "from": current,
            "to": "interrupted",
            "at": now,
            "reason": reason,
        })
        updated = self._update(task, {"status": "interrupted", "lifecycle": metadata}, expected_status=current)
        self._append_event(task, {
            "type": "lifecycle_transition",
            "action": "interrupt",
            "event": "interrupt",
            "from": current,
            "to": "interrupted",
            "status": "interrupted",
            "state": "interrupted",
            "previous_status": current,
            "lifecycle_state": "interrupted",
            "reason": reason,
            "hard_interruption": True,
            "recovery_required": True,
            "evidence_preserved": True,
        }, state=updated)
        try:
            self.recover_stale_operations(
                task,
                force=force_stale,
                reason=reason,
            )
        except Exception as exc:
            self._record_failure_event(task, "stale_operation", exc, state=updated)
            if isinstance(exc, StaleOperationError):
                raise
            raise StaleOperationError("hard interruption stale-operation handling failed") from exc
        if abort_resources:
            try:
                self._cleanup_for_task(
                    task,
                    action="abort",
                    preserve_evidence=preserve_evidence,
                    reason=reason,
                    emit_event=False,
                )
            except ResourceCleanupError:
                # The interrupted state is intentionally left durable.
                raise
        return self._load(task)

    def resume(
        self,
        task_id: str,
        *,
        reason: str | None = None,
        resume_status: str | None = None,
        force_stale: bool | None = None,
        checkpoint: bool = True,
    ) -> dict[str, Any]:
        """Resume a paused/interrupted task using its recorded safe status."""
        task = _validate_task_id(task_id)
        reason = _validate_reason(reason)
        if force_stale is not None:
            force_stale = _validate_bool(force_stale, "force_stale")
        checkpoint = _validate_bool(checkpoint, "checkpoint")
        state = self._load(task)
        current = self._state_status(state)
        if current not in {"paused", "interrupted"} and self._lifecycle_metadata(state).get("pending_action") in {"pause", "abandon"}:
            recovered = self.recover_pending_lifecycle(task)
            if recovered is not None:
                state = self._load(task)
                current = self._state_status(state)
        if current not in {"paused", "interrupted"}:
            raise InvalidLifecycleTransition(f"task must be paused or interrupted, not {current!r}")
        if resume_status is not None:
            if not isinstance(resume_status, str) or not resume_status.strip():
                raise LifecycleContractError("resume_status must be a non-empty string")
            resume_status = resume_status.strip()
        metadata = self._lifecycle_metadata(state)
        target = self._target_for_resume(current, metadata, resume_status)
        # A checkpoint is required even when the state store's implementation
        # does not expose a separate checkpoint method; the hook is the host's
        # durable integration point in that case.  Take it before stale
        # reconciliation so a failed recovery remains restartable.
        if checkpoint:
            self._checkpoint(task, state, action="resume")
        # Any interrupted task gets a conservative stale-operation pass.  This
        # is important after a process restart when the lease may still look
        # live even though the worker died.
        if force_stale is None:
            force_stale = current == "interrupted"
        if force_stale:
            self.recover_stale_operations(task, force=True, reason=reason or "resuming after interruption")
        now = self._now()
        metadata.update({
            "schema_version": LIFECYCLE_SCHEMA_VERSION,
            "status": target,
            "resumed_at": now,
            "resumed_from": current,
            "resume_status": target,
            "last_action": "resume",
            "reason": reason,
            "terminal": False,
            "recovery_required": target == "recovering",
            "evidence_preserved": True,
        })
        metadata.pop("paused_at", None)
        metadata.pop("interrupted_at", None)
        metadata.pop("hard_interruption", None)
        self._append_history(metadata, {
            "action": "resume",
            "from": current,
            "to": target,
            "at": now,
            "reason": reason,
        })
        updated = self._update(task, {"status": target, "lifecycle": metadata}, expected_status=current)
        self._append_event(task, {
            "type": "lifecycle_transition",
            "action": "resume",
            "event": "resume",
            "from": current,
            "to": target,
            "status": target,
            "previous_status": current,
            "lifecycle_state": target,
            "reason": reason,
            "evidence_preserved": True,
        }, state=updated)
        return updated

    def abandon(
        self,
        task_id: str,
        reason: str = "explicit abandonment",
        *,
        abort_resources: bool = True,
        preserve_evidence: bool = True,
        force_stale: bool = True,
        checkpoint: bool = True,
    ) -> dict[str, Any]:
        """Explicitly abandon a task after stale work and host resources settle."""
        task = _validate_task_id(task_id)
        reason = _validate_reason(reason) or "explicit abandonment"
        abort_resources = _validate_bool(abort_resources, "abort_resources")
        preserve_evidence = _validate_bool(preserve_evidence, "preserve_evidence")
        force_stale = _validate_bool(force_stale, "force_stale")
        checkpoint = _validate_bool(checkpoint, "checkpoint")
        state = self._load(task)
        current = self._state_status(state)
        if current in TERMINAL_STATUSES:
            raise InvalidLifecycleTransition(f"task is already terminal ({current})")
        if current not in ACTIVE_STATUSES:
            raise InvalidLifecycleTransition(f"cannot abandon task in status {current!r}")
        pending = self._lifecycle_metadata(state).get("pending_action")
        if pending in {"pause", "abandon"}:
            recovered = self.recover_pending_lifecycle(task)
            if recovered is not None:
                state = self._load(task)
                current = self._state_status(state)
                if current in TERMINAL_STATUSES:
                    raise InvalidLifecycleTransition(f"task is already terminal ({current})")
        self._record_pending_action(
            task,
            current_status=current,
            action="abandon",
            target="abandoned",
            reason=reason,
        )
        # Preserve a last-known-good checkpoint before stale-operation or host
        # cleanup work begins.  If either fails, the task remains recoverable.
        if checkpoint:
            self._checkpoint(task, state, action="abandon")
        if force_stale:
            self.recover_stale_operations(task, force=True, reason=reason)
        if abort_resources:
            self._cleanup_for_task(
                task,
                action="abort",
                preserve_evidence=preserve_evidence,
                reason=reason,
                emit_event=False,
            )
        return self._transition_state(task, "abandoned", action="abandon", reason=reason, checkpoint=False)

    # Explicitly named aliases for API discoverability.
    pause_task = pause
    interrupt_task = interrupt
    resume_task = resume
    abandon_task = abandon
    mark_paused = pause
    mark_interrupted = interrupt
    mark_abandoned = abandon
    close_task = close
    abort_task = abort
    recover = recover_stale_operations

    def transition(self, task_id: str, target: str, *, reason: str | None = None) -> dict[str, Any]:
        """Dispatch a validated lifecycle target through the public methods."""
        if not isinstance(target, str):
            raise LifecycleContractError("transition target must be a string")
        normalized = target.strip().lower()
        if normalized == "paused":
            return self.pause(task_id, reason)
        if normalized in {"interrupted", "interrupt"}:
            return self.interrupt(task_id, reason or "hard interruption")
        if normalized in {"resumed", "resume", "running"}:
            return self.resume(task_id, reason=reason)
        if normalized in {"abandoned", "abandon"}:
            return self.abandon(task_id, reason or "explicit abandonment")
        raise InvalidLifecycleTransition(f"unsupported lifecycle target: {target!r}")


# Descriptive aliases for callers that prefer the longer names.
TaskLifecycleController = LifecycleController
LifecycleStore = TaskStoreProtocol
ResourceCleanup = ResourceCleanupManager
HostCleanup = ResourceCleanupManager


__all__ = [
    "ACTIVE_STATUSES",
    "ALLOWED_TRANSITIONS",
    "CleanupAction",
    "CleanupContract",
    "CleanupError",
    "CleanupManager",
    "CleanupMode",
    "ConcurrentLifecycleError",
    "ContractError",
    "EvidencePreservationError",
    "EvidencePreservationRequired",
    "HostResource",
    "HostResourceCleanup",
    "HostCleanup",
    "HookError",
    "InvalidLifecycleTransition",
    "InvalidTransition",
    "LIFECYCLE_SCHEMA_VERSION",
    "LIFECYCLE_STATES",
    "LIFECYCLE_TRANSITIONS",
    "PAUSED",
    "INTERRUPTED",
    "ABANDONED",
    "LifecycleContractError",
    "LifecycleController",
    "LifecycleError",
    "LifecycleHookError",
    "LifecyclePersistenceError",
    "LifecycleState",
    "LifecycleStatus",
    "LifecycleTransitionError",
    "RESUMABLE_STATUSES",
    "ResourceCleanup",
    "ResourceCleanupContract",
    "ResourceCleanupError",
    "ResourceCleanupManager",
    "ResourceContractError",
    "ResourceNotFound",
    "ResourceRegistrationError",
    "ResourceRegistry",
    "StaleOperationError",
    "TERMINAL_STATUSES",
    "TRANSITIONS",
    "TaskLifecycleController",
    "TaskLifecycleState",
    "TaskStoreProtocol",
    "LifecycleStore",
]

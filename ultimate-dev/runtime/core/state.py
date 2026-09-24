from __future__ import annotations

import json
import math
import os
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, Mapping

try:  # POSIX hosts get cross-process read-modify-write protection.
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None

from .contracts import ContractError, safe_child_path, validate_identifier
from .audit import AuditJournal, AuditJournalError


MAX_STATE_BYTES = 8_000_000
MAX_EVENTS = 10_000
MAX_EVENT_BYTES = 64_000
MAX_OPERATION_IDS = 10_000


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


_OPERATION_STATUSES = frozenset({"pending", "running", "succeeded", "failed", "uncertain", "cancelled"})
_TASK_STATUSES = frozenset({
    "created", "ready", "planning", "planned", "executing", "observing",
    "verifying", "recovering", "replanned", "failed", "completed", "blocked",
    "paused", "interrupted", "abandoned",
    # Compatibility spellings accepted by the standalone lifecycle adapter.
    "running", "in_progress", "pending", "started", "working", "uncertain",
    "cancelled", "canceled", "done", "succeeded", "archived",
})


class TaskStore:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        base = self.project_root / ".memory" / "ultimate-dev" / "tasks"
        resolved_base = base.resolve()
        if resolved_base != self.project_root and self.project_root not in resolved_base.parents:
            raise ContractError("task storage base escapes project root")
        self.base = base
        self.base.mkdir(parents=True, exist_ok=True, mode=0o700)
        with __import__("contextlib").suppress(OSError):
            self.base.chmod(0o700)
        # The token is intentionally not exposed through the public store
        # facade.  Runtime/controller code receives a narrow capability object
        # instead of granting arbitrary callers the internal mutation API.
        self._controller_token = object()

    def task_dir(self, task_id: str) -> Path:
        validate_identifier(task_id, "task_id")
        candidate = self.base / task_id
        base_root = self.base.resolve()
        resolved = candidate.resolve()
        if resolved != base_root and base_root not in resolved.parents:
            raise ContractError("task directory escapes task storage base")
        return candidate

    @contextmanager
    def _task_lock(self, task_id: str) -> Iterator[None]:
        directory = self.task_dir(task_id)
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock_path = directory / ".lock"
        if fcntl is None:  # pragma: no cover - exercised on Windows hosts
            exclusive_path = directory / ".lock.exclusive"
            deadline = time.monotonic() + 10.0
            while True:
                try:
                    descriptor = os.open(exclusive_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                    os.close(descriptor)
                    break
                except FileExistsError:
                    try:
                        if time.time() - exclusive_path.stat().st_mtime > 30:
                            exclusive_path.unlink()
                            continue
                    except FileNotFoundError:
                        continue
                    if time.monotonic() >= deadline:
                        raise TimeoutError("timed out acquiring task state lock")
                    time.sleep(0.01)
            try:
                yield
            finally:
                try:
                    exclusive_path.unlink()
                except FileNotFoundError:
                    pass
            return
        if lock_path.is_symlink():
            raise ContractError("task lock path must not be a symlink")
        with open(lock_path, "a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def create(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(contract, dict):
            raise ValueError("task contract must be an object")
        if not isinstance(contract.get("goal"), str) or not contract["goal"].strip():
            raise ValueError("task contract goal must be a non-empty string")
        task_id = validate_identifier(
            contract.get("task_id") or f"task-{uuid.uuid4().hex[:12]}",
            "task_id",
        )
        d = self.task_dir(task_id)
        d.mkdir(parents=True, exist_ok=False, mode=0o700)
        with __import__("contextlib").suppress(OSError):
            d.chmod(0o700)
        state = {
            "schema_version": "2.5",
            "task_id": task_id,
            "status": "created",
            "created_at": now(),
            "updated_at": now(),
            "revision": 0,
            "contract": contract,
            "completed": [],
            "in_progress": [],
            "next_action": None,
            "changed_files": [],
            "decisions": [],
            "decision_bindings": [],
            "operation_ids": [],
            "failed_approaches": [],
            "verification": {"passed": [], "pending": [], "evidence_refs": []},
            "observations": [],
            "blockers": [],
            "open_questions": [],
            "events": [],
        }
        self._save(task_id, "state.json", state)
        self.save(task_id, "context.json", {"layers": {}, "loaded": [], "budget": None})
        self.save(task_id, "progress.md", "# Progress\n")
        (d / "checkpoints").mkdir()
        (d / "handoffs").mkdir()
        (d / "evidence").mkdir()
        (d / "operations").mkdir()
        return state

    def _save(self, task_id: str, filename: str, value: Any) -> None:
        d = self.task_dir(task_id)
        d.mkdir(parents=True, exist_ok=True)
        target = safe_child_path(d, filename)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=target.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                if isinstance(value, str):
                    f.write(value)
                else:
                    json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, target)
            try:
                directory_fd = os.open(target.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                pass
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def save(self, task_id: str, filename: str, value: Any) -> None:
        task_root = self.task_dir(task_id)
        requested = safe_child_path(task_root, filename)
        state_path = safe_child_path(task_root, "state.json")
        if requested == state_path:
            raise PermissionError("state.json can only be written by the Runtime controller")
        self._save(task_id, filename, value)

    def save_internal(
        self,
        task_id: str,
        filename: str,
        value: Any,
        *,
        _controller: object | None = None,
    ) -> None:
        """Persist an internal artifact through a controller capability.

        ``save_internal`` remains callable for source compatibility, but a
        public caller cannot use it to replace the durable state envelope.
        Runtime uses :meth:`controller` instead.
        """
        if _controller is not self._controller_token:
            raise PermissionError("internal persistence requires a TaskStore controller")
        self._save(task_id, filename, value)

    @staticmethod
    def _reject_json_constant(value: str) -> Any:
        raise ValueError(f"non-finite JSON constant is not allowed: {value}")

    @classmethod
    def _read_json(cls, path: Path, label: str) -> Any:
        def reject_duplicates(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate JSON key in {label}: {key}")
                result[key] = value
            return result

        with open(path, encoding="utf-8") as handle:
            return json.load(
                handle,
                parse_constant=cls._reject_json_constant,
                object_pairs_hook=reject_duplicates,
            )

    def load(self, task_id: str) -> Dict[str, Any]:
        path = safe_child_path(self.task_dir(task_id), "state.json")
        state = self._read_json(path, "task state")
        if not isinstance(state, dict):
            raise ValueError(f"Task state for {task_id!r} must be an object")
        required = {"schema_version", "task_id", "status", "revision", "contract", "verification", "events"}
        missing = sorted(required - set(state))
        if missing:
            raise ValueError(f"Task state is missing fields: {', '.join(missing)}")
        if state.get("task_id") != task_id:
            raise ValueError("Task state identity does not match its path")
        if state.get("schema_version") != "2.5":
            raise ValueError("Unsupported task state schema version")
        if type(state.get("revision")) is not int or state["revision"] < 0:
            raise ValueError("Task state revision must be a non-negative integer")
        if state.get("status") not in _TASK_STATUSES:
            raise ValueError(f"Unknown task state status: {state.get('status')!r}")
        if not isinstance(state.get("contract"), dict) or not isinstance(state.get("verification"), dict):
            raise ValueError("Task state contract and verification must be objects")
        contract = state["contract"]
        if "goal" in contract and (not isinstance(contract["goal"], str) or not contract["goal"].strip()):
            raise ValueError("Task contract goal must be a non-empty string")
        for field in (
            "definition_of_done", "acceptance_criteria", "constraints", "required_evidence",
            "allowed_actions", "forbidden_actions",
        ):
            if field in contract and (
                not isinstance(contract[field], list)
                or any(not isinstance(item, str) or not item for item in contract[field])
            ):
                raise ValueError(f"Task contract {field} must be an array of non-empty strings")
        if not isinstance(state.get("events"), list):
            raise ValueError("Task state events must be an array")
        if len(state["events"]) > MAX_EVENTS:
            raise ValueError("Task state exceeds the event quota")
        try:
            if len(json.dumps(state, ensure_ascii=False, allow_nan=False).encode("utf-8")) > MAX_STATE_BYTES:
                raise ValueError("Task state exceeds the maximum persisted size")
        except (TypeError, ValueError) as exc:
            raise ValueError("Task state is not canonical JSON") from exc
        for index, event in enumerate(state["events"]):
            if not isinstance(event, dict):
                raise ValueError(f"Task state events[{index}] must be an object")
            if not isinstance(event.get("event_id"), str) or not event["event_id"]:
                raise ValueError(f"Task state events[{index}].event_id is required")
            if not isinstance(event.get("at"), str) or not event["at"]:
                raise ValueError(f"Task state events[{index}].at is required")
            if type(event.get("state_revision")) is not int or event["state_revision"] < 1:
                raise ValueError(f"Task state events[{index}].state_revision is invalid")
        for field in ("completed", "in_progress", "changed_files", "decisions", "decision_bindings", "operation_ids", "blockers", "open_questions", "observations"):
            if field in state and not isinstance(state[field], list):
                raise ValueError(f"Task state {field} must be an array")
        verification = state["verification"]
        for field in ("passed", "pending", "evidence_refs"):
            if field in verification and not isinstance(verification[field], list):
                raise ValueError(f"Task verification {field} must be an array")
        if "trusted" in verification and not isinstance(verification["trusted"], bool):
            raise ValueError("Task verification trusted must be boolean")
        if "evidence_digest" in verification and not isinstance(verification["evidence_digest"], str):
            raise ValueError("Task verification evidence_digest must be a string")
        if "evidence_digests" in verification:
            if not isinstance(verification["evidence_digests"], dict):
                raise ValueError("Task verification evidence_digests must be an object")
            for reference, digest in verification["evidence_digests"].items():
                if not isinstance(reference, str) or (isinstance(digest, str) and not digest):
                    raise ValueError("Task verification evidence digest entry is invalid")
                if isinstance(digest, dict):
                    if any(not isinstance(value, str) or not value for value in digest.values()):
                        raise ValueError("Task verification evidence digest entry is invalid")
                elif not isinstance(digest, str):
                    raise ValueError("Task verification evidence digest entry is invalid")
        return state

    _PROTECTED_UPDATE_FIELDS = frozenset({
        "schema_version", "task_id", "status", "revision", "contract", "verification",
        "decisions", "decision_bindings", "operation_ids", "events", "blockers",
    })

    @staticmethod
    def _is_lifecycle_mutation(changes: Mapping[str, Any]) -> bool:
        """Recognize the narrow compatibility surface used by LifecycleController.

        The lifecycle module is an independently shipped integration boundary;
        it is allowed to commit its explicit status/metadata pair without
        receiving the Runtime's private token.  No contract, verification,
        revision, event, or operation field is accepted through this escape.
        """
        return (
            set(changes).issubset({"status", "lifecycle"})
            and (
                (
                    "lifecycle" in changes
                    and isinstance(changes.get("lifecycle"), dict)
                )
                or set(changes) == {"status"}
                or set(changes) == {"lifecycle"}
            )
            and (
                "status" not in changes
                or changes.get("status") in {"paused", "interrupted", "abandoned", "ready", "planning", "planned", "executing", "observing", "verifying", "recovering", "replanned", "failed", "blocked"}
            )
        )

    def _update_unlocked(self, task_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        with self._task_lock(task_id):
            state = self.load(task_id)
            state.update(changes)
            state["revision"] += 1
            state["updated_at"] = now()
            self._save(task_id, "state.json", state)
            return state

    def update(self, task_id: str, **changes: Any) -> Dict[str, Any]:
        protected = sorted(set(changes) & self._PROTECTED_UPDATE_FIELDS)
        if protected:
            raise PermissionError(f"protected task state fields require Runtime control: {', '.join(protected)}")
        return self._update_unlocked(task_id, changes)

    def update_internal(
        self,
        task_id: str,
        *,
        _controller: object | None = None,
        **changes: Any,
    ) -> Dict[str, Any]:
        """Update protected state only through the Runtime controller.

        A narrow status/lifecycle compatibility path remains for the standalone
        LifecycleController integration.  It cannot alter verification,
        contracts, decisions, operation identity, events, or revisions.
        """
        if _controller is not self._controller_token and not self._is_lifecycle_mutation(changes):
            raise PermissionError("internal task mutation requires a TaskStore controller")
        return self._update_unlocked(task_id, changes)

    def update_if_status(
        self,
        task_id: str,
        expected_status: str,
        changes: Dict[str, Any],
        *,
        _internal: bool = False,
        _controller: object | None = None,
    ) -> Dict[str, Any] | None:
        if not isinstance(changes, dict):
            raise ValueError("state changes must be an object")
        trusted = _controller is self._controller_token
        lifecycle_compat = self._is_lifecycle_mutation(changes)
        if _internal and not trusted and not lifecycle_compat:
            raise PermissionError("internal conditional mutation requires a TaskStore controller")
        if not _internal and not trusted:
            protected = sorted(set(changes) & self._PROTECTED_UPDATE_FIELDS)
            if protected:
                raise PermissionError(f"protected task state fields require Runtime control: {', '.join(protected)}")
        with self._task_lock(task_id):
            state = self.load(task_id)
            if state.get("status") != expected_status:
                return None
            state.update(changes)
            state["revision"] += 1
            state["updated_at"] = now()
            self._save(task_id, "state.json", state)
            return state

    def append_decision_binding(
        self,
        task_id: str,
        summary: Dict[str, Any],
        binding: Dict[str, Any],
        *,
        _controller: object | None = None,
    ) -> Dict[str, Any]:
        if _controller is not self._controller_token:
            raise PermissionError("decision bindings require a TaskStore controller")
        if not isinstance(summary, dict) or not isinstance(binding, dict):
            raise ValueError("decision summary and binding must be objects")
        with self._task_lock(task_id):
            state = self.load(task_id)
            state.setdefault("decisions", []).append(summary)
            state.setdefault("decision_bindings", []).append(binding)
            state["revision"] += 1
            state["updated_at"] = now()
            self._save(task_id, "state.json", state)
            return state

    def add_operation_id(
        self,
        task_id: str,
        operation_id: str,
        *,
        _controller: object | None = None,
    ) -> Dict[str, Any]:
        if _controller is not self._controller_token:
            raise PermissionError("operation identity updates require a TaskStore controller")
        validate_identifier(operation_id, "operation_id")
        with self._task_lock(task_id):
            state = self.load(task_id)
            operation_ids = list(dict.fromkeys(state.get("operation_ids", []) + [operation_id]))
            if len(operation_ids) > MAX_OPERATION_IDS:
                raise ValueError("Task state operation-id quota exceeded")
            state["operation_ids"] = operation_ids
            state["revision"] += 1
            state["updated_at"] = now()
            self._save(task_id, "state.json", state)
            return state

    def append_event(self, task_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(event, dict):
            raise ValueError("event must be an object")
        if "event_id" in event and (not isinstance(event["event_id"], str) or not event["event_id"]):
            raise ValueError("event_id must be a non-empty string")
        with self._task_lock(task_id):
            state = self.load(task_id)
            if len(state.get("events", [])) >= MAX_EVENTS:
                raise ValueError("Task state event quota exceeded")
            try:
                if len(json.dumps(event, ensure_ascii=False, allow_nan=False).encode("utf-8")) > MAX_EVENT_BYTES:
                    raise ValueError("Task event exceeds the maximum size")
            except (TypeError, ValueError) as exc:
                raise ValueError("Task event is not bounded JSON") from exc
            record = dict(event)
            record["event_id"] = record.get("event_id") or f"event-{uuid.uuid4().hex}"
            record["at"] = now()
            record["state_revision"] = state["revision"] + 1
            state.setdefault("events", []).append(record)
            AuditJournal(self.task_dir(task_id) / "audit" / "events.jsonl").append(record)
            state["revision"] += 1
            state["updated_at"] = now()
            self._save(task_id, "state.json", state)
            return state

    def verify_audit_journal(self, task_id: str) -> bool:
        journal = AuditJournal(self.task_dir(task_id) / "audit" / "events.jsonl")
        return journal.verify()

    def checkpoint(self, task_id: str) -> Path:
        state = self.load(task_id)
        name = f"{state['revision']:06d}-{uuid.uuid4().hex[:8]}.json"
        self.save(task_id, f"checkpoints/{name}", state)
        return self.task_dir(task_id) / "checkpoints" / name

    def handoff(self, task_id: str, target: str = "next") -> Path:
        validate_identifier(target, "handoff target")
        state = self.load(task_id)
        packet = {
            "schema_version": "2.5",
            "task_id": task_id,
            "target": target,
            "objective": state["contract"].get("goal"),
            "acceptance_criteria": state["contract"].get("acceptance_criteria", []),
            "status": state["status"],
            "completed": state["completed"],
            "in_progress": state["in_progress"],
            "next_action": state["next_action"],
            "changed_files": state["changed_files"],
            "decisions": state["decisions"],
            "failed_approaches": state["failed_approaches"],
            "verification": state["verification"],
            "blockers": state["blockers"],
            "open_questions": state["open_questions"],
            "updated_at": state["updated_at"],
        }
        name = f"{state['revision']:06d}-{target}-{uuid.uuid4().hex[:8]}.json"
        self.save(task_id, f"handoffs/{name}", packet)
        return self.task_dir(task_id) / "handoffs" / name

    def _operation_path(self, task_id: str, operation_id: str) -> Path:
        validate_identifier(operation_id, "operation_id")
        return safe_child_path(self.task_dir(task_id), f"operations/{operation_id}.json")

    def _load_operation_unlocked(self, task_id: str, operation_id: str) -> Dict[str, Any]:
        path = self._operation_path(task_id, operation_id)
        value = self._read_json(path, f"operation {operation_id}")
        if not isinstance(value, dict):
            raise ValueError(f"Operation {operation_id!r} must be an object")
        if value.get("operation_id") != operation_id or value.get("task_id") != task_id:
            raise ValueError("Operation identity does not match its path")
        if value.get("status") not in _OPERATION_STATUSES:
            raise ValueError(f"Operation {operation_id!r} has an unknown status")
        if "attempt" in value and (type(value["attempt"]) is not int or value["attempt"] < 1):
            raise ValueError("Operation attempt must be a positive integer")
        if "idempotency_key" in value and (not isinstance(value["idempotency_key"], str) or not value["idempotency_key"]):
            raise ValueError("Operation idempotency_key must be a non-empty string")
        if "action_fingerprint" in value:
            from .contracts import validate_fingerprint
            validate_fingerprint(value["action_fingerprint"])
        if "capability_id" in value:
            from .contracts import validate_capability_id
            validate_capability_id(value["capability_id"])
        lease = value.get("lease_expires_at_epoch")
        if lease is not None and (isinstance(lease, bool) or not isinstance(lease, (int, float)) or not math.isfinite(float(lease))):
            raise ValueError("Operation lease must be a finite number or null")
        for field in ("worker_id", "fencing_token", "decision_binding_nonce"):
            if field in value and value[field] is not None and (not isinstance(value[field], str) or not value[field]):
                raise ValueError(f"Operation {field} must be a non-empty string")
        return value

    def _operation_records_unlocked(self, task_id: str) -> list[Dict[str, Any]]:
        directory = safe_child_path(self.task_dir(task_id), "operations")
        if not directory.exists():
            return []
        operations: list[Dict[str, Any]] = []
        for path in sorted(directory.glob("*.json")):
            safe_path = safe_child_path(directory, path.name)
            value = self._read_json(safe_path, f"operation {path.stem}")
            if isinstance(value, dict):
                operation_id = path.stem
                if value.get("operation_id") != operation_id or value.get("task_id") != task_id:
                    raise ValueError(f"Operation identity does not match its path: {path.name}")
                self._validate_operation_unlocked(task_id, operation_id, value)
                operations.append(value)
        return operations

    def _write_operation_unlocked(self, task_id: str, operation_id: str, operation: Dict[str, Any]) -> Path:
        path = self._operation_path(task_id, operation_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".tmp-operation-", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(operation, f, indent=2, ensure_ascii=False, allow_nan=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
            try:
                directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                pass
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        return path

    def save_operation(self, task_id: str, operation_id: str, operation: Dict[str, Any]) -> Path:
        validate_identifier(operation_id, "operation_id")
        if not isinstance(operation, dict):
            raise ValueError("operation must be an object")
        if operation.get("operation_id", operation_id) != operation_id or operation.get("task_id", task_id) != task_id:
            raise ValueError("operation identity does not match its path")
        with self._task_lock(task_id):
            # Validate before replacing an existing record.
            self._validate_operation_unlocked(task_id, operation_id, operation)
            return self._write_operation_unlocked(task_id, operation_id, operation)

    def _validate_operation_unlocked(self, task_id: str, operation_id: str, operation: Mapping[str, Any]) -> None:
        if operation.get("operation_id") != operation_id or operation.get("task_id") != task_id:
            raise ValueError("operation identity does not match its path")
        if operation.get("status") not in _OPERATION_STATUSES:
            raise ValueError("operation status is invalid")
        if "attempt" in operation and (type(operation["attempt"]) is not int or operation["attempt"] < 1):
            raise ValueError("operation attempt must be a positive integer")
        if "action_fingerprint" in operation:
            from .contracts import validate_fingerprint
            validate_fingerprint(operation["action_fingerprint"])
        if "capability_id" in operation:
            from .contracts import validate_capability_id
            validate_capability_id(operation["capability_id"])
        for field in ("worker_id", "fencing_token", "decision_binding_nonce"):
            if field in operation and operation[field] is not None and (not isinstance(operation[field], str) or not operation[field]):
                raise ValueError(f"operation {field} must be a non-empty string")

    def _ensure_operation_id_capacity_unlocked(self, task_id: str, operation_id: str) -> None:
        state = self.load(task_id)
        operation_ids = state.get("operation_ids", [])
        if operation_id not in operation_ids and len(operation_ids) >= MAX_OPERATION_IDS:
            raise ValueError("Task state operation-id quota exceeded")

    def _append_operation_id_unlocked(self, task_id: str, operation_id: str) -> None:
        state = self.load(task_id)
        operation_ids = list(dict.fromkeys(state.get("operation_ids", []) + [operation_id]))
        if len(operation_ids) > MAX_OPERATION_IDS:
            raise ValueError("Task state operation-id quota exceeded")
        state["operation_ids"] = operation_ids
        state["revision"] += 1
        state["updated_at"] = now()
        self._save(task_id, "state.json", state)

    def claim_operation(self, task_id: str, operation_id: str, operation: Dict[str, Any]) -> tuple[Path, Dict[str, Any] | None]:
        """Atomically create an operation, including its idempotency key.

        This compatibility method is intentionally conservative: if another
        operation already owns the key, it returns that record rather than
        allowing a caller to create a second side effect.
        """
        validate_identifier(operation_id, "operation_id")
        if not isinstance(operation, dict):
            raise ValueError("operation must be an object")
        required = {"attempt", "idempotency_key", "action_fingerprint", "capability_id", "status"}
        missing = sorted(required - set(operation))
        if missing:
            raise ValueError(f"operation claim is missing fields: {', '.join(missing)}")
        with self._task_lock(task_id):
            self._validate_operation_unlocked(task_id, operation_id, operation)
            try:
                return self._operation_path(task_id, operation_id), self._load_operation_unlocked(task_id, operation_id)
            except FileNotFoundError:
                key = operation.get("idempotency_key")
                if isinstance(key, str) and key:
                    for existing in self._operation_records_unlocked(task_id):
                        if existing.get("idempotency_key") == key:
                            return self._operation_path(task_id, existing["operation_id"]), existing
                path = self._write_operation_unlocked(task_id, operation_id, operation)
                return path, None

    def reserve_operation(
        self,
        task_id: str,
        operation_id: str,
        operation: Dict[str, Any],
        *,
        retry: bool = False,
        reconciliation: bool = False,
    ) -> tuple[Path, Dict[str, Any] | None, str]:
        """Atomically reserve an operation and idempotency key.

        The disposition is one of ``reserved``, ``replayed``,
        ``operation_conflict``, ``idempotency_conflict``, ``in_progress``,
        ``not_retryable``, ``reconciliation_required``, or
        ``new_approval_required``.  Reservation and
        attempt creation happen while holding the same task lock used by all
        operation readers, eliminating the lookup/create race.
        """
        validate_identifier(operation_id, "operation_id")
        if not isinstance(operation, dict):
            raise ValueError("operation must be an object")
        required = {"attempt", "idempotency_key", "action_fingerprint", "capability_id", "status"}
        missing = sorted(required - set(operation))
        if missing:
            raise ValueError(f"operation reservation is missing fields: {', '.join(missing)}")
        with self._task_lock(task_id):
            self._validate_operation_unlocked(task_id, operation_id, operation)
            try:
                existing = self._load_operation_unlocked(task_id, operation_id)
            except FileNotFoundError:
                existing = None
            if existing is not None:
                if existing.get("_public_fixture") is True:
                    return self._operation_path(task_id, operation_id), existing, "operation_conflict"
                if (
                    existing.get("action_fingerprint") != operation.get("action_fingerprint")
                    or existing.get("idempotency_key") != operation.get("idempotency_key")
                ):
                    return self._operation_path(task_id, operation_id), existing, "operation_conflict"
                status = existing.get("status")
                if status == "succeeded":
                    return self._operation_path(task_id, operation_id), existing, "replayed"
                if status in {"pending", "running"}:
                    return self._operation_path(task_id, operation_id), existing, "in_progress"
                if status in {"uncertain", "cancelled"} and existing.get("retry_allowed") is not True:
                    if not (reconciliation and existing.get("retry_allowed") is True):
                        return self._operation_path(task_id, operation_id), existing, "reconciliation_required"
                elif not retry:
                    return self._operation_path(task_id, operation_id), existing, "not_retryable"
                elif status not in {"failed", "cancelled"}:
                    return self._operation_path(task_id, operation_id), existing, "not_retryable"
                if (
                    existing.get("reconciliation")
                    and existing.get("decision_binding_nonce")
                    and operation.get("decision_binding_nonce") == existing.get("decision_binding_nonce")
                ):
                    return self._operation_path(task_id, operation_id), existing, "new_approval_required"
                attempt = int(existing.get("attempt", 0)) + 1
                updated = dict(existing)
                updated.update(operation)
                updated["attempt"] = attempt
                updated["created_at"] = existing.get("created_at", operation.get("created_at", now()))
                updated["fencing_token"] = operation.get("fencing_token") or f"fence-{uuid.uuid4().hex}"
                updated["retry_allowed"] = False
                self._ensure_operation_id_capacity_unlocked(task_id, operation_id)
                self._write_operation_unlocked(task_id, operation_id, updated)
                self._append_operation_id_unlocked(task_id, operation_id)
                return self._operation_path(task_id, operation_id), updated, "reserved"

            key = operation.get("idempotency_key")
            if isinstance(key, str) and key:
                for existing in self._operation_records_unlocked(task_id):
                    if existing.get("idempotency_key") != key:
                        continue
                    if existing.get("_public_fixture") is True:
                        return self._operation_path(task_id, existing["operation_id"]), existing, "idempotency_conflict"
                    if existing.get("action_fingerprint") != operation.get("action_fingerprint"):
                        return self._operation_path(task_id, existing["operation_id"]), existing, "idempotency_conflict"
                    status = existing.get("status")
                    if status == "succeeded":
                        return self._operation_path(task_id, existing["operation_id"]), existing, "replayed"
                    if status == "uncertain":
                        return self._operation_path(task_id, existing["operation_id"]), existing, "reconciliation_required"
                    if (
                        existing.get("reconciliation")
                        and existing.get("decision_binding_nonce")
                        and operation.get("decision_binding_nonce") == existing.get("decision_binding_nonce")
                    ):
                        return self._operation_path(task_id, existing["operation_id"]), existing, "new_approval_required"
                    return self._operation_path(task_id, existing["operation_id"]), existing, "in_progress"
            self._ensure_operation_id_capacity_unlocked(task_id, operation_id)
            self._write_operation_unlocked(task_id, operation_id, operation)
            self._append_operation_id_unlocked(task_id, operation_id)
            return self._operation_path(task_id, operation_id), operation, "reserved"

    def load_operation(self, task_id: str, operation_id: str) -> Dict[str, Any]:
        with self._task_lock(task_id):
            return self._load_operation_unlocked(task_id, operation_id)

    def update_operation(
        self,
        task_id: str,
        operation_id: str,
        mutator: Callable[[Dict[str, Any]], Dict[str, Any]],
        *,
        expected_worker_id: str | None = None,
        expected_attempt: int | None = None,
        expected_fencing_token: str | None = None,
    ) -> Dict[str, Any]:
        if not callable(mutator):
            raise TypeError("operation mutator must be callable")
        with self._task_lock(task_id):
            operation = self._load_operation_unlocked(task_id, operation_id)
            if expected_worker_id is not None and operation.get("worker_id") != expected_worker_id:
                raise PermissionError("operation is fenced by another worker")
            if expected_attempt is not None and operation.get("attempt") != expected_attempt:
                raise PermissionError("operation attempt is fenced")
            if expected_fencing_token is not None and operation.get("fencing_token") != expected_fencing_token:
                raise PermissionError("operation fencing token is stale")
            immutable = {
                key: operation.get(key)
                for key in ("operation_id", "task_id", "idempotency_key", "action_fingerprint", "attempt", "worker_id", "fencing_token")
            }
            updated = mutator(operation)
            if not isinstance(updated, dict):
                raise ValueError("operation mutator must return an object")
            if any(updated.get(key) != value for key, value in immutable.items()):
                raise PermissionError("operation identity and fencing fields are immutable")
            self._validate_operation_unlocked(task_id, operation_id, updated)
            self._write_operation_unlocked(task_id, operation_id, updated)
            return updated

    def renew_operation_lease(
        self,
        task_id: str,
        operation_id: str,
        worker_id: str,
        lease_seconds: float,
        *,
        expected_attempt: int | None = None,
        expected_fencing_token: str | None = None,
    ) -> Dict[str, Any]:
        if not isinstance(worker_id, str) or not worker_id:
            raise ValueError("worker_id is required")
        if (
            isinstance(lease_seconds, bool)
            or not isinstance(lease_seconds, (int, float))
            or not math.isfinite(float(lease_seconds))
            or lease_seconds < 0
        ):
            raise ValueError("lease_seconds must be a finite non-negative number")

        def renew(operation):
            if operation.get("status") not in {"pending", "running"} or operation.get("worker_id") != worker_id:
                raise PermissionError("operation lease is not owned by this worker")
            operation["lease_expires_at_epoch"] = time.time() + max(0.0, float(lease_seconds))
            operation["updated_at"] = now()
            return operation

        return self.update_operation(
            task_id,
            operation_id,
            renew,
            expected_worker_id=worker_id,
            expected_attempt=expected_attempt,
            expected_fencing_token=expected_fencing_token,
        )

    def list_operations(self, task_id: str) -> list[Dict[str, Any]]:
        with self._task_lock(task_id):
            return self._operation_records_unlocked(task_id)

    def find_operation_by_idempotency(self, task_id: str, idempotency_key: str) -> Dict[str, Any] | None:
        if not isinstance(idempotency_key, str) or not idempotency_key:
            raise ValueError("idempotency_key must be a non-empty string")
        with self._task_lock(task_id):
            for operation in self._operation_records_unlocked(task_id):
                if operation.get("idempotency_key") == idempotency_key:
                    return operation
        return None

    def controller(self) -> "TaskStoreController":
        """Return the narrow capability used by Runtime-owned controllers."""
        return TaskStoreController(self)

    def public_view(self) -> "TaskStorePublicView":
        """Return a compatibility view that hides internal mutation APIs."""
        return TaskStorePublicView(self)

    def lifecycle_view(self) -> "TaskStoreLifecycleView":
        """Return the restricted store surface required by LifecycleController."""
        return TaskStoreLifecycleView(self)

    def resume(self, task_id: str) -> Dict[str, Any]:
        return self.load(task_id)


class TaskStoreController:
    """Trusted mutation facade for Runtime-owned control-plane code.

    The facade intentionally exposes the durable store's useful operation and
    lifecycle methods, while keeping the raw internal token private.
    """

    def __init__(self, store: TaskStore):
        self._store = store

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self._store, name)

    def update_internal(self, task_id: str, **changes: Any) -> Dict[str, Any]:
        return self._store.update_internal(task_id, _controller=self._store._controller_token, **changes)

    def update_if_status(
        self,
        task_id: str,
        expected_status: str,
        changes: Dict[str, Any],
        *,
        _internal: bool = False,
    ) -> Dict[str, Any] | None:
        return self._store.update_if_status(
            task_id,
            expected_status,
            changes,
            _internal=_internal,
            _controller=self._store._controller_token,
        )

    def save_internal(self, task_id: str, filename: str, value: Any) -> None:
        self._store.save_internal(task_id, filename, value, _controller=self._store._controller_token)

    def append_decision_binding(self, task_id: str, summary: Dict[str, Any], binding: Dict[str, Any]) -> Dict[str, Any]:
        return self._store.append_decision_binding(
            task_id,
            summary,
            binding,
            _controller=self._store._controller_token,
        )

    def add_operation_id(self, task_id: str, operation_id: str) -> Dict[str, Any]:
        return self._store.add_operation_id(task_id, operation_id, _controller=self._store._controller_token)


class TaskStorePublicView:
    """Read/artifact compatibility facade that cannot mutate state internals."""

    _BLOCKED = frozenset({
        "update_internal",
        "update_if_status",
        "save_internal",
        "append_decision_binding",
        "add_operation_id",
        "claim_operation",
        "reserve_operation",
        "update_operation",
        "renew_operation_lease",
        "save_operation",
        "controller",
        "_controller_token",
        "_update_unlocked",
        "_save",
    })

    def __init__(self, store: TaskStore):
        self._store = store

    def __getattr__(self, name: str):
        if name in self._BLOCKED or name.startswith("_"):
            raise PermissionError("TaskStore internal mutation is not public")
        return getattr(self._store, name)

    def update_internal(self, task_id: str, **changes: Any) -> Dict[str, Any]:
        """Allow only the narrow lifecycle compatibility mutation."""
        if set(changes) == {"status"} or not self._store._is_lifecycle_mutation(changes):
            raise PermissionError("TaskStore internal mutation is not public")
        return self._store.update_internal(task_id, **changes)

    def update_if_status(
        self,
        task_id: str,
        expected_status: str,
        changes: Dict[str, Any],
        *,
        _internal: bool = False,
    ) -> Dict[str, Any] | None:
        if set(changes) == {"status"} or not self._store._is_lifecycle_mutation(changes):
            raise PermissionError("TaskStore internal mutation is not public")
        return self._store.update_if_status(task_id, expected_status, changes, _internal=_internal)

    def save(self, task_id: str, filename: str, value: Any):
        path = Path(filename)
        if path.is_absolute() or ".." in path.parts or path.parts[:1] in {("operations",), ("evidence",)}:
            raise PermissionError("public callers cannot write operation state")
        return self._store.save(task_id, filename, value)

    def save_operation(self, task_id: str, operation_id: str, operation: Dict[str, Any]):
        """Persist a nonterminal fixture without granting execution authority."""
        if not isinstance(operation, dict):
            raise ValueError("operation must be an object")
        if operation.get("status") not in {"pending", "running"}:
            raise PermissionError("public callers cannot create terminal operation records")
        marked = dict(operation)
        marked["_public_fixture"] = True
        return self._store.save_operation(task_id, operation_id, marked)

    def update(self, task_id: str, **changes: Any) -> Dict[str, Any]:
        raise PermissionError("TaskStore state updates are controller-only")

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return f"TaskStorePublicView({self._store.project_root!r})"


class TaskStoreLifecycleView(TaskStorePublicView):
    """Public read/artifact view with the narrow operation hook lifecycle needs."""

    def update_operation(
        self,
        task_id: str,
        operation_id: str,
        mutator,
        *,
        expected_worker_id: str | None = None,
        expected_attempt: int | None = None,
        expected_fencing_token: str | None = None,
    ) -> Dict[str, Any]:
        if not callable(mutator):
            raise TypeError("operation mutator must be callable")
        return self._store.update_operation(
            task_id,
            operation_id,
            mutator,
            expected_worker_id=expected_worker_id,
            expected_attempt=expected_attempt,
            expected_fencing_token=expected_fencing_token,
        )

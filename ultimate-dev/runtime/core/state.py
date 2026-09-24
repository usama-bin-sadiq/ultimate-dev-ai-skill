from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator

try:  # POSIX hosts get cross-process read-modify-write protection.
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None

from .contracts import ContractError, safe_child_path, validate_identifier


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class TaskStore:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        base = self.project_root / ".memory" / "ultimate-dev" / "tasks"
        resolved_base = base.resolve()
        if resolved_base != self.project_root and self.project_root not in resolved_base.parents:
            raise ContractError("task storage base escapes project root")
        self.base = base
        self.base.mkdir(parents=True, exist_ok=True)

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
        directory.mkdir(parents=True, exist_ok=True)
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
        task_id = validate_identifier(
            contract.get("task_id") or f"task-{uuid.uuid4().hex[:12]}",
            "task_id",
        )
        d = self.task_dir(task_id)
        d.mkdir(parents=True, exist_ok=False)
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
        self.save_internal(task_id, "state.json", state)
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

    def save_internal(self, task_id: str, filename: str, value: Any) -> None:
        self._save(task_id, filename, value)

    def load(self, task_id: str) -> Dict[str, Any]:
        path = safe_child_path(self.task_dir(task_id), "state.json")
        with open(path, encoding="utf-8") as f:
            state = json.load(f)
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
        if not isinstance(state.get("revision"), int) or state["revision"] < 0:
            raise ValueError("Task state revision must be a non-negative integer")
        if not isinstance(state.get("status"), str) or not state["status"]:
            raise ValueError("Task state status must be a non-empty string")
        if not isinstance(state.get("contract"), dict) or not isinstance(state.get("verification"), dict):
            raise ValueError("Task state contract and verification must be objects")
        if not isinstance(state.get("events"), list):
            raise ValueError("Task state events must be an array")
        return state

    _PROTECTED_UPDATE_FIELDS = frozenset({
        "schema_version", "task_id", "status", "revision", "contract", "verification",
        "decisions", "decision_bindings", "operation_ids", "events", "blockers",
    })

    def _update_unlocked(self, task_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        with self._task_lock(task_id):
            state = self.load(task_id)
            state.update(changes)
            state["revision"] += 1
            state["updated_at"] = now()
            self.save_internal(task_id, "state.json", state)
            return state

    def update(self, task_id: str, **changes: Any) -> Dict[str, Any]:
        protected = sorted(set(changes) & self._PROTECTED_UPDATE_FIELDS)
        if protected:
            raise PermissionError(f"protected task state fields require Runtime control: {', '.join(protected)}")
        return self._update_unlocked(task_id, changes)

    def update_internal(self, task_id: str, **changes: Any) -> Dict[str, Any]:
        """Update state from the Runtime controller, including protected fields."""
        return self._update_unlocked(task_id, changes)

    def update_if_status(
        self,
        task_id: str,
        expected_status: str,
        changes: Dict[str, Any],
        *,
        _internal: bool = False,
    ) -> Dict[str, Any] | None:
        if not isinstance(changes, dict):
            raise ValueError("state changes must be an object")
        if not _internal:
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
            self.save_internal(task_id, "state.json", state)
            return state

    def append_decision_binding(self, task_id: str, summary: Dict[str, Any], binding: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(summary, dict) or not isinstance(binding, dict):
            raise ValueError("decision summary and binding must be objects")
        with self._task_lock(task_id):
            state = self.load(task_id)
            state.setdefault("decisions", []).append(summary)
            state.setdefault("decision_bindings", []).append(binding)
            state["revision"] += 1
            state["updated_at"] = now()
            self.save_internal(task_id, "state.json", state)
            return state

    def add_operation_id(self, task_id: str, operation_id: str) -> Dict[str, Any]:
        validate_identifier(operation_id, "operation_id")
        with self._task_lock(task_id):
            state = self.load(task_id)
            state["operation_ids"] = list(dict.fromkeys(state.get("operation_ids", []) + [operation_id]))
            state["revision"] += 1
            state["updated_at"] = now()
            self.save_internal(task_id, "state.json", state)
            return state

    def append_event(self, task_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(event, dict):
            raise ValueError("event must be an object")
        with self._task_lock(task_id):
            state = self.load(task_id)
            record = dict(event)
            record["event_id"] = record.get("event_id") or f"event-{uuid.uuid4().hex}"
            record["at"] = now()
            record["state_revision"] = state["revision"] + 1
            state.setdefault("events", []).append(record)
            state["revision"] += 1
            state["updated_at"] = now()
            self.save_internal(task_id, "state.json", state)
            return state

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
        with open(path, encoding="utf-8") as f:
            value = json.load(f)
        if not isinstance(value, dict):
            raise ValueError(f"Operation {operation_id!r} must be an object")
        if value.get("operation_id") != operation_id or value.get("task_id") != task_id:
            raise ValueError("Operation identity does not match its path")
        if not isinstance(value.get("status"), str):
            raise ValueError("Operation status is required")
        return value

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
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        return path

    def save_operation(self, task_id: str, operation_id: str, operation: Dict[str, Any]) -> Path:
        validate_identifier(operation_id, "operation_id")
        if not isinstance(operation, dict):
            raise ValueError("operation must be an object")
        with self._task_lock(task_id):
            return self._write_operation_unlocked(task_id, operation_id, operation)

    def claim_operation(self, task_id: str, operation_id: str, operation: Dict[str, Any]) -> tuple[Path, Dict[str, Any] | None]:
        """Atomically create an operation, returning an existing record if present."""
        with self._task_lock(task_id):
            try:
                return self._operation_path(task_id, operation_id), self._load_operation_unlocked(task_id, operation_id)
            except FileNotFoundError:
                return self._write_operation_unlocked(task_id, operation_id, operation), None

    def load_operation(self, task_id: str, operation_id: str) -> Dict[str, Any]:
        with self._task_lock(task_id):
            return self._load_operation_unlocked(task_id, operation_id)

    def update_operation(self, task_id: str, operation_id: str, mutator) -> Dict[str, Any]:
        if not callable(mutator):
            raise TypeError("operation mutator must be callable")
        with self._task_lock(task_id):
            operation = self._load_operation_unlocked(task_id, operation_id)
            updated = mutator(operation)
            if not isinstance(updated, dict):
                raise ValueError("operation mutator must return an object")
            self._write_operation_unlocked(task_id, operation_id, updated)
            return updated

    def renew_operation_lease(self, task_id: str, operation_id: str, worker_id: str, lease_seconds: float) -> Dict[str, Any]:
        if not isinstance(worker_id, str) or not worker_id:
            raise ValueError("worker_id is required")
        def renew(operation):
            if operation.get("status") not in {"pending", "running"} or operation.get("worker_id") != worker_id:
                raise PermissionError("operation lease is not owned by this worker")
            operation["lease_expires_at_epoch"] = time.time() + max(0.0, float(lease_seconds))
            operation["updated_at"] = now()
            return operation
        return self.update_operation(task_id, operation_id, renew)

    def list_operations(self, task_id: str) -> list[Dict[str, Any]]:
        directory = safe_child_path(self.task_dir(task_id), "operations")
        if not directory.exists():
            return []
        operations = []
        for path in sorted(directory.glob("*.json")):
            safe_path = safe_child_path(directory, path.name)
            value = json.loads(safe_path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                operations.append(value)
        return operations

    def find_operation_by_idempotency(self, task_id: str, idempotency_key: str) -> Dict[str, Any] | None:
        for operation in self.list_operations(task_id):
            if operation.get("idempotency_key") == idempotency_key:
                return operation
        return None

    def resume(self, task_id: str) -> Dict[str, Any]:
        return self.load(task_id)

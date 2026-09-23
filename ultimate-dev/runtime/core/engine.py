from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Iterable
from .state import TaskStore

class Runtime:
    """Durable control plane; deliberately independent of any model/provider."""

    def __init__(self, project_root: str | Path):
        self.store = TaskStore(project_root)

    def start(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        required = ("goal",)
        missing = [k for k in required if not contract.get(k)]
        if missing: raise ValueError(f"Missing task contract fields: {missing}")
        contract = dict(contract)
        contract.setdefault("definition_of_done", [])
        contract.setdefault("acceptance_criteria", [])
        contract.setdefault("constraints", [])
        contract.setdefault("required_evidence", [])
        contract.setdefault("allowed_actions", [])
        contract.setdefault("forbidden_actions", [])
        state = self.store.create(contract)
        self.store.append_event(state["task_id"], {"type": "task_started"})
        return self.store.update(state["task_id"], status="ready")

    def transition(self, task_id: str, status: str, **changes) -> Dict[str, Any]:
        allowed = {
            "created": {"ready"}, "ready": {"planning","blocked"},
            "planning": {"planned","blocked"}, "planned": {"executing","blocked"},
            "executing": {"observing","blocked","failed"}, "observing": {"verifying"},
            "verifying": {"completed","failed","recovering"},
            "recovering": {"replanned","blocked"}, "replanned": {"executing"},
            "failed": {"recovering","blocked"}, "completed": set(), "blocked": {"ready","recovering"}
        }
        current = self.store.load(task_id)["status"]
        if status not in allowed.get(current, set()):
            raise ValueError(f"Invalid transition {current} -> {status}")
        return self.store.update(task_id, status=status, **changes)

    def checkpoint(self, task_id: str):
        return self.store.checkpoint(task_id)

    def handoff(self, task_id: str, target="next"):
        return self.store.handoff(task_id, target)

    def resume(self, task_id: str):
        return self.store.resume(task_id)

    def record_execution(self, task_id: str, action: Dict[str, Any], result: Dict[str, Any]):
        self.store.append_event(task_id, {"type":"execution", "action":action, "result":result})
        changed = result.get("changed_files", [])
        state = self.store.load(task_id)
        merged = list(dict.fromkeys(state["changed_files"] + changed))
        return self.store.update(task_id, changed_files=merged)

    def record_verification(self, task_id: str, passed: Iterable[str], pending: Iterable[str] = (), evidence: Dict[str, Any] | None = None):
        state = self.store.load(task_id)
        verification = {
            "passed": list(dict.fromkeys(state["verification"]["passed"] + list(passed))),
            "pending": list(pending),
        }
        if evidence:
            self.store.save(task_id, f"evidence/{state['revision']:06d}-verification.json", evidence)
        return self.store.update(task_id, verification=verification)

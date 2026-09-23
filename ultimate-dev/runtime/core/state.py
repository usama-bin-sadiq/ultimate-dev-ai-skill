from __future__ import annotations
import json, os, tempfile, time, uuid
from pathlib import Path
from typing import Any, Dict

def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

class TaskStore:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.base = self.project_root / ".memory" / "ultimate-dev" / "tasks"
        self.base.mkdir(parents=True, exist_ok=True)

    def task_dir(self, task_id: str) -> Path:
        return self.base / task_id

    def create(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        task_id = contract.get("task_id") or f"task-{uuid.uuid4().hex[:12]}"
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
            "completed": [], "in_progress": [], "next_action": None,
            "changed_files": [], "decisions": [], "failed_approaches": [],
            "verification": {"passed": [], "pending": []},
            "blockers": [], "open_questions": [],
            "events": []
        }
        self.save(task_id, "state.json", state)
        self.save(task_id, "context.json", {"layers": {}, "loaded": [], "budget": None})
        self.save(task_id, "progress.md", "# Progress\n")
        (d/"checkpoints").mkdir()
        (d/"handoffs").mkdir()
        (d/"evidence").mkdir()
        return state

    def save(self, task_id: str, filename: str, value: Any) -> None:
        d = self.task_dir(task_id); d.mkdir(parents=True, exist_ok=True)
        target = d / filename
        fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=d)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                if isinstance(value, str): f.write(value)
                else: json.dump(value, f, indent=2, ensure_ascii=False)
                f.flush(); os.fsync(f.fileno())
            os.replace(tmp, target)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)

    def load(self, task_id: str) -> Dict[str, Any]:
        with open(self.task_dir(task_id)/"state.json", encoding="utf-8") as f:
            return json.load(f)

    def update(self, task_id: str, **changes) -> Dict[str, Any]:
        state = self.load(task_id)
        state.update(changes)
        state["revision"] += 1
        state["updated_at"] = now()
        self.save(task_id, "state.json", state)
        return state

    def append_event(self, task_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        state = self.load(task_id)
        state["events"].append({"at": now(), **event})
        state["revision"] += 1
        state["updated_at"] = now()
        self.save(task_id, "state.json", state)
        return state

    def checkpoint(self, task_id: str) -> Path:
        state = self.load(task_id)
        cp = self.task_dir(task_id)/"checkpoints"/f"{state['revision']:06d}.json"
        self.save(task_id, f"checkpoints/{cp.name}", state)
        return cp

    def handoff(self, task_id: str, target: str = "next") -> Path:
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
        name = f"{state['revision']:06d}-{target}.json"
        self.save(task_id, f"handoffs/{name}", packet)
        return self.task_dir(task_id)/"handoffs"/name

    def resume(self, task_id: str) -> Dict[str, Any]:
        return self.load(task_id)

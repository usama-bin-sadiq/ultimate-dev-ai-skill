from __future__ import annotations
from pathlib import Path
from typing import Any

LAYERS = ("task","state","decisions","relevant_files","skill","history","deep_project")

class ContextManager:
    """Progressive-disclosure context builder. Never requires full project history."""
    def __init__(self, project_root: str | Path, store):
        self.root = Path(project_root).resolve()
        self.store = store

    def build(self, task_id: str, *, skill: str | None = None, files: list[str] | None = None,
              history: str | None = None, budget: int = 8000) -> dict[str, Any]:
        state = self.store.load(task_id)
        ctx = {
            "task": state["contract"],
            "state": {k: state[k] for k in ("status","completed","in_progress","next_action","changed_files","blockers")},
            "decisions": state["decisions"][-10:],
            "relevant_files": {},
            "skill": skill,
            "history": history,
            "deep_project": None,
            "budget": budget,
        }
        remaining = max(0, budget - len(str(ctx))//4)
        for rel in files or []:
            if remaining <= 0: break
            p = self.root / rel
            if p.is_file() and not any(part in {".git","node_modules","dist","build"} for part in p.parts):
                text = p.read_text(errors="replace")
                max_chars = min(len(text), remaining*4)
                ctx["relevant_files"][rel] = text[:max_chars]
                remaining -= max_chars//4
        self.store.save(task_id, "context.json", ctx)
        return ctx

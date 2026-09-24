from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import safe_child_path

LAYERS = ("task", "state", "decisions", "relevant_files", "skill", "history", "memory", "deep_project")
_EXCLUDED_PARTS = frozenset({".git", "node_modules", "dist", "build", ".memory"})
_EXCLUDED_NAMES = frozenset({".env", "credentials", "secrets", "id_rsa", "id_ed25519"})


class ContextManager:
    """Progressive-disclosure context builder with fail-closed file scope."""

    def __init__(self, project_root: str | Path, store):
        self.root = Path(project_root).resolve()
        self.store = store

    def build(
        self,
        task_id: str,
        *,
        skill: str | None = None,
        files: list[str] | None = None,
        history: str | None = None,
        memory_store=None,
        memory_scope: str = "global",
        memory_budget: int | None = None,
        budget: int = 8000,
    ) -> dict[str, Any]:
        if not isinstance(budget, int) or budget < 0:
            raise ValueError("context budget must be a non-negative integer")
        if files is not None and not isinstance(files, list):
            raise ValueError("context files must be an array")
        state = self.store.load(task_id)
        ctx = {
            "task": state["contract"],
            "state": {
                key: state[key]
                for key in (
                    "status",
                    "completed",
                    "in_progress",
                    "next_action",
                    "changed_files",
                    "blockers",
                    "open_questions",
                )
            },
            "decisions": state.get("decisions", [])[-10:],
            "relevant_files": {},
            "truncated_files": [],
            "skill": None,
            "history": None,
            "deep_project": None,
            "memory": None,
            "budget": budget,
        }
        remaining = max(0, budget - len(str(ctx)) // 4)
        if memory_store is None:
            memory_store = getattr(self, "memory_store", None)
        if memory_store is not None:
            if not hasattr(memory_store, "project_context"):
                raise ValueError("memory_store must provide project_context()")
            projection_budget = remaining * 4 if memory_budget is None else memory_budget
            if isinstance(projection_budget, bool) or not isinstance(projection_budget, int) or projection_budget < 0:
                raise ValueError("memory_budget must be a non-negative integer")
            projection = memory_store.project_context(memory_scope, budget=projection_budget)
            if not isinstance(projection, dict) or not isinstance(projection.get("items"), list):
                raise ValueError("memory_store.project_context() returned an invalid projection")
            ctx["memory"] = projection
            remaining = max(0, remaining - len(str(projection)) // 4)
        for key, value in (("skill", skill), ("history", history)):
            if value is None or remaining <= 0:
                continue
            max_chars = remaining * 4
            text = str(value)
            ctx[key] = text[:max_chars]
            if len(text) > max_chars:
                ctx["truncated_files"].append(key)
            remaining -= max(0, (len(ctx[key]) + 3) // 4)
        for rel in files or []:
            if remaining <= 0:
                break
            path = safe_child_path(self.root, rel)
            relative_parts = path.relative_to(self.root).parts
            if not path.is_file() or any(
                part in _EXCLUDED_PARTS
                or part.lower() in _EXCLUDED_NAMES
                or part.lower().startswith(".env")
                or part.lower().endswith((".pem", ".key", ".secret"))
                for part in relative_parts
            ):
                continue
            max_chars = remaining * 4
            with path.open("rb") as handle:
                raw = handle.read(max_chars + 1)
            truncated_bytes = len(raw) > max_chars
            raw = raw[:max_chars]
            text = raw.decode("utf-8", errors="replace")
            if truncated_bytes or len(text) >= max_chars:
                ctx["truncated_files"].append(rel)
            ctx["relevant_files"][rel] = text
            remaining -= max(0, (len(text) + 3) // 4)
        self.store.save(task_id, "context.json", ctx)
        return ctx

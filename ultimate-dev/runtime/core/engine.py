from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from .state import TaskStore
from .session_manager import SessionManager

class Runtime:
    """Durable control plane with a host-native capability seam.

    JEV is evaluated by the host adapter and supplied as a decision packet.
    This legacy Python runtime persists and gates that packet; it does not
    import a model provider, install a sandbox, or select a browser backend.
    """

    def __init__(self, project_root: str | Path, interactive: bool = False,
                 host_executor=None, require_jev_decision: bool = False):
        self.store = TaskStore(project_root)
        self.session = SessionManager(project_root, host_executor=host_executor)
        self.require_jev_decision = require_jev_decision
        self.jev_decisions: Dict[str, Dict[str, Any]] = {}
        # Ask about legacy preferences at session start (if interactive)
        self.session.ask_sandbox_preferences(interactive=interactive)

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

    def record_jev_decision(self, task_id: str, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Persist a host-produced JEV packet before any execution transition."""
        if not isinstance(decision, dict):
            raise ValueError("JEV decision must be a mapping")
        if not decision.get("schema_version") or not decision.get("execution_effect"):
            raise ValueError("JEV decision is missing schema_version or execution_effect")
        if decision.get("task_id") and decision.get("task_id") != task_id:
            raise ValueError("JEV decision task_id does not match the runtime task")
        state = self.store.load(task_id)
        revision = state["revision"] + 1
        self.store.save(task_id, f"evidence/jev-{revision:06d}.json", decision)
        self.store.append_event(task_id, {
            "type": "jev_decision",
            "execution_effect": decision.get("execution_effect"),
            "guardrail": decision.get("guardrail", {}).get("action"),
        })
        current = self.store.load(task_id)
        reasons = decision.get("guardrail", {}).get("reasons", [])
        summary = {
            "type": "jev_decision",
            "execution_effect": decision.get("execution_effect"),
            "guardrail": decision.get("guardrail", {}).get("action"),
            "route": decision.get("route", {}).get("path"),
            "reason_codes": [item.get("code") for item in reasons if isinstance(item, dict)],
            "evidence": f"evidence/jev-{revision:06d}.json",
        }
        self.store.update(task_id, decisions=current["decisions"] + [summary])
        self.jev_decisions[task_id] = decision
        return decision

    def _jev_allows_execution(self, task_id: str) -> bool:
        decision = self.jev_decisions.get(task_id)
        return bool(
            decision
            and decision.get("ok") is True
            and decision.get("execution_effect") == "execute"
            and decision.get("guardrail", {}).get("action") == "approve"
            and decision.get("route", {}).get("path") in {"lightweight", "flagship"}
        )

    def transition(self, task_id: str, status: str, jev_decision: Dict[str, Any] | None = None, **changes) -> Dict[str, Any]:
        if jev_decision is not None:
            self.record_jev_decision(task_id, jev_decision)
        if status == "executing" and self.require_jev_decision and not self._jev_allows_execution(task_id):
            raise PermissionError("An approved JEV decision is required before execution")
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

    def execute_code(self, task_id: str, code: str, language: str = "python",
                     jev_decision: Dict[str, Any] | None = None,
                     require_jev_decision: bool | None = None, **kwargs) -> Dict[str, Any]:
        """Execute through an injected host adapter after the JEV gate.

        The Python Runtime never chooses a sandbox or browser provider. The
        host adapter supplies an already-evaluated decision packet.
        """
        if jev_decision is not None:
            self.record_jev_decision(task_id, jev_decision)
        required = self.require_jev_decision if require_jev_decision is None else require_jev_decision
        if required and not self._jev_allows_execution(task_id):
            return {
                "success": False,
                "error": "An approved JEV decision is required before execution",
                "code": "jev_decision_required",
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
            }
        task_description = kwargs.pop("task_description", "")
        return self.session.execute_code(code, language=language, task_description=task_description, **kwargs)
    
    def task_requires_execution(self, contract: Dict[str, Any]) -> bool:
        """Return a coarse legacy execution hint, never an authorization."""
        execution_keywords = [
            "execute", "run", "test", "build", "deploy", "compile",
            "lint", "format", "benchmark", "benchmark", "screenshot",
            "browser", "navigate", "click", "type", "scrape",
            "execute_code", "run_code", "run_command"
        ]
        goal = contract.get("goal", "").lower()
        return any(kw in goal for kw in execution_keywords)

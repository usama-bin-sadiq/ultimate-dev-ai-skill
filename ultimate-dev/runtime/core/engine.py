from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from .capabilities import CapabilityRegistry
from .context import ContextManager
from .contracts import (
    ContractError,
    action_fingerprint,
    fingerprint,
    safe_child_path,
    validate_capability_id,
    validate_fingerprint,
    validate_identifier,
    validate_jev_packet,
)
from .policy import Policy
from .session_manager import RuntimeSessionView, SessionManager
from .state import TaskStore
from .verification import Verification


class Runtime:
    """Durable control plane with a host-native capability seam.

    JEV is evaluated by the host adapter and supplied as a decision packet.
    This Python compatibility runtime validates and binds that packet, persists
    state, and delegates approved actions to an explicitly injected executor.
    It never imports a model provider or selects a sandbox/browser provider.
    """

    _ALLOWED_TRANSITION_CHANGES = frozenset({
        "next_action",
        "completed",
        "in_progress",
        "changed_files",
        "blockers",
        "open_questions",
    })

    def __init__(
        self,
        project_root: str | Path,
        interactive: bool = False,
        host_executor=None,
        require_jev_decision: bool = True,
        policy: Policy | None = None,
        capability_registry: CapabilityRegistry | None = None,
        operation_lease_seconds: float = 300.0,
        verification_evaluator=None,
        memory_store=None,
    ):
        self.store = TaskStore(project_root)
        self.context = ContextManager(project_root, self.store)
        self.context.memory_store = memory_store
        self._session = SessionManager(self.store.project_root, host_executor=host_executor)
        self.session = RuntimeSessionView(self._session)
        self.require_jev_decision = bool(require_jev_decision)
        self.policy = policy or Policy()
        self.capability_registry = capability_registry
        self.verification_evaluator = verification_evaluator
        self.memory_store = memory_store
        self.operation_lease_seconds = max(0.0, float(operation_lease_seconds))
        self.worker_id = f"worker-{uuid.uuid4().hex[:12]}"
        self.jev_decisions: Dict[str, Dict[str, Any]] = {}
        self._decision_bindings: Dict[str, str | None] = {}
        self._decision_packet_digests: Dict[str, str] = {}
        self._session.ask_sandbox_preferences(interactive=interactive)

    @staticmethod
    def _error(code: str, message: str, **extra: Any) -> Dict[str, Any]:
        result = {
            "success": False,
            "error": message,
            "code": code,
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
        }
        result.update(extra)
        return result

    def start(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(contract, dict):
            raise ValueError("Task contract must be a mapping")
        if not isinstance(contract.get("goal"), str) or not contract["goal"].strip():
            raise ValueError("Task contract goal must be a non-empty string")
        list_fields = (
            "definition_of_done",
            "acceptance_criteria",
            "constraints",
            "required_evidence",
            "allowed_actions",
            "forbidden_actions",
        )
        for field in list_fields:
            if field in contract:
                if not isinstance(contract[field], list):
                    raise ValueError(f"Task contract {field} must be an array")
                if any(not isinstance(item, str) for item in contract[field]):
                    raise ValueError(f"Task contract {field} must contain strings")
        contract = dict(contract)
        for field in list_fields:
            contract.setdefault(field, [])
        state = self.store.create(contract)
        self.store.append_event(state["task_id"], {"type": "task_started"})
        return self.store.update_internal(state["task_id"], status="ready")

    def _load_persisted_decision(self, task_id: str) -> None:
        """Restore and revalidate the latest packet on every authorization check."""
        self.jev_decisions.pop(task_id, None)
        self._decision_bindings.pop(task_id, None)
        self._decision_packet_digests.pop(task_id, None)
        state = self.store.load(task_id)
        evidence_dir = self.task_evidence_dir(task_id)
        files = sorted(evidence_dir.glob("jev-*.json"))
        if not files:
            return
        path = files[-1]
        binding_map = {
            item.get("evidence"): item
            for item in state.get("decision_bindings", [])
            if isinstance(item, dict) and isinstance(item.get("evidence"), str)
        }
        evidence_ref = f"evidence/{path.name}"
        binding = binding_map.get(evidence_ref)
        try:
            safe_path = safe_child_path(evidence_dir, path.name)
            with open(safe_path, encoding="utf-8") as f:
                candidate = json.load(f)
            candidate = validate_jev_packet(candidate, task_id, strict=True)
            if not binding or binding.get("packet_digest") != fingerprint(candidate):
                raise ContractError("JEV packet binding is missing or does not match the packet")
            if candidate.get("execution_effect") == "execute":
                validate_fingerprint(binding.get("action_fingerprint"))
        except (OSError, json.JSONDecodeError, ContractError, TypeError, ValueError):
            return
        self.jev_decisions[task_id] = candidate
        self._decision_bindings[task_id] = binding.get("action_fingerprint")
        self._decision_packet_digests[task_id] = binding.get("packet_digest")

    def task_evidence_dir(self, task_id: str) -> Path:
        directory = safe_child_path(self.store.task_dir(task_id), "evidence")
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def record_jev_decision(
        self,
        task_id: str,
        decision: Dict[str, Any],
        action_fingerprint: str | None = None,
    ) -> Dict[str, Any]:
        """Validate, bind, and persist a host-produced JEV packet."""
        state = self.store.load(task_id)
        packet = validate_jev_packet(decision, task_id, strict=True)
        if packet.get("execution_effect") == "execute" and action_fingerprint is None:
            raise ContractError("executable JEV decisions require an action fingerprint")
        if action_fingerprint is not None:
            action_fingerprint = validate_fingerprint(action_fingerprint)
        packet_digest = fingerprint(packet)
        for previous in state.get("decision_bindings", []):
            if previous.get("packet_digest") == packet_digest and previous.get("action_fingerprint") != action_fingerprint:
                raise ContractError("JEV packet is already bound to a different action")
        evidence_name = f"jev-{state['revision'] + 1:06d}-{uuid.uuid4().hex[:8]}.json"
        evidence_path = f"evidence/{evidence_name}"
        self.store.save(task_id, evidence_path, packet)
        self.store.append_event(
            task_id,
            {
                "type": "jev_decision",
                "execution_effect": packet.get("execution_effect"),
                "guardrail": packet.get("guardrail", {}).get("action"),
                "evidence": evidence_path,
            },
        )
        reasons = packet.get("guardrail", {}).get("reasons", [])
        summary = {
            "type": "jev_decision",
            "task_id": task_id,
            "execution_effect": packet.get("execution_effect"),
            "guardrail": packet.get("guardrail", {}).get("action"),
            "route": packet.get("route", {}).get("path"),
            "reason_codes": [item.get("code") for item in reasons if isinstance(item, dict)],
            "evidence": evidence_path,
            "action_fingerprint": action_fingerprint,
            "packet_digest": packet_digest,
        }
        binding = {
            "evidence": evidence_path,
            "action_fingerprint": action_fingerprint,
            "packet_digest": packet_digest,
        }
        self.store.append_decision_binding(task_id, summary, binding)
        self.jev_decisions[task_id] = packet
        self._decision_bindings[task_id] = action_fingerprint
        self._decision_packet_digests[task_id] = packet_digest
        return packet

    def _jev_allows_execution(
        self,
        task_id: str,
        action_fingerprint_value: str | None = None,
        capability_id: str | None = None,
    ) -> bool:
        self._load_persisted_decision(task_id)
        decision = self.jev_decisions.get(task_id)
        if not decision:
            return False
        if not (
            decision.get("ok") is True
            and decision.get("execution_effect") == "execute"
            and decision.get("guardrail", {}).get("action") == "approve"
            and decision.get("route", {}).get("path") in {"lightweight", "flagship"}
            and decision.get("capability_plan", {}).get("selected")
        ):
            return False
        if action_fingerprint_value is not None:
            if self._decision_bindings.get(task_id) != action_fingerprint_value:
                return False
        if capability_id is not None:
            validate_capability_id(capability_id)
            selected = decision.get("capability_plan", {}).get("selected", [])
            if capability_id not in selected:
                return False
        return True

    def _completion_blockers(self, task_id: str) -> list[str]:
        state = self.store.load(task_id)
        contract = state.get("contract", {})
        criteria = list(contract.get("acceptance_criteria", []))
        criteria.extend(contract.get("definition_of_done", []))
        passed = set(state.get("verification", {}).get("passed", []))
        blockers = []
        missing = [criterion for criterion in criteria if criterion not in passed]
        if missing:
            blockers.append(f"unproven criteria: {', '.join(map(str, missing))}")
        if state.get("verification", {}).get("pending"):
            blockers.append("verification has pending criteria")
        if state.get("blockers"):
            blockers.append("task has unresolved blockers")
        verification = state.get("verification", {})
        required_evidence = contract.get("required_evidence", [])
        evidence_items = verification.get("evidence_items", [])
        if required_evidence and len(evidence_items) < len(required_evidence):
            blockers.append("required evidence items are incomplete")
        if required_evidence and not verification.get("evidence_refs"):
            blockers.append("required evidence has not been recorded")
        for evidence_ref in verification.get("evidence_refs", []):
            try:
                evidence_path = safe_child_path(self.store.task_dir(task_id), evidence_ref)
                if not evidence_path.is_file():
                    blockers.append(f"evidence file is missing: {evidence_ref}")
                    continue
                with open(evidence_path, encoding="utf-8") as handle:
                    evidence_payload = json.load(handle)
                if not isinstance(evidence_payload.get("items"), list):
                    blockers.append(f"evidence file has no items: {evidence_ref}")
                elif evidence_ref == verification.get("evidence_refs", [])[-1] and fingerprint(evidence_payload["items"]) != verification.get("evidence_digest"):
                    blockers.append(f"evidence digest mismatch: {evidence_ref}")
            except (OSError, json.JSONDecodeError, ContractError, AttributeError):
                blockers.append(f"evidence file is invalid: {evidence_ref}")
        return blockers

    def transition(
        self,
        task_id: str,
        status: str,
        jev_decision: Dict[str, Any] | None = None,
        **changes: Any,
    ) -> Dict[str, Any]:
        forbidden_changes = set(changes) - self._ALLOWED_TRANSITION_CHANGES
        if forbidden_changes:
            raise ValueError(f"transition cannot modify protected state fields: {sorted(forbidden_changes)}")
        state = self.store.load(task_id)
        current = state["status"]
        allowed = {
            "created": {"ready"},
            "ready": {"planning", "blocked"},
            "planning": {"planned", "blocked"},
            "planned": {"executing", "blocked"},
            "executing": {"observing", "blocked", "failed"},
            "observing": {"verifying"},
            "verifying": {"completed", "failed", "recovering"},
            "recovering": {"replanned", "blocked"},
            "replanned": {"executing"},
            "failed": {"recovering", "blocked"},
            "completed": set(),
            "blocked": {"ready", "recovering"},
        }
        if status not in allowed.get(current, set()):
            raise ValueError(f"Invalid transition {current} -> {status}")
        if status == "completed":
            blockers = self._completion_blockers(task_id)
            if blockers:
                raise PermissionError("; ".join(blockers))
        if jev_decision is not None:
            self.record_jev_decision(task_id, jev_decision)
        if status == "executing" and self.require_jev_decision and not self._jev_allows_execution(task_id):
            raise PermissionError("An approved JEV decision is required before execution")
        updated = self.store.update_if_status(task_id, current, {"status": status, **changes}, _internal=True)
        if updated is None:
            raise ValueError("Task state changed concurrently; retry the transition")
        return self.store.append_event(
            task_id,
            {"type": "transition", "from": current, "to": status},
        ) or updated

    def checkpoint(self, task_id: str):
        return self.store.checkpoint(task_id)

    def handoff(self, task_id: str, target: str = "next"):
        return self.store.handoff(task_id, target)

    def recover_stale_operations(self, task_id: str) -> int:
        """Mark expired leases uncertain instead of replaying unknown side effects."""
        recovered = 0
        cutoff = time.time()
        for operation in self.store.list_operations(task_id):
            if operation.get("status") not in {"pending", "running"}:
                continue
            lease = operation.get("lease_expires_at_epoch")
            if not isinstance(lease, (int, float)) or lease >= cutoff:
                continue
            def mark(op):
                op["status"] = "uncertain"
                op["result"] = self._error(
                    "operation_lease_expired",
                    "Operation lease expired; verify external state before retry",
                )
                op["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                op["recovered_at"] = op["updated_at"]
                return op
            self.store.update_operation(task_id, operation["operation_id"], mark)
            recovered += 1
        return recovered

    def resume(self, task_id: str):
        self.recover_stale_operations(task_id)
        self._load_persisted_decision(task_id)
        return self.store.resume(task_id)

    def cancel_operation(self, task_id: str, operation_id: str) -> Dict[str, Any]:
        """Atomically mark a nonterminal operation cancelled."""
        cancelled = {"value": False}

        def cancel(operation):
            if operation.get("status") in {"pending", "running"}:
                operation["status"] = "cancelled"
                operation["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                cancelled["value"] = True
            return operation

        operation = self.store.update_operation(task_id, operation_id, cancel)
        if not cancelled["value"]:
            return self._error("operation_not_cancellable", "Operation is already terminal", operation_id=operation_id)
        return self.store.append_event(task_id, {"type": "operation_cancelled", "operation_id": operation_id})

    def renew_operation(self, task_id: str, operation_id: str) -> Dict[str, Any]:
        """Renew this Runtime worker's lease for a long-running operation."""
        try:
            return self.store.renew_operation_lease(
                task_id,
                operation_id,
                self.worker_id,
                self.operation_lease_seconds,
            )
        except (FileNotFoundError, PermissionError, ValueError) as exc:
            return self._error("operation_lease_denied", str(exc), operation_id=operation_id)

    def observe(self, task_id: str, observations: Any) -> Dict[str, Any]:
        """Persist bounded environment observations before verification."""
        state = self.store.load(task_id)
        if state["status"] not in {"executing", "observing"}:
            raise ValueError("observations require an executing or observing task")
        if isinstance(observations, Mapping):
            normalized = [dict(observations)]
        elif isinstance(observations, list):
            normalized = [dict(item) for item in observations if isinstance(item, Mapping)]
        else:
            raise ValueError("observations must be an object or list of objects")
        retained = (state.get("observations", []) + normalized)[-100:]
        self.store.update_internal(task_id, observations=retained)
        return self.store.append_event(
            task_id,
            {"type": "observation", "count": len(normalized)},
        )

    def record_execution(self, task_id: str, action: Dict[str, Any], result: Dict[str, Any]):
        if not isinstance(action, dict) or not isinstance(result, dict):
            raise ValueError("execution action and result must be objects")
        changed = result.get("changed_files", [])
        if not isinstance(changed, list):
            changed = []
        state = self.store.load(task_id)
        merged = list(dict.fromkeys(state.get("changed_files", []) + changed))
        self.store.update_internal(task_id, changed_files=merged)
        return self.store.append_event(
            task_id,
            {"type": "execution", "action": action, "result": result},
        )

    def record_verification(
        self,
        task_id: str,
        passed: Iterable[str] = (),
        pending: Iterable[str] = (),
        evidence: Dict[str, Any] | None = None,
        evidence_items: list[dict[str, Any]] | None = None,
    ):
        state = self.store.load(task_id)
        if state["status"] not in {"executing", "observing", "verifying"}:
            raise ValueError("verification can only be recorded during execution/observation")
        criteria = list(state.get("contract", {}).get("acceptance_criteria", []))
        criteria.extend(state.get("contract", {}).get("definition_of_done", []))
        if evidence_items is None and isinstance(evidence, Mapping):
            candidate_items = evidence.get("items")
            if isinstance(candidate_items, list):
                evidence_items = candidate_items
        if evidence_items is None:
            raise ContractError("verification requires evidence items with provenance")
        if not isinstance(evidence_items, list):
            raise ContractError("evidence_items must be an array")
        evaluator = self.verification_evaluator or Verification().evaluate
        if not callable(evaluator):
            raise ContractError("verification evaluator must be callable")
        result = evaluator(criteria, evidence_items)
        if not isinstance(result, Mapping) or not isinstance(result.get("proven"), list) or not isinstance(result.get("unresolved"), list):
            raise ContractError("verification evaluator returned an invalid result")
        criteria_set = set(criteria)
        if any(not isinstance(item, str) or item not in criteria_set for item in result["proven"] + result["unresolved"]):
            raise ContractError("verification evaluator returned unknown criteria")
        passed_values = list(passed)
        if passed_values and set(passed_values) != set(result["proven"]):
            raise ContractError("passed criteria must be derived from evidence")
        pending_values = list(dict.fromkeys(list(pending) + result["unresolved"]))
        verification = dict(state.get("verification", {}))
        verification["passed"] = result["proven"]
        verification["pending"] = pending_values
        verification["evidence_items"] = evidence_items
        verification["evidence_digest"] = fingerprint(evidence_items)
        evidence_refs = list(verification.get("evidence_refs", []))
        evidence_name = f"{state['revision'] + 1:06d}-verification.json"
        evidence_path = f"evidence/{evidence_name}"
        payload = dict(evidence) if isinstance(evidence, Mapping) else {}
        payload["items"] = evidence_items
        self.store.save(task_id, evidence_path, payload)
        evidence_refs.append(evidence_path)
        verification["evidence_refs"] = list(dict.fromkeys(evidence_refs))
        self.store.update_internal(task_id, verification=verification)
        return self.store.append_event(
            task_id,
            {"type": "verification", "passed": verification["passed"], "pending": verification["pending"]},
        )

    @staticmethod
    def _contract_allows_action(contract: Mapping[str, Any], operation: str, capability_id: str) -> tuple[bool, str | None]:
        forbidden = set(contract.get("forbidden_actions", []))
        if operation in forbidden or capability_id in forbidden:
            return False, "contract_forbidden_action"
        allowed = set(contract.get("allowed_actions", []))
        if allowed and not ({operation, capability_id, "execute"} & allowed):
            return False, "contract_action_not_allowed"
        return True, None

    _KNOWN_EFFECTS = frozenset({
        "read", "write", "execute", "delete", "network", "communicate",
        "destroy", "force_push", "production", "rotate_credentials", "irreversible",
    })

    def prepare_execution_action(
        self,
        task_id: str,
        code: str,
        language: str = "python",
        *,
        capability_id: str = "shell.execute",
        effects: Iterable[str] = ("execute",),
        scope: Mapping[str, Any] | None = None,
        host_options: Mapping[str, Any] | None = None,
        task_description: str = "",
    ) -> dict[str, Any]:
        """Build the canonical action a host must submit to JEV."""
        validate_capability_id(capability_id)
        effect_values = {effects} if isinstance(effects, str) else set(effects or ())
        effect_values.add("execute")
        if any(not isinstance(effect, str) or effect not in self._KNOWN_EFFECTS for effect in effect_values):
            raise ContractError("effects contains an unknown or non-string value")
        action = {
            "operation": "execute_code",
            "task_id": task_id,
            "code": code,
            "language": language,
            "capability_id": capability_id,
            "effects": sorted(effect_values),
            "scope": dict(scope or {}),
            "task_description": task_description,
            "host_options": dict(host_options or {}),
        }
        return {"action": action, "fingerprint": action_fingerprint(action)}

    def _operation_id(self, operation_id: str | None, fingerprint: str) -> str:
        return validate_identifier(operation_id, "operation_id") if operation_id else f"op-{fingerprint[:24]}"

    def _persist_failed_operation(
        self,
        task_id: str,
        operation_id: str,
        idempotency_key: str,
        fingerprint: str,
        capability_id: str,
        code: str,
        message: str,
        **details: Any,
    ) -> Dict[str, Any]:
        result = self._error(code, message, capability_id=capability_id, **details)
        operation = {
            "operation_id": operation_id,
            "task_id": task_id,
            "attempt": 1,
            "idempotency_key": idempotency_key,
            "action_fingerprint": fingerprint,
            "capability_id": capability_id,
            "status": "failed",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "result": result,
            "worker_id": self.worker_id,
            "lease_expires_at_epoch": None,
        }
        _, existing = self.store.claim_operation(task_id, operation_id, operation)
        if existing is not None:
            if existing.get("action_fingerprint") != fingerprint:
                return self._error("operation_conflict", "operation_id is already bound to a different action", operation_id=operation_id)
            return {**existing.get("result", result), "operation_id": operation_id, "operation_status": existing.get("status", "failed"), "replayed": True}
        self.store.add_operation_id(task_id, operation_id)
        self.store.append_event(task_id, {"type": "operation_failed", "operation_id": operation_id, "code": code})
        return {**result, "operation_id": operation_id, "operation_status": "failed"}

    def execute_code(
        self,
        task_id: str,
        code: str,
        language: str = "python",
        jev_decision: Dict[str, Any] | None = None,
        require_jev_decision: bool | None = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute through an injected host adapter after strict authorization."""
        if require_jev_decision is False and self.require_jev_decision:
            return self._error("jev_decision_required", "Per-call execution cannot disable the Runtime JEV gate")
        required = self.require_jev_decision or bool(require_jev_decision)
        capability_id = kwargs.pop("capability_id", "shell.execute")
        approval_confirmed = kwargs.pop("approval_confirmed", False)
        if not isinstance(approval_confirmed, bool):
            return self._error("invalid_action", "approval_confirmed must be boolean")
        operation_id_input = kwargs.pop("operation_id", None)
        idempotency_key_input = kwargs.pop("idempotency_key", None)
        retry = bool(kwargs.pop("retry", False))
        task_description = kwargs.pop("task_description", "")
        if not isinstance(task_description, str):
            return self._error("invalid_action", "task_description must be a string")
        try:
            validate_capability_id(capability_id)
        except ContractError as exc:
            return self._error("invalid_action", str(exc))
        effects_value = kwargs.pop("effects", ("execute",))
        if isinstance(effects_value, str):
            effects = {effects_value}
        else:
            try:
                effects = set(effects_value or ())
            except TypeError:
                return self._error("invalid_action", "effects must be a string or iterable")
        # The code-execution operation itself is never allowed to under-declare
        # its effect by replacing the default with a narrower caller label.
        effects.add("execute")
        scope = kwargs.pop("scope", {})
        if not isinstance(scope, Mapping):
            return self._error("invalid_action", "scope must be an object")
        host_options = dict(kwargs)
        try:
            action = self.prepare_execution_action(
                task_id,
                code,
                language,
                capability_id=capability_id,
                effects=effects,
                scope=scope,
                host_options=host_options,
                task_description=task_description,
            )["action"]
            fingerprint = action_fingerprint(action)
        except ContractError as exc:
            return self._error("invalid_action", str(exc))
        if jev_decision is not None:
            return self._error(
                "jev_decision_must_be_bound",
                "Record a JEV decision with prepare_execution_action() before execution",
            )
        try:
            state = self.store.load(task_id)
        except (FileNotFoundError, OSError, ValueError) as exc:
            return self._error("task_not_found", f"Unable to load task state: {exc}")
        if state["status"] not in {"planned", "executing"}:
            return self._error("invalid_task_state", f"Task must be planned or executing, not {state['status']}")
        contract_allowed, contract_reason = self._contract_allows_action(state.get("contract", {}), "execute_code", capability_id)
        if not contract_allowed:
            return self._error(contract_reason or "policy_denied", "Task contract does not authorize this action")
        if required and not self._jev_allows_execution(task_id, fingerprint, capability_id):
            return self._error("jev_decision_required", "An approved, action-bound JEV decision is required")
        try:
            operation_id = self._operation_id(operation_id_input, fingerprint)
            idempotency_key = idempotency_key_input or fingerprint
        except ContractError as exc:
            return self._error("invalid_action", str(exc))
        if not isinstance(idempotency_key, str) or not idempotency_key:
            return self._error("invalid_action", "idempotency_key must be a non-empty string")
        capability = None
        if self.capability_registry is not None:
            capability = self.capability_registry.get(capability_id)
            if capability is None or not capability.available:
                return self._persist_failed_operation(
                    task_id,
                    operation_id,
                    idempotency_key,
                    fingerprint,
                    capability_id,
                    "capability_unavailable",
                    f"Capability {capability_id!r} is unavailable",
                )
            declared_effects = set(getattr(capability, "effects", set()))
            if effects and not effects.issubset(declared_effects):
                return self._error(
                    "capability_effect_mismatch",
                    "Requested effects exceed the capability declaration",
                    capability_id=capability_id,
                    declared_effects=sorted(declared_effects),
                )
        if task_id not in self.jev_decisions:
            self._load_persisted_decision(task_id)
        decision = self.jev_decisions.get(task_id, {})
        confirmed = approval_confirmed
        policy_result = self.policy.check_capability(
            capability_id,
            effects,
            confirmed=confirmed,
            irreversible=bool(capability is not None and not getattr(capability, "reversible", True)),
        )
        if not policy_result["allowed"]:
            return self._persist_failed_operation(
                task_id,
                operation_id,
                idempotency_key,
                fingerprint,
                capability_id,
                "policy_denied",
                "Runtime policy denied this capability",
                policy=policy_result,
            )
        if state["status"] == "planned":
            try:
                self.transition(task_id, "executing")
            except (PermissionError, ValueError) as exc:
                return self._error("execution_state_error", str(exc))

        try:
            existing = self.store.load_operation(task_id, operation_id)
        except FileNotFoundError:
            existing = None
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return self._error("operation_state_invalid", f"Unable to load operation state: {exc}", operation_id=operation_id)
        if idempotency_key_input:
            keyed = self.store.find_operation_by_idempotency(task_id, idempotency_key)
            if keyed is not None and keyed.get("operation_id") != operation_id:
                if keyed.get("action_fingerprint") != fingerprint:
                    return self._error("operation_conflict", "idempotency_key is bound to a different action", operation_id=keyed.get("operation_id"))
                if keyed.get("status") == "succeeded":
                    return {**keyed.get("result", {}), "operation_id": keyed.get("operation_id"), "replayed": True}
                return self._error("operation_in_progress", "Idempotency key is already in use", operation_id=keyed.get("operation_id"))
        if existing and (existing.get("action_fingerprint") != fingerprint or existing.get("idempotency_key") != idempotency_key):
            return self._error(
                "operation_conflict",
                "operation_id is already bound to a different action",
                operation_id=operation_id,
            )
        if existing and existing.get("status") == "succeeded":
            return {**existing.get("result", {}), "operation_id": operation_id, "replayed": True}
        if existing and existing.get("status") in {"running", "pending"}:
            return self._error("operation_in_progress", "Operation is already running", operation_id=operation_id)
        if existing and not retry:
            return self._error("operation_not_retryable", "Failed operation requires an explicit retry", operation_id=operation_id)

        attempt = int(existing.get("attempt", 0)) + 1 if existing else 1
        operation = {
            "operation_id": operation_id,
            "task_id": task_id,
            "attempt": attempt,
            "idempotency_key": idempotency_key,
            "action_fingerprint": fingerprint,
            "capability_id": capability_id,
            "status": "running",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "worker_id": self.worker_id,
            "lease_expires_at_epoch": time.time() + self.operation_lease_seconds,
        }
        if existing:
            def restart(previous):
                if previous.get("status") not in {"failed", "uncertain", "cancelled"}:
                    raise ValueError("operation is not retryable")
                previous.update(operation)
                previous["attempt"] = attempt
                return previous
            operation = self.store.update_operation(task_id, operation_id, restart)
        else:
            _, raced = self.store.claim_operation(task_id, operation_id, operation)
            if raced is not None:
                if raced.get("action_fingerprint") != fingerprint:
                    return self._error("operation_conflict", "operation_id is already bound to a different action", operation_id=operation_id)
                if raced.get("status") == "succeeded":
                    return {**raced.get("result", {}), "operation_id": operation_id, "replayed": True}
                return self._error("operation_in_progress", "Operation is already running", operation_id=operation_id)
        self.store.add_operation_id(task_id, operation_id)
        self.store.append_event(task_id, {"type": "operation_started", "operation_id": operation_id, "action_fingerprint": fingerprint})

        executor = self._session.host_executor
        if executor is None and capability is not None:
            executor = capability.execute
        if executor is None:
            result = self._error("capability_unavailable", "No host execution adapter is available")
        else:
            try:
                result = executor(
                    code=code,
                    language=language,
                    task_description=task_description,
                    task_id=task_id,
                    operation_id=operation_id,
                    capability_id=capability_id,
                    action_fingerprint=fingerprint,
                    scope=dict(scope),
                    **host_options,
                )
                if not isinstance(result, dict):
                    result = self._error("malformed_tool_result", "Host executor returned a non-object result")
            except Exception as exc:  # host adapters are an external boundary
                result = self._error("executor_error", f"Host executor failed ({type(exc).__name__})")

        try:
            json.dumps(result, allow_nan=False)
        except (TypeError, ValueError):
            result = self._error("malformed_tool_result", "Host executor returned non-JSON-safe data")
        def finish(previous):
            if previous.get("status") == "cancelled":
                return previous
            previous["status"] = "succeeded" if result.get("success") is True else ("uncertain" if result.get("uncertain") is True else "failed")
            previous["result"] = result
            previous["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            previous["lease_expires_at_epoch"] = None
            return previous
        final_operation = self.store.update_operation(task_id, operation_id, finish)
        operation_status = final_operation.get("status")
        if operation_status == "cancelled":
            result = self._error(
                "operation_cancelled",
                "Operation was cancelled while the host action was in flight",
                operation_id=operation_id,
            )
        self.store.append_event(task_id, {"type": "operation_finished", "operation_id": operation_id, "status": operation_status})
        if operation_status != "cancelled":
            self.record_execution(task_id, {"operation_id": operation_id, "capability_id": capability_id, "action_fingerprint": fingerprint}, result)
        return {**result, "operation_id": operation_id, "operation_status": operation_status}

    def prepare_workflow_action(self, task_id: str, catalog, workflow, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Build the action fingerprint for a capability-backed workflow."""
        definition = catalog.get_workflow(workflow) if isinstance(workflow, str) else workflow
        if definition is None:
            raise ContractError("workflow definition was not found")
        action = {
            "operation": "execute_workflow",
            "task_id": task_id,
            "workflow_id": definition.id,
            "catalog_fingerprint": catalog.fingerprint(),
            "capability_ids": sorted({step.capability for step in definition.steps if step.capability}),
            "context": dict(context or {}),
        }
        return {"action": action, "fingerprint": action_fingerprint(action)}

    def execute_workflow(
        self,
        task_id: str,
        catalog,
        workflow,
        *,
        handlers: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
        capability_authorizer: Any = None,
    ) -> Dict[str, Any]:
        """Run a validated workflow while requiring an explicit capability authority.

        Pure transformation steps may use injected handlers. Any step that names
        a capability is wrapped and must be delegated to ``capability_authorizer``
        so the host can route it through JEV, policy, operations, and evidence.
        """
        try:
            from .workflow import WorkflowExecutor

            state = self.store.load(task_id)
            if state.get("status") not in {"planned", "executing"}:
                return self._error("invalid_task_state", "Workflow execution requires a planned or executing task")
            try:
                definition = catalog.get_workflow(workflow) if isinstance(workflow, str) else workflow
            except KeyError:
                definition = None
            if definition is None:
                return self._error("workflow_not_found", "Workflow definition was not found")
            capability_steps = [step for step in definition.steps if step.capability is not None]
            if capability_steps and self.require_jev_decision:
                prepared = self.prepare_workflow_action(task_id, catalog, definition, context)
                if not self._jev_allows_execution(task_id, prepared["fingerprint"]):
                    return self._error("jev_decision_required", "An approved, workflow-bound JEV decision is required")
                decision = self.jev_decisions.get(task_id, {})
                selected = set(decision.get("capability_plan", {}).get("selected", []))
                if any(step.capability not in selected for step in capability_steps):
                    return self._error("jev_decision_required", "JEV decision does not select every workflow capability")
            if capability_steps and not callable(capability_authorizer):
                return self._error(
                    "workflow_capability_authority_required",
                    "Capability-backed workflow steps require an injected Runtime authorizer",
                )
            effective_handlers = dict(handlers or {})
            for step in capability_steps:
                def governed(*args, _step=step, **kwargs):
                    return capability_authorizer(
                        task_id=task_id,
                        capability_id=_step.capability,
                        step=_step,
                        context=args[0] if args else kwargs.get("context"),
                        results=kwargs.get("results", {}),
                    )
                effective_handlers[step.id] = governed
            result = WorkflowExecutor(catalog, handlers=effective_handlers).execute(
                definition,
                context=context,
            )
            payload = result.to_dict()
            self.store.append_event(
                task_id,
                {
                    "type": "workflow_executed",
                    "workflow_id": payload["workflow_id"],
                    "status": payload["status"],
                    "step_count": len(payload["steps"]),
                },
            )
            return payload
        except (ContractError, ValueError, TypeError) as exc:
            return self._error("workflow_execution_error", str(exc))

    def task_requires_execution(self, contract: Dict[str, Any]) -> bool:
        """Return a coarse legacy execution hint, never an authorization."""
        execution_keywords = [
            "execute", "run", "test", "build", "deploy", "compile",
            "lint", "format", "benchmark", "screenshot", "browser", "navigate",
            "click", "type", "scrape", "execute_code", "run_code", "run_command",
        ]
        goal = str(contract.get("goal", "")).lower()
        return any(keyword in goal for keyword in execution_keywords)

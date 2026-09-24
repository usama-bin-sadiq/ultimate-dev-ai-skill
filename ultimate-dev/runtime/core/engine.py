from __future__ import annotations

import copy
import inspect
import json
import math
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from .capabilities import CapabilityRegistry
from .context import ContextManager
from .contracts import (
    ContractError,
    action_fingerprint as compute_action_fingerprint,
    classify_code_effects,
    fingerprint,
    normalize_effects,
    safe_child_path,
    validate_capability_id,
    validate_fingerprint,
    validate_identifier,
    validate_jev_packet,
)
from .policy import Policy
from .redaction import redact_sensitive
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
        require_trusted_evidence: bool | None = None,
    ):
        if not isinstance(interactive, bool):
            raise ValueError("interactive must be boolean")
        if not isinstance(require_jev_decision, bool):
            raise ValueError("require_jev_decision must be boolean")
        if verification_evaluator is not None and not callable(verification_evaluator):
            raise TypeError("verification_evaluator must be callable or null")
        if policy is not None and not isinstance(policy, Policy):
            raise TypeError("policy must be a Policy or null")
        if capability_registry is not None and not isinstance(capability_registry, CapabilityRegistry):
            raise TypeError("capability_registry must be a CapabilityRegistry or null")
        self._store = TaskStore(project_root)
        self._store_controller = self._store.controller()
        # Runtime exposes a compatibility facade, not the raw internal state
        # mutation surface.  LifecycleController receives the raw store below
        # only inside the Runtime-owned integration boundary.
        self.store = self._store.public_view()
        self.context = ContextManager(project_root, self.store)
        self.context.memory_store = memory_store
        self._session = SessionManager(self._store.project_root, host_executor=host_executor)
        self.session = RuntimeSessionView(self._session)
        self.require_jev_decision = bool(require_jev_decision)
        self.policy = policy or (Policy.secure_defaults() if self.require_jev_decision else Policy())
        self.capability_registry = capability_registry
        self.verification_evaluator = verification_evaluator
        if require_trusted_evidence is not None and not isinstance(require_trusted_evidence, bool):
            raise ValueError("require_trusted_evidence must be boolean or null")
        self.require_trusted_evidence = (
            self.require_jev_decision
            if require_trusted_evidence is None
            else require_trusted_evidence
        )
        self.memory_store = memory_store
        if (
            isinstance(operation_lease_seconds, bool)
            or not isinstance(operation_lease_seconds, (int, float))
            or not math.isfinite(float(operation_lease_seconds))
            or operation_lease_seconds < 0
        ):
            raise ValueError("operation_lease_seconds must be a finite non-negative number")
        self.operation_lease_seconds = float(operation_lease_seconds)
        self.worker_id = f"worker-{uuid.uuid4().hex[:12]}"
        self._closed = False
        self._closing = False
        self._closed_resources: set[int] = set()
        self._resource_manager = None
        self._lifecycle_controller = None
        self.jev_decisions: Dict[str, Dict[str, Any]] = {}
        self._decision_bindings: Dict[str, str | None] = {}
        self._decision_packet_digests: Dict[str, str] = {}
        self._decision_binding_nonces: Dict[str, str] = {}
        self._prepared_actions: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._decision_actions: Dict[str, Dict[str, Any]] = {}
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
        if self._closed or self._closing:
            raise PermissionError("Runtime session is closed or closing")
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
        contract = redact_sensitive(dict(contract))
        if not isinstance(contract, dict):
            raise ContractError("redacted task contract must remain an object")
        for field in list_fields:
            if field != "allowed_actions":
                contract.setdefault(field, [])
        state = self._store.create(contract)
        self._store.append_event(state["task_id"], {"type": "task_started"})
        return self._store_controller.update_internal(state["task_id"], status="ready")

    @staticmethod
    def _action_descriptor(action: Mapping[str, Any]) -> dict[str, Any]:
        """Return a non-secret commitment for a prepared action."""
        operation = action.get("operation")
        task_id = action.get("task_id")
        if not isinstance(operation, str) or not operation or not isinstance(task_id, str) or not task_id:
            raise ContractError("bound action requires operation and task_id")
        descriptor: dict[str, Any] = {
            "operation": operation,
            "task_id": task_id,
            "action_digest": compute_action_fingerprint(action),
        }
        if "capability_id" in action:
            descriptor["capability_id"] = action["capability_id"]
        if "capability_ids" in action:
            descriptor["capability_ids"] = list(action["capability_ids"])
        if "effects" in action:
            descriptor["effects"] = list(action["effects"])
        if "language" in action:
            descriptor["language"] = action["language"]
        if "scope" in action:
            descriptor["scope_digest"] = fingerprint(action["scope"])
        if "host_options" in action:
            descriptor["host_options_digest"] = fingerprint(action["host_options"])
        return descriptor

    def _validate_bound_action(self, task_id: str, action: Mapping[str, Any]) -> None:
        operation = action.get("operation")
        if operation not in {"execute_code", "execute_workflow"}:
            raise ContractError("JEV action operation is not executable by this Runtime")
        if action.get("task_id") != task_id:
            raise ContractError("JEV action task_id does not match runtime task")
        if operation == "execute_code":
            validate_capability_id(action.get("capability_id"))
            if "effects" not in action:
                raise ContractError("executable code action requires effects")
            declared = set(normalize_effects(action["effects"], add_execute=True))
            derived = set(classify_code_effects(action.get("code"), action.get("language", "python")))
            if not derived.issubset(declared):
                raise ContractError("JEV action effects do not cover the code classifier")
        else:
            capability_ids = action.get("capability_ids")
            if not isinstance(capability_ids, list) or any(not isinstance(item, str) for item in capability_ids):
                raise ContractError("workflow action capability_ids must be an array of strings")
            for capability_id in capability_ids:
                validate_capability_id(capability_id)

    def _remember_prepared_action(self, task_id: str, action: Mapping[str, Any]) -> str:
        action_copy = copy.deepcopy(dict(action))
        self._validate_bound_action(task_id, action_copy)
        action_digest = compute_action_fingerprint(action_copy)
        self._prepared_actions.setdefault(task_id, {})[action_digest] = action_copy
        self._decision_actions[task_id] = self._action_descriptor(action_copy)
        return action_digest

    def _load_persisted_decision(self, task_id: str) -> None:
        """Restore and revalidate the latest packet on every authorization check."""
        self.jev_decisions.pop(task_id, None)
        self._decision_bindings.pop(task_id, None)
        self._decision_packet_digests.pop(task_id, None)
        self._decision_binding_nonces.pop(task_id, None)
        self._decision_actions.pop(task_id, None)
        state = self._store.load(task_id)
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
            candidate = self._store._read_json(safe_path, "JEV decision")
            candidate = validate_jev_packet(candidate, task_id, strict=True)
            if not binding or binding.get("packet_digest") != fingerprint(candidate):
                raise ContractError("JEV packet binding is missing or does not match the packet")
            if candidate.get("execution_effect") == "execute":
                bound_fingerprint = validate_fingerprint(binding.get("action_fingerprint"))
                action_descriptor = binding.get("action")
                if not isinstance(action_descriptor, dict):
                    raise ContractError("executable JEV binding is missing its action commitment")
                if binding.get("action_digest") != bound_fingerprint:
                    raise ContractError("JEV action commitment does not match its fingerprint")
                if binding.get("action_descriptor_digest") != fingerprint(action_descriptor):
                    raise ContractError("JEV action descriptor digest mismatch")
                if action_descriptor.get("task_id") != task_id or action_descriptor.get("action_digest") != bound_fingerprint:
                    raise ContractError("JEV action commitment does not match its task")
                if not isinstance(action_descriptor.get("operation"), str) or not action_descriptor["operation"]:
                    raise ContractError("JEV action commitment has no operation")
                if action_descriptor["operation"] == "execute_code" and (
                    "capability_id" not in action_descriptor or "effects" not in action_descriptor
                ):
                    raise ContractError("code action commitment is missing capability/effects")
                for capability_key in ("capability_id", "capability_ids"):
                    if capability_key not in action_descriptor:
                        continue
                    values = action_descriptor[capability_key]
                    if capability_key == "capability_id":
                        values = [values]
                    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
                        raise ContractError("JEV action commitment has invalid capabilities")
                    for value in values:
                        validate_capability_id(value)
                if "effects" in action_descriptor:
                    normalize_effects(action_descriptor["effects"], add_execute=True)
                if not isinstance(binding.get("binding_nonce"), str) or not binding["binding_nonce"]:
                    raise ContractError("executable JEV binding is missing its approval generation")
                self._decision_actions[task_id] = copy.deepcopy(action_descriptor)
        except (OSError, json.JSONDecodeError, ContractError, TypeError, ValueError):
            return
        self.jev_decisions[task_id] = candidate
        self._decision_bindings[task_id] = binding.get("action_fingerprint")
        self._decision_packet_digests[task_id] = binding.get("packet_digest")
        self._decision_binding_nonces[task_id] = binding.get("binding_nonce")

    def task_evidence_dir(self, task_id: str) -> Path:
        directory = safe_child_path(self._store.task_dir(task_id), "evidence")
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def record_jev_decision(
        self,
        task_id: str,
        decision: Dict[str, Any],
        action_fingerprint: str | None = None,
        *,
        action: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Validate, bind, and persist a host-produced JEV packet.

        An executable packet cannot be bound to an arbitrary caller-supplied
        digest.  The digest must either be recomputed from an explicit action
        object or refer to an action prepared by this Runtime.  Only a compact
        action commitment is persisted; source code and host options are not
        copied into task state.
        """
        state = self._store.load(task_id)
        packet = redact_sensitive(validate_jev_packet(decision, task_id, strict=True))
        bound_action: dict[str, Any] | None = None
        if packet.get("execution_effect") == "execute":
            if action is not None:
                if not isinstance(action, Mapping):
                    raise ContractError("JEV action must be an object")
                bound_action = copy.deepcopy(dict(action))
                computed = compute_action_fingerprint(bound_action)
                if action_fingerprint is not None and validate_fingerprint(action_fingerprint) != computed:
                    raise ContractError("JEV action fingerprint does not match the supplied action")
                action_fingerprint = computed
            elif action_fingerprint is not None:
                action_fingerprint = validate_fingerprint(action_fingerprint)
                bound_action = copy.deepcopy(self._prepared_actions.get(task_id, {}).get(action_fingerprint))
                if bound_action is None:
                    raise ContractError(
                        "executable JEV decisions require an explicit action or a Runtime-prepared action"
                    )
            else:
                raise ContractError("executable JEV decisions require an explicit action")
            if bound_action.get("task_id") != task_id:
                raise ContractError("JEV action task_id does not match runtime task")
            self._remember_prepared_action(task_id, bound_action)
        elif action_fingerprint is not None:
            action_fingerprint = validate_fingerprint(action_fingerprint)
            if action is not None:
                if not isinstance(action, Mapping):
                    raise ContractError("JEV action must be an object")
                bound_action = copy.deepcopy(dict(action))
                computed = compute_action_fingerprint(bound_action)
                if computed != action_fingerprint:
                    raise ContractError("JEV action fingerprint does not match the supplied action")
            elif action_fingerprint not in self._prepared_actions.get(task_id, {}):
                raise ContractError("JEV action fingerprint is not bound to a prepared action")
        if action_fingerprint is not None:
            action_fingerprint = validate_fingerprint(action_fingerprint)
        packet_digest = fingerprint(packet)
        for previous in state.get("decision_bindings", []):
            if previous.get("packet_digest") == packet_digest and previous.get("action_fingerprint") != action_fingerprint:
                raise ContractError("JEV packet is already bound to a different action")
        evidence_name = f"jev-{state['revision'] + 1:06d}-{uuid.uuid4().hex[:8]}.json"
        evidence_path = f"evidence/{evidence_name}"
        self._store.save(task_id, evidence_path, packet)
        self._store.append_event(
            task_id,
            {
                "type": "jev_decision",
                "execution_effect": packet.get("execution_effect"),
                "guardrail": packet.get("guardrail", {}).get("action"),
                "evidence": evidence_path,
            },
        )
        reasons = packet.get("guardrail", {}).get("reasons", [])
        binding_nonce = f"approval-{uuid.uuid4().hex}"
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
            "binding_nonce": binding_nonce,
        }
        binding = {
            "evidence": evidence_path,
            "action_fingerprint": action_fingerprint,
            "packet_digest": packet_digest,
            "binding_nonce": binding_nonce,
        }
        if bound_action is not None:
            action_descriptor = self._action_descriptor(bound_action)
            binding["action_digest"] = compute_action_fingerprint(bound_action)
            binding["action_descriptor_digest"] = fingerprint(action_descriptor)
            binding["action"] = action_descriptor
        self._store_controller.append_decision_binding(task_id, summary, binding)
        self.jev_decisions[task_id] = packet
        self._decision_bindings[task_id] = action_fingerprint
        self._decision_packet_digests[task_id] = packet_digest
        self._decision_binding_nonces[task_id] = binding_nonce
        if bound_action is not None:
            self._decision_actions[task_id] = self._action_descriptor(bound_action)
        return packet

    def _jev_allows_execution(
        self,
        task_id: str,
        action_fingerprint_value: str | None = None,
        capability_id: str | None = None,
    ) -> bool:
        self._load_persisted_decision(task_id)
        decision = self.jev_decisions.get(task_id)
        binding = self._decision_bindings.get(task_id)
        action_commitment = self._decision_actions.get(task_id)
        binding_nonce = self._decision_binding_nonces.get(task_id)
        if (
            not decision
            or not isinstance(binding, str)
            or not isinstance(action_commitment, dict)
            or not isinstance(binding_nonce, str)
            or not binding_nonce
        ):
            return False
        if not (
            decision.get("ok") is True
            and decision.get("execution_effect") == "execute"
            and decision.get("guardrail", {}).get("action") == "approve"
            and decision.get("route", {}).get("path") in {"lightweight", "flagship"}
            and decision.get("capability_plan", {}).get("selected")
            and not decision.get("errors")
            and not decision.get("capability_plan", {}).get("missing_capabilities")
        ):
            return False
        if action_fingerprint_value is not None:
            try:
                action_fingerprint_value = validate_fingerprint(action_fingerprint_value)
            except ContractError:
                return False
            if binding != action_fingerprint_value or action_commitment.get("action_digest") != binding:
                return False
        selected = set(decision.get("capability_plan", {}).get("selected", []))
        required_capabilities: set[str] = set()
        committed_capability = action_commitment.get("capability_id")
        if isinstance(committed_capability, str):
            required_capabilities.add(committed_capability)
        if isinstance(action_commitment.get("capability_ids"), list):
            required_capabilities.update(action_commitment["capability_ids"])
        if not required_capabilities.issubset(selected):
            return False
        if self.capability_registry is not None and action_commitment.get("effects"):
            try:
                action_effects = set(normalize_effects(action_commitment["effects"], add_execute=True))
                declared_effects: set[str] = set()
                for selected_id in required_capabilities:
                    selected_capability = self.capability_registry.get(selected_id)
                    if selected_capability is None:
                        return False
                    declared_effects.update(getattr(selected_capability, "effects", set()))
                if not action_effects.issubset(declared_effects):
                    return False
            except (ContractError, TypeError):
                return False
        if capability_id is not None:
            try:
                validate_capability_id(capability_id)
            except ContractError:
                return False
            if capability_id not in selected:
                return False
        return True

    def _completion_blockers(self, task_id: str) -> list[str]:
        state = self._store.load(task_id)
        blockers = []
        try:
            if not self._store.verify_audit_journal(task_id):
                blockers.append("task audit journal verification failed")
        except Exception:
            blockers.append("task audit journal is invalid")
        contract = state.get("contract", {})
        criteria = list(contract.get("acceptance_criteria", []))
        criteria.extend(contract.get("definition_of_done", []))
        passed = set(state.get("verification", {}).get("passed", []))
        missing = [criterion for criterion in criteria if criterion not in passed]
        if missing:
            blockers.append(f"unproven criteria: {', '.join(map(str, missing))}")
        if state.get("verification", {}).get("pending"):
            blockers.append("verification has pending criteria")
        if state.get("blockers"):
            blockers.append("task has unresolved blockers")
        verification = state.get("verification", {})
        if self.require_trusted_evidence and verification.get("trusted") is not True:
            blockers.append("verification requires an injected trusted verifier")
        required_evidence = contract.get("required_evidence", [])
        evidence_items = verification.get("evidence_items", [])
        if required_evidence and len(evidence_items) < len(required_evidence):
            blockers.append("required evidence items are incomplete")
        if required_evidence and not verification.get("evidence_refs"):
            blockers.append("required evidence has not been recorded")
        evidence_digests = verification.get("evidence_digests", {})
        for evidence_ref in verification.get("evidence_refs", []):
            try:
                evidence_path = safe_child_path(self._store.task_dir(task_id), evidence_ref)
                if not evidence_path.is_file():
                    blockers.append(f"evidence file is missing: {evidence_ref}")
                    continue
                evidence_payload = self._store._read_json(evidence_path, "verification evidence")
                if not isinstance(evidence_payload, dict) or not isinstance(evidence_payload.get("items"), list):
                    blockers.append(f"evidence file has no items: {evidence_ref}")
                    continue
                actual_item_digest = fingerprint(evidence_payload["items"])
                expected = evidence_digests.get(evidence_ref) if isinstance(evidence_digests, dict) else None
                if isinstance(expected, dict):
                    if fingerprint(evidence_payload) != expected.get("payload") or actual_item_digest != expected.get("items"):
                        blockers.append(f"evidence digest mismatch: {evidence_ref}")
                else:
                    # Compatibility for pre-hardening state: older records only
                    # bound the item list.  New records always use the full
                    # payload digest above.
                    if expected is None and evidence_ref == verification.get("evidence_refs", [])[-1]:
                        expected = verification.get("evidence_digest")
                    if expected is not None and actual_item_digest != expected:
                        blockers.append(f"evidence digest mismatch: {evidence_ref}")
            except (OSError, json.JSONDecodeError, ContractError, AttributeError, TypeError, ValueError):
                blockers.append(f"evidence file is invalid: {evidence_ref}")
        return blockers

    def transition(
        self,
        task_id: str,
        status: str,
        jev_decision: Dict[str, Any] | None = None,
        **changes: Any,
    ) -> Dict[str, Any]:
        if self._closed or self._closing:
            raise PermissionError("Runtime session is closed or closing")
        forbidden_changes = set(changes) - self._ALLOWED_TRANSITION_CHANGES
        if forbidden_changes:
            raise ValueError(f"transition cannot modify protected state fields: {sorted(forbidden_changes)}")
        state = self._store.load(task_id)
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
        updated = self._store_controller.update_if_status(task_id, current, {"status": status, **changes}, _internal=True)
        if updated is None:
            raise ValueError("Task state changed concurrently; retry the transition")
        return self._store.append_event(
            task_id,
            {"type": "transition", "from": current, "to": status},
        ) or updated

    def checkpoint(self, task_id: str):
        return self._store.checkpoint(task_id)

    def handoff(self, task_id: str, target: str = "next"):
        return self._store.handoff(task_id, target)

    def task_health(self, task_id: str) -> Dict[str, Any]:
        """Return a bounded operational health snapshot for one task."""
        state = self._store.load(task_id)
        operations = self._store.list_operations(task_id)
        now = time.time()
        statuses: Dict[str, int] = {}
        stale = 0
        uncertain = 0
        for operation in operations:
            status = str(operation.get("status", "unknown"))
            statuses[status] = statuses.get(status, 0) + 1
            lease = operation.get("lease_expires_at_epoch")
            if status in {"pending", "running"} and isinstance(lease, (int, float)) and lease < now:
                stale += 1
            if status in {"uncertain", "failed", "cancelled"}:
                uncertain += 1
        return {
            "task_id": task_id,
            "status": state.get("status"),
            "revision": state.get("revision"),
            "operation_count": len(operations),
            "operation_statuses": statuses,
            "stale_operations": stale,
            "uncertain_operations": uncertain,
            "healthy": stale == 0 and uncertain == 0 and not state.get("blockers"),
        }

    def health_snapshot(self, *, limit: int = 1000) -> Dict[str, Any]:
        """Return a bounded, redacted aggregate health envelope for operators."""
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 10000:
            raise ValueError("health snapshot limit must be between 1 and 10000")
        base = self._store.base
        records = []
        for task_id in sorted(path.name for path in base.iterdir() if path.is_dir() and not path.is_symlink())[:limit]:
            try:
                records.append(self.task_health(task_id))
            except (FileNotFoundError, OSError, ValueError, ContractError):
                records.append({"task_id": task_id, "healthy": False, "status": "invalid"})
        unhealthy = [item for item in records if not item.get("healthy")]
        return {
            "schema_version": "1.0",
            "task_count": len(records),
            "healthy": not unhealthy,
            "unhealthy_count": len(unhealthy),
            "tasks": records,
            "runtime_closed": self._closed,
        }

    def recover_stale_operations(self, task_id: str) -> int:
        """Mark expired leases uncertain instead of replaying unknown side effects."""
        recovered = 0
        cutoff = time.time()
        for operation in self._store.list_operations(task_id):
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
                    uncertain=True,
                )
                op["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                op["recovered_at"] = op["updated_at"]
                return op
            try:
                self._store.update_operation(
                    task_id,
                    operation["operation_id"],
                    mark,
                    expected_worker_id=operation.get("worker_id"),
                    expected_attempt=operation.get("attempt"),
                    expected_fencing_token=operation.get("fencing_token"),
                )
            except (FileNotFoundError, PermissionError, ValueError):
                # A retry/reconciliation won the race after the snapshot.
                # Never let stale recovery overwrite the newer fenced attempt.
                continue
            recovered += 1
        return recovered

    def resume(self, task_id: str):
        state = self._store.load(task_id)
        if state.get("status") in {"paused", "interrupted"}:
            return self.resume_task(task_id)
        self.recover_stale_operations(task_id)
        self._load_persisted_decision(task_id)
        return self._store.resume(task_id)

    def session_start(self, task_id: str | None = None):
        """Host session hook: resume a task when supplied, otherwise report readiness."""
        if task_id is None:
            return {"ready": True, "closed": self._closed}
        return self.resume(task_id)

    def session_end(self):
        return self.close()

    def install_session_hooks(self, task_id: str | None = None, signals=None):
        from .session_hooks import install_session_hooks

        return install_session_hooks(self, task_id=task_id, signals=signals)

    def lifecycle_controller(self, resources=None, **kwargs):
        """Build a lifecycle controller bound to this Runtime's durable store."""
        from .lifecycle import LifecycleController, ResourceCleanupManager

        if resources is None:
            if self._lifecycle_controller is None:
                manager = ResourceCleanupManager()
                for resource_id, resource in (
                    ("session", self._session),
                    ("host", self._session.host_executor),
                ):
                    if resource is not None and (
                        callable(getattr(resource, "close", None))
                        or callable(getattr(resource, "abort", None))
                        or callable(getattr(resource, "shutdown", None))
                        or callable(getattr(resource, "cleanup", None))
                    ):
                        manager.register(resource, resource_id)
                self._resource_manager = manager
                kwargs.setdefault("include_global_resources", False)
                self._lifecycle_controller = LifecycleController(
                    self._store.lifecycle_view(),
                    resources=manager,
                    **kwargs,
                )
            return self._lifecycle_controller
        kwargs.setdefault("resources", resources)
        return LifecycleController(self._store.lifecycle_view(), **kwargs)

    def pause_task(self, task_id: str, reason: str | None = None, **kwargs):
        return self.lifecycle_controller().pause(task_id, reason=reason, **kwargs)

    def interrupt_task(self, task_id: str, reason: str = "hard interruption", **kwargs):
        return self.lifecycle_controller().interrupt(task_id, reason=reason, **kwargs)

    def resume_task(self, task_id: str, reason: str | None = None, **kwargs):
        return self.lifecycle_controller().resume(task_id, reason=reason, **kwargs)

    def abandon_task(self, task_id: str, reason: str = "explicit abandonment", **kwargs):
        return self.lifecycle_controller().abandon(task_id, reason=reason, **kwargs)

    def cleanup_task_resources(self, task_id: str, **kwargs):
        return self.lifecycle_controller().cleanup(task_id, **kwargs)

    def cleanup_tasks(self, policy=None, **kwargs):
        """Plan or execute safe task retention cleanup."""
        from .retention import TaskRetentionManager

        return TaskRetentionManager(self._store.project_root, policy=policy).cleanup(**kwargs)

    def plan_task_cleanup(self, policy=None):
        from .retention import TaskRetentionManager

        return TaskRetentionManager(self._store.project_root, policy=policy).plan_cleanup()

    def archive_tasks(self, policy=None):
        from .retention import TaskRetentionManager

        return TaskRetentionManager(self._store.project_root, policy=policy).archive_tasks()

    def delete_tasks(self, confirmation_token: str, policy=None):
        from .retention import TaskRetentionManager

        return TaskRetentionManager(self._store.project_root, policy=policy).delete_tasks(confirmation_token)

    def route_user_message(self, text: str, current_task=None, **kwargs):
        """Classify a follow-up without allowing ambiguous messages to execute."""
        from .task_router import TaskRouter

        if current_task is None:
            task_id = kwargs.get("current_task_id") or kwargs.get("task_id")
            if task_id is not None:
                current_task = self._store.load(task_id)
        router = TaskRouter(project_root=self._store.project_root)
        return router.route(text, current_task=current_task, **kwargs)

    def route_and_apply_user_message(self, text: str, current_task=None, **kwargs):
        """Route a message and transactionally apply only safe state changes."""
        from .task_router import RouteDecision

        route = self.route_user_message(text, current_task=current_task, **kwargs)
        if route.decision is RouteDecision.CONTINUATION:
            task_id = route.task_id
            return {"route": route.to_dict(), "task_state": self._store.load(task_id) if task_id else None}
        if route.decision is RouteDecision.NEW_TASK and route.task_id:
            state = self.start({
                "goal": text.strip(),
                "task_id": route.task_id,
                "parent_task_id": route.parent_task_id,
            })
            return {"route": route.to_dict(), "task_state": state}
        if route.decision is RouteDecision.ABANDON and route.task_id:
            state = self.abandon_task(route.task_id, reason="explicit route abandon")
            return {"route": route.to_dict(), "task_state": state}
        return {"route": route.to_dict(), "task_state": None}

    route_question = route_user_message

    def cancel_operation(
        self,
        task_id: str,
        operation_id: str,
        *,
        expected_worker_id: str | None = None,
        expected_attempt: int | None = None,
        expected_fencing_token: str | None = None,
    ) -> Dict[str, Any]:
        """Atomically mark a nonterminal operation cancelled with optional fencing."""
        cancelled = {"value": False}

        def cancel(operation):
            if operation.get("status") in {"pending", "running"}:
                operation["status"] = "cancelled"
                operation["result"] = self._error(
                    "operation_cancelled",
                    "Operation was cancelled; external effects require reconciliation",
                    uncertain=True,
                )
                operation["retry_allowed"] = False
                operation["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                cancelled["value"] = True
            return operation

        try:
            operation = self._store.update_operation(
                task_id,
                operation_id,
                cancel,
                expected_worker_id=expected_worker_id,
                expected_attempt=expected_attempt,
                expected_fencing_token=expected_fencing_token,
            )
        except PermissionError as exc:
            return self._error("operation_fenced", str(exc), operation_id=operation_id)
        if not cancelled["value"]:
            return self._error("operation_not_cancellable", "Operation is already terminal", operation_id=operation_id)
        return self._store.append_event(task_id, {"type": "operation_cancelled", "operation_id": operation_id})

    def renew_operation(
        self,
        task_id: str,
        operation_id: str,
        *,
        expected_attempt: int | None = None,
        expected_fencing_token: str | None = None,
    ) -> Dict[str, Any]:
        """Renew this Runtime worker's lease for a long-running operation."""
        try:
            return self._store.renew_operation_lease(
                task_id,
                operation_id,
                self.worker_id,
                self.operation_lease_seconds,
                expected_attempt=expected_attempt,
                expected_fencing_token=expected_fencing_token,
            )
        except (FileNotFoundError, PermissionError, ValueError) as exc:
            return self._error("operation_lease_denied", str(exc), operation_id=operation_id)

    def reconcile_operation(
        self,
        task_id: str,
        operation_id: str,
        outcome: str = "not_executed",
        *,
        evidence: Mapping[str, Any] | None = None,
        reconciled_by: str | None = None,
        result: Mapping[str, Any] | None = None,
        expected_attempt: int | None = None,
        expected_fencing_token: str | None = None,
    ) -> Dict[str, Any]:
        """Record an explicit external-state reconciliation for uncertainty.

        ``uncertain`` is a durable safety state, not a retry hint.  A host may
        reconcile it to ``succeeded`` or to a proven not-executed/failed state;
        only the latter sets ``retry_allowed`` for a new, fenced attempt.
        """
        aliases = {
            "not_executed": "not_executed",
            "reconciled_not_executed": "not_executed",
            "no_effect": "not_executed",
            "safe_to_retry": "not_executed",
            "failed": "not_executed",
            "succeeded": "succeeded",
            "success": "succeeded",
            "cancelled": "cancelled",
            "canceled": "cancelled",
            "still_uncertain": "uncertain",
            "uncertain": "uncertain",
        }
        normalized = aliases.get(outcome)
        if normalized is None:
            raise ContractError("reconciliation outcome is not supported")
        if result is not None:
            if evidence is not None:
                raise ContractError("provide evidence or result, not both")
            evidence = result
        if not isinstance(evidence, Mapping) or not evidence:
            raise ContractError("reconciliation requires a non-empty evidence object")
        if reconciled_by is not None and (not isinstance(reconciled_by, str) or not reconciled_by.strip()):
            raise ContractError("reconciled_by must be a non-empty string")
        safe_evidence = redact_sensitive(dict(evidence))
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        def apply(operation):
            if operation.get("status") not in {"uncertain", "cancelled"}:
                raise PermissionError("only an uncertain or in-flight cancelled operation can be reconciled")
            operation["reconciled_at"] = timestamp
            operation["reconciliation"] = {
                "outcome": normalized,
                "evidence": safe_evidence,
                "reconciled_by": reconciled_by,
                "at": timestamp,
            }
            operation["updated_at"] = timestamp
            operation["lease_expires_at_epoch"] = None
            if normalized == "succeeded":
                operation["status"] = "succeeded"
                operation["result"] = self._error("reconciled_succeeded", "External state was reconciled as succeeded", reconciled=True)
                operation["retry_allowed"] = False
            elif normalized == "cancelled":
                operation["status"] = "cancelled"
                operation["result"] = self._error("reconciled_cancelled", "External operation was reconciled as cancelled", reconciled=True)
                operation["retry_allowed"] = True
            elif normalized == "not_executed":
                operation["status"] = "failed"
                operation["result"] = self._error("reconciled_not_executed", "External state was reconciled as not executed", reconciled=True)
                operation["retry_allowed"] = True
            else:
                operation["status"] = "uncertain"
                operation["result"] = self._error("reconciliation_uncertain", "External state remains uncertain", uncertain=True, reconciled=True)
                operation["retry_allowed"] = False
            return operation

        operation = self._store.update_operation(
            task_id,
            operation_id,
            apply,
            expected_attempt=expected_attempt,
            expected_fencing_token=expected_fencing_token,
        )
        self._store.append_event(
            task_id,
            {"type": "operation_reconciled", "operation_id": operation_id, "outcome": normalized},
        )
        return operation

    def observe(self, task_id: str, observations: Any) -> Dict[str, Any]:
        """Persist bounded environment observations before verification."""
        state = self._store.load(task_id)
        if state["status"] not in {"executing", "observing"}:
            raise ValueError("observations require an executing or observing task")
        if isinstance(observations, Mapping):
            normalized = [dict(observations)]
        elif isinstance(observations, list):
            normalized = [dict(item) for item in observations if isinstance(item, Mapping)]
        else:
            raise ValueError("observations must be an object or list of objects")
        retained = (state.get("observations", []) + normalized)[-100:]
        self._store_controller.update_internal(task_id, observations=retained)
        return self._store.append_event(
            task_id,
            {"type": "observation", "count": len(normalized)},
        )

    def record_execution(self, task_id: str, action: Dict[str, Any], result: Dict[str, Any]):
        if not isinstance(action, dict) or not isinstance(result, dict):
            raise ValueError("execution action and result must be objects")
        safe_action = redact_sensitive(action)
        safe_result = redact_sensitive(result)
        changed = safe_result.get("changed_files", [])
        if not isinstance(changed, list) or any(not isinstance(item, str) for item in changed):
            changed = []
        state = self._store.load(task_id)
        merged = list(dict.fromkeys(state.get("changed_files", []) + changed))
        self._store_controller.update_internal(task_id, changed_files=merged)
        return self._store.append_event(
            task_id,
            {"type": "execution", "action": safe_action, "result": safe_result},
        )

    def record_verification(
        self,
        task_id: str,
        passed: Iterable[str] = (),
        pending: Iterable[str] = (),
        evidence: Dict[str, Any] | None = None,
        evidence_items: list[dict[str, Any]] | None = None,
    ):
        state = self._store.load(task_id)
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
        if not isinstance(evidence_items, list) or len(evidence_items) > 10_000:
            raise ContractError("evidence_items must be a bounded array")
        evaluator = self.verification_evaluator or Verification().evaluate
        if not callable(evaluator):
            raise ContractError("verification evaluator must be callable")
        try:
            result = evaluator(criteria, evidence_items)
        except Exception as exc:
            raise ContractError(f"verification evaluator failed ({type(exc).__name__})") from exc
        if not isinstance(result, Mapping) or not isinstance(result.get("proven"), list) or not isinstance(result.get("unresolved"), list):
            raise ContractError("verification evaluator returned an invalid result")
        criteria_set = set(criteria)
        if any(not isinstance(item, str) or item not in criteria_set for item in result["proven"] + result["unresolved"]):
            raise ContractError("verification evaluator returned unknown criteria")
        if len(result["proven"]) != len(set(result["proven"])) or len(result["unresolved"]) != len(set(result["unresolved"])):
            raise ContractError("verification evaluator returned duplicate criteria")
        if set(result["proven"]) & set(result["unresolved"]):
            raise ContractError("verification evaluator returned contradictory criteria")
        if "trusted" in result and not isinstance(result["trusted"], bool):
            raise ContractError("verification evaluator trusted flag must be boolean")
        if "provenance" in result and (not isinstance(result["provenance"], str) or not result["provenance"].strip()):
            raise ContractError("verification evaluator provenance must be a non-empty string")
        try:
            passed_values = list(passed)
            pending_values = list(pending)
        except TypeError as exc:
            raise ContractError("passed and pending must be iterable") from exc
        if any(not isinstance(item, str) or item not in criteria_set for item in passed_values + pending_values):
            raise ContractError("passed/pending contains an unknown criterion")
        if len(passed_values) != len(set(passed_values)) or len(pending_values) != len(set(pending_values)):
            raise ContractError("passed/pending criteria must be unique")
        if passed_values and set(passed_values) != set(result["proven"]):
            raise ContractError("passed criteria must be derived from evidence")
        pending_values = list(dict.fromkeys(pending_values + result["unresolved"]))
        safe_evidence_items = redact_sensitive(evidence_items)
        verification = dict(state.get("verification", {}))
        verification["passed"] = list(result["proven"])
        verification["pending"] = pending_values
        verification["evidence_items"] = safe_evidence_items
        verification["evidence_digest"] = fingerprint(safe_evidence_items)
        # An injected evaluator is an explicit host trust boundary.  The
        # built-in helper is shape-only and therefore never satisfies strict
        # completion unless the caller explicitly injects a verifier.
        verification["trusted"] = self.verification_evaluator is not None and result.get("trusted", True) is not False
        verification["provenance"] = result.get("provenance", "injected_verifier" if self.verification_evaluator is not None else "shape_only")
        evidence_refs = list(verification.get("evidence_refs", []))
        evidence_digests = dict(verification.get("evidence_digests", {}))
        evidence_name = f"{state['revision'] + 1:06d}-{uuid.uuid4().hex[:8]}-verification.json"
        evidence_path = f"evidence/{evidence_name}"
        payload = dict(evidence) if isinstance(evidence, Mapping) else {}
        payload = redact_sensitive(payload)
        payload["items"] = safe_evidence_items
        try:
            json.dumps(payload, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ContractError(f"verification evidence must be JSON-safe: {exc}") from exc
        self._store.save(task_id, evidence_path, payload)
        evidence_refs.append(evidence_path)
        evidence_digests[evidence_path] = {
            "payload": fingerprint(payload),
            "items": fingerprint(safe_evidence_items),
        }
        verification["evidence_refs"] = list(dict.fromkeys(evidence_refs))
        verification["evidence_digests"] = evidence_digests
        self._store_controller.update_internal(task_id, verification=verification)
        return self._store.append_event(
            task_id,
            {"type": "verification", "passed": verification["passed"], "pending": verification["pending"]},
        )

    @staticmethod
    def _contract_allows_action(contract: Mapping[str, Any], operation: str, capability_id: str) -> tuple[bool, str | None]:
        if not isinstance(contract, Mapping):
            return False, "contract_invalid"
        forbidden_value = contract.get("forbidden_actions", [])
        allowed_value = contract.get("allowed_actions", None)
        if not isinstance(forbidden_value, list) or any(not isinstance(item, str) for item in forbidden_value):
            return False, "contract_forbidden_action_invalid"
        if allowed_value is not None and (
            not isinstance(allowed_value, list) or any(not isinstance(item, str) for item in allowed_value)
        ):
            return False, "contract_action_not_allowed"
        forbidden = set(forbidden_value)
        if operation in forbidden or capability_id in forbidden:
            return False, "contract_forbidden_action"
        # An omitted allowlist is retained as the legacy open contract.  Once
        # the field is present, matching is exact: there is deliberately no
        # ``execute`` wildcard, and an explicit empty list denies all actions.
        if allowed_value is not None:
            allowed = set(allowed_value)
            if operation not in allowed and capability_id not in allowed:
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
        """Build a canonical, conservatively classified action for JEV."""
        validate_capability_id(capability_id)
        validate_identifier(task_id, "task_id")
        if scope is not None and not isinstance(scope, Mapping):
            raise ContractError("scope must be an object")
        if host_options is not None and not isinstance(host_options, Mapping):
            raise ContractError("host_options must be an object")
        scope = {} if scope is None else scope
        host_options = {} if host_options is None else host_options
        if not isinstance(task_description, str):
            raise ContractError("task_description must be a string")
        caller_effects = normalize_effects(effects, add_execute=True)
        derived_effects = classify_code_effects(code, language)
        effect_values = set(caller_effects) | set(derived_effects)
        if self.capability_registry is not None:
            capability = self.capability_registry.get(capability_id)
            if capability is not None:
                effect_values.update(getattr(capability, "effects", set()))
        action = {
            "operation": "execute_code",
            "task_id": task_id,
            "code": code,
            "language": language,
            "capability_id": capability_id,
            "effects": sorted(effect_values),
            "scope": copy.deepcopy(dict(scope)),
            "task_description": task_description,
            "host_options": copy.deepcopy(dict(host_options)),
        }
        action_digest = compute_action_fingerprint(action)
        self._remember_prepared_action(task_id, action)
        return {"action": action, "fingerprint": action_digest}

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
        _, existing = self._store.claim_operation(task_id, operation_id, operation)
        if existing is not None:
            if existing.get("_public_fixture") is True:
                return self._error("operation_conflict", "operation identity is not Runtime-authorized", operation_id=operation_id)
            if existing.get("action_fingerprint") != fingerprint:
                return self._error("operation_conflict", "operation_id is already bound to a different action", operation_id=existing.get("operation_id", operation_id))
            return {
                **existing.get("result", result),
                "operation_id": existing.get("operation_id", operation_id),
                "operation_status": existing.get("status", "failed"),
                "replayed": True,
            }
        self._store_controller.add_operation_id(task_id, operation_id)
        self._store.append_event(task_id, {"type": "operation_failed", "operation_id": operation_id, "code": code})
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
        if self._closed:
            return self._error("runtime_closed", "Runtime session is closed")
        if require_jev_decision is False and self.require_jev_decision:
            return self._error("jev_decision_required", "Per-call execution cannot disable the Runtime JEV gate")
        required = self.require_jev_decision or bool(require_jev_decision)
        capability_id = kwargs.pop("capability_id", "shell.execute")
        approval_confirmed = kwargs.pop("approval_confirmed", False)
        if not isinstance(approval_confirmed, bool):
            return self._error("invalid_action", "approval_confirmed must be boolean")
        operation_id_input = kwargs.pop("operation_id", None)
        idempotency_key_input = kwargs.pop("idempotency_key", None)
        retry = kwargs.pop("retry", False)
        reconciliation = kwargs.pop("reconciliation", False)
        if not isinstance(retry, bool) or not isinstance(reconciliation, bool):
            return self._error("invalid_action", "retry and reconciliation must be boolean")
        task_description = kwargs.pop("task_description", "")
        if not isinstance(task_description, str):
            return self._error("invalid_action", "task_description must be a string")
        try:
            validate_capability_id(capability_id)
        except ContractError as exc:
            return self._error("invalid_action", str(exc))
        effects_value = kwargs.pop("effects", ("execute",))
        try:
            caller_effects = normalize_effects(effects_value, add_execute=True)
            derived_effects = classify_code_effects(code, language)
            effects = set(caller_effects) | set(derived_effects)
        except ContractError as exc:
            return self._error("invalid_action", str(exc))
        # The code-execution operation itself is never allowed to under-declare
        # its effect.  The classifier above is authoritative for code-derived
        # side effects; capability declarations are unioned below as a second
        # trusted host signal.
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
            fingerprint = compute_action_fingerprint(action)
        except ContractError as exc:
            return self._error("invalid_action", str(exc))
        if jev_decision is not None:
            return self._error(
                "jev_decision_must_be_bound",
                "Record a JEV decision with prepare_execution_action() before execution",
            )
        try:
            state = self._store.load(task_id)
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
        if (
            not isinstance(idempotency_key, str)
            or not idempotency_key
            or len(idempotency_key) > 256
            or any(ord(char) < 0x20 for char in idempotency_key)
        ):
            return self._error("invalid_action", "idempotency_key must be a bounded non-empty string")
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
            try:
                declared_effects = set(normalize_effects(getattr(capability, "effects", set()), add_execute=True))
            except ContractError as exc:
                return self._error("capability_effect_invalid", str(exc))
            effects.update(declared_effects)
            if effects and not effects.issubset(declared_effects):
                return self._error(
                    "capability_effect_mismatch",
                    "Requested or derived effects exceed the capability declaration",
                    capability_id=capability_id,
                    requested_effects=sorted(effects),
                    declared_effects=sorted(declared_effects),
                )
            action["effects"] = sorted(effects)
            fingerprint = compute_action_fingerprint(action)
            self._remember_prepared_action(task_id, action)
        if task_id not in self.jev_decisions:
            self._load_persisted_decision(task_id)
        decision = self.jev_decisions.get(task_id, {})
        confirmed = approval_confirmed or (
            required and self._jev_allows_execution(task_id, fingerprint, capability_id)
        )
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
                try:
                    refreshed = self._store.load(task_id)
                except (OSError, ValueError):
                    refreshed = {}
                if refreshed.get("status") != "executing":
                    return self._error("execution_state_error", str(exc))

        decision_binding_nonce = self._decision_binding_nonces.get(task_id) if required else None
        operation_candidate = {
            "operation_id": operation_id,
            "task_id": task_id,
            "attempt": 1,
            "idempotency_key": idempotency_key,
            "action_fingerprint": fingerprint,
            "capability_id": capability_id,
            "status": "running",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "worker_id": self.worker_id,
            "fencing_token": f"fence-{uuid.uuid4().hex}",
            "lease_expires_at_epoch": time.time() + self.operation_lease_seconds,
            "retry_allowed": False,
            "decision_binding_nonce": decision_binding_nonce,
        }
        try:
            _, operation, disposition = self._store.reserve_operation(
                task_id,
                operation_id,
                operation_candidate,
                retry=retry,
                reconciliation=reconciliation,
            )
        except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
            return self._error("operation_state_invalid", f"Unable to reserve operation state: {exc}", operation_id=operation_id)
        if disposition == "replayed":
            return {
                **operation.get("result", {}),
                "operation_id": operation.get("operation_id", operation_id),
                "operation_status": operation.get("status", "succeeded"),
                "replayed": True,
            }
        if disposition in {"operation_conflict", "idempotency_conflict"}:
            return self._error(
                "operation_conflict",
                "operation identity or idempotency key is already bound to a different action",
                operation_id=operation.get("operation_id", operation_id),
            )
        if disposition == "in_progress":
            return self._error("operation_in_progress", "Operation is already running", operation_id=operation.get("operation_id", operation_id))
        if disposition == "reconciliation_required":
            return self._error(
                "operation_reconciliation_required",
                "Uncertain operation requires an explicit reconciliation result before retry",
                operation_id=operation.get("operation_id", operation_id),
            )
        if disposition == "not_retryable":
            return self._error(
                "operation_not_retryable",
                "Failed operation requires an explicit retry",
                operation_id=operation.get("operation_id", operation_id),
            )
        if disposition == "new_approval_required":
            return self._error(
                "operation_new_approval_required",
                "A reconciled operation requires a newly recorded scoped approval before retry",
                operation_id=operation.get("operation_id", operation_id),
            )
        if disposition != "reserved" or not isinstance(operation, dict):
            return self._error("operation_state_invalid", "Runtime could not reserve operation", operation_id=operation_id)
        attempt = int(operation.get("attempt", 1))
        fencing_token = operation.get("fencing_token")
        self._store.append_event(task_id, {"type": "operation_started", "operation_id": operation_id, "action_fingerprint": fingerprint, "attempt": attempt})

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
                    result["uncertain"] = True
            except Exception as exc:  # host adapters are an external boundary
                # Once dispatch begins, an exception is not proof that the
                # external side effect did not happen.  Persist uncertainty.
                result = self._error(
                    "executor_error",
                    f"Host executor failed ({type(exc).__name__})",
                    uncertain=True,
                    dispatch_phase="after_dispatch",
                )

        try:
            json.dumps(result, allow_nan=False)
        except (TypeError, ValueError):
            result = self._error(
                "malformed_tool_result",
                "Host executor returned non-JSON-safe data",
                uncertain=True,
            )
        if not isinstance(result, dict):
            result = self._error("malformed_tool_result", "Host executor returned an invalid result", uncertain=True)
        if "success" in result and not isinstance(result.get("success"), bool):
            result = self._error("malformed_tool_result", "Host executor success flag must be boolean", uncertain=True)
        for uncertainty_key in ("uncertain", "indeterminate"):
            if uncertainty_key in result and not isinstance(result.get(uncertainty_key), bool):
                result = self._error("malformed_tool_result", f"Host executor {uncertainty_key} flag must be boolean", uncertain=True)
        # A contradictory success/uncertain response is unsafe to interpret as
        # success.  Preserve the contradiction as evidence, but normalize the
        # durable operation to the conservative state.
        contradictory = result.get("success") is True and (
            result.get("uncertain") is True or result.get("indeterminate") is True
        )
        if contradictory:
            result = dict(result)
            result["success"] = False
            result["uncertain"] = True
            result["code"] = "executor_uncertain"
            result["contradictory_success"] = True
        safe_result = redact_sensitive(result)

        def finish(previous):
            if previous.get("status") == "cancelled":
                return previous
            if (
                previous.get("worker_id") != self.worker_id
                or previous.get("attempt") != attempt
                or previous.get("fencing_token") != fencing_token
            ):
                raise PermissionError("operation result is fenced by a newer attempt")
            if result.get("uncertain") is True or result.get("indeterminate") is True:
                previous["status"] = "uncertain"
            elif result.get("success") is True:
                previous["status"] = "succeeded"
            else:
                previous["status"] = "failed"
            previous["result"] = safe_result
            previous["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            previous["lease_expires_at_epoch"] = None
            previous["retry_allowed"] = False
            return previous

        try:
            final_operation = self._store.update_operation(
                task_id,
                operation_id,
                finish,
                expected_worker_id=self.worker_id,
                expected_attempt=attempt,
                expected_fencing_token=fencing_token,
            )
        except PermissionError as exc:
            return self._error("operation_fenced", str(exc), operation_id=operation_id, attempt=attempt)
        operation_status = final_operation.get("status")
        if operation_status == "cancelled":
            result = self._error(
                "operation_cancelled",
                "Operation was cancelled while the host action was in flight",
                operation_id=operation_id,
            )
        self._store.append_event(task_id, {"type": "operation_finished", "operation_id": operation_id, "status": operation_status, "attempt": attempt})
        if operation_status != "cancelled":
            self.record_execution(task_id, {"operation_id": operation_id, "capability_id": capability_id, "action_fingerprint": fingerprint}, result)
        return {**result, "operation_id": operation_id, "operation_status": operation_status, "attempt": attempt}

    def prepare_workflow_action(self, task_id: str, catalog, workflow, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Build the action fingerprint for a capability-backed workflow."""
        definition = catalog.get_workflow(workflow) if isinstance(workflow, str) else workflow
        if definition is None:
            raise ContractError("workflow definition was not found")
        validate_identifier(task_id, "task_id")
        action = {
            "operation": "execute_workflow",
            "task_id": task_id,
            "workflow_id": definition.id,
            "catalog_fingerprint": catalog.fingerprint(),
            "capability_ids": sorted({step.capability for step in definition.steps if step.capability}),
            "context": dict(context or {}),
        }
        action_digest = compute_action_fingerprint(action)
        self._remember_prepared_action(task_id, action)
        return {"action": action, "fingerprint": action_digest}

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

            state = self._store.load(task_id)
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
            self._store.append_event(
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

    def close(self) -> Dict[str, Any]:
        """Close host resources with retryable, fail-closed state transitions."""
        if self._closed:
            return {"success": True, "closed": True, "repeated": True}
        if self._closing:
            return {"success": False, "closed": False, "retryable": True, "errors": ["close_in_progress"]}
        self._closing = True
        errors: list[str] = []
        owners = [self._session, self._session.host_executor]
        seen: set[int] = set()
        for owner in owners:
            if owner is None or id(owner) in seen:
                continue
            seen.add(id(owner))
            if id(owner) in self._closed_resources:
                continue
            closed = False
            had_callable = False
            for method_name in ("close", "shutdown", "cleanup"):
                method = getattr(owner, method_name, None)
                if not callable(method):
                    continue
                had_callable = True
                try:
                    outcome = method()
                    if inspect.isawaitable(outcome):
                        from .lifecycle import _await_cleanup_result

                        _await_cleanup_result(outcome, 30.0)
                    self._closed_resources.add(id(owner))
                    closed = True
                except Exception as exc:
                    errors.append(f"{method_name}:{type(exc).__name__}")
                break
            if not had_callable:
                # A resource without a cleanup primitive is not an error; the
                # Runtime still records that no callable ownership exists.
                self._closed_resources.add(id(owner))
        self._closing = False
        if errors:
            return {
                "success": False,
                "closed": False,
                "retryable": True,
                "errors": errors,
            }
        self._closed = True
        return {"success": True, "closed": True, "repeated": False, "errors": []}

    shutdown = close

    def task_requires_execution(self, contract: Dict[str, Any]) -> bool:
        """Return a coarse legacy execution hint, never an authorization."""
        execution_keywords = [
            "execute", "run", "test", "build", "deploy", "compile",
            "lint", "format", "benchmark", "screenshot", "browser", "navigate",
            "click", "type", "scrape", "execute_code", "run_code", "run_command",
        ]
        goal = str(contract.get("goal", "")).lower()
        return any(keyword in goal for keyword in execution_keywords)

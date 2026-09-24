import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from runtime.core import ContextManager, Policy, Runtime
from runtime.core.memory import MemoryStore
from runtime.core.registry import CapabilityDescriptor, WorkflowCatalog, WorkflowDescriptor, WorkflowStepDescriptor
from runtime.core.capabilities import Capability, CapabilityRegistry
from runtime.core.contracts import ContractError, action_fingerprint


def packet(task_id, *, selected=("shell.execute",), effect="execute", action="approve", route="lightweight"):
    return {
        "schema_version": "1.0",
        "task_id": task_id,
        "orchestration_state_id": "state-1",
        "capability_catalog_version": "host-1",
        "policy_version": "policy-1",
        "ok": True,
        "execution_effect": effect,
        "errors": [],
        "heads": {
            "noul": {
                "urgent": False,
                "destructive": False,
                "policy_sensitive": False,
                "human_approval_required": False,
                "evidence_required": False,
            },
            "choice": {
                "pattern": "inline",
                "task_size": "moderate",
                "preferred_path": route,
                "primary_domain": "testing",
            },
            "score": {
                "risk": 0.1,
                "complexity": 0.1,
                "urgency": 0.0,
                "confidence": 0.9,
                "context_pressure": 0.1,
            },
        },
        "aggregate": {
            "risk": 0.1,
            "complexity": 0.1,
            "urgency": 0.0,
            "confidence": 0.9,
            "context_pressure": 0.1,
            "load": 0.1,
        },
        "guardrail": {"action": action, "reasons": []},
        "route": {
            "pattern": "inline",
            "path": route,
            "task_size": "moderate",
            "primary_domain": "testing",
            "reasons": [],
            "authority": "recommendation",
        },
        "capability_plan": {
            "selected": list(selected),
            "omitted": [],
            "missing_capabilities": [],
        },
        "context_plan": {
            "profile": "minimal",
            "reasons": [],
            "authority": "recommendation",
        },
        "trace": {"rules_applied": [], "deterministic": True},
    }


class RuntimeHardeningTests(unittest.TestCase):
    def test_operation_cancellation_is_durable(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False)
            state = runtime.start({"goal": "cancel"})
            tid = state["task_id"]
            runtime.store.save_operation(tid, "op-cancel", {
                "operation_id": "op-cancel",
                "task_id": tid,
                "attempt": 1,
                "idempotency_key": "key",
                "action_fingerprint": "0" * 64,
                "capability_id": "shell.execute",
                "status": "running",
                "created_at": "now",
            })
            runtime.cancel_operation(tid, "op-cancel")
            self.assertEqual(runtime.store.load_operation(tid, "op-cancel")["status"], "cancelled")

    def test_task_contract_rejects_invalid_field_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False)
            with self.assertRaises(ValueError):
                runtime.start({"goal": "bad", "acceptance_criteria": "not-a-list"})

    def test_default_gate_cannot_be_disabled_per_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp)
            state = runtime.start({"goal": "execute"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            result = runtime.execute_code(tid, "print('x')", require_jev_decision=False)
            self.assertEqual(result["code"], "jev_decision_required")

    def test_malformed_or_mismatched_packet_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False)
            state = runtime.start({"goal": "execute"})
            tid = state["task_id"]
            bad = packet("other-task")
            with self.assertRaises(ContractError):
                runtime.record_jev_decision(tid, bad)
            malformed = packet(tid)
            malformed["guardrail"]["action"] = "unknown"
            with self.assertRaises(ContractError):
                runtime.record_jev_decision(tid, malformed)

    def test_decision_rehydrates_and_operation_is_idempotent(self):
        calls = []

        def executor(**kwargs):
            calls.append(kwargs)
            return {"success": True, "stdout": "ok", "stderr": "", "exit_code": 0}

        with tempfile.TemporaryDirectory() as tmp:
            first = Runtime(tmp, host_executor=executor)
            state = first.start({"goal": "execute"})
            tid = state["task_id"]
            first.transition(tid, "planning")
            first.transition(tid, "planned")
            decision = packet(tid)
            prepared = first.prepare_execution_action(tid, "print('x')")
            first.record_jev_decision(tid, decision, action_fingerprint=prepared["fingerprint"])
            result = first.execute_code(tid, "print('x')", approval_confirmed=True)
            self.assertTrue(result["success"])
            operation_id = result["operation_id"]

            second = Runtime(tmp, host_executor=executor)
            replay = second.execute_code(tid, "print('x')", operation_id=operation_id)
            self.assertTrue(replay["replayed"])
            self.assertEqual(len(calls), 1)

    def test_idempotency_key_replays_across_operation_ids(self):
        calls = []

        def executor(**kwargs):
            calls.append(kwargs)
            return {"success": True, "stdout": "", "stderr": "", "exit_code": 0}

        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False, host_executor=executor)
            state = runtime.start({"goal": "idempotent"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            first = runtime.execute_code(tid, "print('x')", operation_id="op-one", idempotency_key="key-one")
            second = runtime.execute_code(tid, "print('x')", operation_id="op-two", idempotency_key="key-one")
            self.assertTrue(first["success"])
            self.assertTrue(second["replayed"])
            self.assertEqual(len(calls), 1)

    def test_operation_id_cannot_be_rebound_to_another_action(self):
        calls = []

        def executor(**kwargs):
            calls.append(kwargs)
            return {"success": True, "stdout": "", "stderr": "", "exit_code": 0}

        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False, host_executor=executor)
            state = runtime.start({"goal": "execute"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            first = runtime.execute_code(tid, "print('a')", operation_id="op-fixed")
            self.assertTrue(first["success"])
            second = runtime.execute_code(tid, "print('b')", operation_id="op-fixed")
            self.assertEqual(second["code"], "operation_conflict")
            self.assertEqual(len(calls), 1)

    def test_action_binding_and_selected_capability_are_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=True)
            state = runtime.start({"goal": "execute"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            prepared = runtime.prepare_execution_action(tid, "print('x')")
            runtime.record_jev_decision(
                tid,
                packet(tid, selected=("filesystem.read",)),
                action_fingerprint=prepared["fingerprint"],
            )
            result = runtime.execute_code(tid, "print('x')")
            self.assertEqual(result["code"], "jev_decision_required")

    def test_jev_nested_schema_and_empty_selection_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=True)
            state = runtime.start({"goal": "execute"})
            tid = state["task_id"]
            malformed = packet(tid)
            malformed["aggregate"]["risk"] = 2
            with self.assertRaises(ContractError):
                runtime.record_jev_decision(tid, malformed, action_fingerprint="0" * 64)
            unhashable = packet(tid)
            unhashable["capability_plan"]["selected"] = [{}]
            with self.assertRaises(ContractError):
                runtime.record_jev_decision(tid, unhashable, action_fingerprint="0" * 64)
            empty = packet(tid, selected=())
            prepared = runtime.prepare_execution_action(tid, "print('x')")
            runtime.record_jev_decision(tid, empty, action_fingerprint=prepared["fingerprint"])
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            self.assertEqual(runtime.execute_code(tid, "print('x')", approval_confirmed=True)["code"], "jev_decision_required")

    def test_persisted_decision_is_revalidated_and_nested_copy_is_immutable(self):
        calls = []

        def executor(**kwargs):
            calls.append(kwargs)
            return {"success": True, "stdout": "", "stderr": "", "exit_code": 0}

        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, host_executor=executor)
            state = runtime.start({"goal": "execute"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            prepared = runtime.prepare_execution_action(tid, "print('x')")
            decision = packet(tid)
            runtime.record_jev_decision(tid, decision, action_fingerprint=prepared["fingerprint"])
            decision["guardrail"]["action"] = "deny"
            result = runtime.execute_code(tid, "print('x')", approval_confirmed=True)
            self.assertTrue(result["success"])
            self.assertEqual(len(calls), 1)
            evidence = sorted(runtime.task_evidence_dir(tid).glob("jev-*.json"))[-1]
            payload = json.loads(evidence.read_text())
            payload["guardrail"]["action"] = "deny"
            evidence.write_text(json.dumps(payload))
            denied = runtime.execute_code(tid, "print('x')", approval_confirmed=True, operation_id="op-after-tamper")
            self.assertEqual(denied["code"], "jev_decision_required")
            self.assertEqual(len(calls), 1)

    def test_contract_policy_registry_and_session_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(
                tmp,
                require_jev_decision=False,
                policy=Policy(denied_capabilities={"shell.execute"}),
            )
            state = runtime.start({"goal": "execute", "forbidden_actions": ["execute_code"]})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            denied = runtime.execute_code(tid, "print('x')")
            self.assertEqual(denied["code"], "contract_forbidden_action")
            self.assertEqual(runtime.session.execute_code("print('x')")["code"], "runtime_authorization_required")

        with tempfile.TemporaryDirectory() as tmp:
            registry = CapabilityRegistry()
            registry.register(Capability("filesystem.read", "read", lambda **_: {"success": True}, effects={"read"}))
            runtime = Runtime(tmp, require_jev_decision=False, capability_registry=registry)
            state = runtime.start({"goal": "read"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            mismatch = runtime.execute_code(tid, "read", capability_id="filesystem.read", effects={"write"})
            self.assertEqual(mismatch["code"], "capability_effect_mismatch")

    def test_packet_cannot_be_rebound_and_host_options_change_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=True)
            state = runtime.start({"goal": "execute"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            first = runtime.prepare_execution_action(tid, "print('a')", host_options={"env": "dev"})
            decision = packet(tid)
            runtime.record_jev_decision(tid, decision, action_fingerprint=first["fingerprint"])
            second = runtime.prepare_execution_action(tid, "print('a')", host_options={"env": "prod"})
            self.assertNotEqual(first["fingerprint"], second["fingerprint"])
            with self.assertRaises(ContractError):
                runtime.record_jev_decision(tid, decision, action_fingerprint=second["fingerprint"])
            self.assertEqual(runtime.execute_code(tid, "print('a')", env="prod")["code"], "jev_decision_required")

    def test_concurrent_events_do_not_overwrite_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False)
            state = runtime.start({"goal": "record"})
            tid = state["task_id"]
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(lambda value: runtime.store.append_event(tid, {"type": "probe", "value": value}), range(20)))
            final = runtime.store.load(tid)
            self.assertEqual(len([event for event in final["events"] if event["type"] == "probe"]), 20)

    def test_observations_require_execution_state_and_are_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False)
            state = runtime.start({"goal": "observe"})
            tid = state["task_id"]
            with self.assertRaises(ValueError):
                runtime.observe(tid, {"readiness": "unknown"})
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            runtime.transition(tid, "executing")
            result = runtime.observe(tid, [{"readiness": "ready"}])
            self.assertEqual(result["observations"][-1]["readiness"], "ready")

    def test_symlinked_task_storage_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            outside = Path(tmp) / "outside-tasks"
            outside.mkdir()
            base = root / ".memory" / "ultimate-dev"
            base.mkdir(parents=True)
            try:
                (base / "tasks").symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("symlinks are unavailable")
            with self.assertRaises(ContractError):
                Runtime(root, require_jev_decision=False)

    def test_expired_operation_lease_is_recovered_as_uncertain(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False)
            state = runtime.start({"goal": "recover"})
            tid = state["task_id"]
            runtime.store.save_operation(tid, "op-stale", {
                "operation_id": "op-stale",
                "task_id": tid,
                "attempt": 1,
                "idempotency_key": "stale",
                "action_fingerprint": "0" * 64,
                "capability_id": "shell.execute",
                "status": "running",
                "lease_expires_at_epoch": 0,
            })
            self.assertEqual(runtime.recover_stale_operations(tid), 1)
            self.assertEqual(runtime.store.load_operation(tid, "op-stale")["status"], "uncertain")

    def test_cancellation_during_host_call_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime_holder = {}

            def executor(**kwargs):
                tid = kwargs["task_id"]
                runtime_holder["runtime"].cancel_operation(tid, kwargs["operation_id"])
                return {"success": True, "stdout": "late", "stderr": "", "exit_code": 0}

            runtime = Runtime(tmp, require_jev_decision=False, host_executor=executor)
            runtime_holder["runtime"] = runtime
            state = runtime.start({"goal": "cancel in flight"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            result = runtime.execute_code(tid, "print('x')", operation_id="op-inflight")
            self.assertEqual(result["code"], "operation_cancelled")
            self.assertEqual(runtime.store.load_operation(tid, "op-inflight")["status"], "cancelled")

    def test_context_rejects_sensitive_project_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text("SECRET=1")
            (root / "credentials").write_text("SECRET=2")
            (root / "safe.txt").write_text("ok")
            runtime = Runtime(root, require_jev_decision=False)
            state = runtime.start({"goal": "read"})
            tid = state["task_id"]
            context = ContextManager(root, runtime.store).build(
                tid,
                files=[".env", "credentials", "safe.txt"],
                budget=2000,
            )
            self.assertNotIn(".env", context["relevant_files"])
            self.assertNotIn("credentials", context["relevant_files"])
            self.assertIn("safe.txt", context["relevant_files"])

    def test_capability_backed_workflow_requires_runtime_authorizer(self):
        with tempfile.TemporaryDirectory() as tmp:
            capability = CapabilityDescriptor(
                id="tool.read",
                description="Read a value",
                effects=("read",),
            )
            workflow = WorkflowDescriptor(
                id="read-flow",
                description="Read through an authority",
                steps=(WorkflowStepDescriptor(id="read", capability="tool.read"),),
            )
            catalog = WorkflowCatalog(capabilities=(capability,), workflows=(workflow,))
            runtime = Runtime(tmp, require_jev_decision=False)
            state = runtime.start({"goal": "workflow"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            denied = runtime.execute_workflow(tid, catalog, "read-flow")
            self.assertEqual(denied["code"], "workflow_capability_authority_required")
            calls = []

            def authorizer(**kwargs):
                calls.append(kwargs)
                return {"value": 7}

            result = runtime.execute_workflow(
                tid,
                catalog,
                "read-flow",
                capability_authorizer=authorizer,
            )
            self.assertEqual(result["status"], "succeeded")
            self.assertEqual(calls[0]["capability_id"], "tool.read")

    def test_capability_workflow_is_jev_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            capability = CapabilityDescriptor(id="tool.read", description="Read", effects=("read",))
            workflow = WorkflowDescriptor(
                id="bound-flow",
                description="Bound workflow",
                steps=(WorkflowStepDescriptor(id="read", capability="tool.read"),),
            )
            catalog = WorkflowCatalog(capabilities=(capability,), workflows=(workflow,))
            runtime = Runtime(tmp)
            state = runtime.start({"goal": "workflow"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            prepared = runtime.prepare_workflow_action(tid, catalog, "bound-flow")
            denied = runtime.execute_workflow(tid, catalog, "bound-flow", capability_authorizer=lambda **_: {"ok": True})
            self.assertEqual(denied["code"], "jev_decision_required")
            runtime.record_jev_decision(tid, packet(tid, selected=("tool.read",)), action_fingerprint=prepared["fingerprint"])
            runtime.transition(tid, "executing")
            result = runtime.execute_workflow(tid, catalog, "bound-flow", capability_authorizer=lambda **_: {"ok": True})
            self.assertEqual(result["status"], "succeeded")

    def test_context_projects_scoped_provenance_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            memory = MemoryStore(root)
            memory.add(
                "decision",
                "use the verified parser",
                source="test-suite",
                scope="project/alpha",
                key="parser",
            )
            runtime = Runtime(root, require_jev_decision=False, memory_store=memory)
            state = runtime.start({"goal": "context"})
            tid = state["task_id"]
            context = runtime.context.build(
                tid,
                memory_scope="project/alpha",
                budget=2000,
            )
            self.assertEqual(context["memory"]["items"][0]["content"], "use the verified parser")

    def test_context_caps_untrusted_history_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False)
            state = runtime.start({"goal": "read"})
            tid = state["task_id"]
            context = ContextManager(tmp, runtime.store).build(
                tid,
                history="x" * 10000,
                budget=2000,
            )
            self.assertLessEqual(len(context["history"]), 8000)
            self.assertIn("history", context["truncated_files"])

    def test_completion_rejects_forged_or_protected_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False)
            state = runtime.start({
                "goal": "finish",
                "acceptance_criteria": ["tests pass"],
                "required_evidence": ["test output"],
            })
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            with self.assertRaises(ValueError):
                runtime.transition(tid, "executing", verification={"passed": ["tests pass"]})
            with self.assertRaises(PermissionError):
                runtime.store.update(tid, status="completed")
            with self.assertRaises(PermissionError):
                runtime.store.save(tid, "state.json", {"status": "completed"})
            with self.assertRaises(PermissionError):
                runtime.store.save(tid, "./state.json", {"status": "completed"})
            runtime.transition(tid, "executing")
            runtime.transition(tid, "observing")
            runtime.transition(tid, "verifying")
            with self.assertRaises(ContractError):
                runtime.record_verification(
                    tid,
                    evidence={"items": [{"criterion": "tests pass", "passed": True}]},
                )
            with self.assertRaises(PermissionError):
                runtime.transition(tid, "completed")

    def test_completion_requires_criteria_and_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False)
            state = runtime.start({
                "goal": "finish",
                "acceptance_criteria": ["tests pass"],
                "required_evidence": ["test output"],
            })
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            runtime.transition(tid, "executing")
            runtime.transition(tid, "observing")
            runtime.transition(tid, "verifying")
            with self.assertRaises(PermissionError):
                runtime.transition(tid, "completed")
            runtime.record_verification(
                tid,
                passed=["tests pass"],
                evidence={
                    "command": "pytest",
                    "exit_code": 0,
                    "items": [{"criterion": "tests pass", "passed": True, "command": "pytest"}],
                },
            )
            final = runtime.transition(tid, "completed")
            self.assertEqual(final["status"], "completed")

    def test_task_id_and_context_paths_are_contained(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = Runtime(root, require_jev_decision=False)
            with self.assertRaises(ContractError):
                runtime.start({"goal": "bad", "task_id": "../escape"})
            state = runtime.start({"goal": "read"})
            tid = state["task_id"]
            (root.parent / "outside.txt").write_text("secret")
            with self.assertRaises(ContractError):
                ContextManager(root, runtime.store).build(tid, files=["../outside.txt"])

    def test_destructive_effect_requires_policy_confirmation(self):
        calls = []

        def executor(**kwargs):
            calls.append(kwargs)
            return {"success": True, "stdout": "", "stderr": "", "exit_code": 0}

        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False, host_executor=executor)
            state = runtime.start({"goal": "delete"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            result = runtime.execute_code(tid, "rm", effects={"delete"})
            self.assertEqual(result["code"], "policy_denied")
            self.assertEqual(calls, [])

    def test_executor_exception_is_structured_and_persisted(self):
        def executor(**kwargs):
            raise RuntimeError("provider unavailable")

        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False, host_executor=executor)
            state = runtime.start({"goal": "execute"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            result = runtime.execute_code(tid, "print('x')")
            self.assertEqual(result["code"], "executor_error")
            operation_id = result["operation_id"]
            self.assertEqual(runtime.store.load_operation(tid, operation_id)["status"], "failed")

    def test_optional_capability_registry_blocks_unavailable_capability(self):
        registry = CapabilityRegistry()
        registry.register(Capability("shell.execute", "shell", lambda **_: None, available=False))
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False, capability_registry=registry, host_executor=lambda **_: {"success": True})
            state = runtime.start({"goal": "execute"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            result = runtime.execute_code(tid, "print('x')")
            self.assertEqual(result["code"], "capability_unavailable")
            self.assertEqual(runtime.store.load_operation(tid, result["operation_id"])["status"], "failed")


if __name__ == "__main__":
    unittest.main()

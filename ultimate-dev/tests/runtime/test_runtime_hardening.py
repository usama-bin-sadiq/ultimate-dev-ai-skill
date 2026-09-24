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
            runtime._store.save_operation(tid, "op-cancel", {
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
            with self.assertRaises(ContractError):
                runtime.record_jev_decision(tid, empty, action_fingerprint=prepared["fingerprint"])

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

    def test_task_state_event_quota_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False)
            state = runtime.start({"goal": "quota"})
            tid = state["task_id"]
            original = __import__("runtime.core.state", fromlist=["MAX_EVENTS"]).MAX_EVENTS
            try:
                __import__("runtime.core.state", fromlist=["MAX_EVENTS"]).MAX_EVENTS = 1
                with self.assertRaises(ValueError):
                    runtime._store.append_event(tid, {"type": "one"})
            finally:
                __import__("runtime.core.state", fromlist=["MAX_EVENTS"]).MAX_EVENTS = original

    def test_concurrent_events_do_not_overwrite_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False)
            state = runtime.start({"goal": "record"})
            tid = state["task_id"]
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(lambda value: runtime._store.append_event(tid, {"type": "probe", "value": value}), range(20)))
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

    def test_task_health_reports_stale_operations(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False)
            state = runtime.start({"goal": "health"})
            tid = state["task_id"]
            runtime._store.save_operation(tid, "op-stale", {
                "operation_id": "op-stale",
                "task_id": tid,
                "attempt": 1,
                "idempotency_key": "stale",
                "action_fingerprint": "0" * 64,
                "capability_id": "shell.execute",
                "status": "running",
                "lease_expires_at_epoch": 0,
            })
            health = runtime.task_health(tid)
            self.assertEqual(health["stale_operations"], 1)
            self.assertFalse(health["healthy"])

    def test_expired_operation_lease_is_recovered_as_uncertain(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False)
            state = runtime.start({"goal": "recover"})
            tid = state["task_id"]
            runtime._store.save_operation(tid, "op-stale", {
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

    def test_runtime_close_is_idempotent_and_preserves_task_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            class Executor:
                def __init__(self):
                    self.closed = 0

                def __call__(self, **kwargs):
                    return {"success": True}

                def close(self):
                    self.closed += 1

            executor = Executor()
            runtime = Runtime(tmp, require_jev_decision=False, host_executor=executor)
            state = runtime.start({"goal": "close"})
            tid = state["task_id"]
            self.assertTrue(runtime.session_start()["ready"])
            self.assertTrue(runtime.session_end()["success"])
            self.assertEqual(executor.closed, 1)
            self.assertEqual(runtime.execute_code(tid, "print('x')")["code"], "runtime_closed")
            self.assertTrue(runtime.shutdown()["repeated"])
            self.assertEqual(executor.closed, 1)
            self.assertTrue((runtime.store.task_dir(tid) / "state.json").exists())

    def test_runtime_close_bridges_async_host_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            class AsyncResource:
                def __init__(self):
                    self.closed = False

                def __call__(self, **kwargs):
                    return {"success": True}

                async def close(self):
                    self.closed = True

            resource = AsyncResource()
            runtime = Runtime(tmp, require_jev_decision=False, host_executor=resource)
            result = runtime.close()
            self.assertTrue(result["success"])
            self.assertTrue(resource.closed)

    def test_close_failure_remains_retryable_and_blocks_new_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            class FailingResource:
                def __init__(self):
                    self.calls = 0

                def __call__(self, **kwargs):
                    return {"success": True}

                def close(self):
                    self.calls += 1
                    if self.calls == 1:
                        raise RuntimeError("close unavailable")

            resource = FailingResource()
            runtime = Runtime(tmp, require_jev_decision=False, host_executor=resource)
            first = runtime.close()
            self.assertFalse(first["success"])
            self.assertTrue(first["retryable"])
            self.assertFalse(runtime._closed)
            self.assertEqual(runtime.execute_code("missing", "print('x')")["code"], "task_not_found")
            second = runtime.close()
            self.assertTrue(second["success"])
            self.assertTrue(runtime._closed)
            self.assertEqual(runtime.execute_code("missing", "print('x')")["code"], "runtime_closed")

    def test_durable_evidence_and_operation_results_redact_common_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            def executor(**kwargs):
                return {"success": True, "stdout": "token=supersecret", "stderr": "", "exit_code": 0}

            runtime = Runtime(tmp, require_jev_decision=False, host_executor=executor)
            state = runtime.start({
                "goal": "redact",
                "acceptance_criteria": ["redacted"],
                "api_token": "contract-supersecret",
            })
            tid = state["task_id"]
            self.assertNotIn("contract-supersecret", json.dumps(runtime.store.load(tid)))
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            result = runtime.execute_code(tid, "print('x')", operation_id="op-redact")
            persisted = runtime.store.load_operation(tid, result["operation_id"])
            self.assertNotIn("supersecret", json.dumps(persisted))
            runtime.transition(tid, "observing")
            runtime.transition(tid, "verifying")
            runtime.record_verification(
                tid,
                evidence={"items": [{"criterion": "redacted", "passed": True, "source": "token=supersecret"}]},
            )
            evidence = runtime.store.task_dir(tid) / "evidence"
            contents = "\n".join(path.read_text() for path in evidence.glob("*.json"))
            self.assertNotIn("supersecret", contents)

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
            persisted = runtime.store.load_operation(tid, operation_id)
            self.assertEqual(persisted["status"], "uncertain")
            self.assertFalse(persisted.get("retry_allowed", False))

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
    def test_jev_gated_runtime_uses_secure_policy_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp)
            self.assertIn("write", runtime.policy.confirmation_required)
            self.assertIn("network", runtime.policy.confirmation_required)
            self.assertEqual(runtime.policy.check_capability("shell.execute", {"write"}).get("reason"), "confirmation_required")

    def test_shape_only_evidence_cannot_complete_when_trust_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False, require_trusted_evidence=True)
            state = runtime.start({"goal": "trusted evidence", "acceptance_criteria": ["tests pass"]})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            runtime.transition(tid, "executing")
            runtime.transition(tid, "observing")
            runtime.transition(tid, "verifying")
            runtime.record_verification(
                tid,
                evidence={"items": [{"criterion": "tests pass", "passed": True, "command": "pytest"}]},
            )
            with self.assertRaises(PermissionError):
                runtime.transition(tid, "completed")

    def test_contradictory_success_and_uncertain_is_normalized_to_uncertain(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(
                tmp,
                require_jev_decision=False,
                host_executor=lambda **kwargs: {"success": True, "uncertain": True},
            )
            state = runtime.start({"goal": "contradictory result"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            result = runtime.execute_code(tid, "print('x')", operation_id="op-contradictory")
            self.assertEqual(result["operation_status"], "uncertain")
            self.assertFalse(result["success"])
            self.assertTrue(result.get("contradictory_success"))

    def test_uncertain_operation_requires_reconciliation_before_retry(self):
        calls = []

        def executor(**kwargs):
            calls.append(kwargs["operation_id"])
            if len(calls) == 1:
                return {"success": False, "uncertain": True, "stdout": "timeout", "stderr": "", "exit_code": -1}
            return {"success": True, "stdout": "", "stderr": "", "exit_code": 0}

        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False, host_executor=executor)
            state = runtime.start({"goal": "uncertain"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            first = runtime.execute_code(tid, "print('x')", operation_id="op-uncertain")
            self.assertEqual(first["operation_status"], "uncertain")
            denied = runtime.execute_code(tid, "print('x')", operation_id="op-uncertain", retry=True)
            self.assertEqual(denied["code"], "operation_reconciliation_required")
            self.assertEqual(len(calls), 1)
            runtime.reconcile_operation(
                tid,
                "op-uncertain",
                outcome="not_executed",
                evidence={"readback": "no external record"},
                reconciled_by="test",
            )
            retried = runtime.execute_code(tid, "print('x')", operation_id="op-uncertain", retry=True)
            self.assertTrue(retried["success"])
            self.assertEqual(len(calls), 2)

    def test_execute_allowlist_is_exact_and_empty_allowlist_denies(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            runtime = Runtime(
                tmp,
                require_jev_decision=False,
                host_executor=lambda **kwargs: calls.append(kwargs) or {"success": True},
            )
            state = runtime.start({"goal": "allowlist", "allowed_actions": ["execute"]})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            denied = runtime.execute_code(tid, "print('x')")
            self.assertEqual(denied["code"], "contract_action_not_allowed")
            self.assertEqual(calls, [])

            second = Runtime(tmp, require_jev_decision=False, host_executor=lambda **kwargs: {"success": True})
            state = second.start({"goal": "empty allowlist", "task_id": "task-empty-allowlist", "allowed_actions": []})
            second.transition(state["task_id"], "planning")
            second.transition(state["task_id"], "planned")
            empty_denied = second.execute_code(state["task_id"], "print('x')")
            self.assertEqual(empty_denied["code"], "contract_action_not_allowed")

    def test_code_effect_classification_cannot_be_narrowed_by_caller(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False)
            prepared = runtime.prepare_execution_action(
                "task-effects",
                "open('output.txt', 'w').write('x')",
                effects={"execute"},
            )
            self.assertIn("write", prepared["action"]["effects"])

    def test_same_idempotency_key_is_reserved_atomically(self):
        calls = []

        def executor(**kwargs):
            calls.append(kwargs["operation_id"])
            return {"success": True, "stdout": "", "stderr": "", "exit_code": 0}

        with tempfile.TemporaryDirectory() as tmp:
            first = Runtime(tmp, require_jev_decision=False, host_executor=executor)
            state = first.start({"goal": "idempotency race", "task_id": "task-idempotency"})
            tid = state["task_id"]
            first.transition(tid, "planning")
            first.transition(tid, "planned")
            first.transition(tid, "executing")
            second = Runtime(tmp, require_jev_decision=False, host_executor=executor)
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(
                    pool.map(
                        lambda pair: pair[0].execute_code(
                            tid,
                            "print('x')",
                            operation_id=pair[1],
                            idempotency_key="same-key",
                        ),
                        [(first, "op-race-a"), (second, "op-race-b")],
                    )
                )
            self.assertEqual(len(calls), 1)
            self.assertTrue(any(item.get("replayed") for item in results) or any(item.get("success") for item in results))

    def test_public_store_cannot_mutate_protected_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=False)
            state = runtime.start({"goal": "public store"})
            with self.assertRaises(PermissionError):
                runtime.store.update_internal(state["task_id"], status="completed")
            with self.assertRaises(PermissionError):
                runtime.store.save_internal(state["task_id"], "state.json", {})

    def test_executable_packet_with_missing_capabilities_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(tmp, require_jev_decision=True)
            state = runtime.start({"goal": "packet invariants"})
            tid = state["task_id"]
            runtime.transition(tid, "planning")
            runtime.transition(tid, "planned")
            prepared = runtime.prepare_execution_action(tid, "print('x')")
            invalid = packet(tid, selected=("shell.execute",))
            invalid["capability_plan"]["missing_capabilities"] = ["filesystem.read"]
            with self.assertRaises(ContractError):
                runtime.record_jev_decision(tid, invalid, action_fingerprint=prepared["fingerprint"])

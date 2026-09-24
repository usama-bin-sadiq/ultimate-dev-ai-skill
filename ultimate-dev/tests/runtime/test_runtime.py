import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from runtime.core import Runtime, TaskStore, ContextManager, Policy, Verification, Capability, CapabilityRegistry


def make_packet(task_id, *, effect="execute", selected=("shell.execute",), action="approve", route="lightweight"):
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


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = Runtime(self.tmp.name, require_jev_decision=False)

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_checkpoint_resume(self):
        s = self.rt.start({"goal": "ship feature", "acceptance_criteria": ["tests pass"]})
        tid = s["task_id"]
        self.assertEqual(self.rt.resume(tid)["status"], "ready")
        self.rt.transition(tid, "planning")
        self.rt.transition(tid, "planned")
        cp = self.rt.checkpoint(tid)
        self.assertTrue(cp.exists())
        self.assertEqual(self.rt.resume(tid)["contract"]["goal"], "ship feature")

    def test_jev_gate_blocks_execution_until_approved_packet(self):
        rt = Runtime(self.tmp.name, require_jev_decision=True)
        s = rt.start({"goal": "execute a host capability"})
        tid = s["task_id"]
        rt.transition(tid, "planning")
        rt.transition(tid, "planned")
        with self.assertRaises(PermissionError):
            rt.transition(tid, "executing")
        decision = make_packet(tid)
        prepared = rt.prepare_execution_action(tid, "print('x')")
        rt.record_jev_decision(tid, decision, action_fingerprint=prepared["fingerprint"])
        state = rt.transition(tid, "executing")
        self.assertEqual(state["status"], "executing")
        evidence = list((Path(self.tmp.name) / ".memory" / "ultimate-dev" / "tasks" / tid / "evidence").glob("jev-*.json"))
        self.assertEqual(len(evidence), 1)
        self.assertEqual(rt.resume(tid)["decisions"][-1]["guardrail"], "approve")

    def test_jev_human_review_route_cannot_be_executed(self):
        rt = Runtime(self.tmp.name, require_jev_decision=True)
        s = rt.start({"goal": "review a host capability"})
        tid = s["task_id"]
        rt.transition(tid, "planning")
        rt.transition(tid, "planned")
        decision = make_packet(tid, effect="review", selected=(), action="human_review", route="human_review")
        rt.record_jev_decision(tid, decision)
        result = rt.execute_code(tid, "print('x')")
        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "jev_decision_required")

    def test_execution_without_host_adapter_is_unavailable(self):
        s = self.rt.start({"goal": "execute code"})
        tid = s["task_id"]
        self.rt.transition(tid, "planning")
        self.rt.transition(tid, "planned")
        result = self.rt.execute_code(tid, "print('x')")
        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "capability_unavailable")

    def test_injected_host_executor_receives_explicit_arguments(self):
        calls = []

        def executor(**kwargs):
            calls.append(kwargs)
            return {"success": True, "stdout": "ok", "stderr": "", "exit_code": 0}

        rt = Runtime(self.tmp.name, require_jev_decision=False, host_executor=executor)
        state = rt.start({"goal": "execute code"})
        tid = state["task_id"]
        rt.transition(tid, "planning")
        rt.transition(tid, "planned")
        result = rt.execute_code(tid, "print('x')", language="python", task_description="smoke")
        self.assertTrue(result["success"])
        self.assertEqual(calls[0]["code"], "print('x')")
        self.assertEqual(calls[0]["language"], "python")
        self.assertEqual(calls[0]["task_description"], "smoke")
        self.assertEqual(calls[0]["task_id"], tid)

    def test_handoff_contains_next_action_and_evidence(self):
        s = self.rt.start({"goal": "x"})
        tid = s["task_id"]
        self.rt.transition(tid, "planning", next_action="inspect tests")
        path = self.rt.handoff(tid, "backend")
        packet = json.loads(path.read_text())
        self.assertEqual(packet["next_action"], "inspect tests")

    def test_context_progressive(self):
        s = self.rt.start({"goal": "read a file"})
        tid = s["task_id"]
        p = Path(self.tmp.name) / "a.txt"
        p.write_text("hello")
        ctx = ContextManager(self.tmp.name, self.rt.store).build(tid, files=["a.txt"], budget=2000)
        self.assertIn("a.txt", ctx["relevant_files"])

    def test_capability_registry_exports_jev_descriptors(self):
        registry = CapabilityRegistry()
        registry.register(
            Capability(
                name="filesystem.read",
                description="Read a file",
                execute=lambda **_: None,
                effects={"read"},
            )
        )
        descriptor = registry.jev_catalog()[0]
        self.assertEqual(descriptor["id"], "filesystem.read")
        self.assertEqual(descriptor["effects"], ["read"])
        self.assertTrue(descriptor["available"])
        canonical = registry.catalog_descriptors()[0]
        self.assertEqual(canonical.id, "filesystem.read")
        self.assertEqual(canonical.effects, ("read",))

    def test_policy(self):
        self.assertFalse(Policy().check("drop_database")["allowed"])
        self.assertTrue(Policy().check("drop_database", confirmed=True)["allowed"])

    def test_verification(self):
        out = Verification().evaluate(["tests pass"], [{"criterion": "tests pass", "passed": True, "command": "pytest"}])
        self.assertTrue(out["passed"])
        out = Verification().evaluate(["tests pass"], [])
        self.assertFalse(out["passed"])
        with self.assertRaises(ValueError):
            Verification().evaluate(["tests pass"], [{"criterion": "tests pass", "passed": True}])


if __name__ == "__main__":
    unittest.main()

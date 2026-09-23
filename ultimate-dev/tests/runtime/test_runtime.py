import json, tempfile, unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from runtime.core import Runtime, TaskStore, ContextManager, Policy, Verification

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.rt=Runtime(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()

    def test_create_checkpoint_resume(self):
        s=self.rt.start({"goal":"ship feature","acceptance_criteria":["tests pass"]})
        tid=s["task_id"]
        self.assertEqual(self.rt.resume(tid)["status"],"ready")
        self.rt.transition(tid,"planning")
        self.rt.transition(tid,"planned")
        cp=self.rt.checkpoint(tid)
        self.assertTrue(cp.exists())
        self.assertEqual(self.rt.resume(tid)["contract"]["goal"],"ship feature")

    def test_handoff_contains_next_action_and_evidence(self):
        s=self.rt.start({"goal":"x"})
        tid=s["task_id"]
        self.rt.transition(tid,"planning", next_action="inspect tests")
        path=self.rt.handoff(tid,"backend")
        packet=json.loads(path.read_text())
        self.assertEqual(packet["next_action"],"inspect tests")

    def test_context_progressive(self):
        s=self.rt.start({"goal":"read a file"})
        tid=s["task_id"]
        p=Path(self.tmp.name)/"a.txt"; p.write_text("hello")
        ctx=ContextManager(self.tmp.name,self.rt.store).build(tid,files=["a.txt"],budget=2000)
        self.assertIn("a.txt",ctx["relevant_files"])

    def test_policy(self):
        self.assertFalse(Policy().check("drop_database")["allowed"])
        self.assertTrue(Policy().check("drop_database",confirmed=True)["allowed"])

    def test_verification(self):
        out=Verification().evaluate(["tests pass"],[{"criterion":"tests pass","passed":True,"command":"pytest"}])
        self.assertTrue(out["passed"])
        out=Verification().evaluate(["tests pass"],[])
        self.assertFalse(out["passed"])

if __name__=="__main__": unittest.main()

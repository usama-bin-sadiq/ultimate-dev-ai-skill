"""Contract tests for the governed self-evolution candidate store."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from runtime.core.evolution import (  # noqa: E402
    AdmissionRequired,
    EvolutionContractError,
    EvolutionStore,
    InvalidCandidateTransition,
)


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 9, 24, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.value

    def advance(self, seconds: int) -> None:
        self.value += timedelta(seconds=seconds)


def proposal(target: str = "skills/example/SKILL.md") -> dict:
    return {
        "name": "example-capability",
        "source": {"kind": "repeated-gap", "task_id": "task-1", "occurrences": 3},
        "evidence": [
            {"command": "python -m unittest", "result": "passed"},
            {"artifact": "trace.json", "hash": "sha256:example"},
        ],
        "diff": {"target": target, "patch": "@@ -1 +1 @@\n-old\n+new"},
        "rollback": {"target": target, "patch": "@@ -1 +1 @@\n-new\n+old"},
        "description": "A staged reusable capability.",
    }


def passing_evaluators(calls: list[str] | None = None):
    def deterministic(candidate):
        if calls is not None:
            calls.append("deterministic")
        return {"passed": True, "check": "deterministic"}

    def repeated(candidate, trial_index=0, trials=3):
        if calls is not None:
            calls.append(f"repeated-{trial_index}")
        return {"passed": True, "trial": trial_index}

    def security(candidate):
        if calls is not None:
            calls.append("security")
        return {"passed": True, "risk": "low"}

    return {"deterministic": deterministic, "repeated": repeated, "security": security}


class GovernedEvolutionTests(unittest.TestCase):
    def test_stage_persists_complete_metadata_only_under_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canonical = root / "skills" / "example" / "SKILL.md"
            canonical.parent.mkdir(parents=True)
            canonical.write_text("canonical sentinel\n", encoding="utf-8")
            before = canonical.read_bytes()

            store = EvolutionStore(root)
            candidate = store.stage(proposal(), candidate_id="candidate-one")

            self.assertEqual(candidate.status, "staged")
            self.assertEqual(candidate["source"]["task_id"], "task-1")
            self.assertEqual(candidate["evidence"][0]["command"], "python -m unittest")
            self.assertIn("rollback", candidate["proposal"])
            self.assertEqual(canonical.read_bytes(), before)
            self.assertTrue(candidate_path(root, "candidate-one").exists())
            index = json.loads((root / ".memory" / "ultimate-dev" / "evolution" / "index.json").read_text())
            self.assertIn("candidate-one", index["candidates"])

    def test_evaluation_requires_all_families_and_publish_requires_admission(self):
        calls: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            store = EvolutionStore(tmp, evaluators=passing_evaluators(calls))
            candidate = store.stage(proposal(), candidate_id="candidate-gate")

            with self.assertRaises(AdmissionRequired):
                store.publish("candidate-gate")

            candidate = store.evaluate("candidate-gate", trials=3)
            self.assertEqual(candidate.status, "evaluated")
            self.assertTrue(candidate["evaluation"]["passed"])
            self.assertEqual(calls.count("repeated-0"), 1)
            self.assertEqual(calls.count("repeated-1"), 1)
            self.assertEqual(calls.count("repeated-2"), 1)

            with self.assertRaises(AdmissionRequired):
                store.publish("candidate-gate")

            candidate = store.admit("candidate-gate", actor="maintainer")
            self.assertEqual(candidate.status, "approved")
            self.assertEqual(candidate["admission_state"], "admitted")
            self.assertTrue(candidate["admission"]["explicit"])

            candidate = store.publish_global("candidate-gate")
            self.assertEqual(candidate.status, "published")
            self.assertFalse(candidate["publication"]["canonical_write"])
            self.assertEqual(candidate["publication"]["canonical_target"], "skills/example/SKILL.md")
            self.assertEqual(candidate["publication"]["publication_mode"], "memory_receipt_only")
            self.assertEqual(len(store.publications("candidate-gate")), 1)

    def test_protected_security_regression_failure_cannot_be_admitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            def failing_security(candidate):
                return {"passed": False, "protected_regression": "existing behavior changed"}

            evaluators = passing_evaluators()
            evaluators["security"] = failing_security
            store = EvolutionStore(tmp, evaluators=evaluators)
            store.stage(proposal(), candidate_id="candidate-regression")
            candidate = store.evaluate("candidate-regression")

            self.assertEqual(candidate.status, "rejected")
            self.assertTrue(candidate["protected_regression_failure"])
            self.assertEqual(candidate["failure"]["code"], "protected_regression_failure")
            with self.assertRaises(AdmissionRequired):
                store.admit("candidate-regression", actor="maintainer")
            self.assertFalse(store.can_publish("candidate-regression"))

    def test_reject_expire_and_restart_state(self):
        clock = Clock()
        with tempfile.TemporaryDirectory() as tmp:
            store = EvolutionStore(tmp, clock=clock)
            store.stage(proposal(), candidate_id="candidate-reject")
            rejected = store.reject("candidate-reject", reason="not reusable", actor="reviewer")
            self.assertEqual(rejected.status, "rejected")
            self.assertEqual(rejected["failure"]["message"], "not reusable")

            store.stage(proposal(), candidate_id="candidate-expire", ttl_seconds=10)
            clock.advance(11)
            expired = EvolutionStore(tmp, clock=clock).get_candidate("candidate-expire")
            self.assertEqual(expired.status, "expired")
            with self.assertRaises(InvalidCandidateTransition):
                EvolutionStore(tmp, clock=clock).evaluate("candidate-expire")

    def test_explicit_approval_is_bound_to_evaluation_and_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvolutionStore(tmp, evaluators=passing_evaluators())
            store.stage(proposal(), candidate_id="candidate-bound")
            store.evaluate("candidate-bound")
            store.approve("candidate-bound", "reviewer", approved=True)
            approved = store.get_candidate("candidate-bound")
            self.assertEqual(approved["admission"]["approved_by"], "reviewer")

            # A new version does not inherit the old admission.
            child = store.create_version("candidate-bound", candidate_id_new="candidate-v2")
            self.assertEqual(child.version, 2)
            self.assertIsNone(child["admission"])
            self.assertEqual(child.status, "staged")

    def test_version_publication_and_memory_only_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = EvolutionStore(root, evaluators=passing_evaluators())
            parent = store.stage(proposal(), candidate_id="candidate-v1")
            self.assertEqual(parent.version, 1)
            child = store.create_version(parent["candidate_id"], candidate_id_new="candidate-v2")
            store.evaluate(child["candidate_id"])
            store.admit(child["candidate_id"], actor="maintainer")
            store.publish(child["candidate_id"])
            rolled = store.rollback(child["candidate_id"], target_version=1, reason="bad rollout", actor="maintainer")

            self.assertEqual(rolled.status, "rolled_back")
            self.assertEqual(rolled["active_version"], 1)
            self.assertFalse(rolled["canonical_write_performed"])
            self.assertEqual(len(store.rollbacks(child["candidate_id"])), 1)
            self.assertFalse((root / "skills").exists())

    def test_no_argument_evaluators_are_supported_without_bypassing_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvolutionStore(tmp)
            store.stage(proposal(), candidate_id="candidate-noargs")
            result = store.evaluate(
                "candidate-noargs",
                deterministic=lambda: True,
                repeated=lambda: True,
                security=lambda: True,
                trials=2,
            )
            self.assertEqual(result.status, "evaluated")
            with self.assertRaises(AdmissionRequired):
                store.publish("candidate-noargs")

    def test_evaluator_exceptions_and_malformed_results_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            def explode(candidate):
                raise RuntimeError("provider unavailable")

            evaluators = passing_evaluators()
            evaluators["deterministic"] = explode
            store = EvolutionStore(tmp, evaluators=evaluators)
            store.stage(proposal(), candidate_id="candidate-error")
            result = store.evaluate("candidate-error")
            self.assertEqual(result.status, "rejected")
            self.assertFalse(result["evaluation"]["checks"][0]["passed"])
            with self.assertRaises(AdmissionRequired):
                store.publish("candidate-error")

    def test_missing_evaluator_is_a_contract_error_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvolutionStore(tmp, evaluators={"deterministic": lambda candidate: True})
            store.stage(proposal(), candidate_id="candidate-missing")
            with self.assertRaises(EvolutionContractError):
                store.evaluate("candidate-missing")
            self.assertEqual(store.get_candidate("candidate-missing").status, "staged")

    def test_candidate_metadata_rejects_escape_paths_and_non_json_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvolutionStore(tmp)
            escaped = proposal()
            escaped["diff"] = {"target": "../outside", "patch": "x"}
            with self.assertRaises(EvolutionContractError):
                store.stage(escaped)
            bad = proposal()
            bad["evidence"] = [{"command": "ok"}, {"untyped": object()}]
            with self.assertRaises(EvolutionContractError):
                store.stage(bad)


def candidate_path(root: Path, candidate_id: str) -> Path:
    return root / ".memory" / "ultimate-dev" / "evolution" / "candidates" / f"{candidate_id}.json"


if __name__ == "__main__":
    unittest.main()

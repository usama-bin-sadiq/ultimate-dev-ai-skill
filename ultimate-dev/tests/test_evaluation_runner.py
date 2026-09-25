#!/usr/bin/env python3
"""Focused tests for the provider-neutral evaluation runner."""

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.evaluation import (  # noqa: E402
    STATUS_FAIL,
    STATUS_NOT_RUN,
    STATUS_PASS,
    STATUS_UNCERTAIN,
    EvaluationRunner,
    load_cases,
    load_golden_cases,
    run_evaluation,
)


class EvaluationRunnerTests(unittest.TestCase):
    def test_routing_scenarios_use_injected_classifier(self):
        cases = [
            {
                "id": "route-atomic",
                "task": "rename a local variable",
                "expected_size": "atomic",
                "expected_domains": [],
                "expected_risk": "none",
            },
            {
                "id": "route-api",
                "task": "design an authenticated REST API",
                "expected_size": "moderate",
                "expected_domains": ["backend"],
                "expected_risk": "security",
            },
        ]

        def classifier(case):
            if case["id"] == "route-atomic":
                return {"size": "atomic", "domains": [], "risk": "none"}
            return {
                "size": "moderate",
                "domains": ["backend"],
                "risk": "security",
                "route": "backend",
            }

        def agent(task, classification):
            return {
                "answer": "classified and answered",
                "tool_calls": 1,
                "tokens": {"input": 7, "output": 5},
                "cost_usd": 0.25,
                "latency_ms": 12,
            }

        def verifier(result):
            return {"passed": result["answer"] == "classified and answered"}

        result = run_evaluation(cases, classifier, agent, verifier)

        self.assertEqual(result["provenance"]["mode"], "injected_callables")
        self.assertFalse(result["provenance"]["is_model_benchmark"])
        self.assertEqual(len(result["cases"]), 2)
        for case in result["cases"]:
            self.assertEqual(case["status"], STATUS_PASS)
            self.assertEqual(case["trials"][0]["routing"]["status"], STATUS_PASS)
            self.assertEqual(case["trials"][0]["success"], True)
        self.assertEqual(result["summary"]["tool_calls"], 2)
        self.assertEqual(result["summary"]["tokens"]["input"], 14)
        self.assertEqual(result["summary"]["cost"], 0.5)
        self.assertEqual(result["summary"]["latency_ms"]["total"], 24)
        json.dumps(result, allow_nan=False)

    def test_verifier_failure_is_fail_not_uncertain(self):
        def classifier(case):
            return {"size": "atomic", "domains": [], "risk": "none"}

        def agent(case):
            return {"answer": "wrong"}

        def verifier(result, case):
            return {"status": "fail", "reason": "answer did not satisfy case"}

        result = run_evaluation(
            [
                {
                    "id": "bad-answer",
                    "task": "return the required value",
                    "expected_size": "atomic",
                    "expected_domains": [],
                    "expected_risk": "none",
                }
            ],
            classifier,
            agent,
            verifier,
        )
        trial = result["cases"][0]["trials"][0]
        self.assertEqual(trial["status"], STATUS_FAIL)
        self.assertIs(trial["success"], False)
        self.assertIn("verifier_status_fail", trial["status_reasons"])

    def test_repeated_trials_report_consistency_and_best_of_k_separately(self):
        verdicts = iter([True, False, True])
        calls = {"classifier": 0, "agent": 0, "verifier": 0}

        def classifier(case):
            calls["classifier"] += 1
            return {"size": "atomic", "domains": [], "risk": "none"}

        def agent(case):
            calls["agent"] += 1
            return {"answer": "trial"}

        def verifier(result):
            calls["verifier"] += 1
            return next(verdicts)

        result = run_evaluation(
            [
                {
                    "id": "repeat",
                    "task": "repeatable scripted case",
                    "expected_size": "atomic",
                    "expected_domains": [],
                    "expected_risk": "none",
                }
            ],
            classifier,
            agent,
            verifier,
            trials=3,
            pass_k=2,
        )
        case = result["cases"][0]
        self.assertEqual(calls, {"classifier": 3, "agent": 3, "verifier": 3})
        self.assertEqual(len(case["trials"]), 3)
        self.assertEqual([trial["status"] for trial in case["trials"]], [
            STATUS_PASS,
            STATUS_FAIL,
            STATUS_PASS,
        ])
        self.assertAlmostEqual(case["pass_at_k"], 1.0)
        self.assertAlmostEqual(case["pass^k"], 1 / 3)
        self.assertEqual(result["summary"]["pass_at_k"], 1.0)
        self.assertAlmostEqual(result["summary"]["pass^k"], 1 / 3)

    def test_trace_redacts_case_payloads_and_backend_events(self):
        case = {
            "id": "redaction",
            "task": "use the api_key=sk-case-secret",
            "api_key": "sk-case-secret",
            "expected_size": "atomic",
            "expected_domains": [],
            "expected_risk": "none",
        }

        def classifier(case):
            return {"size": "atomic", "domains": [], "risk": "none"}

        def agent(case):
            return {
                "answer": "done",
                "trace": [
                    {
                        "event": "tool_call",
                        "tool": "http.request",
                        "args": {"Authorization": "Bearer sk-trace-secret"},
                    }
                ],
            }

        def verifier(result):
            return True

        result = run_evaluation([case], classifier, agent, verifier)
        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn("sk-case-secret", serialized)
        self.assertNotIn("sk-trace-secret", serialized)
        self.assertIn("[REDACTED]", serialized)
        self.assertEqual(result["cases"][0]["trials"][0]["trace"][2]["event"], "agent")

    def test_no_provider_mode_is_explicitly_not_run(self):
        result = EvaluationRunner([{"id": "offline", "task": "do not execute"}]).run(trials=2)
        self.assertEqual(result["provenance"]["mode"], "no_provider")
        self.assertFalse(result["provenance"]["is_model_benchmark"])
        self.assertEqual(result["summary"]["executed_trials"], 0)
        self.assertFalse(result["summary"]["scored"])
        self.assertEqual(result["summary"]["status_counts"][STATUS_NOT_RUN], 2)
        for trial in result["cases"][0]["trials"]:
            self.assertEqual(trial["status"], STATUS_NOT_RUN)
            self.assertIsNone(trial["success"])
            self.assertEqual(
                [event["status"] for event in trial["trace"] if event["event"] in {"classifier", "agent", "verifier"}],
                [STATUS_NOT_RUN, STATUS_NOT_RUN, STATUS_NOT_RUN],
            )
        self.assertIn("not_run", json.dumps(result["provenance"]["limitations"]))

    def test_routing_contract_checks_forbidden_domains_and_capability_gap(self):
        def classifier(case):
            return {
                "size": "moderate",
                "domains": ["unknown-unclassified"],
                "risk": "data",
                "deliverable": "unknown",
                "clarity": "resolvable",
                "activated_forbidden_domains": [],
                "capability_gap": "partial",
            }

        result = run_evaluation(
            [
                {
                    "id": "unknown-gap",
                    "task": "Assess an unfamiliar domain",
                    "expected_size": "moderate",
                    "expected_domains": ["unknown-unclassified"],
                    "expected_risk": "data",
                    "expected_deliverable": "unknown",
                    "expected_clarity": "resolvable",
                    "expected_forbidden_domains": ["frontend"],
                    "expected_capability_gap": "partial",
                }
            ],
            classifier,
            lambda case, classification=None: {"answer": "bounded"},
            lambda result, case=None: True,
        )
        trial = result["cases"][0]["trials"][0]
        self.assertEqual(trial["routing"]["status"], STATUS_PASS)
        self.assertTrue(trial["success"])


    def test_missing_verifier_is_uncertain(self):
        result = run_evaluation(
            [{"id": "unverified", "task": "run only an injected agent"}],
            agent=lambda case: {"answer": "maybe"},
        )
        trial = result["cases"][0]["trials"][0]
        self.assertEqual(trial["status"], STATUS_UNCERTAIN)
        self.assertIsNone(trial["success"])

    def test_golden_and_json_case_loading(self):
        golden = load_golden_cases()
        self.assertGreaterEqual(len(golden), 150)
        self.assertEqual(golden[0]["id"], "atomic-001")
        self.assertTrue(golden.fixture_only)
        self.assertGreaterEqual(
            sum(
                1
                for case in golden
                if str(case.get("category", "")).lower() in {"near-miss", "nearmiss", "negative"}
                or "nearmiss" in str(case.get("id", "")).lower()
            ),
            60,
        )

        scripted = load_cases(
            json.dumps(
                {
                    "cases": [
                        {
                            "id": "scripted-1",
                            "task": "scripted response",
                            "script": [{"tool": "fixture.read", "result": "ok"}],
                        }
                    ]
                }
            )
        )
        self.assertEqual(scripted[0]["id"], "scripted-1")
        self.assertIn("script", scripted[0])


if __name__ == "__main__":
    unittest.main()

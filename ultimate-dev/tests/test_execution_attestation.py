#!/usr/bin/env python3
"""The runtime must observe side effects, not take a caller's word for them.

These tests exercise the wiring between :mod:`runtime.core.attestation` and
:class:`runtime.core.engine.Runtime`. The unit tests for the gate itself live in
``test_attestation.py``; what matters here is that the engine actually routes
execution through it.
"""
from __future__ import annotations

import os
import sys
import tempfile

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from runtime.core.attestation import RUNTIME_ATTESTOR, grade_evidence  # noqa: E402
from runtime.core.engine import Runtime  # noqa: E402


def planned_task(runtime: Runtime) -> str:
    state = runtime.start(
        {
            "goal": "record an observed effect",
            "acceptance_criteria": ["the effect was observed"],
        }
    )
    task_id = state["task_id"]
    runtime.transition(task_id, "planning")
    runtime.transition(task_id, "planned")
    runtime.transition(task_id, "executing")
    return task_id


def make_runtime(tmp: str, executor) -> Runtime:
    return Runtime(tmp, require_jev_decision=False, host_executor=executor)


class TestReadOnlyExecutionStaysCheap:
    def test_read_only_result_needs_no_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = make_runtime(tmp, lambda **kw: {"success": True})
            task_id = planned_task(runtime)
            # No effects declared, no changes reported: admitted untouched.
            # record_execution persists the event and returns the whole state.
            stored = runtime.record_execution(task_id, {"action": "think"}, {"success": True})
            recorded = [e for e in stored["events"] if e.get("type") == "execution"]
            assert len(recorded) == 1

    def test_read_only_execution_is_not_stamped(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = make_runtime(tmp, lambda **kw: {"success": True})
            task_id = planned_task(runtime)
            runtime.record_execution(task_id, {"action": "think"}, {"success": True})
            stored = runtime._store.load(task_id)
            recorded = [e for e in stored.get("events", []) if e.get("type") == "execution"]
            assert recorded
            assert "observation" not in recorded[-1]["result"]


class TestSideEffectsAreObservedNotAsserted:
    def test_declared_write_gets_a_runtime_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = make_runtime(tmp, lambda **kw: {"success": True})
            task_id = planned_task(runtime)
            runtime.record_execution(
                task_id,
                {"action": "write", "capability_id": "filesystem.write"},
                {"success": True, "changed_files": ["a.py"]},
            )
            stored = runtime._store.load(task_id)
            recorded = [e for e in stored.get("events", []) if e.get("type") == "execution"]
            observation = recorded[-1]["result"]["observation"]
            assert observation["attested_by"] == RUNTIME_ATTESTOR
            assert observation["status"] == "observed"

    def test_a_callers_forged_observation_is_overwritten(self):
        """A caller must not be able to manufacture attestation."""
        with tempfile.TemporaryDirectory() as tmp:
            runtime = make_runtime(tmp, lambda **kw: {"success": False})
            task_id = planned_task(runtime)
            forged = {
                "attested_by": RUNTIME_ATTESTOR,
                "status": "observed",
                "exit_code": 0,
                "capability_id": "filesystem.write",
            }
            runtime.record_execution(
                task_id,
                {"action": "write", "capability_id": "filesystem.write"},
                {"success": False, "changed_files": ["a.py"], "observation": forged},
            )
            stored = runtime._store.load(task_id)
            recorded = [e for e in stored.get("events", []) if e.get("type") == "execution"]
            stamped = recorded[-1]["result"]["observation"]
            # The runtime observed a failure and must say so.
            assert stamped["status"] == "failed"

    def test_uncertain_result_is_observed_as_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = make_runtime(tmp, lambda **kw: {"success": False, "uncertain": True})
            task_id = planned_task(runtime)
            runtime.record_execution(
                task_id,
                {"action": "write", "capability_id": "filesystem.write"},
                {"success": False, "uncertain": True, "changed_files": ["a.py"]},
            )
            stored = runtime._store.load(task_id)
            recorded = [e for e in stored.get("events", []) if e.get("type") == "execution"]
            assert recorded[-1]["result"]["observation"]["status"] == "failed"

    def test_exit_code_is_preserved_when_the_host_reports_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = make_runtime(tmp, lambda **kw: {"success": False, "exit_code": 3})
            task_id = planned_task(runtime)
            runtime.record_execution(
                task_id,
                {"action": "write", "capability_id": "shell.execute"},
                {"success": False, "exit_code": 3, "changed_files": ["a.py"]},
            )
            stored = runtime._store.load(task_id)
            recorded = [e for e in stored.get("events", []) if e.get("type") == "execution"]
            assert recorded[-1]["result"]["observation"]["exit_code"] == 3

    def test_a_boolean_exit_code_is_not_mistaken_for_a_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = make_runtime(tmp, lambda **kw: {"success": True})
            task_id = planned_task(runtime)
            runtime.record_execution(
                task_id,
                {"action": "write", "capability_id": "filesystem.write"},
                {"success": True, "exit_code": True, "changed_files": ["a.py"]},
            )
            stored = runtime._store.load(task_id)
            recorded = [e for e in stored.get("events", []) if e.get("type") == "execution"]
            assert recorded[-1]["result"]["observation"]["exit_code"] is None

    def test_evidence_only_result_is_treated_as_a_claimed_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = make_runtime(tmp, lambda **kw: {"success": True})
            task_id = planned_task(runtime)
            runtime.record_execution(
                task_id,
                {"action": "write"},
                {"success": True, "evidence": {"files_created": ["a.py"]}},
            )
            stored = runtime._store.load(task_id)
            recorded = [e for e in stored.get("events", []) if e.get("type") == "execution"]
            assert recorded[-1]["result"]["observation"]["attested_by"] == RUNTIME_ATTESTOR


class TestTheGateIsActuallyWired:
    def test_engine_module_imports_the_attestation_gate(self):
        import runtime.core.engine as engine_module

        source = open(engine_module.__file__, encoding="utf-8").read()
        assert "attestation" in source, "engine must depend on the attestation gate"

    def test_stamped_evidence_grades_as_tool_attested(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = make_runtime(tmp, lambda **kw: {"success": True})
            task_id = planned_task(runtime)
            runtime.record_execution(
                task_id,
                {"action": "write", "capability_id": "filesystem.write"},
                {"success": True, "changed_files": ["a.py"]},
            )
            stored = runtime._store.load(task_id)
            recorded = [e for e in stored.get("events", []) if e.get("type") == "execution"]
            assert grade_evidence([recorded[-1]["result"]["observation"]]).value == "TOOL_ATTESTED"

    def test_a_read_only_result_alone_never_grades_attested(self):
        """The gate must not be satisfiable by claiming nothing happened."""
        with tempfile.TemporaryDirectory() as tmp:
            runtime = make_runtime(tmp, lambda **kw: {"success": True})
            task_id = planned_task(runtime)
            runtime.record_execution(task_id, {"action": "think"}, {"success": True})
            stored = runtime._store.load(task_id)
            recorded = [e for e in stored.get("events", []) if e.get("type") == "execution"]
            assert grade_evidence([recorded[-1]["result"]]).value == "SELF_REPORTED"


class TestStampingCannotBeSilentlyDisabled:
    """Prove the wiring is load-bearing rather than decorative."""

    def test_removing_the_stamp_would_leave_evidence_unattested(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = make_runtime(tmp, lambda **kw: {"success": True})
            task_id = planned_task(runtime)
            unstamped = {"success": True, "changed_files": ["a.py"]}
            # What record_execution would store if the stamp were removed.
            assert grade_evidence([unstamped]).value == "SELF_REPORTED"
            # What it actually stores.
            runtime.record_execution(
                task_id,
                {"action": "write", "capability_id": "filesystem.write"},
                {"success": True, "changed_files": ["a.py"]},
            )
            stored = runtime._store.load(task_id)
            recorded = [e for e in stored.get("events", []) if e.get("type") == "execution"]
            assert grade_evidence([recorded[-1]["result"]["observation"]]).value == "TOOL_ATTESTED"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

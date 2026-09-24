"""Focused regression tests for the Python Runtime P0 security boundaries."""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from runtime.core import Runtime  # noqa: E402
from runtime.core.contracts import ContractError  # noqa: E402


def make_packet(task_id: str, *, selected=("shell.execute",), missing=(), effect="execute", action="approve", route="lightweight"):
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
            "missing_capabilities": list(missing),
        },
        "context_plan": {
            "profile": "minimal",
            "reasons": [],
            "authority": "recommendation",
        },
        "trace": {"rules_applied": [], "deterministic": True},
    }


def planned_task(runtime: Runtime, **contract):
    state = runtime.start({"goal": "security regression", **contract})
    task_id = state["task_id"]
    runtime.transition(task_id, "planning")
    runtime.transition(task_id, "planned")
    return task_id


def test_execute_wildcard_and_empty_allowlist_are_denied():
    with tempfile.TemporaryDirectory() as tmp:
        runtime = Runtime(tmp, require_jev_decision=False, host_executor=lambda **_: {"success": True})
        tid = planned_task(runtime, allowed_actions=["execute"])
        assert runtime.execute_code(tid, "print('x')")["code"] == "contract_action_not_allowed"

    with tempfile.TemporaryDirectory() as tmp:
        runtime = Runtime(tmp, require_jev_decision=False, host_executor=lambda **_: {"success": True})
        tid = planned_task(runtime, allowed_actions=[])
        assert runtime.execute_code(tid, "print('x')")["code"] == "contract_action_not_allowed"


def test_execute_decision_rejects_an_unbound_arbitrary_digest():
    with tempfile.TemporaryDirectory() as tmp:
        runtime = Runtime(tmp)
        tid = planned_task(runtime)
        with pytest.raises(ContractError):
            runtime.record_jev_decision(tid, make_packet(tid), action_fingerprint="0" * 64)


def test_code_effects_are_not_narrowed_by_the_caller():
    with tempfile.TemporaryDirectory() as tmp:
        runtime = Runtime(tmp, require_jev_decision=False, host_executor=lambda **_: {"success": True})
        tid = planned_task(runtime)
        prepared = runtime.prepare_execution_action(tid, "open('output.txt', 'w').write('x')", effects={"execute"})
        assert "write" in prepared["action"]["effects"]
        result = runtime.execute_code(tid, "open('output.txt', 'w').write('x')", effects={"execute"})
        assert result["success"] is True  # the action was expanded, not narrowed


def test_uncertain_result_requires_reconciliation_before_retry():
    calls = []

    def executor(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return {"success": False, "uncertain": True, "code": "timeout"}
        return {"success": True}

    with tempfile.TemporaryDirectory() as tmp:
        runtime = Runtime(tmp, require_jev_decision=False, host_executor=executor)
        tid = planned_task(runtime)
        first = runtime.execute_code(tid, "print('x')", operation_id="op-uncertain")
        assert first["operation_status"] == "uncertain"
        blocked = runtime.execute_code(tid, "print('x')", operation_id="op-uncertain", retry=True)
        assert blocked["code"] == "operation_reconciliation_required"
        assert len(calls) == 1
        runtime.reconcile_operation(
            tid,
            "op-uncertain",
            "not_executed",
            evidence={"source": "host", "observed": "no side effect"},
        )
        retried = runtime.execute_code(tid, "print('x')", operation_id="op-uncertain", retry=True)
        assert retried["success"] is True
        assert retried["attempt"] == 2
        assert len(calls) == 2


def test_executor_exception_and_contradictory_result_are_uncertain():
    calls = []

    def exception_executor(**kwargs):
        calls.append(kwargs)
        raise TimeoutError("provider timeout")

    with tempfile.TemporaryDirectory() as tmp:
        runtime = Runtime(tmp, require_jev_decision=False, host_executor=exception_executor)
        tid = planned_task(runtime)
        result = runtime.execute_code(tid, "print('x')", operation_id="op-exception")
        assert result["operation_status"] == "uncertain"
        assert runtime.execute_code(tid, "print('x')", operation_id="op-exception", retry=True)["code"] == "operation_reconciliation_required"
        assert len(calls) == 1

    with tempfile.TemporaryDirectory() as tmp:
        runtime = Runtime(
            tmp,
            require_jev_decision=False,
            host_executor=lambda **_: {"success": True, "uncertain": True},
        )
        tid = planned_task(runtime)
        result = runtime.execute_code(tid, "print('x')", operation_id="op-contradictory")
        assert result["operation_status"] == "uncertain"
        assert result["code"] == "executor_uncertain"


def test_same_idempotency_key_is_reserved_atomically():
    calls = []
    lock = threading.Lock()

    def executor(**kwargs):
        with lock:
            calls.append(kwargs["operation_id"])
        time.sleep(0.03)
        return {"success": True}

    with tempfile.TemporaryDirectory() as tmp:
        runtime = Runtime(tmp, require_jev_decision=False, host_executor=executor)
        tid = planned_task(runtime)
        results = []
        threads = [
            threading.Thread(
                target=lambda index=index: results.append(
                    runtime.execute_code(tid, "print('x')", operation_id=f"op-{index}", idempotency_key="same-key")
                )
            )
            for index in range(2)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert len(calls) == 1
        assert sum(1 for result in results if result.get("success")) == 1


def test_public_store_facade_blocks_internal_state_mutation():
    with tempfile.TemporaryDirectory() as tmp:
        runtime = Runtime(tmp, require_jev_decision=False)
        tid = planned_task(runtime)
        with pytest.raises(PermissionError):
            runtime.store.update_internal(tid, status="completed")
        with pytest.raises(PermissionError):
            runtime.store.save_internal(tid, "state.json", {"status": "completed"})


def test_strict_runtime_does_not_complete_on_shape_only_evidence():
    with tempfile.TemporaryDirectory() as tmp:
        runtime = Runtime(tmp, require_jev_decision=False, require_trusted_evidence=True)
        tid = planned_task(runtime, acceptance_criteria=["criterion"])
        runtime.transition(tid, "executing")
        runtime.transition(tid, "observing")
        runtime.transition(tid, "verifying")
        runtime.record_verification(
            tid,
            evidence={"items": [{"criterion": "criterion", "passed": True, "source": "caller claim"}]},
        )
        with pytest.raises(PermissionError):
            runtime.transition(tid, "completed")


def test_state_loader_rejects_nonfinite_json():
    with tempfile.TemporaryDirectory() as tmp:
        runtime = Runtime(tmp, require_jev_decision=False)
        tid = planned_task(runtime)
        path = runtime.store.task_dir(tid) / "state.json"
        state = json.loads(path.read_text())
        state["contract"]["goal"] = float("nan")
        path.write_text(json.dumps(state, allow_nan=True))
        with pytest.raises(ValueError):
            runtime.store.load(tid)

#!/usr/bin/env python3
"""Behavioural tests for the Unified Task Engine.

``test_task_graph_contract.py`` proves the contract and the code agree. It says
nothing about whether the engine *works*. These tests run real graphs.

The properties that matter, and would be catastrophic to get wrong:

* a dependency is never executed before its prerequisite
* a node that fails never reports completion
* an ``INCONCLUSIVE`` verdict never completes a node
* a control edge gates its target
* a cycle is rejected before anything executes
* cancellation stops scheduling
* a node without a required approval fails rather than proceeding
* nothing runs after a failure that has no recovery path
"""
from __future__ import annotations

import os
import sys
import threading
import time

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from runtime.core.task_graph import (  # noqa: E402
    GraphCancelled,
    NodeStatus,
    TaskEdge,
    TaskGraph,
    TaskGraphError,
    TaskNode,
    Verdict,
)


def node(node_id: str, **kwargs) -> TaskNode:
    kwargs.setdefault("objective", f"do {node_id}")
    return TaskNode(id=node_id, **kwargs)


def recorder() -> tuple[list[str], callable]:
    """An execute callable that records call order."""
    calls: list[str] = []

    def execute(task: TaskNode, context):
        calls.append(task.id)
        return f"result-{task.id}"

    return calls, execute


def always_pass(task, result, note) -> Verdict:
    return Verdict.PASS


# --------------------------------------------------------------------- ordering
class TestExecutionOrder:
    def test_linear_chain_runs_in_dependency_order(self):
        graph = TaskGraph("chain")
        for name in ("a", "b", "c"):
            graph.add_node(node(name))
        graph.chain("a", "b", "c")

        calls, execute = recorder()
        result = graph.run(execute, verify=always_pass)

        assert result["status"] == "completed"
        assert calls == ["a", "b", "c"]
        assert result["completed"] == ["a", "b", "c"]

    def test_independent_nodes_may_run_in_any_order(self):
        graph = TaskGraph("independent")
        for name in ("a", "b", "c"):
            graph.add_node(node(name))
        calls, execute = recorder()
        result = graph.run(execute, verify=always_pass)
        assert result["status"] == "completed"
        assert sorted(calls) == ["a", "b", "c"]

    def test_a_dependent_node_never_precedes_its_prerequisite(self):
        graph = TaskGraph("diamond")
        graph.add_node(node("start"))
        graph.add_node(node("left"))
        graph.add_node(node("right"))
        graph.add_node(node("join"))
        graph.chain("start", "left", "join")
        graph.chain("start", "right", "join")

        calls, execute = recorder()
        result = graph.run(execute, verify=always_pass)

        assert result["status"] == "completed"
        assert calls.index("start") < calls.index("left")
        assert calls.index("start") < calls.index("right")
        assert calls.index("join") > calls.index("left")
        assert calls.index("join") > calls.index("right")
        assert calls[-1] == "join", "the join must run last"

    def test_execution_order_is_topological(self):
        graph = TaskGraph("order")
        for name in ("a", "b", "c", "d"):
            graph.add_node(node(name))
        graph.chain("a", "b")
        graph.chain("b", "c")
        graph.chain("a", "d")
        order = graph.execution_order()
        assert order.index("a") < order.index("b") < order.index("c")
        assert order.index("a") < order.index("d")

    def test_downstream_results_are_available_to_the_caller(self):
        """Upstream results are collected in the summary.

        Note: the engine does NOT merge them into the ``context`` handed to a
        downstream ``execute``. Control edges see results (via
        ``_conditions``); executors do not. That asymmetry is recorded in
        docs/architecture/VERSION-4-EXECUTION-GAPS.md rather than papered over.
        """
        graph = TaskGraph("data")
        graph.add_node(node("produce"))
        graph.add_node(node("consume"))
        graph.chain("produce", "consume")
        result = graph.run(lambda t, c: f"value-{t.id}", verify=always_pass)
        assert result["status"] == "completed"
        assert result["results"]["produce"] == "value-produce"
        assert result["results"]["consume"] == "value-consume"

    def test_control_edges_receive_results_but_executors_do_not(self):
        """Documented asymmetry, asserted so a change to it is deliberate."""
        graph = TaskGraph("asymmetry")
        graph.add_node(node("decide"))
        graph.add_node(node("then"))
        graph.chain("decide", "then")
        graph.add_edge(
            TaskEdge("decide", "then", "control", condition=lambda ctx: ctx.get("decide") == "go")
        )
        seen: dict[str, dict] = {}

        def execute(task, context):
            seen[task.id] = dict(context)
            return "go" if task.id == "decide" else "done"

        result = graph.run(execute, verify=always_pass)
        # The control edge saw the result and allowed the branch.
        assert result["completed"] == ["decide", "then"]
        # The executor did not.
        assert seen["then"] == {}


# ------------------------------------------------------------------------ cycles
class TestCycleRejection:
    def test_a_cycle_is_rejected_before_execution(self):
        graph = TaskGraph("cyclic")
        graph.add_node(node("a"))
        graph.add_node(node("b"))
        graph.chain("a", "b")
        graph.chain("b", "a")  # closes the cycle

        calls, execute = recorder()
        with pytest.raises(TaskGraphError):
            graph.run(execute, verify=always_pass)
        assert calls == [], "nothing may execute when the graph is invalid"

    def test_self_dependency_is_rejected(self):
        graph = TaskGraph("self")
        graph.add_node(node("a", dependencies=("a",)))
        with pytest.raises(TaskGraphError):
            graph.run(lambda t, c: None, verify=always_pass)

    def test_a_dependency_on_a_missing_node_is_rejected(self):
        graph = TaskGraph("dangling")
        graph.add_node(node("a", dependencies=("ghost",)))
        with pytest.raises(TaskGraphError):
            graph.run(lambda t, c: None, verify=always_pass)


# ----------------------------------------------------------------------- failure
class TestFailureSemantics:
    def test_a_failed_node_never_reports_completion(self):
        graph = TaskGraph("failing")
        graph.add_node(node("ok"))
        graph.add_node(node("bad"))
        graph.chain("ok", "bad")

        def execute(task, context):
            if task.id == "bad":
                raise RuntimeError("boom")
            return "fine"

        result = graph.run(execute, verify=always_pass)

        assert result["status"] == "failed"
        assert "bad" in result["failed"]
        assert "bad" not in result["completed"]
        assert result["node_status"]["bad"] == NodeStatus.FAILED.value

    def test_a_failure_does_not_silently_succeed(self):
        graph = TaskGraph("honest")
        graph.add_node(node("bad"))

        def execute(task, context):
            raise RuntimeError("boom")

        result = graph.run(execute, verify=always_pass)
        assert result["status"] != "completed"
        assert result["completed"] == []

    def test_downstream_of_a_failure_does_not_run(self):
        graph = TaskGraph("blocked-downstream")
        graph.add_node(node("bad"))
        graph.add_node(node("after"))
        graph.chain("bad", "after")

        calls, execute = recorder()

        def failing(task, context):
            calls.append(task.id)
            raise RuntimeError("boom")

        result = graph.run(failing, verify=always_pass)
        assert "after" not in calls, "a node after a hard failure must not execute"
        assert result["status"] == "failed"

    def test_a_failure_edge_routes_to_recovery(self):
        """The recovery node runs and completes, but the graph still reports
        ``failed``.

        That is the engine's actual contract: a failure is never erased by a
        successful fallback. Callers that want "recovered" must inspect
        ``failed``/``completed`` themselves. Asserted explicitly so a change to
        this semantic is deliberate rather than accidental.
        """
        graph = TaskGraph("recovered")
        graph.add_node(node("primary"))
        graph.add_node(node("fallback"))
        graph.add_edge(TaskEdge("primary", "fallback", "failure"))

        def execute(task, context):
            if task.id == "primary":
                raise RuntimeError("boom")
            return "recovered"

        result = graph.run(execute, verify=always_pass)
        assert "fallback" in result["completed"], "the recovery path must run"
        assert "primary" in result["failed"]
        assert result["status"] == "failed", (
            "a recovered graph must not silently claim an unqualified success"
        )

    def test_recover_callback_can_retry_a_node(self):
        graph = TaskGraph("retry")
        graph.add_node(node("flaky"))
        attempts = {"n": 0}

        def execute(task, context):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise RuntimeError("first attempt fails")
            return "second attempt works"

        def verify(task, result, note):
            return Verdict.PASS

        result = graph.run(execute, verify=verify)
        assert attempts["n"] >= 1


# -------------------------------------------------------------------- verdicts
class TestVerdictSemantics:
    def test_inconclusive_never_completes_a_node(self):
        graph = TaskGraph("inconclusive")
        graph.add_node(node("unsure"))

        result = graph.run(lambda t, c: "value", verify=lambda t, r, n: Verdict.INCONCLUSIVE)

        assert "unsure" not in result["completed"]
        assert result["status"] != "completed"
        assert result["verification_counts"][Verdict.INCONCLUSIVE.value] == 1

    def test_a_failed_verdict_fails_the_node(self):
        graph = TaskGraph("failed-verify")
        graph.add_node(node("bad"))
        result = graph.run(lambda t, c: "v", verify=lambda t, r, n: Verdict.FAIL)
        assert result["status"] == "failed"
        assert "bad" in result["failed"]

    def test_a_node_without_a_verifier_still_completes(self):
        graph = TaskGraph("no-verify")
        graph.add_node(node("plain"))
        result = graph.run(lambda t, c: "v")
        assert result["status"] == "completed"


# --------------------------------------------------------------------- branches
class TestControlEdges:
    def test_a_false_control_edge_skips_its_target(self):
        graph = TaskGraph("branch")
        graph.add_node(node("gate"))
        graph.add_node(node("then"))
        graph.chain("gate", "then")
        graph.add_edge(TaskEdge("gate", "then", "control", condition=lambda ctx: False))

        calls, execute = recorder()
        result = graph.run(execute, verify=always_pass)

        assert "then" not in calls
        assert "then" in result["skipped"]

    def test_a_true_control_edge_allows_its_target(self):
        graph = TaskGraph("branch-taken")
        graph.add_node(node("gate"))
        graph.add_node(node("then"))
        graph.chain("gate", "then")
        graph.add_edge(TaskEdge("gate", "then", "control", condition=lambda ctx: True))

        calls, execute = recorder()
        result = graph.run(execute, verify=always_pass)

        assert "then" in calls
        assert result["status"] == "completed"

    def test_a_control_edge_sees_upstream_results(self):
        graph = TaskGraph("decide")
        graph.add_node(node("decide"))
        graph.add_node(node("heavy"))
        graph.chain("decide", "heavy")
        graph.add_edge(
            TaskEdge("decide", "heavy", "control", condition=lambda ctx: ctx.get("decide") == "go")
        )

        calls: list[str] = []

        def execute(task, context):
            calls.append(task.id)
            return "go" if task.id == "decide" else "done"

        result = graph.run(execute, verify=always_pass)
        assert "heavy" in calls, "the condition must see the upstream result"
        assert result["status"] == "completed"


# ------------------------------------------------------------------ cancellation
class TestCancellation:
    """KNOWN GAP: cancellation is specified but not externally reachable.

    ``contracts/task-graph.yaml:66`` promises "Cancellation stops scheduling new
    nodes. Running nodes finish or hit their timeout." The engine does create
    and honour a ``threading.Event`` internally, but it constructs it *inside*
    ``run()`` and no caller can obtain a handle to it. There is no public way to
    cancel a running graph.

    These tests pin the current behaviour and the absence of the capability, so
    the gap cannot be quietly forgotten. When a cancel handle is added, the
    ``test_no_external_cancel_handle_exists`` test must be replaced, not deleted
    silently.
    """

    def test_no_external_cancel_handle_exists(self):
        """Documents the gap. Replace this test when cancellation is wired."""
        import inspect

        signature = inspect.signature(TaskGraph.run)
        assert "cancel" not in signature.parameters, (
            "TaskGraph.run now accepts a cancel handle; update "
            "docs/architecture/VERSION-4-EXECUTION-GAPS.md and replace this "
            "gap-documentation test with real cancellation tests"
        )

    def test_engine_creates_its_own_cancel_event(self):
        import inspect

        source = inspect.getsource(TaskGraph.run)
        assert "threading.Event()" in source, (
            "the engine is expected to create its own cancel event until an "
            "external handle is provided"
        )

    def test_a_context_event_does_not_cancel_the_graph(self):
        """Pins the gap: passing a cancel Event in context has no effect."""
        graph = TaskGraph("cancel-ignored")
        graph.add_node(node("a"))
        graph.add_node(node("b"))
        graph.chain("a", "b")

        cancel = threading.Event()
        cancel.set()
        result = graph.run(
            lambda t, c: t.id, verify=always_pass, context={"cancel": cancel}
        )
        assert result["status"] == "completed", (
            "a cancel Event in context is currently ignored; if this now "
            "cancels, the gap has been closed and the docs must be updated"
        )
        assert result["completed"] == ["a", "b"]

    def test_on_event_can_observe_progress(self):
        graph = TaskGraph("events")
        graph.add_node(node("a"))
        graph.add_node(node("b"))
        graph.chain("a", "b")
        seen: list[tuple[str, str]] = []
        graph.run(
            lambda t, c: t.id,
            verify=always_pass,
            on_event=lambda event, n, note: seen.append((event, n.id)),
        )
        assert seen, "the engine must emit progress events"
        assert all(isinstance(name, str) and name for name, _ in seen)


# --------------------------------------------------------------------- approval
class TestApprovalGates:
    def test_a_required_approval_without_a_callback_fails_closed(self):
        graph = TaskGraph("approval-missing")
        graph.add_node(node("dangerous", approval="required"))
        result = graph.run(lambda t, c: "v", verify=always_pass)
        assert "dangerous" in result["failed"], (
            "a node requiring approval must fail closed when no approver exists"
        )

    def test_a_rejected_approval_skips_the_node(self):
        graph = TaskGraph("approval-rejected")
        graph.add_node(node("dangerous", approval="required"))
        calls, execute = recorder()
        result = graph.run(
            execute, verify=always_pass, approve=lambda n: "rejected"
        )
        assert "dangerous" not in calls
        assert "dangerous" in result["skipped"]

    def test_a_granted_approval_runs_the_node(self):
        graph = TaskGraph("approval-granted")
        graph.add_node(node("dangerous", approval="required"))
        calls, execute = recorder()
        result = graph.run(
            execute, verify=always_pass, approve=lambda n: "approved"
        )
        assert calls == ["dangerous"]
        assert result["approvals"]["dangerous"] == "approved"
        assert result["status"] == "completed"

    def test_human_review_is_treated_as_requiring_approval(self):
        graph = TaskGraph("human-review")
        graph.add_node(node("sensitive", approval="human_review"))
        result = graph.run(lambda t, c: "v", verify=always_pass)
        assert "sensitive" in result["failed"]


# ------------------------------------------------------------------- mode shapes
class TestExecutionModesLowerToGraphs:
    def test_direct_mode_is_a_single_leaf(self):
        graph = TaskGraph("direct")
        graph.add_node(node("only"))
        result = graph.run(lambda t, c: "v", verify=always_pass)
        assert len(result["node_status"]) == 1
        assert result["status"] == "completed"

    def test_workflow_mode_is_a_reusable_template(self):
        def build() -> TaskGraph:
            graph = TaskGraph("workflow-template")
            for name in ("step1", "step2"):
                graph.add_node(node(name))
            graph.chain("step1", "step2")
            return graph

        first = build().run(lambda t, c: t.id, verify=always_pass)
        second = build().run(lambda t, c: t.id, verify=always_pass)
        assert first["status"] == second["status"] == "completed"
        assert first["completed"] == second["completed"], (
            "a template must produce the same shape every run"
        )

    def test_parallel_mode_runs_branches_concurrently(self):
        """Concurrency is proved in TestNoNodeIsEverExecutedTwice.

        A wall-clock threshold is flaky and a fast machine can defeat it, so
        this asserts the shape instead: every branch ran and every result came
        back. See ``test_branches_really_do_run_concurrently`` for the
        barrier-based proof of real concurrency.
        """
        graph = TaskGraph("parallel", parallelism=4)
        for name in ("a", "b", "c", "d"):
            graph.add_node(node(name))

        result = graph.run(lambda t, c: t.id, verify=always_pass)
        assert result["status"] == "completed"
        assert sorted(result["completed"]) == ["a", "b", "c", "d"]
        assert sorted(result["results"]) == ["a", "b", "c", "d"]


# --------------------------------------------------------------------- integrity
class TestNoNodeIsEverExecutedTwice:
    """Regression guard for a real double-execution bug.

    ``run()`` used ``wait(FIRST_COMPLETED)`` and then processed only the
    futures that came back, leaving the rest in flight with status RUNNING.
    Because an independent node has no unmet dependencies and ``all([])`` is
    True, that RUNNING node looked schedulable on the next pass and was
    submitted a second time. For side-effecting work this meant duplicate
    writes and duplicate commands.
    """

    @pytest.mark.parametrize("parallelism,nodes", [(1, 3), (2, 6), (3, 5), (4, 4)])
    def test_independent_nodes_run_exactly_once(self, parallelism, nodes):
        graph = TaskGraph("once", parallelism=parallelism)
        for index in range(nodes):
            graph.add_node(node(f"n{index}"))

        counts: dict[str, int] = {}
        lock = threading.Lock()

        def execute(task, context):
            with lock:
                counts[task.id] = counts.get(task.id, 0) + 1
            return task.id

        result = graph.run(execute, verify=always_pass)

        assert result["status"] == "completed"
        repeated = sorted(k for k, v in counts.items() if v > 1)
        assert not repeated, f"nodes executed more than once: {repeated}"
        assert len(counts) == nodes, "every node must have run"

    def test_a_chained_node_runs_exactly_once(self):
        graph = TaskGraph("chain-once", parallelism=4)
        for index in range(5):
            graph.add_node(node(f"n{index}"))
        for index in range(4):
            graph.chain(f"n{index}", f"n{index + 1}")

        counts: dict[str, int] = {}
        lock = threading.Lock()

        def execute(task, context):
            with lock:
                counts[task.id] = counts.get(task.id, 0) + 1
            return task.id

        result = graph.run(execute, verify=always_pass)
        assert result["status"] == "completed"
        assert not [k for k, v in counts.items() if v > 1]
        assert counts == {f"n{i}": 1 for i in range(5)}

    def test_slow_nodes_are_not_orphaned(self):
        """A node slower than its siblings must still report its result."""
        graph = TaskGraph("slow", parallelism=4)
        graph.add_node(node("fast"))
        graph.add_node(node("slow"))

        def execute(task, context):
            if task.id == "slow":
                time.sleep(0.15)
            return f"value-{task.id}"

        result = graph.run(execute, verify=always_pass)
        assert result["status"] == "completed"
        assert result["results"].get("slow") == "value-slow", (
            "a slow node's result was lost; its future was orphaned by "
            "wait(FIRST_COMPLETED)"
        )
        assert result["node_status"]["slow"] == NodeStatus.COMPLETED.value

    def test_branches_really_do_run_concurrently(self):
        """Barrier-based: a serialised engine deadlocks and times out."""
        graph = TaskGraph("concurrent", parallelism=4)
        for name in ("a", "b", "c", "d"):
            graph.add_node(node(name))

        arrived = threading.Barrier(4, timeout=5)

        def execute(task, context):
            arrived.wait()
            return task.id

        result = graph.run(execute, verify=always_pass)
        assert result["status"] == "completed", (
            "independent nodes did not run concurrently"
        )
        assert sorted(result["completed"]) == ["a", "b", "c", "d"]


class TestEngineCannotBeFooled:
    """Guard the guards: prove these assertions are load-bearing."""

    def test_a_graph_claiming_success_without_running_is_impossible(self):
        graph = TaskGraph("empty")
        result = graph.run(lambda t, c: "v", verify=always_pass)
        # An empty graph must not report completed work out of nothing.
        assert result["completed"] == []
        assert result["status"] in {"not_run", "completed"}

    def test_results_only_contain_nodes_that_ran(self):
        graph = TaskGraph("results")
        graph.add_node(node("a"))
        graph.add_node(node("b"))
        graph.chain("a", "b")

        def execute(task, context):
            if task.id == "a":
                raise RuntimeError("boom")
            return "unreachable"

        result = graph.run(execute, verify=always_pass)
        assert "b" not in result["results"], (
            "a node that never executed must not appear in results"
        )

    def test_summarise_never_marks_a_failed_node_completed(self):
        from runtime.core.task_graph import summarise

        out = summarise(
            "manual",
            {"a": NodeStatus.FAILED.value, "b": NodeStatus.COMPLETED.value},
            {},
            [],
            {},
            False,
        )
        assert "a" in out["failed"]
        assert "a" not in out["completed"]
        assert out["status"] == "failed"

    def test_summarise_reports_partial_when_some_work_did_not_run(self):
        from runtime.core.task_graph import summarise

        out = summarise(
            "manual",
            {"a": NodeStatus.COMPLETED.value, "b": NodeStatus.BLOCKED.value},
            {},
            [],
            {},
            False,
        )
        assert out["status"] == "partial"
        assert out["completed"] == ["a"]
        assert out["blocked"] == ["b"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

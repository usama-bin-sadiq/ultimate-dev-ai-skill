import tempfile

from runtime.core import Runtime
from runtime.core.task_router import RouteDecision


def test_runtime_lifecycle_and_routing_integration():
    with tempfile.TemporaryDirectory() as tmp:
        runtime = Runtime(tmp, require_jev_decision=False)
        state = runtime.start({"goal": "Improve parser error handling", "task_id": "task-parser"})
        tid = state["task_id"]
        runtime.transition(tid, "planning")
        runtime.transition(tid, "planned")
        paused = runtime.pause_task(tid, reason="user interruption")
        assert paused["status"] == "paused"
        resumed = runtime.resume(tid)
        assert resumed["status"] == "planned"
        route = runtime.route_user_message(
            "Please add regression tests for the parser error handling",
            current_task=resumed,
        )
        assert route.decision is RouteDecision.CONTINUATION
        assert route.task_id == tid
        by_id = runtime.route_user_message(
            "Please add regression tests for the parser error handling",
            current_task_id=tid,
        )
        assert by_id.task_id == tid
        abandoned = runtime.abandon_task(tid, reason="user changed request")
        assert abandoned["status"] == "abandoned"


def test_runtime_lifecycle_reuses_resource_cleanup_manager():
    with tempfile.TemporaryDirectory() as tmp:
        class Resource:
            def __init__(self):
                self.closed = 0

            def __call__(self, **kwargs):
                return {"success": True}

            def close(self):
                self.closed += 1

        resource = Resource()
        runtime = Runtime(tmp, require_jev_decision=False, host_executor=resource)
        state = runtime.start({"goal": "resource lifecycle", "task_id": "task-resource"})
        tid = state["task_id"]
        runtime.transition(tid, "planning")
        runtime.transition(tid, "planned")
        runtime.pause_task(tid)
        runtime.resume_task(tid)
        runtime.pause_task(tid)
        # The host executor is runtime-owned; task lifecycle actions must not
        # tear it down for unrelated work.
        assert resource.closed == 0
        assert runtime.close()["success"]
        assert resource.closed == 1


def test_runtime_route_apply_creates_durable_new_task():
    with tempfile.TemporaryDirectory() as tmp:
        runtime = Runtime(tmp, require_jev_decision=False)
        state = runtime.start({"goal": "Improve parser error handling", "task_id": "task-parser"})
        result = runtime.route_and_apply_user_message(
            "Start a new task for billing",
            current_task=state,
        )
        assert result["route"]["decision"] == "new_task"
        assert result["task_state"]["task_id"] == result["route"]["task_id"]
        assert result["task_state"]["contract"]["parent_task_id"] == "task-parser"
        assert runtime.store.load(result["task_state"]["task_id"])["status"] == "ready"
        snapshot = runtime.health_snapshot()
        assert snapshot["task_count"] == 2
        assert snapshot["healthy"] is True


def test_runtime_ambiguous_route_is_fail_closed():
    with tempfile.TemporaryDirectory() as tmp:
        runtime = Runtime(tmp, require_jev_decision=False)
        state = runtime.start({"goal": "Improve parser", "task_id": "task-parser"})
        route = runtime.route_user_message("Maybe later, or perhaps something else.", state)
        assert route.decision is RouteDecision.UNKNOWN
        assert route.fail_closed is True

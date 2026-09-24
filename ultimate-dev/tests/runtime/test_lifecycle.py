"""Tests for the dependency-free task lifecycle controller."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from runtime.core.lifecycle import (  # noqa: E402
    EvidencePreservationError,
    InvalidLifecycleTransition,
    LifecycleController,
    LifecycleHookError,
    ResourceCleanupError,
    ResourceCleanupManager,
    StaleOperationError,
)
from runtime.core.state import TaskStore  # noqa: E402


class CountingResource:
    def __init__(self, *, fail_close: bool = False, fail_abort: bool = False) -> None:
        self.close_calls = 0
        self.abort_calls = 0
        self.fail_close = fail_close
        self.fail_abort = fail_abort

    def close(self) -> None:
        self.close_calls += 1
        if self.fail_close:
            raise RuntimeError("close failed")

    def abort(self) -> None:
        self.abort_calls += 1
        if self.fail_abort:
            raise RuntimeError("abort failed")


class MemoryStore:
    """Small injected store used to prove the controller has no engine dependency."""

    def __init__(self, status: str = "executing") -> None:
        self.state = {
            "task_id": "task-lifecycle",
            "schema_version": "2.5",
            "status": status,
            "revision": 0,
            "contract": {"goal": "exercise lifecycle"},
            "verification": {"evidence_refs": []},
            "events": [],
        }
        self.operations: dict[str, dict] = {}
        self.checkpoints: list[dict] = []
        self.evidence = {"items": [{"result": "kept"}]}

    def load(self, task_id: str):
        assert task_id == self.state["task_id"]
        return dict(self.state)

    def update_internal(self, task_id: str, **changes):
        assert task_id == self.state["task_id"]
        self.state.update(changes)
        self.state["revision"] += 1
        return dict(self.state)

    def append_event(self, task_id: str, event):
        assert task_id == self.state["task_id"]
        record = dict(event)
        record.setdefault("event_id", f"event-{len(self.state['events']) + 1}")
        self.state["events"].append(record)
        self.state["revision"] += 1
        return dict(self.state)

    def checkpoint(self, task_id: str):
        assert task_id == self.state["task_id"]
        snapshot = dict(self.state)
        self.checkpoints.append(snapshot)
        return f"checkpoints/{len(self.checkpoints)}.json"

    def save_operation(self, operation_id: str, operation: dict) -> None:
        self.operations[operation_id] = dict(operation)

    def list_operations(self, task_id: str):
        assert task_id == self.state["task_id"]
        return [dict(operation) for operation in self.operations.values()]

    def update_operation(self, task_id: str, operation_id: str, mutator):
        assert task_id == self.state["task_id"]
        value = mutator(dict(self.operations[operation_id]))
        self.operations[operation_id] = value
        return dict(value)


class LifecycleControllerTests(unittest.TestCase):
    def make_task(self, store: TaskStore, *, status: str = "planned") -> str:
        state = store.create({"goal": "lifecycle", "task_id": "task-lifecycle"})
        task_id = state["task_id"]
        store.update_internal(task_id, status=status)
        store.save(
            task_id,
            "evidence/proof.json",
            {"items": [{"criterion": "proof", "passed": True}], "message": "keep me"},
        )
        return task_id

    def test_hard_interruption_marks_operation_uncertain_and_aborts_once(self):
        store = MemoryStore("executing")
        resource = CountingResource()
        resources = ResourceCleanupManager()
        resources.register(resource, "browser")
        store.save_operation("op-live", {
            "operation_id": "op-live",
            "task_id": store.state["task_id"],
            "status": "running",
            "lease_expires_at_epoch": 0,
        })
        checkpoint_events = []
        events = []
        controller = LifecycleController(
            store,
            resources=resources,
            checkpoint_hook=lambda path: checkpoint_events.append(path),
            event_hook=lambda event: events.append(event),
        )

        state = controller.interrupt("task-lifecycle", reason="process killed")

        self.assertEqual(state["status"], "interrupted")
        self.assertEqual(store.operations["op-live"]["status"], "uncertain")
        self.assertEqual(resource.abort_calls, 1)
        self.assertEqual(resource.close_calls, 0)
        self.assertTrue(state["lifecycle"]["hard_interruption"])
        self.assertTrue(any(event.get("action") == "interrupt" for event in store.state["events"]))
        self.assertTrue(any(event.get("type") == "stale_operation_handled" for event in store.state["events"]))
        self.assertEqual(len(events), len(store.state["events"]))

        resumed = controller.resume("task-lifecycle")
        self.assertEqual(resumed["status"], "recovering")
        self.assertEqual(resumed["lifecycle"]["resumed_from"], "interrupted")
        self.assertEqual(resource.abort_calls, 1)

    def test_repeated_pause_resume_preserves_evidence_and_checkpoints(self):
        store = MemoryStore("planned")
        resource = CountingResource()
        resources = ResourceCleanupManager()
        resources.register(resource, "worker")
        controller = LifecycleController(store, resources=resources)

        first_pause = controller.pause("task-lifecycle", reason="user pause")
        self.assertEqual(first_pause["status"], "paused")
        self.assertEqual(first_pause["lifecycle"]["resume_status"], "planned")
        first_resume = controller.resume("task-lifecycle")
        self.assertEqual(first_resume["status"], "planned")
        second_pause = controller.pause("task-lifecycle", reason="pause again")
        self.assertEqual(second_pause["status"], "paused")
        second_resume = controller.resume("task-lifecycle")
        self.assertEqual(second_resume["status"], "planned")

        self.assertEqual(resource.close_calls, 1)
        self.assertEqual(len(store.checkpoints), 4)
        self.assertEqual(store.evidence["items"][0]["result"], "kept")
        actions = [event.get("action") for event in store.state["events"]]
        self.assertEqual(actions.count("pause"), 2)
        self.assertEqual(actions.count("resume"), 2)

    def test_abandon_is_terminal_and_resume_is_rejected(self):
        store = MemoryStore("planned")
        resource = CountingResource()
        controller = LifecycleController(
            store,
            resources=ResourceCleanupManager({"host": resource}),
        )

        state = controller.abandon("task-lifecycle", reason="user abandoned")

        self.assertEqual(state["status"], "abandoned")
        self.assertTrue(state["lifecycle"]["terminal"])
        self.assertEqual(resource.abort_calls, 1)
        self.assertEqual(store.evidence["items"][0]["result"], "kept")
        with self.assertRaises(InvalidLifecycleTransition):
            controller.resume("task-lifecycle")
        with self.assertRaises(InvalidLifecycleTransition):
            controller.pause("task-lifecycle")

    def test_async_resource_cleanup_is_bridged_and_idempotent(self):
        class AsyncResource:
            def __init__(self):
                self.calls = 0

            async def close(self):
                self.calls += 1

        store = MemoryStore("planned")
        resource = AsyncResource()
        controller = LifecycleController(
            store,
            resources=ResourceCleanupManager(async_timeout_seconds=1.0),
        )
        controller.resource_manager.register(resource, "async")
        controller.pause("task-lifecycle")
        controller.cleanup("task-lifecycle", action="close")
        self.assertEqual(resource.calls, 1)
        self.assertEqual(store.state["status"], "paused")

    def test_cleanup_is_idempotent_for_close_and_abort(self):
        store = MemoryStore("planned")
        resource = CountingResource()
        controller = LifecycleController(
            store,
            resources=ResourceCleanupManager({"resource": resource}),
        )

        first = controller.cleanup("task-lifecycle", action="close")
        second = controller.cleanup("task-lifecycle", action="close")
        self.assertTrue(first["cleanup"]["changed"])
        self.assertEqual(second["cleanup"]["changed"], 0)
        self.assertEqual(second["cleanup"]["already_done"], 1)
        self.assertEqual(resource.close_calls, 1)

        # A terminal close is also a terminal abort: do not call a second
        # host primitive after the resource has already been released.
        controller.abort("task-lifecycle")
        self.assertEqual(resource.abort_calls, 0)
        self.assertTrue(store.evidence["items"])

    def test_failure_paths_leave_state_and_evidence_recoverable(self):
        store = MemoryStore("planned")
        resource = CountingResource(fail_abort=True)
        controller = LifecycleController(
            store,
            resources=ResourceCleanupManager({"host": resource}),
        )

        with self.assertRaises(ResourceCleanupError):
            controller.abandon("task-lifecycle")
        self.assertEqual(store.state["status"], "planned")
        self.assertTrue(store.evidence["items"])

        # A cleanup request that explicitly disables preservation fails before
        # invoking a host callback.
        with self.assertRaises(EvidencePreservationError):
            controller.cleanup("task-lifecycle", preserve_evidence=False)
        self.assertEqual(resource.abort_calls, 1)

    def test_checkpoint_hook_failure_prevents_transition(self):
        store = MemoryStore("planned")

        def fail_checkpoint(path):
            raise RuntimeError("checkpoint unavailable")

        controller = LifecycleController(store, checkpoint_hook=fail_checkpoint)
        with self.assertRaises(LifecycleHookError):
            controller.pause("task-lifecycle")
        self.assertEqual(store.state["status"], "planned")
        self.assertEqual(store.evidence["items"][0]["result"], "kept")

    def test_event_and_stale_hook_failures_leave_durable_evidence(self):
        store = MemoryStore("executing")
        store.save_operation("op-event", {
            "operation_id": "op-event",
            "task_id": store.state["task_id"],
            "status": "running",
            "lease_expires_at_epoch": 0,
        })

        def fail_event(event):
            raise RuntimeError("event sink unavailable")

        with self.assertRaises(LifecycleHookError):
            LifecycleController(store, event_hook=fail_event).pause("task-lifecycle")
        self.assertEqual(store.state["status"], "paused")
        self.assertTrue(store.evidence["items"])

        interrupted_store = MemoryStore("executing")
        interrupted_store.save_operation("op-stale", {
            "operation_id": "op-stale",
            "task_id": interrupted_store.state["task_id"],
            "status": "running",
            "lease_expires_at_epoch": 0,
        })

        def fail_stale(operation):
            raise RuntimeError("stale sink unavailable")

        with self.assertRaises(StaleOperationError):
            LifecycleController(interrupted_store, stale_operation_handler=fail_stale).interrupt(
                "task-lifecycle"
            )
        self.assertEqual(interrupted_store.state["status"], "interrupted")
        self.assertTrue(interrupted_store.evidence["items"])

    def test_fresh_resource_manager_honors_persisted_cleanup_marker(self):
        store = MemoryStore("planned")
        first_resource = CountingResource()
        first = LifecycleController(store, resources={"worker": first_resource})
        first.cleanup("task-lifecycle")

        second_resource = CountingResource()
        second = LifecycleController(store, resources={"worker": second_resource})
        report = second.cleanup("task-lifecycle")

        self.assertEqual(first_resource.close_calls, 1)
        self.assertEqual(second_resource.close_calls, 0)
        self.assertEqual(report["cleanup"]["already_done"], 1)

    def test_custom_stale_handler_and_invalid_transition(self):
        store = MemoryStore("planned")
        store.save_operation("op-old", {
            "operation_id": "op-old",
            "task_id": store.state["task_id"],
            "status": "running",
            "lease_expires_at_epoch": 0,
        })
        seen = []

        def handle(operation, reason):
            seen.append((operation["operation_id"], reason))
            return {"operation_id": operation["operation_id"], "status": "cancelled"}

        controller = LifecycleController(store, stale_operation_handler=handle)
        self.assertEqual(controller.recover_stale_operations("task-lifecycle"), 1)
        self.assertEqual(seen, [("op-old", "stale operation")])
        self.assertEqual(store.operations["op-old"]["status"], "cancelled")
        with self.assertRaises(InvalidLifecycleTransition):
            controller.resume("task-lifecycle")

    def test_file_store_round_trip_preserves_lifecycle_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskStore(tmp)
            task_id = self.make_task(store, status="executing")
            controller = LifecycleController(store)
            paused = controller.pause(task_id)
            self.assertEqual(paused["status"], "paused")
            resumed = controller.resume(task_id)
            self.assertEqual(resumed["status"], "executing")
            self.assertEqual(resumed["lifecycle"]["resumed_from"], "paused")
            evidence = Path(tmp) / ".memory" / "ultimate-dev" / "tasks" / task_id / "evidence" / "proof.json"
            self.assertTrue(evidence.exists())
            self.assertEqual(json.loads(evidence.read_text())["message"], "keep me")


if __name__ == "__main__":
    unittest.main()

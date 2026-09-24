"""Contract tests for the dependency-free task/new-question guardrail."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.task_router import (
    RouteDecision,
    RouteMetadata,
    RouteMetadataStore,
    TaskContext,
    TaskRouter,
    TaskRouterError,
)


class TaskRouterTests(unittest.TestCase):
    def setUp(self):
        self.context = TaskContext(
            task_id="task-parser",
            goal="Improve parser error handling",
            summary="Harden the parser and add regression coverage",
            keywords=("parser", "errors"),
            parent_task_id="parent-platform",
        )

    def test_file_store_has_record_and_byte_quotas(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RouteMetadataStore(Path(tmp) / "routes.json", max_records=2, max_bytes=4096)
            for index in range(3):
                store.save(str(index), {"created_at": "2026-09-24T00:00:00Z", "value": index})
            assert len(store._read_document()["routes"]) == 2

    def test_terminal_context_cannot_continue_and_routes_to_new_task(self):
        router = TaskRouter(id_factory=lambda: "task-after-completion")
        context = TaskContext(task_id="task-parser", goal="Improve parser", status="completed")
        result = router.route("Start a new billing task", context, persist=False)
        self.assertIs(result.decision, RouteDecision.NEW_TASK)
        self.assertEqual(result.task_id, "task-after-completion")
        self.assertEqual(result.parent_task_id, "task-parser")

    def test_terminal_context_rejects_explicit_continuation(self):
        router = TaskRouter()
        context = TaskContext(task_id="task-parser", goal="Improve parser", status="abandoned")
        result = router.route("continue", context, explicit_decision="continuation", persist=False)
        self.assertIs(result.decision, RouteDecision.UNKNOWN)
        self.assertIsNone(result.task_id)

    def test_same_task_follow_up_reuses_active_task_and_parent_link(self):
        router = TaskRouter()

        result = router.route(
            "Please add regression tests for the parser error handling",
            self.context,
            persist=False,
        )

        self.assertIs(result.decision, RouteDecision.CONTINUATION)
        self.assertEqual(result.task_id, "task-parser")
        self.assertEqual(result.parent_task_id, "parent-platform")
        self.assertEqual(result.current_task_id, "task-parser")
        self.assertGreaterEqual(result.confidence, 0.72)
        self.assertTrue(result.safe_to_execute)
        self.assertFalse(result.fail_closed)

    def test_unrelated_task_creates_child_with_parent_link(self):
        router = TaskRouter(id_factory=lambda: "task-billing")

        result = router.route(
            "Start a new task to update the billing dashboard",
            self.context,
            persist=False,
        )

        self.assertIs(result.decision, RouteDecision.NEW_TASK)
        self.assertEqual(result.task_id, "task-billing")
        self.assertEqual(result.new_task_id, "task-billing")
        self.assertEqual(result.parent_task_id, "task-parser")
        self.assertNotEqual(result.task_id, self.context.task_id)
        self.assertFalse(result.fail_closed)

    def test_clarification_is_non_executable_and_keeps_current_identity(self):
        router = TaskRouter()

        result = router.route(
            "Can you clarify whether the parser should reject empty input?",
            self.context,
            persist=False,
        )

        self.assertIs(result.decision, RouteDecision.CLARIFICATION)
        self.assertEqual(result.task_id, "task-parser")
        self.assertTrue(result.requires_clarification)
        self.assertTrue(result.fail_closed)
        self.assertFalse(result.safe_to_execute)

    def test_explicit_abandon_never_implicitly_creates_a_replacement(self):
        router = TaskRouter(id_factory=lambda: "must-not-be-created")

        result = router.route(
            "Cancel this task; I no longer need the parser change",
            self.context,
            persist=False,
        )

        self.assertIs(result.decision, RouteDecision.ABANDON)
        self.assertEqual(result.task_id, "task-parser")
        self.assertIsNone(result.new_task_id)
        self.assertEqual(result.parent_task_id, "parent-platform")
        self.assertTrue(result.fail_closed)

    def test_ambiguous_text_fails_closed_without_guessing_a_target(self):
        router = TaskRouter()

        result = router.route(
            "Maybe later, or perhaps something else.",
            self.context,
            persist=False,
        )

        self.assertIs(result.decision, RouteDecision.UNKNOWN)
        self.assertTrue(result.unknown)
        self.assertTrue(result.ambiguous)
        self.assertTrue(result.fail_closed)
        self.assertTrue(result.requires_clarification)
        self.assertIsNone(result.task_id)
        self.assertIsNone(result.parent_task_id)
        self.assertEqual(result.current_task_id, "task-parser")
        self.assertEqual(result.confidence, 0.0)
        self.assertFalse(result.safe_to_execute)

    def test_route_metadata_survives_router_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "routes.json"
            first_router = TaskRouter(storage_path=path, id_factory=lambda: "task-restart")
            first = first_router.route(
                "Start a new task to update the billing dashboard",
                self.context,
            )

            # A fresh process-like router must recover the exact generated ID
            # and parent link instead of allocating a second task.
            second_router = TaskRouter(
                storage_path=path,
                id_factory=lambda: "different-id-on-restart",
            )
            second = second_router.route(
                "Start a new task to update the billing dashboard",
                self.context,
            )

            self.assertEqual(second.to_dict(), first.to_dict())
            self.assertEqual(second.task_id, "task-restart")
            self.assertEqual(second.parent_task_id, "task-parser")
            self.assertTrue(second.persisted)

            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "1.0")
            record = next(iter(payload["routes"].values()))
            self.assertEqual(record["decision"], "new_task")
            self.assertEqual(record["task_id"], "task-restart")
            self.assertEqual(record["parent_task_id"], "task-parser")

    def test_ambiguous_route_metadata_is_also_restart_safe_and_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "routes.json"
            first_router = TaskRouter(storage_path=path)
            first = first_router.route(
                "Maybe later, or perhaps something else.",
                self.context,
            )
            second_router = TaskRouter(storage_path=path)
            second = second_router.route(
                "Maybe later, or perhaps something else.",
                self.context,
            )
            self.assertEqual(second.to_dict(), first.to_dict())
            self.assertIs(second.decision, RouteDecision.UNKNOWN)
            self.assertTrue(second.fail_closed)
            self.assertIsNone(second.task_id)

    def test_persistence_hooks_are_called_and_survive_recreation(self):
        records = {}

        def load_hook(key):
            return records.get(key)

        def save_hook(key, metadata):
            records[key] = dict(metadata)

        first_router = TaskRouter(
            load_hook=load_hook,
            save_hook=save_hook,
            id_factory=lambda: "task-hook",
        )
        first = first_router.route(
            "Start a new task to write the migration guide",
            self.context,
        )
        self.assertTrue(first.persisted)
        self.assertTrue(records)

        second_router = TaskRouter(
            load_hook=load_hook,
            save_hook=save_hook,
            id_factory=lambda: "must-not-be-used",
        )
        second = second_router.route(
            "Start a new task to write the migration guide",
            self.context,
        )
        self.assertEqual(second.to_dict(), first.to_dict())
        self.assertEqual(second.task_id, "task-hook")

    def test_unknown_and_bad_explicit_decision_are_fail_closed(self):
        router = TaskRouter()
        result = router.route("continue", persist=False)
        self.assertIs(result.decision, RouteDecision.UNKNOWN)
        self.assertIsNone(result.task_id)

        invalid = router.route(object(), persist=False)
        self.assertIs(invalid.decision, RouteDecision.UNKNOWN)
        self.assertTrue(invalid.fail_closed)

        def broken_load(_key):
            raise RuntimeError("host store unavailable")

        broken = TaskRouter(load_hook=broken_load, save_hook=lambda _key, _value: None)
        broken_result = broken.route(
            "Please add regression tests for the parser error handling",
            self.context,
        )
        self.assertIs(broken_result.decision, RouteDecision.UNKNOWN)
        self.assertTrue(broken_result.fail_closed)

        conflict = router.route(
            "Continue with the parser",
            self.context,
            explicit_decision=RouteDecision.ABANDON,
            signals={"continuation": True},
            persist=False,
        )
        self.assertIs(conflict.decision, RouteDecision.UNKNOWN)
        self.assertTrue(conflict.fail_closed)

        invalid_parent = router.route(
            "Continue with the parser",
            self.context,
            parent_task_id="../escape",
            persist=False,
        )
        self.assertIs(invalid_parent.decision, RouteDecision.UNKNOWN)
        self.assertTrue(invalid_parent.fail_closed)

        with self.assertRaises(TaskRouterError):
            TaskContext("bad/id")

    def test_metadata_round_trip_and_tampered_store_fail_closed(self):
        metadata = RouteMetadata(
            decision=RouteDecision.CONTINUATION,
            task_id="task-a",
            confidence=0.91,
            reason="anchored",
        )
        restored = RouteMetadata.from_dict(metadata.to_dict())
        self.assertEqual(restored.to_dict(), metadata.to_dict())

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "routes.json"
            router = TaskRouter(storage_path=path, id_factory=lambda: "task-new")
            router.route(
                "Start a new task to update the billing dashboard",
                self.context,
            )
            path.write_text("{not valid json", encoding="utf-8")
            restarted = TaskRouter(storage_path=path)
            result = restarted.route(
                "Start a new task to update the billing dashboard",
                self.context,
            )
            self.assertIs(result.decision, RouteDecision.UNKNOWN)
            self.assertTrue(result.fail_closed)
            self.assertIsNone(result.task_id)


if __name__ == "__main__":
    unittest.main()

"""Safety and lifecycle tests for durable task retention cleanup."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import retention as retention_module  # noqa: E402
from runtime.core.retention import (  # noqa: E402
    RetentionPlanChanged,
    RetentionPolicy,
    TaskRetentionManager,
    UnsafeRetentionPath,
)


UTC = timezone.utc
NOW = datetime(2026, 9, 24, 12, 0, 0, tzinfo=UTC)
OLD = (NOW - timedelta(days=90)).isoformat().replace("+00:00", "Z")
RECENT = (NOW - timedelta(days=2)).isoformat().replace("+00:00", "Z")


class FixedClock:
    def __call__(self) -> datetime:
        return NOW


class TaskRetentionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.tasks = self.root / ".memory" / "ultimate-dev" / "tasks"
        self.tasks.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def manager(
        self,
        *,
        policy: RetentionPolicy | None = None,
        persist_reports: bool = True,
    ) -> TaskRetentionManager:
        return TaskRetentionManager(
            self.root,
            policy=policy,
            clock=FixedClock(),
            persist_reports=persist_reports,
        )

    def create_task(
        self,
        task_id: str,
        *,
        status: str = "completed",
        updated_at: str = OLD,
        operations: tuple[dict[str, object], ...] = (),
        extra_state: dict[str, object] | None = None,
    ) -> Path:
        task_path = self.tasks / task_id
        operations_path = task_path / "operations"
        operations_path.mkdir(parents=True)
        state: dict[str, object] = {
            "schema_version": "2.5",
            "task_id": task_id,
            "status": status,
            "created_at": OLD,
            "updated_at": updated_at,
            "revision": 3,
            "contract": {"goal": f"finish {task_id}"},
            "completed": ["implementation"],
            "in_progress": [],
            "next_action": None,
            "changed_files": [],
            "decisions": [],
            "decision_bindings": [],
            "operation_ids": [operation["operation_id"] for operation in operations],
            "failed_approaches": [],
            "verification": {"passed": ["tests"], "pending": [], "evidence_refs": []},
            "observations": [],
            "blockers": [],
            "open_questions": [],
            "events": [],
        }
        if extra_state:
            state.update(extra_state)
        (task_path / "state.json").write_text(json.dumps(state), encoding="utf-8")
        for operation in operations:
            operation_id = str(operation["operation_id"])
            (operations_path / f"{operation_id}.json").write_text(
                json.dumps(operation),
                encoding="utf-8",
            )
        return task_path

    @staticmethod
    def entry(report: object, task_id: str):
        for item in report.entries:  # type: ignore[attr-defined]
            if item.task_id == task_id:
                return item
        raise AssertionError(f"missing report entry for {task_id}")

    def test_dry_run_is_non_mutating_and_issues_bound_token(self) -> None:
        task_path = self.create_task("dry-old")
        archive_root = self.root / ".memory" / "ultimate-dev" / "task-archives"
        manager = self.manager(persist_reports=False)

        report = manager.plan_cleanup()

        self.assertTrue(report.dry_run)
        self.assertEqual(report.mode, "delete")
        self.assertEqual(report.selected_count, 1)
        self.assertEqual(report.would_delete_count, 1)
        self.assertTrue(report.confirmation_required)
        self.assertTrue(report.confirmation_token.startswith("retention-delete-"))
        self.assertTrue(task_path.is_dir())
        self.assertFalse(archive_root.exists())
        json.dumps(report.to_dict(), allow_nan=False)

    def test_age_status_and_uncertainty_policies_preserve_by_default(self) -> None:
        for status in ("executing", "blocked", "failed", "uncertain"):
            self.create_task(f"keep-{status}", status=status)
        self.create_task("keep-recent", updated_at=RECENT)
        self.create_task("eligible", status="completed")
        self.create_task(
            "keep-uncertain-operation",
            operations=(
                {
                    "operation_id": "op-uncertain",
                    "task_id": "keep-uncertain-operation",
                    "status": "uncertain",
                },
            ),
        )

        report = self.manager().plan_cleanup()

        self.assertEqual([item.task_id for item in report.entries if item.eligible], ["eligible"])
        for status in ("executing", "blocked", "failed", "uncertain"):
            entry = self.entry(report, f"keep-{status}")
            self.assertEqual(entry.action, "preserved")
            self.assertEqual(entry.reason, "status_preserved")
        self.assertEqual(self.entry(report, "keep-recent").reason, "within_retention")
        uncertain = self.entry(report, "keep-uncertain-operation")
        self.assertEqual(uncertain.reason, "uncertain_task")
        self.assertIn("operation_uncertain", uncertain.error or "")

    def test_default_policy_includes_terminal_abandoned_and_cancelled_tasks(self) -> None:
        self.create_task("old-abandoned", status="abandoned")
        self.create_task("old-cancelled", status="cancelled")
        self.create_task("old-paused", status="paused")
        self.create_task("old-interrupted", status="interrupted")

        report = self.manager().plan_cleanup()

        self.assertEqual(
            [item.task_id for item in report.entries if item.eligible],
            ["old-abandoned", "old-cancelled"],
        )
        self.assertEqual(self.entry(report, "old-paused").reason, "status_preserved")
        self.assertEqual(self.entry(report, "old-interrupted").reason, "status_preserved")

    def test_explicit_status_policy_can_replace_preservation_defaults(self) -> None:
        self.create_task("old-completed")
        self.create_task("old-failed", status="failed")
        self.create_task("old-active", status="executing")
        policy = RetentionPolicy(
            max_age=timedelta(days=30),
            eligible_statuses={"completed", "failed"},
            preserve_statuses=(),
        )

        report = self.manager(policy=policy).plan_cleanup()

        self.assertEqual(
            [item.task_id for item in report.entries if item.eligible],
            ["old-completed", "old-failed"],
        )
        self.assertEqual(self.entry(report, "old-active").reason, "status_not_eligible")

    def test_archive_is_reversible_and_cleanup_is_idempotent(self) -> None:
        task_path = self.create_task("archive-me")
        manager = self.manager()

        archived = manager.archive_tasks()

        entry = self.entry(archived, "archive-me")
        self.assertEqual(entry.action, "archived")
        self.assertTrue(entry.archived)
        self.assertFalse(entry.deleted)
        self.assertFalse(task_path.exists())
        archived_task = self.root / str(entry.archive_path)
        self.assertTrue((archived_task / "state.json").is_file())
        manifest = json.loads((archived_task.parent / "retention.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["delete_requested"])

        repeated = manager.archive_tasks()
        self.assertEqual(repeated.selected_count, 0)
        self.assertEqual(repeated.archived_count, 0)
        self.assertTrue(archived_task.is_dir())

    def test_archive_can_be_restored_and_restore_is_idempotent(self) -> None:
        task_path = self.create_task("restore-me")
        manager = self.manager()
        archived = manager.archive_tasks()
        archive_path = str(self.entry(archived, "restore-me").archive_path)

        restored = manager.restore(archive_path)
        self.assertEqual(restored["status"], "restored")
        self.assertTrue(task_path.is_dir())
        self.assertEqual(manager.restore(archive_path)["status"], "already_restored")

    def test_restore_rejects_tampered_manifest(self) -> None:
        self.create_task("tampered-restore")
        manager = self.manager()
        archived = manager.archive_tasks()
        archive_path = str(self.entry(archived, "tampered-restore").archive_path)
        manifest_path = (self.root / archive_path).parent / "retention.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["state_digest"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaises(UnsafeRetentionPath):
            manager.restore(archive_path)

    def test_delete_requires_token_and_archives_before_rmtree(self) -> None:
        task_path = self.create_task("delete-me")
        task_path.joinpath("evidence").mkdir()
        task_path.joinpath("evidence", "proof.txt").write_text("verified", encoding="utf-8")
        manager = self.manager()
        plan = manager.plan_cleanup()
        token = str(plan.confirmation_token)

        with self.assertRaises(PermissionError):
            manager.delete_tasks("not-the-issued-token")
        self.assertTrue(task_path.is_dir())

        original_rmtree = retention_module.shutil.rmtree
        observed: list[bool] = []

        def checking_rmtree(path: Path) -> None:
            record = Path(path)
            self.assertEqual(record.parent, manager.archive_root)
            self.assertTrue((record / "task" / "state.json").is_file())
            manifest = json.loads((record / "retention.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["delete_requested"])
            observed.append(True)
            original_rmtree(record)

        with mock.patch.object(retention_module.shutil, "rmtree", side_effect=checking_rmtree):
            deleted = manager.delete_tasks(token)

        self.assertEqual(observed, [True])
        self.assertFalse(task_path.exists())
        self.assertEqual(deleted.deleted_count, 1)
        self.assertEqual(self.entry(deleted, "delete-me").action, "deleted")
        self.assertIsNone(deleted.confirmation_token)
        self.assertTrue(deleted.confirmation_verified)
        report_path = self.root / str(deleted.report_path)
        persisted = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertNotIn("confirmation_token", persisted)
        self.assertTrue(persisted["confirmation_verified"])

        replay = manager.delete_tasks(token)
        self.assertEqual(replay.selected_count, 0)
        self.assertEqual(replay.deleted_count, 0)

    def test_confirmation_token_is_bound_to_the_exact_task_snapshot(self) -> None:
        task_path = self.create_task("changed-after-plan")
        manager = self.manager()
        token = str(manager.plan_cleanup().confirmation_token)
        state_path = task_path / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["revision"] += 1
        state_path.write_text(json.dumps(state), encoding="utf-8")

        with self.assertRaises(RetentionPlanChanged):
            manager.delete_tasks(token)

        self.assertTrue(task_path.is_dir())

    def test_direct_task_symlinks_and_symlinked_storage_escape_are_rejected(self) -> None:
        outside = self.root / "outside-task"
        outside.mkdir()
        (outside / "state.json").write_text('{"outside": true}', encoding="utf-8")
        try:
            (self.tasks / "escape").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("symlinks are unavailable")

        report = self.manager().archive_tasks()

        escaped = self.entry(report, "escape")
        self.assertEqual(escaped.reason, "symlink_escape")
        self.assertTrue((outside / "state.json").is_file())
        self.assertTrue((self.tasks / "escape").is_symlink())

        storage_root = self.root / "symlink-project"
        storage_outer = self.root / "outside-tasks"
        storage_outer.mkdir()
        memory = storage_root / ".memory" / "ultimate-dev"
        memory.mkdir(parents=True)
        try:
            (memory / "tasks").symlink_to(storage_outer, target_is_directory=True)
        except OSError:
            self.skipTest("symlinks are unavailable")
        with self.assertRaises(UnsafeRetentionPath):
            TaskRetentionManager(storage_root)

    def test_nested_task_symlink_is_unlinked_without_deleting_external_target(self) -> None:
        outside = self.root / "outside-evidence"
        outside.mkdir()
        sentinel = outside / "keep.txt"
        sentinel.write_text("must survive", encoding="utf-8")
        task_path = self.create_task("nested-symlink")
        try:
            (task_path / "evidence").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("symlinks are unavailable")
        manager = self.manager()
        token = str(manager.plan_cleanup().confirmation_token)

        report = manager.delete_tasks(token)

        self.assertEqual(report.deleted_count, 1)
        self.assertFalse(task_path.exists())
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "must survive")
        self.assertTrue(outside.is_dir())

    def test_confirmation_expires_and_cannot_be_reused(self) -> None:
        self.create_task("expiring-token")
        token = str(self.manager().plan_cleanup().confirmation_token)
        later = TaskRetentionManager(self.root, clock=lambda: NOW + timedelta(hours=1))
        with self.assertRaises(PermissionError):
            later.delete_tasks(token)

    def test_confirmation_survives_manager_recreation(self) -> None:
        self.create_task("cross-manager")
        token = str(self.manager().plan_cleanup().confirmation_token)
        report = self.manager().delete_tasks(token)
        self.assertEqual(report.deleted_count, 1)

    def test_concurrent_cleanup_deletes_once_and_replays_cleanly(self) -> None:
        for index in range(6):
            self.create_task(f"concurrent-{index}")
        first_manager = self.manager()
        token = str(first_manager.plan_cleanup().confirmation_token)
        managers = [self.manager(), self.manager(), first_manager, self.manager()]

        with ThreadPoolExecutor(max_workers=4) as pool:
            reports = list(
                pool.map(
                    lambda manager: manager.delete_tasks(token),
                    managers,
                )
            )

        self.assertEqual(sum(report.deleted_count for report in reports), 6)
        self.assertEqual(sum(1 for report in reports if report.deleted_count), 1)
        self.assertEqual(sum(report.error_count for report in reports), 0)
        self.assertFalse(any((self.tasks / f"concurrent-{index}").exists() for index in range(6)))
        replay = first_manager.delete_tasks(token)
        self.assertEqual(replay.selected_count, 0)
        self.assertEqual(replay.deleted_count, 0)

    def test_malformed_or_mismatched_state_is_reported_and_never_deleted(self) -> None:
        malformed = self.tasks / "malformed"
        malformed.mkdir()
        (malformed / "state.json").write_text("{not-json", encoding="utf-8")
        mismatch = self.create_task("mismatch")
        mismatch_state = json.loads((mismatch / "state.json").read_text(encoding="utf-8"))
        mismatch_state["task_id"] = "some-other-task"
        (mismatch / "state.json").write_text(json.dumps(mismatch_state), encoding="utf-8")
        non_object = self.tasks / "non-object"
        non_object.mkdir()
        (non_object / "state.json").write_text("[]", encoding="utf-8")
        self.create_task("valid-old")
        manager = self.manager()

        plan = manager.plan_cleanup()
        self.assertEqual([item.task_id for item in plan.entries if item.eligible], ["valid-old"])
        self.assertEqual(self.entry(plan, "malformed").reason, "malformed_state")
        self.assertEqual(self.entry(plan, "mismatch").reason, "identity_mismatch")
        self.assertEqual(self.entry(plan, "non-object").reason, "malformed_state")

        result = manager.delete_tasks(str(plan.confirmation_token))

        self.assertEqual(result.deleted_count, 1)
        self.assertGreaterEqual(result.error_count, 3)
        self.assertTrue((malformed / "state.json").is_file())
        self.assertTrue((mismatch / "state.json").is_file())
        self.assertTrue((non_object / "state.json").is_file())


if __name__ == "__main__":
    unittest.main()

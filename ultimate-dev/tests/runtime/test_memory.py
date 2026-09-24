import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.memory import (
    MemoryStore,
    SecretDetected,
    compute_digest,
    redact,
)


UTC = dt.timezone.utc
BASE_TIME = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


class FixedClock:
    def __init__(self, value=BASE_TIME):
        self.value = value

    def __call__(self):
        return self.value


class MemoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = MemoryStore(self.root, clock=FixedClock())

    def tearDown(self):
        self.temp.cleanup()

    def add(self, **kwargs):
        values = {
            "source": {"name": "unit-test", "version": 1},
            "scope": "project/test",
            "observed_at": BASE_TIME,
            "created_at": BASE_TIME,
            "updated_at": BASE_TIME,
        }
        values.update(kwargs)
        return self.store.add(**values)

    def test_record_persists_provenance_and_digest_across_restart(self):
        record = self.add(
            kind="decision",
            content={"choice": "use-json"},
            verified_at=BASE_TIME,
            confidence=0.91,
            key="storage-format",
        )
        expected_digest = compute_digest(
            record.content,
            record.reference,
            kind=record.kind,
            source=record.source,
            scope=record.scope,
        )
        self.assertEqual(record.digest, expected_digest)
        self.assertEqual(record.observed_at, "2026-01-01T12:00:00Z")
        self.assertEqual(record.verified_at, "2026-01-01T12:00:00Z")
        self.assertEqual(record.source["name"], "unit-test")
        self.assertEqual(record.projection_dict()["provenance"]["digest"], record.digest)

        memory_file = self.root / ".memory" / "ultimate-dev" / "memory" / "records.json"
        self.assertTrue(memory_file.is_file())
        persisted = json.loads(memory_file.read_text(encoding="utf-8"))
        self.assertEqual(persisted["schema_version"], "1.0")
        self.assertEqual(persisted["records"][0]["digest"], record.digest)

        restarted = MemoryStore(self.root)
        restored = restarted.get(record.id)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.to_dict(), record.to_dict())

    def test_stale_and_expired_records_are_excluded_from_active_projection(self):
        stale = self.add(
            kind="observation",
            content="old observation",
            stale_after=10,
            key="stale-item",
        )
        expired = self.add(
            kind="observation",
            content="short-lived observation",
            ttl=5,
            key="expiring-item",
        )
        later = BASE_TIME + dt.timedelta(seconds=20)

        projection = self.store.project_context("project/test", now=later, budget=4000)
        self.assertEqual(projection["items"], [])
        self.assertIsNone(self.store.get(stale.id, now=later))
        self.assertIsNone(self.store.get(expired.id, now=later))
        self.assertEqual(
            self.store.get(stale.id, include_inactive=True, now=later).status,
            "stale",
        )
        self.assertEqual(
            self.store.get(expired.id, include_inactive=True, now=later).status,
            "expired",
        )

        stale_projection = self.store.project_context(
            "project/test",
            now=later,
            budget=4000,
            include_stale=True,
        )
        self.assertEqual([item["id"] for item in stale_projection["items"]], [stale.id])
        self.assertEqual(self.store.cleanup(now=later), 1)
        self.assertIsNotNone(self.store.get(stale.id, include_inactive=True, now=later))
        self.assertIsNone(self.store.get(expired.id, include_inactive=True, now=later))

    def test_supersession_preserves_old_record_and_updates_lifecycle(self):
        old = self.add(kind="fact", content="blue", key="theme")
        replacement = self.add(kind="fact", content="green", key="theme")

        self.assertEqual(replacement.supersedes, (old.id,))
        self.assertIsNone(self.store.get(old.id))
        old_history = self.store.get(old.id, include_inactive=True)
        self.assertEqual(old_history.status, "superseded")
        self.assertEqual(old_history.superseded_by, replacement.id)
        self.assertEqual(old_history.content, "blue")
        self.assertEqual(self.store.get(replacement.id).content, "green")

        explicit = self.add(
            kind="fact",
            content="blue-again",
            key="theme",
            supersedes=replacement.id,
        )
        self.assertEqual(self.store.get(replacement.id, include_inactive=True).status, "superseded")
        self.assertEqual(explicit.supersedes, (replacement.id,))

    def test_scope_isolation_keeps_other_projects_out_of_projection(self):
        alpha = self.add(kind="fact", content="alpha", scope="project/alpha", key="one")
        beta = self.add(kind="fact", content="beta", scope="project/beta", key="two")
        shared = self.add(kind="preference", content="shared", scope="global", key="three")

        alpha_view = self.store.project_context("project/alpha", budget=4000)
        ids = [item["id"] for item in alpha_view["items"]]
        self.assertIn(alpha.id, ids)
        self.assertIn(shared.id, ids)
        self.assertNotIn(beta.id, ids)
        self.assertEqual(
            {record.record_id for record in self.store.list("project/alpha")},
            {alpha.id, shared.id},
        )

    def test_secret_material_is_refused_and_sensitive_material_is_redacted(self):
        with self.assertRaises(SecretDetected):
            self.store.add(
                kind="secret-note",
                content={"password": "correct horse battery staple"},
                source="unit-test",
                scope="project/test",
            )
        self.assertEqual(self.store.list(include_inactive=True), [])

        safe = self.store.add(
            kind="contact",
            content={"email": "person@example.com", "note": "keep this"},
            source="unit-test",
            scope="project/test",
            sensitivity="sensitive",
        )
        self.assertEqual(safe.content["email"], "[REDACTED]")
        self.assertNotIn("person@example.com", json.dumps(safe.to_dict()))
        self.assertEqual(redact({"token": "opaque-value"})["token"], "[REDACTED]")
        with self.assertRaises(SecretDetected):
            self.store.add(
                kind="secret-note",
                content="ordinary text",
                source="unit-test",
                scope="project/test",
                sensitivity="secret",
            )

    def test_retention_cleanup_removes_old_records_and_is_idempotent(self):
        store = MemoryStore(self.root, retention_seconds=10, clock=FixedClock())
        old = store.add(
            kind="fact",
            content="old",
            source="unit-test",
            scope="project/test",
            observed_at=BASE_TIME,
            created_at=BASE_TIME,
            updated_at=BASE_TIME,
        )
        later = BASE_TIME + dt.timedelta(seconds=11)
        self.assertEqual(store.cleanup(now=later), 1)
        self.assertIsNone(store.get(old.id, include_inactive=True))
        self.assertEqual(store.cleanup(now=later), 0)

    def test_projection_is_deterministic_scope_safe_and_budget_bounded(self):
        first = self.add(
            kind="fact",
            content="a" * 160,
            confidence=0.7,
            key="first",
            observed_at=BASE_TIME,
        )
        second = self.add(
            kind="fact",
            content="b" * 160,
            confidence=0.95,
            key="second",
            observed_at=BASE_TIME + dt.timedelta(seconds=1),
        )
        self.add(
            kind="fact",
            content="private beta",
            confidence=1.0,
            key="other-scope",
            scope="project/other",
        )

        projection = self.store.project_context(
            "project/test",
            budget=2000,
            now=BASE_TIME + dt.timedelta(seconds=2),
        )
        repeated = self.store.project_context(
            "project/test",
            budget=2000,
            now=BASE_TIME + dt.timedelta(seconds=2),
        )
        self.assertEqual(projection, repeated)
        self.assertLessEqual(projection["used"], projection["budget"])
        self.assertLessEqual(
            sum(len(json.dumps(item, sort_keys=True, separators=(",", ":"))) for item in projection["items"]),
            projection["budget"],
        )
        self.assertEqual([item["id"] for item in projection["items"]], [second.id, first.id])
        self.assertNotIn("private beta", json.dumps(projection))
        self.assertTrue(projection["deterministic"])

    def test_reference_only_record_and_invalid_payload_fail_closed(self):
        record = self.add(kind="reference", reference="docs/architecture.md")
        self.assertIsNone(record.content)
        self.assertEqual(record.reference, "docs/architecture.md")
        with self.assertRaises(ValueError):
            self.store.add(kind="invalid", content=None, reference=None, source="unit-test")
        with self.assertRaises(ValueError):
            self.store.add(kind="invalid", content="x", source="unit-test", confidence=1.5)


if __name__ == "__main__":
    unittest.main()

import datetime as dt
import tempfile

import pytest

from runtime.core.memory import MemoryStore
from runtime.core.memory_retention import MemoryRetentionManager, MemoryRetentionPlanChanged, MemoryRetentionPolicy


def test_memory_cleanup_is_dry_run_then_explicitly_confirmed():
    base = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore(tmp, clock=lambda: base)
        old = store.add(
            kind="observation",
            content="old",
            source="test",
            scope="project/test",
            observed_at=base - dt.timedelta(days=90),
            created_at=base - dt.timedelta(days=90),
            updated_at=base - dt.timedelta(days=90),
        )
        keep = store.add(
            kind="decision",
            content="keep",
            source="test",
            scope="project/test",
            observed_at=base,
            created_at=base,
            updated_at=base,
        )
        manager = MemoryRetentionManager(store, policy=MemoryRetentionPolicy(max_age_seconds=30 * 86400), clock=lambda: base)
        plan = manager.plan()
        assert plan["dry_run"] is True
        assert old.id in {entry["record_id"] for entry in plan["entries"] if entry["action"] == "would_delete"}
        assert store.get(old.id, include_inactive=True) is not None
        result = manager.apply(plan["confirmation_token"])
        assert result["deleted"] == 1
        assert store.get(old.id, include_inactive=True) is None
        assert store.get(keep.id, include_inactive=True) is not None
        with pytest.raises(Exception):
            manager.apply(plan["confirmation_token"])


def test_memory_cleanup_preserves_sensitive_records_by_default():
    moment = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore(tmp, clock=lambda: moment)
        record = store.add(
            kind="observation",
            content="old",
            source="test",
            scope="project/test",
            sensitivity="restricted",
            observed_at=moment - dt.timedelta(days=90),
            created_at=moment - dt.timedelta(days=90),
            updated_at=moment - dt.timedelta(days=90),
        )
        manager = MemoryRetentionManager(store, policy=MemoryRetentionPolicy(max_age_seconds=0), clock=lambda: moment)
        plan = manager.plan()
        assert next(item for item in plan["entries"] if item["record_id"] == record.id)["reason"] == "preserved_sensitivity"

import json
import tempfile

from runtime.core.evolution import EvolutionStore


def test_evolution_event_log_is_bounded_by_rotation():
    with tempfile.TemporaryDirectory() as tmp:
        store = EvolutionStore(tmp)
        original = __import__("runtime.core.evolution", fromlist=["MAX_EVENT_FILE_BYTES"]).MAX_EVENT_FILE_BYTES
        try:
            __import__("runtime.core.evolution", fromlist=["MAX_EVENT_FILE_BYTES"]).MAX_EVENT_FILE_BYTES = 1
            for index in range(5):
                store._write_event_unlocked({"type": "test", "index": index, "payload": "x" * 100})
        finally:
            __import__("runtime.core.evolution", fromlist=["MAX_EVENT_FILE_BYTES"]).MAX_EVENT_FILE_BYTES = original
        base = store.events_path.parent
        assert store.events_path.is_file()
        assert (base / "events.jsonl.1").is_file()
        assert all((base / f"events.jsonl.{index}").stat().st_size <= 200 for index in (1, 2))

import tempfile
import time
from pathlib import Path

from runtime.core.lite_mode import BootstrapCache, LiteMode


def test_lite_cache_uses_contained_keys_and_cleanup():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "SKILL.md").write_text("skill")
        (root / "AGENTS.md").write_text("agents")
        (root / "VERSION").write_text("3.0.0")
        mode = LiteMode(str(root))
        mode.set_cached_init("../escape", {"value": 1})
        assert mode.get_cached_init("../escape")["value"] == 1
        assert mode.cleanup(max_age_seconds=0, now=time.time() + 1) == 1
        assert mode.get_cached_init("../escape") is None


def test_lite_mode_does_not_fast_path_complex_or_destructive_requests():
    with tempfile.TemporaryDirectory() as tmp:
        mode = LiteMode(tmp)
        assert mode.should_use_lite("refactor system and deploy") is False
        assert mode.should_use_lite("rm -rf build") is False
        assert mode.should_use_lite("short ambiguous request") is False
        assert mode.should_use_lite("explain this function") is True
        assert mode.get_lite_config()["skip_preflight"] is False


def test_bootstrap_cache_writes_atomically_and_invalidates():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "SKILL.md").write_text("skill")
        (root / "AGENTS.md").write_text("agents")
        (root / "VERSION").write_text("3.0.0")
        cache = BootstrapCache(str(root))
        cache.set({"value": 2})
        assert cache.get()["value"] == 2
        cache.invalidate()
        assert cache.get() is None

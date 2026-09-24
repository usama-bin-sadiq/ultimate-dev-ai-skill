import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sync_version", ROOT / "scripts" / "sync-version.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_sync_text_replaces_only_the_managed_version_line():
    source = "version: \"3.0.0\"  # keep this comment\nname: example\n"
    updated = MODULE.sync_text(source, "3.0.1", label="example")
    assert updated == "version: \"3.0.1\"  # keep this comment\nname: example\n"


def test_sync_text_rejects_ambiguous_version_lines():
    try:
        MODULE.sync_text("version: 3.0.0\nversion: 3.0.0\n", "3.0.1")
    except MODULE.SyncVersionError:
        pass
    else:
        raise AssertionError("ambiguous config was accepted")

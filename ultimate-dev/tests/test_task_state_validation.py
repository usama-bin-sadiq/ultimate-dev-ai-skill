#!/usr/bin/env python3
"""Tests for durable task-state validation."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-task-state.py"


def _load():
    spec = importlib.util.spec_from_file_location("validate_task_state", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(directory: Path, name: str, text: str) -> Path:
    path = directory / name / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_valid_state_file_passes(tmp_path):
    module = _load()
    path = _write(tmp_path, "ok", json.dumps({
        "task_id": "ok", "status": "completed", "updated_at": "2026-09-26T00:00:00Z",
        "schema_version": "2.5",
    }))
    report = module.check_file(path)
    assert report["ok"], report
    assert report["task_id"] == "ok"


def test_yaml_written_as_json_is_reported_precisely(tmp_path):
    module = _load()
    path = _write(tmp_path, "yaml", "task_id: yaml\nstatus: completed\nupdated_at: 2026-09-24\n")
    report = module.check_file(path)
    assert not report["ok"]
    assert any("YAML or plain text" in error for error in report["errors"])


def test_concatenated_documents_are_reported_precisely(tmp_path):
    module = _load()
    path = _write(
        tmp_path,
        "double",
        json.dumps({"task_id": "a", "status": "completed", "updated_at": "x"})
        + "\n"
        + json.dumps({"updated": "2026-09-24"}),
    )
    report = module.check_file(path)
    assert not report["ok"]
    assert any("concatenated documents" in error for error in report["errors"])


def test_missing_required_field_is_an_error(tmp_path):
    module = _load()
    path = _write(tmp_path, "thin", json.dumps({"task_id": "thin"}))
    report = module.check_file(path)
    assert not report["ok"]
    assert any("missing field: status" in error for error in report["errors"])
    assert any("missing field: updated_at" in error for error in report["errors"])


def test_empty_file_is_an_error(tmp_path):
    module = _load()
    path = _write(tmp_path, "empty", "   \n")
    report = module.check_file(path)
    assert not report["ok"]
    assert "file is empty" in report["errors"]


def test_directory_scan_counts_invalid_files(tmp_path):
    module = _load()
    _write(tmp_path, "good", json.dumps({
        "task_id": "good", "status": "completed", "updated_at": "x", "schema_version": "2.5",
    }))
    _write(tmp_path, "bad", "{not json")
    report = module.check_tree(tmp_path)
    assert report["total"] == 2
    assert report["invalid"] == 1

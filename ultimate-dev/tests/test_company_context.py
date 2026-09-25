#!/usr/bin/env python3
"""Tests for the optional company-context validator."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-company-context.py"
TEMPLATE = ROOT / "reference" / "company-context-template.yaml"


def run(path: Path, *extra: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(path), *extra],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_template_is_valid_in_template_mode():
    result = run(TEMPLATE, "--template")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout


def test_active_pack_requires_real_values_and_rejects_secrets():
    data = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
    data.update({
        "status": "active",
        "company": "Example Co",
        "effective_date": "2026-09-25",
        "owner": "platform-team",
        "last_verified": "2026-09-25",
    })
    for key in ("company", "effective_date", "owner", "last_verified"):
        data[key] = str(data[key]).replace("<name>", "Example Co").replace("<YYYY-MM-DD>", "2026-09-25").replace("<role-or-team>", "platform-team")
    data["terminology"] = {"terms": [], "prohibited_inferences": []}
    data["policies"] = {key: None for key in ("finance", "legal", "privacy", "security", "people", "procurement", "audit")}
    data["approvals"] = {"matrix": None, "human_review_required": []}
    data["templates"] = {"reports": [], "artifacts": []}
    data["unknowns"] = []
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "context.yaml"
        path.write_text(yaml.safe_dump(data), encoding="utf-8")
        valid = run(path)
        assert valid.returncode == 0, valid.stdout + valid.stderr
        data["terminology"]["api_key"] = "should-not-be-here"
        path.write_text(yaml.safe_dump(data), encoding="utf-8")
        invalid = run(path)
        assert invalid.returncode == 1
        assert "secret-like" in invalid.stdout

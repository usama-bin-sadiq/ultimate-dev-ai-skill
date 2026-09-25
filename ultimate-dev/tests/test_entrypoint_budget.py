#!/usr/bin/env python3
"""Tests for the always-loaded entrypoint budget."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "measure-entrypoint.py"


def test_entrypoint_budget_passes_and_reports_files():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--strict"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["within_budget"] is True
    assert {item["file"] for item in report["entries"]} >= {"SKILL.md", "AGENTS.md", "AGENT.md"}
    assert report["total_words"] > 0

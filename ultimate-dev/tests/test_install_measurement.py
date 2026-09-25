#!/usr/bin/env python3
"""Tests for reproducible staged-install measurements."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "measure-install.py"


def test_measure_install_reports_cache_free_payload():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--strict"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["version"] == "3.0.2"
    assert report["allocated_kib"] > 0
    assert report["logical_bytes"] > 0
    assert report["file_count"] > 100
    assert report["cache_directories"] == []
    assert report["symlinks"] == []
    assert report["protected_files"] == []
    assert "Payload size:" in report["installer_output"]


def test_measure_install_is_not_a_provider_benchmark():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "payload:" in result.stdout
    assert "provider" not in result.stdout.lower()

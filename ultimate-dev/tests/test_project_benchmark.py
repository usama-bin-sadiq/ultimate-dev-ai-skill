#!/usr/bin/env python3
"""Tests for the dependency-free project-context benchmark."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "benchmark-project-context.py"


def test_benchmark_passes_on_a_minimal_checkout():
    with tempfile.TemporaryDirectory() as directory:
        project = Path(directory)
        (project / "README.md").write_text("Example project", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--project", str(project), "--json", "--strict"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        report = json.loads(result.stdout)
        assert report["status"] == "pass"
        assert report["checks"]["dependencies_installed"] is False
        assert report["checks"]["all_candidate_commands_not_run"] is True
        assert report["metrics"]["unknowns"] >= 1


def test_benchmark_reports_manifest_and_path_signals():
    with tempfile.TemporaryDirectory() as directory:
        project = Path(directory)
        (project / "README.md").write_text("Example", encoding="utf-8")
        (project / "package.json").write_text('{"scripts":{"test":"node test.js"}}', encoding="utf-8")
        (project / "src").mkdir()
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--project", str(project), "--json", "--strict"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        report = json.loads(result.stdout)
        assert report["metrics"]["manifests_detected"] == 1
        assert report["metrics"]["important_paths"] >= 1
        assert report["metrics"]["candidate_commands"] == 1

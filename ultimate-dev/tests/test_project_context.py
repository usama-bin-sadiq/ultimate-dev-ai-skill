#!/usr/bin/env python3
"""Tests for the provider-free project-context recipe generator."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate-project-context.py"


def test_generator_reports_candidates_without_running_them():
    with tempfile.TemporaryDirectory() as directory:
        project = Path(directory)
        (project / "package.json").write_text(
            json.dumps({
                "scripts": {"test": "vitest", "build": "vite build"},
                "workspaces": ["packages/*"],
            }),
            encoding="utf-8",
        )
        (project / "src").mkdir()
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--project", str(project)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        recipe = yaml.safe_load(result.stdout)
        assert recipe["project"] == project.name
        assert isinstance(recipe["stack"], list)
        assert isinstance(recipe["manifests"], list)
        assert "src" in recipe["important_paths"]
        assert any("packages/*" in rule for rule in recipe["path_rules"])
        commands = {item["name"]: item for item in recipe["commands"]}
        assert commands["test"]["command"] == "npm run test"
        assert commands["test"]["status"] == "not_run"
        assert recipe["unknowns"]


def test_generator_recognizes_gradle_metadata_without_running_it():
    with tempfile.TemporaryDirectory() as directory:
        project = Path(directory)
        (project / "build.gradle.kts").write_text("plugins { kotlin(\"jvm\") }", encoding="utf-8")
        (project / "gradlew").write_text("#!/bin/sh\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--project", str(project)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        recipe = yaml.safe_load(result.stdout)
        assert "java" in recipe["stack"]
        assert "kotlin" in recipe["stack"]
        assert any(item["command"] == "./gradlew test" and item["status"] == "not_run" for item in recipe["commands"])


def test_generator_is_read_only_without_output_flag():
    with tempfile.TemporaryDirectory() as directory:
        project = Path(directory)
        (project / "README.md").write_text("Example", encoding="utf-8")
        before = sorted(path.name for path in project.iterdir())
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--project", str(project)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert sorted(path.name for path in project.iterdir()) == before


def test_check_mode_rejects_stale_recipe():
    with tempfile.TemporaryDirectory() as directory:
        project = Path(directory)
        output = project / "context.yaml"
        output.write_text("version: old\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--project", str(project), "--output", str(output), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        assert "stale" in result.stderr

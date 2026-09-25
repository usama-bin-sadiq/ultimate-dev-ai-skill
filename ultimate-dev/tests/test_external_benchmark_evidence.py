#!/usr/bin/env python3
"""Validate recorded external-repository benchmark evidence."""
from pathlib import Path

TASK = Path(__file__).resolve().parents[2] / ".memory" / "ultimate-dev" / "tasks" / "external-repo-benchmark-and-release-2026-09-25" / "evidence"


def test_external_benchmarks_are_recorded_without_dependencies():
    for name, repository in (("vscode-benchmark.md", "microsoft/vscode"), ("intellij-benchmark.md", "JetBrains/intellij-community")):
        text = (TASK / name).read_text(encoding="utf-8")
        assert repository in text
        assert "Dependencies installed: **none**" in text
        assert "deleted after benchmark" in text
        assert "strict `fixture_audit_pass`" in text

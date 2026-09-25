#!/usr/bin/env python3
"""Validate recorded external-repository benchmark evidence.

The evidence lives under the project-local .memory tree, which is intentionally
untracked and is not part of the distributed package. The checks therefore skip
when the evidence is absent rather than failing, so a clean clone of the
repository does not report a failure for a file it was never meant to ship.
"""
from pathlib import Path

import pytest

TASK = (
    Path(__file__).resolve().parents[2]
    / ".memory"
    / "ultimate-dev"
    / "tasks"
    / "external-repo-benchmark-and-release-2026-09-25"
    / "evidence"
)


@pytest.mark.skipif(
    not TASK.is_dir(),
    reason="recorded benchmark evidence is project-local and not distributed",
)
def test_external_benchmarks_are_recorded_without_dependencies():
    for name, repository in (
        ("vscode-benchmark.md", "microsoft/vscode"),
        ("intellij-benchmark.md", "JetBrains/intellij-community"),
    ):
        evidence = TASK / name
        if not evidence.is_file():
            pytest.skip(f"{name} is not recorded in this project-local tree")
        text = evidence.read_text(encoding="utf-8")
        assert repository in text
        assert "Dependencies installed: **none**" in text
        assert "deleted after benchmark" in text
        assert "strict `fixture_audit_pass`" in text

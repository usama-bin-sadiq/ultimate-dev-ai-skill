#!/usr/bin/env python3
"""Verify the repository can be reconstructed from a clean checkout.

Every blocker in the v4 plan except one was "it is not committed". A test that
only runs in the developer's working tree cannot prove that. These tests clone
the repository into a temporary directory and check the payload, the runtime
and the test suite all survive the round trip.

Untracked files are the failure mode being guarded: work that passes locally
and is silently absent from a fresh install.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL = os.path.join(REPO, "ultimate-dev")

# Files the runtime and the prompt core require. If any is untracked, a fresh
# install is broken and no local test would notice.
REQUIRED_TRACKED = [
    "ultimate-dev/contracts/task-graph.yaml",
    "ultimate-dev/runtime/core/task_graph.py",
    "ultimate-dev/runtime/core/attestation.py",
    "ultimate-dev/scripts/runtime-probe.py",
    "ultimate-dev/scripts/capability-probe.py",
    "ultimate-dev/scripts/doctor.py",
    "ultimate-dev/tests/test_task_graph_behaviour.py",
    "ultimate-dev/tests/test_attestation.py",
    "ultimate-dev/tests/test_capability_probe.py",
    "ultimate-dev/tests/test_doctor.py",
    "ultimate-dev/tests/test_model_independence.py",
    "ultimate-dev/tests/test_prompt_plane_wiring.py",
]


def git(*args: str, cwd: str = REPO) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=300, check=False
    )


def tracked(path: str) -> bool:
    return git("ls-files", "--error-unmatch", path).returncode == 0


@pytest.fixture(scope="module")
def clone(tmp_path_factory) -> str:
    """Clone HEAD into a temp dir once for the whole module."""
    target = str(tmp_path_factory.mktemp("clone"))
    result = git("clone", "--quiet", "--depth", "1", REPO, target)
    if result.returncode != 0:
        pytest.skip(f"clone unavailable: {result.stderr[-200:]}")
    return target


class TestNothingRequiredIsUntracked:
    @pytest.mark.parametrize("relative", REQUIRED_TRACKED)
    def test_required_file_is_committed(self, relative):
        assert tracked(relative), (
            f"{relative} is required by the runtime or its tests but is not "
            "committed. A fresh install would be missing it while local tests "
            "still pass."
        )

    def test_no_keystone_file_is_untracked(self):
        result = git("status", "--porcelain", "--", "ultimate-dev/runtime/core")
        dirty = [
            line for line in result.stdout.splitlines() if line.startswith("??")
        ]
        assert not dirty, f"untracked runtime files: {dirty}"

    def test_no_contract_is_untracked(self):
        result = git("status", "--porcelain", "--", "ultimate-dev/contracts")
        dirty = [
            line for line in result.stdout.splitlines() if line.startswith("??")
        ]
        assert not dirty, f"untracked contract files: {dirty}"


class TestFreshCloneIsComplete:
    @pytest.mark.parametrize("relative", REQUIRED_TRACKED)
    def test_required_file_exists_in_a_fresh_clone(self, clone, relative):
        assert os.path.isfile(os.path.join(clone, relative)), (
            f"{relative} is committed but absent from a fresh clone"
        )

    def test_version_file_exists(self, clone):
        assert os.path.isfile(os.path.join(clone, "VERSION"))

    def test_payload_has_no_json_definitions(self, clone):
        """The file-format rule must hold in the clone, not just locally."""
        offenders: list[str] = []
        for directory, dirs, names in os.walk(os.path.join(clone, "ultimate-dev")):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for name in names:
                if name.endswith(".json"):
                    offenders.append(os.path.join(directory, name))
        # Only the Node-consumed JEV schemas and policy snapshot are legal.
        allowed = {"jev-decision-request.schema.json", "jev-decision-packet.schema.json", "jev-policy.json"}
        unexpected = [
            p for p in offenders if os.path.basename(p) not in allowed
        ]
        assert not unexpected, f"unexpected JSON definitions in a fresh clone: {unexpected}"

    def test_clone_passes_the_structural_validator(self, clone):
        result = subprocess.run(
            [sys.executable, os.path.join("ultimate-dev", "scripts", "validate-consistency.py")],
            cwd=clone, capture_output=True, text=True, timeout=300, check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr


class TestCleanCloneRunsTheSuite:
    def test_pytest_passes_in_a_fresh_clone(self, clone):
        """The decisive check: the work is real only if it survives a clone."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"],
            cwd=os.path.join(clone, "ultimate-dev"),
            capture_output=True, text=True, timeout=1800, check=False,
        )
        assert result.returncode == 0, (
            "the suite fails in a fresh clone:\n"
            + (result.stdout[-3000:] or result.stderr[-2000:])
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

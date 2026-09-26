#!/usr/bin/env python3
"""``doctor`` must be able to fail, and must never fake a pass.

A diagnostic that always reports green is worse than none, because it is
trusted. These tests inject known defects and require the corresponding check
to notice, then require the report to name the evidence behind every claim.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(BASE, "scripts", "doctor.py")


_DOCTOR = None


def load_doctor():
    """Import doctor.py once and reuse it.

    A fresh instance per call would create a fresh ``Status`` enum, so
    ``finding.status is doctor.Status.FAIL`` would be False even when the
    status matches. The module must be a singleton across these tests.
    """
    global _DOCTOR
    if _DOCTOR is not None:
        return _DOCTOR
    spec = importlib.util.spec_from_file_location("doctor_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    _DOCTOR = module
    return module


class TestReportShape:
    def test_every_finding_names_its_evidence(self):
        doctor = load_doctor()
        for finding in doctor.collect(include_slow=False):
            assert finding.evidence, (
                f"{finding.check} reports {finding.status.value} without naming "
                "the check that produced it"
            )

    def test_statuses_are_from_the_declared_set(self):
        doctor = load_doctor()
        allowed = {s.value for s in doctor.Status}
        for finding in doctor.collect(include_slow=False):
            assert finding.status.value in allowed

    def test_slow_checks_are_excludable(self):
        """Running the suite from inside the suite is recursive.

        ``collect()`` shells out to pytest. Its own tests must opt out, and
        that opt-out has to exist or the tool cannot be tested at all.
        """
        doctor = load_doctor()
        checks = {f.check for f in doctor.collect(include_slow=False)}
        assert "test-suite" not in checks
        assert "contract-drift:task-graph" in checks, "fast checks must still run"

    def test_json_output_is_machine_readable(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, "--json", "--quick"],
            cwd=BASE, capture_output=True, text=True, timeout=300,
        )
        assert result.returncode in (0, 1), result.stderr
        report = json.loads(result.stdout)
        for key in ("findings", "pass", "fail", "warn", "not_run"):
            assert key in report
        assert report["pass"] + report["fail"] + report["warn"] + report["not_run"] == len(
            report["findings"]
        )

    def test_quick_mode_omits_the_recursive_check(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, "--json", "--quick"],
            cwd=BASE, capture_output=True, text=True, timeout=300,
        )
        report = json.loads(result.stdout)
        checks = {item["check"] for item in report["findings"]}
        assert "test-suite" not in checks, (
            "--quick must omit the check that runs pytest, or doctor cannot be "
            "invoked from inside the suite it reports on"
        )

    def test_current_repository_has_no_failures(self):
        doctor = load_doctor()
        findings = doctor.collect(include_slow=False)
        failures = [f.check for f in findings if f.status is doctor.Status.FAIL]
        assert not failures, f"doctor reports failures in a clean tree: {failures}"


class TestChecksDetectRealDefects:
    """Inject a defect, require the matching check to fail."""

    def test_contract_drift_is_detected(self):
        doctor = load_doctor()
        path = os.path.join(BASE, "contracts", "task-graph.yaml")
        backup = path + ".bak"
        shutil.copy2(path, backup)
        try:
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            # The extra field must land inside node_fields. Appending to the
            # end of the file would put it under `scheduling` and test nothing.
            anchor = '  checkpoint: "Whether node completion is checkpointed."\n'
            assert anchor in text, "node_fields anchor not found; update this test"
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(
                    text.replace(
                        anchor,
                        anchor + '  phantom_field: "promised by the contract only"\n',
                        1,
                    )
                )
            findings = [
                f
                for f in doctor.collect(include_slow=False)
                if f.check == "contract-drift:task-graph"
            ]
            assert findings, "the contract-drift check did not run"
            assert findings[0].status is doctor.Status.FAIL, (
                "a contract promising a field the code lacks must be a FAIL"
            )
            assert any("phantom_field" in item for item in findings[0].items)
        finally:
            shutil.move(backup, path)

    def test_model_literal_is_detected(self):
        """Inject a model name into real runtime code and require a FAIL.

        The target must be a file the scanner actually walks. Pointing this at
        a module that no longer exists tested nothing.
        """
        doctor = load_doctor()
        path = os.path.join(BASE, "runtime", "core", "policy.py")
        backup = path + ".bak"
        shutil.copy2(path, backup)
        cache = os.path.join(BASE, "runtime", "core", "__pycache__")
        try:
            with open(path, "a", encoding="utf-8") as handle:
                handle.write("\nLEAKED_DEFAULT = 'gpt-4o-mini'\n")
            findings = [
                f
                for f in doctor.collect(include_slow=False)
                if f.check == "model-independence"
            ]
            assert findings[0].status is doctor.Status.FAIL
            assert findings[0].items, "the offending line must be identified"
        finally:
            shutil.move(backup, path)
            # A stale bytecode entry keyed to the temporary name can make the
            # next run fail on a file that is no longer there.
            if os.path.isdir(cache):
                for name in os.listdir(cache):
                    if name.startswith("policy."):
                        os.remove(os.path.join(cache, name))

    def test_missing_artifact_is_detected(self):
        doctor = load_doctor()
        findings = [f for f in doctor.collect(include_slow=False) if f.check == "required-artifacts"]
        assert findings, "the required-artifacts check did not run"
        # Prove the check can fail by asking it about a path that cannot exist.
        original = doctor.os.path.isfile
        doctor.os.path.isfile = lambda p: False
        try:
            broken = doctor.check_repository_present()
            assert broken[0].status is doctor.Status.FAIL
            assert broken[0].items
        finally:
            doctor.os.path.isfile = original

    def test_entrypoint_budget_failure_is_detected(self):
        doctor = load_doctor()
        original = doctor._run
        doctor._run = lambda argv, cwd=None: (
            0,
            json.dumps(
                {
                    "within_budget": False,
                    "entries": [
                        {
                            "file": "AGENTS.md",
                            "words": 9999,
                            "word_limit": 3200,
                            "within_limit": False,
                        }
                    ],
                }
            ),
        )
        try:
            findings = doctor.check_entrypoint_budget()
            assert findings[0].status is doctor.Status.FAIL
            assert any("AGENTS.md" in item for item in findings[0].items)
        finally:
            doctor._run = original


class TestScannerIsNotBlind:
    def test_relative_imports_are_recognised(self):
        """A scanner that ignores `from .x import y` calls everything orphaned."""
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            module = os.path.join(tmp, "consumer.py")
            with open(module, "w", encoding="utf-8") as handle:
                handle.write("from .attestation import Observation\n")
            names = doctor._imported_names(module)
        assert any("attestation" in name for name in names), (
            f"relative import not recognised; got {names}"
        )

    def test_absolute_imports_are_recognised(self):
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            module = os.path.join(tmp, "consumer.py")
            with open(module, "w", encoding="utf-8") as handle:
                handle.write("from runtime.core.task_graph import TaskGraph\n")
            names = doctor._imported_names(module)
        assert any("task_graph" in name for name in names)

    def test_unparseable_source_does_not_crash_the_scanner(self):
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            broken = os.path.join(tmp, "broken.py")
            with open(broken, "w", encoding="utf-8") as handle:
                handle.write("def (:\n")
            assert doctor._imported_names(broken) == set()

    def test_package_markers_are_not_reported_as_shadowing(self):
        doctor = load_doctor()
        findings = [f for f in doctor.collect(include_slow=False) if f.check == "duplicate-module-names"]
        assert findings, "the duplicate-module-names check did not run"
        assert not any("__init__" in item for item in findings[0].items), (
            "__init__ is a package marker, not a shadowing module"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""The capability probe must report absence honestly.

Observed defect: a tool call to ``bash`` failed with *"No tool named bash is
currently available."* The prompt core gave no warning, so a missing
capability surfaced as an error string rather than a declared gap.

These tests pin the probe's behaviour: it must never claim a capability it did
not verify, must always exit 0 so a host can ask without being blocked, and
must name the degradation behaviour when something is absent.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(BASE, "scripts", "capability-probe.py")

_PROBE = None


def load_probe():
    """Load once so patched module state cannot leak between tests."""
    global _PROBE
    if _PROBE is None:
        spec = importlib.util.spec_from_file_location("capability_probe_under_test", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        finally:
            sys.modules.pop(spec.name, None)
        _PROBE = module
    return _PROBE


class TestProbeOutput:
    def test_json_output_is_valid(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, "--json"],
            cwd=BASE, capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        for key in ("shell", "python", "durable_runtime", "absent_capabilities", "plane"):
            assert key in report

    def test_probe_always_exits_zero(self):
        """A host must be able to ask without being blocked by the answer."""
        result = subprocess.run(
            [sys.executable, SCRIPT], cwd=BASE, capture_output=True, text=True, timeout=120
        )
        assert result.returncode == 0

    def test_report_shape_is_complete(self):
        report = load_probe().report()
        assert isinstance(report["shell"], bool)
        assert isinstance(report["python"], bool)
        assert isinstance(report["durable_runtime"], bool)
        assert isinstance(report["absent_capabilities"], list)
        assert report["plane"] in {"RUNTIME_AVAILABLE", "PROMPT_ONLY"}
        assert report["evidence_grade"] in {"TOOL_ATTESTED", "SELF_REPORTED"}


class TestAbsenceIsReportedNotAssumed:
    def test_absent_shell_is_listed(self, monkeypatch):
        probe = load_probe()
        monkeypatch.setattr(probe, "has_shell_binary", lambda: False)
        report = probe.report()
        assert "shell" in report["absent_capabilities"]
        assert report["shell"] is False

    def test_absent_runtime_downgrades_the_evidence_grade(self, monkeypatch):
        probe = load_probe()
        monkeypatch.setattr(probe, "runtime_available", lambda: False)
        report = probe.report()
        assert report["plane"] == "PROMPT_ONLY"
        assert report["evidence_grade"] == "SELF_REPORTED"
        assert "durable_runtime" in report["absent_capabilities"]

    def test_absent_python_is_listed(self, monkeypatch):
        probe = load_probe()
        monkeypatch.setattr(probe, "has_python", lambda: False)
        report = probe.report()
        assert "python" in report["absent_capabilities"]

    def test_a_crashing_probe_does_not_raise(self, monkeypatch):
        """If capability detection itself fails, degrade rather than crash."""
        probe = load_probe()

        def boom():
            raise RuntimeError("probe exploded")

        monkeypatch.setattr(probe, "has_shell_binary", boom)
        # report() must survive an exploding individual check.
        result = probe.report()
        assert isinstance(result, dict)
        assert "absent_capabilities" in result

    def test_no_capabilities_present_yields_an_empty_list(self, monkeypatch):
        probe = load_probe()
        monkeypatch.setattr(probe, "has_shell_binary", lambda: True)
        monkeypatch.setattr(probe, "has_python", lambda: True)
        monkeypatch.setattr(probe, "runtime_available", lambda: True)
        report = probe.report()
        assert report["absent_capabilities"] == []
        assert report["plane"] == "RUNTIME_AVAILABLE"


class TestPromptCoreCarriesTheRule:
    def test_agents_md_requires_absent_capabilities(self):
        with open(os.path.join(BASE, "AGENTS.md"), encoding="utf-8") as handle:
            text = handle.read()
        preflight = text.split("ultimate-dev-preflight:")[-1].split("```")[0]
        assert "absent_capabilities" in preflight, (
            "preflight must record which capabilities are missing, so an "
            "unrunnable check is reported rather than silently skipped"
        )

    def test_agents_md_tells_a_shellless_host_what_to_do(self):
        with open(os.path.join(BASE, "AGENTS.md"), encoding="utf-8") as handle:
            text = handle.read()
        assert "capability-probe.py" in text
        assert "no shell" in text.lower() or "absent" in text.lower()
        assert "not_run" in text

    def test_grounding_rules_forbid_assuming_a_capability(self):
        with open(os.path.join(BASE, "router", "grounding-rules.md"), encoding="utf-8") as handle:
            text = handle.read()
        assert "Never assume a capability exists" in text
        assert "tool list" in text, (
            "the rule must cover calling a tool the host does not expose"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

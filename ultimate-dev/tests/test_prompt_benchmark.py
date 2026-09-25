#!/usr/bin/env python3
"""Contract tests for the provider-free prompt routing benchmark."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "benchmark-prompt-routing.py"


def run_benchmark() -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_provider_free_benchmark_is_structural_and_honest():
    report = run_benchmark()
    assert report["status"] == "fixture_audit_pass"
    assert report["provenance"]["is_model_benchmark"] is False
    assert report["provenance"]["external_calls"] == 0
    assert report["metrics"]["total_cases"] >= 150
    assert report["metrics"]["negative_or_near_miss_ratio"] >= 0.40
    assert report["metrics"]["missing_expected_deliverable"] == 0
    assert report["metrics"]["ambiguous_without_clarity"] == 0
    assert report["metrics"]["unknown_cases"] >= 1
    assert report["metrics"]["forbidden_route_cases"] >= 50
    assert report["metrics"]["scored"] is False
    assert report["metrics"]["executed_cases"] == 0
    assert report["metrics"]["noncanonical_fixture_domains"] > 0
    assert report["metrics"]["safe_alias_fixture_domains"] > 0
    assert report["metrics"]["ambiguous_fixture_domains"] == 0
    assert report["metrics"]["domain_comparison_unscored_cases"] == 0
    assert any("aliases available" in warning for warning in report["warnings"])
    assert not any("ambiguous labels" in warning for warning in report["warnings"])


def test_benchmark_strict_mode_accepts_the_fixture_audit_without_claiming_a_model_score():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--strict"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "not a model benchmark" in result.stdout


def test_required_contract_and_unknown_route_are_visible():
    report = run_benchmark()
    assert report["metrics"]["deliverables_covered"] >= 20
    assert report["metrics"]["categories"].get("unknown", 0) >= 10
    assert not report["errors"]


def test_structured_capability_gap_is_comparable():
    spec = importlib.util.spec_from_file_location("prompt_benchmark", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    passed, reasons = module._compare(
        {"capability_gap": "partial"},
        {"capability_gap": {"level": "partial", "missing": ["x"]}},
    )
    assert passed, reasons


def test_empty_expected_domains_are_not_scored_as_a_zero_domain_requirement():
    spec = importlib.util.spec_from_file_location("prompt_benchmark_empty_domains", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    passed, reasons = module._compare(
        {"domains": []},
        {"domains": ["software-engineering"]},
    )
    assert passed, reasons


def test_forbidden_domain_aliases_are_normalized_before_comparison():
    spec = importlib.util.spec_from_file_location("prompt_benchmark_forbidden_alias", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    passed, reasons = module._compare(
        {"forbidden_domains": ["backend"]},
        {"activated_forbidden_domains": ["software-engineering"]},
        {"backend": "software-engineering"},
        set(),
    )
    assert not passed
    assert "forbidden_domain_activated" in reasons

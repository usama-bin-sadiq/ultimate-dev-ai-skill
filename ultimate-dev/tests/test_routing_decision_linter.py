#!/usr/bin/env python3
"""Tests for the provider-free routing decision linter."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-routing-decision.py"


def run(decision: dict) -> dict:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "decision.json"
        path.write_text(json.dumps(decision), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(path), "--json", "--strict"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode in {0, 1}, result.stdout + result.stderr
        return json.loads(result.stdout)


def test_valid_canonical_decision_passes():
    report = run({
        "deliverable": "code",
        "size": "moderate",
        "domains": ["software-engineering"],
        "risk": "none",
        "clarity": "clear",
        "capability_gap": "none",
        "route": "coding",
    })
    assert report["ok"], report


def test_linter_rejects_legacy_domain_and_forbidden_route():
    report = run({
        "deliverable": "code",
        "size": "moderate",
        "domains": ["backend"],
        "risk": "none",
        "clarity": "clear",
        "capability_gap": "none",
        "route": "coding",
        "expected_forbidden_domains": ["software-engineering"],
        "activated_forbidden_domains": ["software-engineering"],
    })
    assert not report["ok"]
    assert any("non-canonical" in item for item in report["errors"])
    assert any("forbidden" in item for item in report["errors"])


def test_linter_accepts_structured_capability_gap():
    report = run({
        "deliverable": "answer",
        "size": "moderate",
        "domains": ["unknown-unclassified"],
        "risk": "none",
        "clarity": "resolvable",
        "capability_gap": {"level": "partial", "missing": ["domain-fact"]},
        "route": "universal-task",
    })
    assert report["ok"], report


def test_linter_bounds_self_check_to_one_pass():
    base = {
        "deliverable": "code",
        "size": "atomic",
        "domains": ["software-engineering"],
        "risk": "none",
        "clarity": "clear",
        "capability_gap": "none",
        "route": "coding",
    }
    assert run({**base, "self_check": {"passes": 1, "unresolved": []}})["ok"]
    looping = run({**base, "self_check": {"passes": 2, "unresolved": []}})
    assert not looping["ok"]
    assert any("bounded to one pass" in item for item in looping["errors"])


def test_linter_rejects_unfamiliar_domain_without_a_reported_gap():
    report = run({
        "deliverable": "research",
        "size": "moderate",
        "domains": ["unknown-unclassified"],
        "risk": "none",
        "clarity": "clear",
        "capability_gap": "none",
        "route": "research",
    })
    assert not report["ok"]
    assert any("unknown-unclassified" in item for item in report["errors"])


def test_linter_requires_a_named_impact_for_raised_risk():
    unjustified = {
        "deliverable": "communication",
        "size": "moderate",
        "domains": ["internal-communications"],
        "risk": "data",
        "clarity": "clear",
        "capability_gap": "none",
        "route": "internal-communications",
    }
    report = run(unjustified)
    assert not report["ok"]
    assert any("risk_basis" in item for item in report["errors"])
    justified = run({
        **unjustified,
        "risk_basis": "merges customer personal records from a production export",
    })
    assert justified["ok"], justified


def test_linter_warns_when_none_risk_carries_an_impact_basis():
    report = run({
        "deliverable": "code",
        "size": "atomic",
        "domains": ["software-engineering"],
        "risk": "none",
        "risk_basis": "touches the authentication boundary",
        "clarity": "clear",
        "capability_gap": "none",
        "route": "coding",
    })
    assert report["ok"], report
    assert any("risk 'none'" in item for item in report["warnings"])


def test_linter_rejects_forbidden_domains_restating_the_selection():
    """A self-report about avoided domains must not echo the selected domains."""
    report = run({
        "deliverable": "code",
        "size": "atomic",
        "domains": ["software-engineering"],
        "risk": "none",
        "clarity": "clear",
        "capability_gap": "none",
        "route": "coding",
        "activated_forbidden_domains": ["software-engineering"],
    })
    assert not report["ok"]
    assert any("restates the selected domains" in item for item in report["errors"])


def test_linter_accepts_genuinely_avoided_domains():
    report = run({
        "deliverable": "answer",
        "size": "atomic",
        "domains": ["software-engineering"],
        "risk": "none",
        "clarity": "clear",
        "capability_gap": "none",
        "route": "documentation",
        "activated_forbidden_domains": ["legal-privacy-contracts"],
    })
    assert report["ok"], report


def test_linter_rejects_a_narrative_risk_basis():
    report = run({
        "deliverable": "audit",
        "size": "complex",
        "domains": ["accounting-controls"],
        "risk": "compliance",
        "risk_basis": " ".join(["word"] * 30),
        "clarity": "clear",
        "capability_gap": "none",
        "route": "audit-controls",
    })
    assert not report["ok"]
    assert any("short impact clause" in item for item in report["errors"])

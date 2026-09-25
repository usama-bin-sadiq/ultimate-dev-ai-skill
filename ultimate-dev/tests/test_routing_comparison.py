#!/usr/bin/env python3
"""Tests for recorded host-routing comparison."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "compare-routing-predictions.py"
ALIASES = ROOT / "evals" / "domain-aliases.json"


def test_comparison_normalizes_safe_aliases_and_quarantines_ambiguous_domains():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        gold = root / "gold.json"
        predictions = root / "predictions.json"
        gold.write_text(json.dumps([
            {
                "id": "safe",
                "expected_size": "moderate",
                "expected_domains": ["backend"],
                "expected_risk": "none",
                "expected_deliverable": "code",
                "expected_capability_gap": "none",
            },
            {
                "id": "ambiguous",
                "expected_size": "moderate",
                "expected_domains": ["finance"],
                "expected_risk": "compliance",
                "expected_deliverable": "financial-analysis",
            },
        ]), encoding="utf-8")
        predictions.write_text(json.dumps([
            {
                "id": "safe",
                "size": "moderate",
                "domains": ["software-engineering"],
                "risk": "none",
                "deliverable": "code",
                "capability_gap": {"level": "none", "missing": []},
            },
            {
                "id": "ambiguous",
                "size": "moderate",
                "domains": ["finance-fpa"],
                "risk": "compliance",
                "deliverable": "financial-analysis",
                "capability_gap": "none",
            },
        ]), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable, str(SCRIPT), "--gold", str(gold),
                "--predictions", str(predictions), "--aliases", str(ALIASES),
                "--json", "--strict",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        report = json.loads(result.stdout)
        assert report["metrics"]["passed"] == 1
        assert report["metrics"]["unscored"] == 1
        assert report["metrics"]["domain_comparison_unscored_cases"] == 1
        assert report["metrics"]["failed"] == 0
        assert report["provenance"]["is_independent_model"] is False


def test_comparison_reports_missing_predictions_in_strict_mode():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        gold = root / "gold.json"
        predictions = root / "predictions.json"
        gold.write_text(json.dumps([{"id": "missing", "expected_size": "atomic"}]), encoding="utf-8")
        predictions.write_text("[]", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable, str(SCRIPT), "--gold", str(gold),
                "--predictions", str(predictions), "--aliases", str(ALIASES),
                "--json", "--strict",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        report = json.loads(result.stdout)
        assert report["metrics"]["missing_predictions"] == 1
        assert report["metrics"]["failed"] == 1

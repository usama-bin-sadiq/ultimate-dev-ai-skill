#!/usr/bin/env python3
"""Tests for the provider-free replay regression gate."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "replay-gate.py"
EVIDENCE = Path("/Users/usamakhan/Learning/ultimate-dev/.memory/ultimate-dev/tasks")


def _load_module():
    spec = importlib.util.spec_from_file_location("replay_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(directory: Path, name: str, rows: list[dict]) -> Path:
    path = directory / name
    path.write_text(json.dumps(rows), encoding="utf-8")
    return path


GOLD = [
    {"id": "a", "expected_size": "atomic", "expected_deliverable": "answer", "expected_risk": "none"},
    {"id": "b", "expected_size": "moderate", "expected_deliverable": "code", "expected_risk": "none"},
]


def test_gate_passes_when_predictions_match(tmp_path):
    module = _load_module()
    gold = _write(tmp_path, "gold.json", GOLD)
    predictions = _write(
        tmp_path,
        "predictions.json",
        [
            {"id": "a", "size": "atomic", "deliverable": "answer", "risk": "none"},
            {"id": "b", "size": "moderate", "deliverable": "code", "risk": "none"},
        ],
    )
    report = module.gate(gold, predictions, None, 1.0)
    assert report["gate"]["ok"], report
    assert report["current_metrics"]["pass_rate_scored"] == 1.0


def test_gate_detects_regression_against_baseline(tmp_path):
    module = _load_module()
    gold = _write(tmp_path, "gold.json", GOLD)
    baseline = _write(
        tmp_path,
        "baseline.json",
        [
            {"id": "a", "size": "atomic", "deliverable": "answer", "risk": "none"},
            {"id": "b", "size": "moderate", "deliverable": "code", "risk": "none"},
        ],
    )
    current = _write(
        tmp_path,
        "current.json",
        [
            {"id": "a", "size": "complex", "deliverable": "answer", "risk": "none"},
            {"id": "b", "size": "moderate", "deliverable": "code", "risk": "none"},
        ],
    )
    report = module.gate(gold, current, baseline, 0.0)
    assert not report["gate"]["ok"]
    assert report["gate"]["regressions"] == ["a"]


def test_gate_fails_on_forbidden_domain_activation(tmp_path):
    module = _load_module()
    gold = [
        {
            "id": "a",
            "expected_size": "atomic",
            "expected_deliverable": "answer",
            "expected_risk": "none",
            "expected_forbidden_domains": ["security"],
        }
    ]
    gold_path = _write(tmp_path, "gold.json", gold)
    predictions = _write(
        tmp_path,
        "predictions.json",
        [{"id": "a", "size": "atomic", "deliverable": "answer", "risk": "none", "activated_forbidden_domains": ["security"]}],
    )
    report = module.gate(gold_path, predictions, None, 0.0)
    assert not report["gate"]["ok"]
    assert report["gate"]["forbidden_failures"] == ["a"]


def test_recorded_replay_evidence_is_still_comparable():
    """The gate must remain usable against previously recorded replays."""
    module = _load_module()
    gold = EVIDENCE / "behavioral-and-organization-evaluation-2026-09-25" / "evidence" / "behavioral-gold.json"
    predictions = EVIDENCE / "behavioral-and-organization-evaluation-2026-09-25" / "evidence" / "behavioral-predictions-calibrated.json"
    if not gold.is_file() or not predictions.is_file():
        return
    report = module.gate(gold, predictions, None, 0.0)
    assert report["current_metrics"]["total_cases"] == 32
    assert report["provenance"]["external_calls"] == 0

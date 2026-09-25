#!/usr/bin/env python3
"""Validate local behavioral calibration and holdout fixtures."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "evals" / "calibration-cases.json"
HOLDOUT = ROOT / "evals" / "holdout-cases.json"
LINTER = ROOT / "scripts" / "validate-routing-decision.py"
ENTRYPOINTS = ("SKILL.md", "AGENTS.md", "AGENT.md", "agents/orchestrator.md")


def _load_linter():
    spec = importlib.util.spec_from_file_location("routing_linter", LINTER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _decision(row: dict) -> dict:
    """Normalize a replay row (expected_* fields) or fixture into one record."""
    if "expected" in row:
        return dict(row["expected"])
    return {
        "deliverable": row.get("expected_deliverable"),
        "size": row.get("expected_size"),
        "domains": row.get("expected_domains"),
        "risk": row.get("expected_risk"),
        "risk_basis": row.get("expected_risk_basis"),
        "clarity": row.get("expected_clarity"),
        "capability_gap": row.get("expected_capability_gap"),
        "route": row.get("expected_route"),
    }


def test_calibration_cases_are_valid_against_local_linter():
    data = _load(CALIBRATION)
    assert data["kind"] == "behavioral-calibration-cases"
    assert len(data["cases"]) >= 8
    linter = _load_linter()
    for case in data["cases"]:
        result = linter.validate(case["expected"])
        assert result["ok"], (case["id"], result)
        assert case["reason"]


def test_calibration_cases_cover_observed_failure_classes():
    data = _load(CALIBRATION)
    reasons = " ".join(case["reason"].lower() for case in data["cases"])
    for term in ("bug-fix", "content", "audit", "financial", "unknown", "risk"):
        assert term in reasons


def test_holdout_cases_are_valid_and_canonical():
    data = _load(HOLDOUT)
    assert data["kind"] == "behavioral-holdout-cases"
    assert data["provenance"]["is_model_benchmark"] is False
    assert data["provenance"]["external_calls"] == 0
    assert len(data["cases"]) >= 10
    linter = _load_linter()
    identifiers = set()
    for case in data["cases"]:
        assert case["id"] not in identifiers
        identifiers.add(case["id"])
        result = linter.validate(_decision(case))
        assert result["ok"], (case["id"], result)


def test_holdout_oracle_limits_are_declared():
    data = _load(HOLDOUT)
    oracle = data["oracle"]
    assert oracle["status"] == "reference_only"
    assert set(oracle["reliable_fields"]) == {"deliverable", "size", "domains", "route"}
    assert set(oracle["unreliable_fields"]) == {"risk", "clarity", "capability_gap"}
    assert data["provenance"]["is_model_benchmark"] is False


def test_holdout_prompts_are_not_embedded_in_entrypoints():
    data = _load(HOLDOUT)
    prompts = [case["task"] for case in data["cases"]]
    for relative in ENTRYPOINTS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        for prompt in prompts:
            assert prompt not in text, f"holdout prompt leaked into {relative}"


def test_holdout_and_calibration_do_not_overlap():
    calibration = _load(CALIBRATION)
    holdout = _load(HOLDOUT)
    calibration_ids = {case["id"] for case in calibration["cases"]}
    holdout_ids = {case["id"] for case in holdout["cases"]}
    assert not calibration_ids.intersection(holdout_ids)
    calibration_prompts = {case["task"].lower() for case in calibration["cases"]}
    holdout_prompts = {case["task"].lower() for case in holdout["cases"]}
    assert not calibration_prompts.intersection(holdout_prompts)

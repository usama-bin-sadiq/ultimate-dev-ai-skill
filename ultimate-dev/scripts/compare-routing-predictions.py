#!/usr/bin/env python3
"""Compare saved host-routing predictions with exported expectations.

This tool is provider-free and dependency-free. It compares a recorded host
session; it does not call a model and does not claim independent model quality.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ALIASES = ROOT / "evals" / "domain-aliases.json"
FIELDS = {
    "size": "expected_size",
    "risk": "expected_risk",
    "deliverable": "expected_deliverable",
    "route": "expected_route",
    "clarity": "expected_clarity",
    "capability_gap": "expected_capability_gap",
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _value(value: Any) -> Any:
    if isinstance(value, dict) and "level" in value:
        return value.get("level")
    return value


def _domains(values: list[Any], aliases: dict[str, str]) -> set[str]:
    return {aliases.get(str(value), str(value)) for value in values or []}


def compare(gold_path: Path, predictions_path: Path, aliases_path: Path = DEFAULT_ALIASES) -> dict[str, Any]:
    gold_rows = _load(gold_path)
    prediction_rows = _load(predictions_path)
    if not isinstance(gold_rows, list) or not isinstance(prediction_rows, list):
        raise ValueError("gold and predictions must be JSON arrays")
    policy = _load(aliases_path) if aliases_path.is_file() else {}
    aliases = policy.get("safe_aliases", {}) if isinstance(policy, dict) else {}
    ambiguous = set(policy.get("ambiguous_labels", [])) if isinstance(policy, dict) else set()
    gold = {str(row.get("id")): row for row in gold_rows if isinstance(row, dict) and row.get("id")}
    predictions = {str(row.get("id")): row for row in prediction_rows if isinstance(row, dict) and row.get("id")}
    missing = sorted(set(gold) - set(predictions))
    extra = sorted(set(predictions) - set(gold))
    results: list[dict[str, Any]] = []
    field_totals = {field: 0 for field in FIELDS}
    field_matches = {field: 0 for field in FIELDS}
    passed = failed = unscored = 0
    domain_comparison_unscored_cases = 0
    for identifier, expected in gold.items():
        actual = predictions.get(identifier)
        reasons: list[str] = []
        case_unscored = False
        if actual is None:
            results.append({"id": identifier, "status": "missing_prediction", "mismatches": ["missing_prediction"]})
            failed += 1
            continue
        for field, expected_key in FIELDS.items():
            if expected_key not in expected:
                continue
            field_totals[field] += 1
            if str(_value(actual.get(field))).lower() == str(expected[expected_key]).lower():
                field_matches[field] += 1
            else:
                reasons.append(field)
        expected_domains = expected.get("expected_domains") or []
        if expected_domains:
            if set(map(str, expected_domains)).intersection(ambiguous):
                case_unscored = True
                domain_comparison_unscored_cases += 1
            elif _domains(expected_domains, aliases) != _domains(actual.get("domains") or [], aliases):
                reasons.append("domains")
        forbidden = expected.get("expected_forbidden_domains") or []
        if forbidden and set(map(str, forbidden)).intersection(map(str, actual.get("activated_forbidden_domains") or [])):
            reasons.append("forbidden_domains")
        if reasons:
            status = "fail"
            failed += 1
        elif case_unscored:
            status = "unscored"
            unscored += 1
        else:
            status = "pass"
            passed += 1
        results.append({"id": identifier, "status": status, "mismatches": reasons})
    total = len(gold)
    scored = passed + failed
    return {
        "provenance": {
            "mode": "recorded_host_replay_comparison",
            "is_independent_model": False,
            "external_calls": 0,
            "gold": str(gold_path),
            "predictions": str(predictions_path),
        },
        "metrics": {
            "total_cases": total,
            "scored_cases": scored,
            "passed": passed,
            "failed": failed,
            "unscored": unscored,
            "domain_comparison_unscored_cases": domain_comparison_unscored_cases,
            "pass_rate_scored": round(passed / scored, 4) if scored else None,
            "missing_predictions": len(missing),
            "extra_predictions": len(extra),
            "field_agreement": {
                field: round(field_matches[field] / field_totals[field], 4)
                for field in FIELDS if field_totals[field]
            },
        },
        "missing_predictions": missing,
        "extra_predictions": extra,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--aliases", type=Path, default=DEFAULT_ALIASES)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = compare(args.gold, args.predictions, args.aliases)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"compare-routing-predictions: {exc}")
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        metrics = report["metrics"]
        print(f"status: {'fail' if metrics['failed'] else 'pass'}")
        print(f"passed: {metrics['passed']}/{metrics['scored_cases']} scored")
        print(f"unscored: {metrics['unscored']}; missing: {metrics['missing_predictions']}")
        if report["missing_predictions"]:
            print(f"missing: {', '.join(report['missing_predictions'])}")
    return 1 if args.strict and report["metrics"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

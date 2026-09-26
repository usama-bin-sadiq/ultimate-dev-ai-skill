#!/usr/bin/env python3
"""Gate a recorded routing replay against a baseline and a minimum pass rate.

This tool is provider-free. It compares saved prediction files; it does not call
a model. A gate fails when a previously passing case regresses, when the pass
rate drops below a threshold, or when a prediction violates a recorded
forbidden-domain expectation.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
COMPARE_SCRIPT = ROOT / "scripts" / "compare-routing-predictions.py"
ALIASES = ROOT / "evals" / "domain-aliases.yaml"


def _load_compare_module() -> Any:
    spec = importlib.util.spec_from_file_location("compare_routing", COMPARE_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _status_map(report: dict[str, Any]) -> dict[str, str]:
    return {str(row["id"]): str(row["status"]) for row in report["results"] if "id" in row}


def gate(
    gold: Path,
    current: Path,
    baseline: Path | None = None,
    min_pass_rate: float = 0.0,
) -> dict[str, Any]:
    compare = _load_compare_module()
    current_report = compare.compare(gold, current, ALIASES)
    current_status = _status_map(current_report)

    regressions: list[str] = []
    improved: list[str] = []
    baseline_status: dict[str, str] = {}
    baseline_report: dict[str, Any] | None = None
    if baseline is not None:
        baseline_report = compare.compare(gold, baseline, ALIASES)
        baseline_status = _status_map(baseline_report)
        for identifier, status in baseline_status.items():
            new_status = current_status.get(identifier)
            if status == "pass" and new_status != "pass":
                regressions.append(identifier)
            elif status != "pass" and new_status == "pass":
                improved.append(identifier)

    metrics = current_report["metrics"]
    rate = metrics["pass_rate_scored"] or 0.0
    forbidden_failures = sorted(
        str(row["id"]) for row in current_report["results"] if "forbidden_domains" in row.get("mismatches", [])
    )
    failures: list[str] = []
    if regressions:
        failures.append(f"regressions: {len(regressions)}")
    if rate < min_pass_rate:
        failures.append(f"pass rate {rate} below minimum {min_pass_rate}")
    if forbidden_failures:
        failures.append(f"forbidden-domain activations: {len(forbidden_failures)}")
    if metrics["missing_predictions"]:
        failures.append(f"missing predictions: {metrics['missing_predictions']}")

    return {
        "provenance": {
            "mode": "replay_gate_over_recorded_predictions",
            "is_independent_model": False,
            "external_calls": 0,
            "gold": str(gold),
            "current": str(current),
            "baseline": str(baseline) if baseline else None,
        },
        "gate": {
            "ok": not failures,
            "failures": failures,
            "min_pass_rate": min_pass_rate,
            "regressions": sorted(regressions),
            "improved": sorted(improved),
            "forbidden_failures": forbidden_failures,
        },
        "baseline_metrics": baseline_report["metrics"] if baseline_report else None,
        "current_metrics": metrics,
        "field_agreement": metrics["field_agreement"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--min-pass-rate", type=float, default=0.0)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = gate(args.gold, args.predictions, args.baseline, args.min_pass_rate)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"replay-gate: {exc}")
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "pass" if report["gate"]["ok"] else "fail"
        metrics = report["current_metrics"]
        print(f"status: {status}")
        print(
            f"passed: {metrics['passed']}/{metrics['scored_cases']} scored"
            f" ({metrics['pass_rate_scored']})"
        )
        if report["baseline_metrics"]:
            base = report["baseline_metrics"]
            print(f"baseline: {base['passed']}/{base['scored_cases']} scored ({base['pass_rate_scored']})")
        if report["gate"]["regressions"]:
            print(f"regressions: {', '.join(report['gate']['regressions'])}")
        if report["gate"]["improved"]:
            print(f"improved: {len(report['gate']['improved'])}")
        for failure in report["gate"]["failures"]:
            print(f"gate failure: {failure}")
    return 1 if args.strict and not report["gate"]["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

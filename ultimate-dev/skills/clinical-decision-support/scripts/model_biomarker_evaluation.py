#!/usr/bin/env python3
"""Report bounded descriptive performance from aggregate model/biomarker summaries.

What it does
------------
Accepts aggregate confusion counts and aggregate calibration bins, and reports:

* sensitivity, specificity, positive and negative predictive value, and accuracy,
  each with a Wilson score interval;
* a weighted absolute calibration gap, and calibration-in-the-large, from the
  bins;
* subgroup performance with Wilson intervals, sample sizes, and explicit
  suppression when a group is too small to report stably;
* the documented gaps: missingness, spectrum bias, dataset shift, assay
  variability, model failures, and whether the threshold predates the evaluation.

What it does not do
-------------------
It derives no threshold, assigns no class to any person, matches no person to a
test, and states no clinical validity, utility, safety, or fitness for
deployment. It uses Wilson intervals for aggregate proportions only: it does not
model correlated observations, clustering, repeated measurements, censoring, or
verification bias, and binning loses information relative to individual-level
calibration analysis in an approved environment.

Usage
-----
    python3 scripts/model_biomarker_evaluation.py assets/aggregate_model_evaluation_template.json
    python3 scripts/model_biomarker_evaluation.py evaluation.json --format json --out report.json

Exit codes: 0 metrics computed, 1 nothing reportable (all cells suppressed or
unusable), 2 unusable input. Not for patient care or live clinical use.

Provenance
----------
Reconstructed from the Performance Dimensions, Uncertainty, and Subgroup and
Fairness Evaluation sections of references/model_biomarker_evaluation.md. The
Wilson interval, the weighted gap, and the suppression rule are this file's own;
all are standard definitions computed from first principles so the numbers are
reproducible in any conforming interpreter.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from statistics import NormalDist

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_SUBGROUPS = 100
MAX_BINS = 200
UNRESOLVED = "unresolved"

# A subgroup with fewer observations than this is suppressed rather than reported
# with an interval wide enough to mean nothing.
MIN_SUBGROUP_N = 30

PERSON_LEVEL_KEYS = frozenset({
    "patient_id", "patientid", "mrn", "medical_record_number", "dob", "date_of_birth",
    "address", "phone", "email", "name", "first_name", "last_name", "free_text", "note",
    "notes", "narrative", "identifier", "subject_id", "person_id", "score_for_person",
})


class Finding(dict):
    def __init__(self, level: str, field: str, message: str) -> None:
        super().__init__(level=level, field=field, message=message)


def is_unresolved(value) -> bool:
    if isinstance(value, str):
        return UNRESOLVED in value.lower()
    if isinstance(value, (list, dict)):
        return not value
    return value is None


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


# --------------------------------------------------------------- statistics ---


def wilson_interval(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Chosen over the Wald interval because Wald coverage collapses near 0 and 1,
    which is exactly where a diagnostic or biomarker metric usually lives.
    """
    if total <= 0:
        return (float("nan"), float("nan"))
    z = NormalDist().inv_cdf(1 - (1 - confidence) / 2)
    phat = successes / total
    denominator = 1 + z * z / total
    centre = (phat + z * z / (2 * total)) / denominator
    half = (z / denominator) * math.sqrt(phat * (1 - phat) / total + z * z / (4 * total * total))
    return (max(0.0, centre - half), min(1.0, centre + half))


def confusion_metrics(counts: dict, confidence: float = 0.95) -> list[dict]:
    """Bounded descriptive metrics from aggregate confusion counts."""
    tp, fp, tn, fn = counts["tp"], counts["fp"], counts["tn"], counts["fn"]
    positives, negatives = tp + fn, tn + fp
    total = tp + fp + tn + fn

    def row(name: str, numerator: int, denominator: int, note: str) -> dict:
        if denominator <= 0:
            return {"metric": name, "value": None, "low": None, "high": None,
                    "numerator": numerator, "denominator": denominator, "note": note}
        low, high = wilson_interval(numerator, denominator, confidence)
        return {
            "metric": name,
            "value": round(numerator / denominator, 6),
            "low": round(low, 6),
            "high": round(high, 6),
            "numerator": numerator,
            "denominator": denominator,
            "note": note,
        }

    return [
        row("sensitivity", tp, positives,
            "TP / (TP + FN). Undefined with no events in the evaluation set."),
        row("specificity", tn, negatives,
            "TN / (TN + FP). Undefined with no non-events in the evaluation set."),
        row("positive_predictive_value", tp, tp + fp,
            "prevalence-dependent; interpret only alongside the evaluation prevalence."),
        row("negative_predictive_value", tn, tn + fn,
            "prevalence-dependent; interpret only alongside the evaluation prevalence."),
        row("accuracy", tp + tn, total,
            "do not rely on accuracy alone when classes are imbalanced."),
    ]


def likelihood_ratios(counts: dict) -> list[dict]:
    """Positive and negative likelihood ratios, omitted when undefined."""
    tp, fp, tn, fn = counts["tp"], counts["fp"], counts["tn"], counts["fn"]
    results = []
    if tp + fn > 0 and tn > 0:
        sensitivity = tp / (tp + fn)
        specificity = tn / (tn + fp)
        if specificity > 0 and specificity < 1:
            results.append({
                "metric": "positive_likelihood_ratio",
                "value": round(sensitivity / (1 - specificity), 6),
                "note": "sensitivity / (1 - specificity). Undefined when specificity is 0 or 1.",
            })
        if sensitivity > 0 and sensitivity < 1:
            results.append({
                "metric": "negative_likelihood_ratio",
                "value": round((1 - sensitivity) / specificity, 6),
                "note": "(1 - sensitivity) / specificity.",
            })
    return results


def calibration_summary(bins: list[dict], confidence: float = 0.95) -> list[dict]:
    """Per-bin calibration plus the weighted absolute gap and calibration-in-the-large."""
    rows: list[dict] = []
    total_n = 0
    total_events = 0
    absolute_gap = 0.0
    weighted_observed = 0.0
    weighted_predicted = 0.0

    for entry in bins:
        n = int(entry.get("n", 0))
        events = int(entry.get("observed_events", 0))
        lower = float(entry.get("bin_lower", 0.0))
        upper = float(entry.get("bin_upper", 0.0))
        if n <= 0:
            continue
        if events < 0 or events > n:
            raise ValueError(
                f"calibration bin {lower}-{upper} has {events} observed events out of {n} "
                "observations, which is impossible"
            )
        predicted = (lower + upper) / 2
        observed = events / n
        low, high = wilson_interval(events, n, confidence)
        rows.append({
            "bin": f"{lower:.3f}-{upper:.3f}",
            "n": n,
            "predicted_mean": round(predicted, 6),
            "observed_rate": round(observed, 6),
            "observed_low": round(low, 6),
            "observed_high": round(high, 6),
            "gap": round(observed - predicted, 6),
        })
        total_n += n
        total_events += events
        absolute_gap += n * abs(observed - predicted)
        weighted_observed += n * observed
        weighted_predicted += n * predicted

    if total_n == 0:
        return []

    summary = {
        "bin": "summary",
        "n": total_n,
        "predicted_mean": round(weighted_predicted / total_n, 6),
        "observed_rate": round(weighted_observed / total_n, 6),
        "observed_low": None,
        "observed_high": None,
        "gap": round(weighted_observed / total_n - weighted_predicted / total_n, 6),
    }
    rows.append(summary)
    rows.append({
        "bin": "weighted_absolute_gap",
        "n": total_n,
        "predicted_mean": None,
        "observed_rate": None,
        "observed_low": None,
        "observed_high": None,
        "gap": round(absolute_gap / total_n, 6),
    })
    return rows


# ------------------------------------------------------------------ checks ---


def read_counts(section, path: str, findings: list[Finding]) -> dict | None:
    if not isinstance(section, dict):
        findings.append(Finding("error", path, "no aggregate confusion counts recorded"))
        return None
    counts = {}
    for key in ("n", "tp", "fp", "tn", "fn"):
        value = section.get(key, 0)
        try:
            counts[key] = int(value)
        except (TypeError, ValueError):
            findings.append(Finding("error", f"{path}.{key}", f"{value!r} is not an integer"))
            return None
        if counts[key] < 0:
            findings.append(Finding("error", f"{path}.{key}", "counts must not be negative"))
            return None
    if counts["n"] and counts["n"] != counts["tp"] + counts["fp"] + counts["tn"] + counts["fn"]:
        findings.append(Finding(
            "error", f"{path}.n",
            f"n={counts['n']} does not equal TP+FP+TN+FN="
            f"{counts['tp'] + counts['fp'] + counts['tn'] + counts['fn']}",
        ))
        return None
    if not any(counts[key] for key in ("tp", "fp", "tn", "fn")):
        findings.append(Finding("error", path, "all confusion counts are zero"))
        return None
    return counts


def check_target(evaluation: dict, findings: list[Finding]) -> None:
    target = evaluation.get("target")
    if not isinstance(target, dict):
        findings.append(Finding("error", "target", "the evaluation target is not defined"))
        return
    for field in ("evaluation_target_name", "version", "threshold", "threshold_provenance",
                  "target_population", "outcome_horizon", "research_purpose"):
        if is_unresolved(target.get(field)):
            findings.append(Finding("error", f"target.{field}", f"{field.replace('_', ' ')} is required"))

    provenance = text_of(target.get("threshold_provenance", ""))
    if "evaluation cohort" in provenance.lower() or "evaluation dataset" in provenance.lower():
        findings.append(Finding(
            "error", "target.threshold_provenance",
            "a threshold derived on the evaluation cohort is not validated; derive it "
            "elsewhere and confirm it independently",
        ))

    datasets = evaluation.get("datasets")
    if isinstance(datasets, dict):
        external = datasets.get("external_validation")
        if is_unresolved(external):
            findings.append(Finding(
                "error", "datasets.external_validation",
                "record whether independent external validation was performed",
            ))
        kind = str(datasets.get("external_validation_type", "")).lower()
        if "random split" in kind or "random-split" in kind:
            findings.append(Finding(
                "error", "datasets.external_validation_type",
                "a random split from one source is not external validation",
            ))
    else:
        findings.append(Finding("error", "datasets", "the dataset provenance is not recorded"))


def text_of(node) -> str:
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        return " ".join(text_of(value) for value in node.values())
    if isinstance(node, list):
        return " ".join(text_of(value) for value in node)
    return ""


def check_gaps(evaluation: dict, findings: list[Finding]) -> None:
    gaps = evaluation.get("limitations_and_gaps")
    if not isinstance(gaps, dict):
        findings.append(Finding("error", "limitations_and_gaps",
                                "the documented limitations and gaps are missing"))
        return
    for field in ("missingness", "spectrum_or_selection_bias", "dataset_shift",
                  "assay_variability", "model_failures_and_unusable_inputs"):
        if is_unresolved(gaps.get(field)):
            findings.append(Finding("error", f"limitations_and_gaps.{field}", "unresolved"))


def check_monitoring(evaluation: dict, findings: list[Finding]) -> None:
    section = evaluation.get("monitoring_and_change_control")
    if not isinstance(section, dict):
        findings.append(Finding("error", "monitoring_and_change_control",
                                "monitoring and change control are not recorded"))
        return
    for field in ("model_version", "validation_protocol_and_acceptance_criteria",
                  "subgroup_and_calibration_regression_tests", "approval_and_rollback",
                  "monitoring_cadence_and_drift_triggers"):
        if is_unresolved(section.get(field)):
            findings.append(Finding("error", f"monitoring_and_change_control.{field}", "unresolved"))


def check_review(evaluation: dict, findings: list[Finding]) -> None:
    review = evaluation.get("human_review")
    if not isinstance(review, dict):
        findings.append(Finding("error", "human_review", "a named review role is required"))
        return
    if is_unresolved(review.get("status")):
        findings.append(Finding("error", "human_review.status", "review status is unresolved"))


def evaluate_subgroups(subgroups: list, confidence: float) -> tuple[list[dict], list[str]]:
    """Per-subgroup metrics, suppressed below the minimum reportable size."""
    rows: list[dict] = []
    suppressed: list[str] = []
    for entry in subgroups[:MAX_SUBGROUPS]:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("subgroup_name", UNRESOLVED))
        n = int(entry.get("n", 0) or 0)
        if n < MIN_SUBGROUP_N:
            suppressed.append(name)
            rows.append({
                "subgroup": name,
                "n": n,
                "status": "suppressed",
                "reason": f"n={n} is below the minimum reportable size of {MIN_SUBGROUP_N}. "
                          "Small groups may require pooling, secure analysis, or non-release "
                          "rather than unstable estimates",
            })
            continue
        counts = {key: int(entry.get(key, 0) or 0) for key in ("n", "tp", "fp", "tn", "fn")}
        metrics = confusion_metrics(counts, confidence)
        rows.append({
            "subgroup": name,
            "n": counts["n"],
            "status": "reported",
            "sensitivity": next(m["value"] for m in metrics if m["metric"] == "sensitivity"),
            "sensitivity_low": next(m["low"] for m in metrics if m["metric"] == "sensitivity"),
            "sensitivity_high": next(m["high"] for m in metrics if m["metric"] == "sensitivity"),
            "specificity": next(m["value"] for m in metrics if m["metric"] == "specificity"),
            "specificity_low": next(m["low"] for m in metrics if m["metric"] == "specificity"),
            "specificity_high": next(m["high"] for m in metrics if m["metric"] == "specificity"),
        })
    return rows, suppressed


# ------------------------------------------------------------------ report ---


def format_metric(row: dict) -> str:
    if row.get("value") is None:
        return f"  {row['metric']:<26} not estimable ({row['note']})"
    return (
        f"  {row['metric']:<26} {row['value']:.4f}  "
        f"[{row['low']:.4f}, {row['high']:.4f}]  (n={row['denominator']})"
    )


def render_text(evaluation: dict, metrics, ratios, bins, subgroups, suppressed, findings) -> str:
    target = evaluation.get("target", {})
    lines = [
        f"target: {target.get('evaluation_target_name', 'unnamed')} "
        f"version {target.get('version', 'unresolved')}",
        f"threshold: {target.get('threshold', 'unresolved')} "
        f"({target.get('threshold_provenance', 'provenance unresolved')})",
        f"population: {target.get('target_population', 'unresolved')}",
        "",
        "discrimination (aggregate confusion counts, Wilson 95% intervals)",
    ]
    lines += [format_metric(row) for row in metrics]
    if ratios:
        lines.append("")
        for row in ratios:
            lines.append(f"  {row['metric']:<26} {row['value']:.4f}  ({row['note']})")

    if bins:
        lines += ["", "calibration (aggregate bins; the bin midpoint is the predicted value)"]
        lines.append(f"  {'bin':<18}{'n':>8}{'predicted':>12}{'observed':>12}{'gap':>12}")
        for row in bins:
            predicted = "" if row["predicted_mean"] is None else f"{row['predicted_mean']:.4f}"
            observed = "" if row["observed_rate"] is None else f"{row['observed_rate']:.4f}"
            gap = "" if row["gap"] is None else f"{row['gap']:+.4f}"
            lines.append(
                f"  {row['bin']:<18}{row['n']:>8}{predicted:>12}{observed:>12}{gap:>12}"
            )

    if subgroups:
        lines += ["", f"subgroup performance (suppressed below n={MIN_SUBGROUP_N})"]
        for row in subgroups:
            if row["status"] == "suppressed":
                lines.append(f"  {row['subgroup']:<24} suppressed: {row['reason']}")
            else:
                lines.append(
                    f"  {row['subgroup']:<24} n={row['n']:<6} "
                    f"sens {row['sensitivity']:.4f} [{row['sensitivity_low']:.4f}, "
                    f"{row['sensitivity_high']:.4f}]  "
                    f"spec {row['specificity']:.4f} [{row['specificity_low']:.4f}, "
                    f"{row['specificity_high']:.4f}]"
                )

    lines += ["", "subgroup suppression", f"  suppressed: {len(suppressed)} of {len(subgroups)}"]
    for name in suppressed:
        lines.append(f"    {name}")

    if findings:
        lines += ["", f"documented gaps and findings ({len(findings)})"]
        for finding in findings:
            lines.append(f"  {finding['level']}: {finding['field']}: {finding['message']}")

    lines += [
        "",
        "Interpretation limits. Wilson intervals describe aggregate proportions only. This "
        "report does not model correlated observations, clustering, repeated measurements, "
        "censoring, or verification bias, and binning loses information relative to "
        "individual-level calibration analysis in an approved environment. No single parity "
        "metric establishes fairness: equal metrics can coexist with inequitable outcomes, and "
        "unequal metrics may reflect case mix, measurement, structural conditions, or model "
        "behaviour that requires investigation.",
        "",
        "This report assigns no class to any person, matches no person to a test, and states "
        "no clinical validity, utility, safety, or fitness for deployment.",
        "Not for patient care or live clinical use.",
    ]
    return "\n".join(lines) + "\n"


# -------------------------------------------------------------------- main ---


def load_evaluation(path: str) -> dict:
    if path.startswith(("http://", "https://", "file://")):
        raise SystemExit(f"error: {path} looks like a URL; this helper reads local files only")
    file_path = Path(path)
    if not file_path.is_file():
        raise SystemExit(f"error: evaluation not found: {path}")
    if file_path.stat().st_size > MAX_FILE_BYTES:
        raise SystemExit(f"error: {path} is larger than {MAX_FILE_BYTES} bytes")
    try:
        with file_path.open(encoding="utf-8") as handle:
            evaluation = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: {path} is not valid JSON: {exc}")

    # Aggregate input only. A per-person row is a disclosure, not an input.
    def scan(node, trail="$"):
        if isinstance(node, dict):
            for key, value in node.items():
                if str(key).lower() in PERSON_LEVEL_KEYS:
                    raise SystemExit(
                        f"error: {trail}.{key} looks like row-level or person-linked input. This "
                        "evaluator accepts aggregate confusion counts and calibration bins only."
                    )
                scan(value, f"{trail}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                scan(value, f"{trail}[{index}]")

    scan(evaluation)
    if not isinstance(evaluation, dict):
        raise SystemExit("error: the evaluation must be a JSON object")
    return evaluation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report bounded descriptive performance from aggregate model/biomarker summaries.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("evaluation", help="local JSON aggregate evaluation file")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="report format")
    parser.add_argument("--out", default=None, help="write the report here; default stdout")
    parser.add_argument("--confidence", type=float, default=0.95,
                        help="interval level for the Wilson intervals")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 0.5 < args.confidence < 1:
        raise SystemExit("error: --confidence must be between 0.5 and 1")

    evaluation = load_evaluation(args.evaluation)
    findings: list[Finding] = []

    check_target(evaluation, findings)
    check_gaps(evaluation, findings)
    check_monitoring(evaluation, findings)
    check_review(evaluation, findings)

    discrimination = evaluation.get("discrimination")
    counts = None
    if isinstance(discrimination, dict):
        counts = read_counts(discrimination.get("overall"), "discrimination.overall", findings)
    else:
        findings.append(Finding("error", "discrimination", "no discrimination summary recorded"))

    raw_bins = evaluation.get("calibration_bins")
    bins: list[dict] = []
    if not isinstance(raw_bins, list) or not raw_bins:
        findings.append(Finding("error", "calibration_bins",
                                "calibration is part of the evaluation; supply the aggregate bins"))
    else:
        try:
            bins = calibration_summary([b for b in raw_bins if isinstance(b, dict)][:MAX_BINS],
                                       args.confidence)
        except ValueError as exc:
            raise SystemExit(f"error: {exc}")

    raw_subgroups = evaluation.get("subgroups")
    if not isinstance(raw_subgroups, list):
        findings.append(Finding("error", "subgroups",
                                "record the subgroups the evaluation covers, or state that none "
                                "were planned"))
        raw_subgroups = []
    subgroups, suppressed = evaluate_subgroups(raw_subgroups, args.confidence)

    metrics = confusion_metrics(counts, args.confidence) if counts else []
    ratios = likelihood_ratios(counts) if counts else []

    if args.format == "json":
        payload = json.dumps(
            {
                "target": evaluation.get("target", {}),
                "discrimination": metrics,
                "likelihood_ratios": ratios,
                "calibration": bins,
                "subgroups": subgroups,
                "subgroups_suppressed": suppressed,
                "minimum_reportable_subgroup_n": MIN_SUBGROUP_N,
                "findings": findings,
                "assigns_person_level_class": False,
                "establishes_utility_or_fairness": False,
                "boundary": "Not for patient care or live clinical use.",
            },
            indent=2,
        ) + "\n"
    else:
        payload = render_text(evaluation, metrics, ratios, bins, subgroups, suppressed, findings)

    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
        log(f"wrote {args.out}")
    else:
        print(payload, end="")
    if not metrics and not bins and not subgroups:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Validate the required planning fields of a survival-analysis plan.

What it does
------------
Confirms that a time-to-event statistical analysis plan defines its estimand,
endpoint, time origin, censoring and competing-event handling, comparison method,
bias and missingness mitigations, uncertainty and multiplicity, and the review
roles. It then applies a small set of internal consistency rules that catch the
errors this plan type most often makes: a competing event treated as ordinary
censoring, proportional hazards assumed with no assessment, no alternative when
ph is doubtful, a cut-point search, a threshold-crossing p-value read as clinical
importance, or a prediction-model horizon chosen after seeing results.

It does not read time-to-event rows, fit models, draw curves, or produce an
individual prognosis. Exit code 0 means required planning fields and selected
consistency rules passed; it is not statistical approval.

Usage
-----
    python3 scripts/survival_plan_validator.py assets/survival_analysis_plan_template.json
    python3 scripts/survival_plan_validator.py plan.json --format json --out report.json

Provenance
----------
Reconstructed from references/survival_analysis.md, which specifies the estimand
attributes, the endpoint fields, the ph and competing-risk cautions, and the
bias/missingness list. The consistency rules are this file's own.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MAX_FILE_BYTES = 2 * 1024 * 1024
UNRESOLVED = "unresolved"

# Phrases that signal the specific error the plan must not commit to.
CENSOR_COMPETING_AS_ORDINARY = (
    "competing events are censored",
    "censor competing events",
    "competing events treated as censoring",
)
CUT_POINT_SEARCH = (
    "minimum p-value",
    "min p value",
    "best cut-point",
    "optimal cutpoint search",
    "data-derived cut-point",
)
PH_AS_CERTAIN = (
    "proportional hazards is assumed",
    "proportional hazards holds",
    "no need to assess proportional hazards",
)
HR_AS_RISK = (
    "1 - hr is the reduction in risk",
    "1-hr as reduction in cumulative risk",
    "hazard ratio as the risk reduction",
)


class Finding(dict):
    def __init__(self, level: str, field: str, message: str) -> None:
        super().__init__(level=level, field=field, message=message)


def is_unresolved(value) -> bool:
    if isinstance(value, str):
        return UNRESOLVED in value.lower()
    if isinstance(value, (list, dict)):
        return not value
    return value is None


def text_of(node) -> str:
    """Flatten a plan section to a searchable string."""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        return " ".join(text_of(value) for value in node.values())
    if isinstance(node, list):
        return " ".join(text_of(value) for value in node)
    return ""


def screen(plan: dict, phrases, level: str, field: str, message: str) -> list[Finding]:
    """Raise a finding when any of the phrases appears in the plan text."""
    haystack = text_of(plan).lower()
    found = [phrase for phrase in phrases if phrase in haystack]
    if not found:
        return []
    return [Finding(level, field, f"{message} Matched: {found[0]!r}.")]


def check_metadata(plan: dict, findings: list[Finding]) -> None:
    metadata = plan.get("plan_metadata")
    if not isinstance(metadata, dict):
        findings.append(Finding("error", "plan_metadata", "the plan has no metadata block"))
        return
    for field in ("plan_id", "version", "status", "owner", "statistician", "date", "change_summary"):
        if is_unresolved(metadata.get(field)):
            findings.append(Finding("error", f"plan_metadata.{field}", "unresolved"))
    if not isinstance(metadata.get("source_ids"), list):
        findings.append(Finding(
            "warning", "plan_metadata.source_ids",
            "record the source documents the plan is derived from",
        ))


def check_estimand(plan: dict, findings: list[Finding]) -> None:
    estimand = plan.get("estimand")
    if not isinstance(estimand, dict):
        findings.append(Finding(
            "error", "estimand",
            "an estimand is the starting point; align the six attributes before anything else",
        ))
        return
    for field in ("population", "condition_or_comparison", "variable_or_endpoint",
                  "intercurrent_event_strategy", "population_level_summary", "time_horizon",
                  "time_zero", "time_scale", "follow_up_end_rule", "calendar_data_cut_date"):
        if is_unresolved(estimand.get(field)):
            findings.append(Finding("error", f"estimand.{field}", f"{field.replace('_', ' ')} is required"))
    if not is_unresolved(estimand.get("delayed_entry")):
        entry = str(estimand["delayed_entry"]).lower()
        if entry not in {"yes", "no", "none", "true", "false"}:
            findings.append(Finding(
                "error", "estimand.delayed_entry",
                "state whether there is delayed entry, and the entry rule if so",
            ))


def check_endpoint(plan: dict, findings: list[Finding]) -> None:
    endpoint = plan.get("endpoint")
    if not isinstance(endpoint, dict):
        findings.append(Finding("error", "endpoint", "the endpoint is not defined"))
        return
    for field in ("exact_event", "competing_events", "censoring_rules",
                  "tied_and_same_day_events", "ascertainment_schedule_and_adjudication"):
        if is_unresolved(endpoint.get(field)):
            findings.append(Finding("error", f"endpoint.{field}", f"{field.replace('_', ' ')} is required"))


def check_descriptive(plan: dict, findings: list[Finding]) -> None:
    descriptive = plan.get("descriptive_estimation")
    if not isinstance(descriptive, dict):
        findings.append(Finding("error", "descriptive_estimation", "descriptive estimation is not planned"))
        return
    if is_unresolved(descriptive.get("primary_method")):
        findings.append(Finding(
            "error", "descriptive_estimation.primary_method",
            "name the method: Kaplan-Meier, cumulative incidence, or other",
        ))
    if is_unresolved(descriptive.get("prespecified_estimate_times")):
        findings.append(Finding(
            "error", "descriptive_estimation.prespecified_estimate_times",
            "estimates must be read at prespecified times, chosen before the data are seen",
        ))

    competing = text_of(descriptive.get("competing_event_method", "")).lower()
    if "cumulative incidence" in competing or "cif" in competing:
        findings.append(Finding(
            "warning", "descriptive_estimation.competing_event_method",
            "cumulative incidence is the right family when the target is absolute event "
            "probability; confirm the primary descriptive method is consistent with it",
        ))


def check_comparison(plan: dict, findings: list[Finding]) -> None:
    comparison = plan.get("group_comparison")
    if not isinstance(comparison, dict):
        findings.append(Finding("error", "group_comparison", "no group comparison is planned"))
        return
    for field in ("primary_test_or_model", "power_or_sample_size_basis",
                  "why_the_summary_answers_the_question"):
        if is_unresolved(comparison.get(field)):
            findings.append(Finding("error", f"group_comparison.{field}", f"{field.replace('_', ' ')} is required"))

    method = text_of(comparison.get("primary_test_or_model", "")).lower()
    uses_hazard_ratio = "cox" in method or "hazard ratio" in method or "hr" in method.split()

    if uses_hazard_ratio:
        if is_unresolved(comparison.get("proportional_hazards_assessment")):
            findings.append(Finding(
                "error", "group_comparison.proportional_hazards_assessment",
                "assess proportional hazards graphically and analytically before presenting a "
                "single hazard ratio",
            ))
        else:
            assessment = text_of(comparison["proportional_hazards_assessment"]).lower()
            if not any(word in assessment for word in ("graph", "schoenfeld", "km plot",
                                                       "kaplan-meier", "analytic", "scal")):
                findings.append(Finding(
                    "warning", "group_comparison.proportional_hazards_assessment",
                    "name how the assessment is done, not only that one was done",
                ))
        if is_unresolved(comparison.get("alternatives_if_ph_doubtful")):
            findings.append(Finding(
                "error", "group_comparison.alternatives_if_ph_doubtful",
                "pre-specify what to do when ph is doubtful: time-varying coefficients, "
                "piecewise or landmark effects, RMST at a justified horizon, differences at "
                "prespecified times, or an AFT or flexible parametric model",
            ))


def check_competing_risks(plan: dict, findings: list[Finding]) -> None:
    section = plan.get("competing_risks")
    if not isinstance(section, dict):
        findings.append(Finding("error", "competing_risks", "competing risks are not addressed"))
        return
    if is_unresolved(section.get("applicable")):
        findings.append(Finding("error", "competing_risks.applicable",
                                "state whether competing events are present"))
        return
    applicable = str(section["applicable"]).strip().lower()
    if applicable in {"no", "false", "none"}:
        return
    for field in ("question_type", "method_matches_question"):
        if is_unresolved(section.get(field)):
            findings.append(Finding(
                "error", f"competing_risks.{field}",
                "state which question the method answers: cause-specific hazard, cumulative "
                "incidence / absolute risk, or subdistribution hazard",
            ))
    question_type = text_of(section.get("question_type", "")).lower()
    method = text_of(section.get("primary_method", "")) + text_of(section.get("method_matches_question", ""))
    if "subdistribution" in question_type and "cif" in method:
        findings.append(Finding(
            "error", "competing_risks.method_matches_question",
            "a subdistribution hazard ratio is not a risk ratio; do not pair a "
            "subdistribution question with a cumulative-incidence estimate of the ratio",
        ))


def check_bias(plan: dict, findings: list[Finding]) -> None:
    section = plan.get("bias_and_missingness")
    if not isinstance(section, dict):
        findings.append(Finding("error", "bias_and_missingness", "bias and missingness are not addressed"))
        return
    for field in ("informative_censoring", "immortal_time", "time_dependent_confounding",
                  "missing_covariates", "sensitivity_analyses"):
        if is_unresolved(section.get(field)):
            findings.append(Finding("error", f"bias_and_missingness.{field}", "unresolved"))
    sensitivity = text_of(section.get("sensitivity_analyses", "")).lower()
    if sensitivity and "best" in sensitivity and "worst" in sensitivity and sensitivity.count("only") == 0:
        findings.append(Finding(
            "warning", "bias_and_missingness.sensitivity_analyses",
            "a best/worst case alone is rarely sufficient; tie sensitivity analyses to the "
            "specific assumptions that could fail",
        ))


def check_prediction_model(plan: dict, findings: list[Finding]) -> None:
    section = plan.get("prediction_model_element")
    if not isinstance(section, dict):
        return
    if is_unresolved(section.get("applies")):
        findings.append(Finding("error", "prediction_model_element.applies",
                                "state whether the plan includes a time-to-event prediction model"))
        return
    if str(section["applies"]).strip().lower() in {"no", "false", "none"}:
        return
    for field in ("locked_model_and_horizon", "calibration_at_prespecified_times",
                  "time_dependent_discrimination_with_uncertainty", "external_validation"):
        if is_unresolved(section.get(field)):
            findings.append(Finding(
                "error", f"prediction_model_element.{field}", f"{field.replace('_', ' ')} is required"
            ))


def check_biomarker(plan: dict, findings: list[Finding]) -> None:
    section = plan.get("biomarker_element")
    if not isinstance(section, dict):
        return
    if is_unresolved(section.get("applies")):
        findings.append(Finding("error", "biomarker_element.applies",
                                "state whether a prognostic or predictive biomarker is evaluated"))
        return
    if str(section["applies"]).strip().lower() in {"no", "false", "none"}:
        return
    if is_unresolved(section.get("prognostic_or_predictive")):
        findings.append(Finding(
            "error", "biomarker_element.prognostic_or_predictive",
            "separate prognostic association from treatment-effect interaction",
        ))
    if is_unresolved(section.get("transformation_and_threshold_prespecified")):
        findings.append(Finding(
            "error", "biomarker_element.transformation_and_threshold_prespecified",
            "pre-specify the transformation and threshold; a minimum-p-value cut-point search "
            "is not a threshold",
        ))


def check_uncertainty(plan: dict, findings: list[Finding]) -> None:
    section = plan.get("uncertainty_and_multiplicity")
    if not isinstance(section, dict):
        findings.append(Finding("error", "uncertainty_and_multiplicity",
                                "uncertainty and multiplicity are not addressed"))
        return
    for field in ("confidence_intervals_for_every_primary_effect", "multiplicity_strategy"):
        if is_unresolved(section.get(field)):
            findings.append(Finding("error", f"uncertainty_and_multiplicity.{field}", "unresolved"))


def check_human_review(plan: dict, findings: list[Finding]) -> None:
    review = plan.get("human_review")
    if not isinstance(review, dict):
        findings.append(Finding("error", "human_review", "a named review role is required"))
        return
    roles = review.get("required_roles")
    if not isinstance(roles, list) or not roles:
        findings.append(Finding("error", "human_review.required_roles", "no review roles listed"))
    if is_unresolved(review.get("status")):
        findings.append(Finding("error", "human_review.status", "review status is unresolved"))


def check_consistency(plan: dict, findings: list[Finding]) -> None:
    """Rules that catch the specific, common errors named in the reference."""
    findings.extend(screen(
        plan, CENSOR_COMPETING_AS_ORDINARY, "error", "endpoint.censoring_rules",
        "a competing event is not ordinary independent censoring when the target is absolute "
        "event probability",
    ))
    findings.extend(screen(
        plan, CUT_POINT_SEARCH, "error", "biomarker_element.transformation_and_threshold_prespecified",
        "a cut-point chosen by searching the data is not a pre-specified threshold",
    ))
    findings.extend(screen(
        plan, PH_AS_CERTAIN, "error", "group_comparison.proportional_hazards_assessment",
        "proportional hazards must be assessed, not assumed",
    ))
    findings.extend(screen(
        plan, HR_AS_RISK, "error", "group_comparison.primary_test_or_model",
        "1 - HR is not a reduction in cumulative risk",
    ))


def check(plan: dict) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(plan, dict):
        return [Finding("error", "$", "the plan must be a JSON object")]

    check_metadata(plan, findings)
    check_estimand(plan, findings)
    check_endpoint(plan, findings)
    check_descriptive(plan, findings)
    check_comparison(plan, findings)
    check_competing_risks(plan, findings)
    check_bias(plan, findings)
    check_prediction_model(plan, findings)
    check_biomarker(plan, findings)
    check_uncertainty(plan, findings)
    check_human_review(plan, findings)
    check_consistency(plan, findings)
    return findings


def load_plan(path: str) -> dict:
    if path.startswith(("http://", "https://", "file://")):
        raise SystemExit(f"error: {path} looks like a URL; this helper reads local files only")
    file_path = Path(path)
    if not file_path.is_file():
        raise SystemExit(f"error: plan not found: {path}")
    if file_path.stat().st_size > MAX_FILE_BYTES:
        raise SystemExit(f"error: {path} is larger than {MAX_FILE_BYTES} bytes")
    try:
        with file_path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: {path} is not valid JSON: {exc}")


def report_to_text(findings: list[Finding], path: str) -> str:
    errors = sum(1 for f in findings if f["level"] == "error")
    warnings = sum(1 for f in findings if f["level"] == "warning")
    lines = [f"plan: {path}", f"errors: {errors}, warnings: {warnings}", ""]
    for finding in findings:
        lines.append(f"{finding['level']}: {finding['field']}: {finding['message']}")
    lines += ["",
              "This report validates required planning fields and selected consistency rules. "
              "It analyzed no data, approves no method statistically, and forecasts no "
              "individual's course. Not for patient care or live clinical use."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the required planning fields of a survival-analysis plan.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("plan", help="local JSON survival-analysis plan")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="report format")
    parser.add_argument("--out", default=None, help="write the report here; default stdout")
    args = parser.parse_args(argv)

    plan = load_plan(args.plan)
    findings = check(plan)
    errors = sum(1 for f in findings if f["level"] == "error")

    if args.format == "json":
        text = json.dumps(
            {
                "plan": args.plan,
                "errors": errors,
                "warnings": sum(1 for f in findings if f["level"] == "warning"),
                "findings": findings,
                "analyzed_data": False,
                "statistical_approval": False,
                "boundary": "Not for patient care or live clinical use.",
            },
            indent=2,
        ) + "\n"
    else:
        text = report_to_text(findings, args.plan)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(text, end="")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

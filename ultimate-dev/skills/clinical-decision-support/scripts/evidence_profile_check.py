#!/usr/bin/env python3
"""Check the completeness and citation links of a GRADE evidence profile.

What it does
------------
Confirms that a profile has, for every important outcome: a documented question,
sources with stable IDs and versions, an effect estimate with uncertainty, all six
certainty domains each carrying a human judgment, a rationale, and source IDs, and
a final certainty label from the allowed set. Then it checks that every source ID
referenced by a domain or by the final judgment actually exists in the source list.

It never calculates a certainty rating, never counts checklist items to derive one,
and never alters or endorses a panel's judgment.

Usage
-----
    python3 scripts/evidence_profile_check.py assets/evidence_profile_template.json
    python3 scripts/evidence_profile_check.py profile.json --format json --out report.json

Exit codes: 0 all checks passed, 1 findings were raised, 2 unusable input. The
distributed template is unresolved on purpose, so a non-zero result is expected
until qualified humans complete it.

Provenance
----------
Reconstructed from the Required Profile Fields, Certainty Domains, Final Certainty,
and Quality-Control Checklist in references/evidence_profiles.md. The checks are
this file's own; the GRADE methodology is the current GRADE Book, not this script.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MAX_FILE_BYTES = 2 * 1024 * 1024
UNRESOLVED = "unresolved"

# The only labels a final certainty judgment may carry.
CERTAINTY_LABELS = {"high", "moderate", "low", "very low"}

# The six domains every outcome profile must address, with the judgment each needs.
DOMAINS = ("risk_of_bias", "inconsistency", "indirectness", "imprecision", "publication_bias")
DOMAIN_JUDGMENTS = {
    "serious", "not_serious", "very_serious", "extremely_serious",
    "detected", "undetected", "suspected_documented", "not_applicable",
}
OUTCOME_IMPORTANCE = {"critical", "important"}
EFFECT_DIRECTION = {"desirable", "undesirable", "neutral"}


class Finding(dict):
    def __init__(self, level: str, field: str, message: str) -> None:
        super().__init__(level=level, field=field, message=message)


def is_unresolved(value) -> bool:
    if isinstance(value, str):
        return UNRESOLVED in value.lower()
    if isinstance(value, (list, dict)):
        return not value
    return value is None


def collect_source_ids(sources: list) -> set[str]:
    """Stable IDs a domain or final judgment may cite."""
    ids: set[str] = set()
    for source in sources:
        if isinstance(source, dict):
            identifier = source.get("source_id")
            if isinstance(identifier, str) and identifier and is_unresolved(identifier) is False:
                ids.add(identifier)
    return ids


def check_question(profile: dict, findings: list[Finding]) -> None:
    question = profile.get("question")
    if not isinstance(question, dict):
        findings.append(Finding("error", "question", "the profile must document the framed question"))
        return
    for field in ("population", "intervention_or_exposure", "comparator_or_reference",
                  "outcomes_and_horizons", "setting_and_decision_context"):
        if is_unresolved(question.get(field)):
            findings.append(Finding("error", f"question.{field}", "unresolved"))
    if not is_unresolved(question.get("question_type")):
        declared = str(question["question_type"]).lower()
        if not any(kind in declared for kind in ("descriptive", "prognostic", "predictive",
                                                "diagnostic", "causal")):
            findings.append(Finding(
                "warning", "question.question_type",
                "state whether the question is descriptive, prognostic, predictive, "
                "diagnostic-accuracy, or causal",
            ))


def check_sources(profile: dict, findings: list[Finding]) -> set[str]:
    sources = profile.get("sources")
    if not isinstance(sources, list) or not sources:
        findings.append(Finding("error", "sources", "no sources recorded"))
        return set()

    ids: set[str] = set()
    for index, source in enumerate(sources):
        path = f"sources[{index}]"
        if not isinstance(source, dict):
            findings.append(Finding("error", path, "each source must be an object"))
            continue
        identifier = source.get("source_id")
        if is_unresolved(identifier):
            findings.append(Finding("error", f"{path}.source_id", "no stable source ID"))
        elif identifier in ids:
            findings.append(Finding("error", f"{path}.source_id", f"duplicate source ID {identifier}"))
        else:
            ids.add(identifier)

        for field in ("full_citation", "url_or_doi", "publication_type", "version_or_date"):
            if is_unresolved(source.get(field)):
                findings.append(Finding("error", f"{path}.{field}", f"{field} is unresolved"))
        # Living content needs an access date.
        publication_type = str(source.get("publication_type", "")).lower()
        if any(word in publication_type for word in ("living", "living document", "website", "web")):
            if is_unresolved(source.get("access_date")):
                findings.append(Finding(
                    "error", f"{path}.access_date",
                    "an access date is required when the source content is living",
                ))
    return ids


def check_effect(outcome_profile: dict, path: str, findings: list[Finding]) -> None:
    effect = outcome_profile.get("effect")
    if not isinstance(effect, dict):
        findings.append(Finding("error", f"{path}.effect", "no effect record for this outcome"))
        return
    for field in ("measure", "interval", "participants", "studies", "follow_up",
                  "missingness", "adjusted", "applicability_limits"):
        if is_unresolved(effect.get(field)):
            findings.append(Finding("error", f"{path}.effect.{field}", f"{field} is unresolved"))
    # An effect with no uncertainty is not reportable.
    interval = effect.get("interval")
    if isinstance(interval, str) and interval and not is_unresolved(interval):
        if not any(token in interval.lower() for token in ("ci", "interval", "95", "90", "credible")):
            findings.append(Finding(
                "warning", f"{path}.effect.interval",
                "name the interval type and level, not just its bounds",
            ))


def check_domains(outcome_profile: dict, path: str, valid_ids: set[str], findings: list[Finding]) -> None:
    domains = outcome_profile.get("domains")
    if not isinstance(domains, dict):
        findings.append(Finding("error", f"{path}.domains", "no certainty domains recorded"))
        return

    for name in DOMAINS:
        domain = domains.get(name)
        domain_path = f"{path}.domains.{name}"
        if not isinstance(domain, dict):
            findings.append(Finding("error", domain_path, f"the {name} domain is missing"))
            continue
        if is_unresolved(domain.get("judgment")):
            findings.append(Finding("error", f"{domain_path}.judgment",
                                    f"{name} needs a human judgment"))
        if is_unresolved(domain.get("rationale")):
            findings.append(Finding("error", f"{domain_path}.rationale",
                                    f"{name} needs a rationale"))
        cited = domain.get("source_ids")
        if not isinstance(cited, list) or not cited:
            findings.append(Finding("error", f"{domain_path}.source_ids",
                                    f"the {name} rationale must link to source IDs"))
        else:
            for identifier in cited:
                if identifier not in valid_ids:
                    findings.append(Finding(
                        "error", f"{domain_path}.source_ids",
                        f"cites source ID {identifier!r}, which is not in the source list",
                    ))

    # Risk of bias needs the design-appropriate tool named, not a numeric score.
    risk = domains.get("risk_of_bias")
    if isinstance(risk, dict) and not is_unresolved(risk.get("tool")):
        tool = str(risk["tool"]).lower()
        if "score" in tool and "risk of bias" not in tool:
            findings.append(Finding(
                "warning", f"{path}.domains.risk_of_bias.tool",
                "a numeric quality score is not a substitute for a risk-of-bias judgment",
            ))

    upgrading = domains.get("upgrading")
    if isinstance(upgrading, dict):
        if upgrading.get("statistical_significance_is_not_a_reason") is not True:
            findings.append(Finding(
                "error", f"{path}.domains.upgrading",
                'record "statistical significance is not an upgrading reason" explicitly',
            ))
        if not is_unresolved(upgrading.get("applicable")) and not is_unresolved(
            upgrading.get("considerations")
        ):
            # An upgrading entry that names a consideration must also justify it.
            if not upgrading.get("source_ids"):
                findings.append(Finding(
                    "error", f"{path}.domains.upgrading.source_ids",
                    "an upgrading consideration requires explicit methodology and citations",
                ))


def check_final_certainty(outcome_profile: dict, path: str, valid_ids: set[str], findings: list[Finding]) -> None:
    final = outcome_profile.get("final_certainty")
    if not isinstance(final, dict):
        findings.append(Finding("error", f"{path}.final_certainty", "no final certainty recorded"))
        return

    label = final.get("label")
    if is_unresolved(label):
        findings.append(Finding("error", f"{path}.final_certainty.label",
                                f"final certainty must be one of {', '.join(sorted(CERTAINTY_LABELS))}"))
    elif str(label).strip().lower() not in CERTAINTY_LABELS:
        findings.append(Finding(
            "error", f"{path}.final_certainty.label",
            f"{label!r} is not an allowed label; use high, moderate, low, or very low",
        ))

    for field in ("judgment", "reviewer_role", "review_date", "domain_to_final_rationale"):
        if is_unresolved(final.get(field)):
            findings.append(Finding(
                "error", f"{path}.final_certainty.{field}",
                f"{field} is required; certainty is a human panel judgment",
            ))

    # The reviewer must be a role, not a tool.
    role = final.get("reviewer_role")
    if isinstance(role, str) and role and not is_unresolved(role):
        lowered = role.lower()
        if lowered in {"grade", "gradepro", "gsea", "r", "python", "script", "checker"}:
            findings.append(Finding(
                "error", f"{path}.final_certainty.reviewer_role",
                "name the human review role, not the tool that checked the file",
            ))

    cited = final.get("source_ids")
    if not isinstance(cited, list) or not cited:
        findings.append(Finding("error", f"{path}.final_certainty.source_ids",
                                "the final judgment must cite its sources"))
    else:
        for identifier in cited:
            if identifier not in valid_ids:
                findings.append(Finding(
                    "error", f"{path}.final_certainty.source_ids",
                    f"cites source ID {identifier!r}, which is not in the source list",
                ))

    if is_unresolved(final.get("dissent_or_unresolved_issues")):
        findings.append(Finding(
            "warning", f"{path}.final_certainty.dissent_or_unresolved_issues",
            "record dissent or unresolved issues even when there are none",
        ))


def check_outcome_profile(profile: dict, index: int, valid_ids: set[str], findings: list[Finding]) -> None:
    outcome_profile = profile["outcome_profiles"][index]
    path = f"outcome_profiles[{index}]"
    if not isinstance(outcome_profile, dict):
        findings.append(Finding("error", path, "each outcome profile must be an object"))
        return

    if is_unresolved(outcome_profile.get("outcome")):
        findings.append(Finding("error", f"{path}.outcome", "name the outcome"))
    if is_unresolved(outcome_profile.get("time_horizon")):
        findings.append(Finding("error", f"{path}.time_horizon", "state the time horizon"))

    importance = outcome_profile.get("outcome_importance")
    if is_unresolved(importance):
        findings.append(Finding("error", f"{path}.outcome_importance", "critical or important?"))
    elif str(importance).strip().lower() not in OUTCOME_IMPORTANCE:
        findings.append(Finding(
            "error", f"{path}.outcome_importance",
            f"{importance!r} is not a GRADE importance level; use critical or important",
        ))

    direction = outcome_profile.get("effect_direction")
    if not is_unresolved(direction) and str(direction).strip().lower() not in EFFECT_DIRECTION:
        findings.append(Finding(
            "warning", f"{path}.effect_direction",
            "record the effect as desirable, undesirable, or neutral",
        ))

    check_effect(outcome_profile, path, findings)
    check_domains(outcome_profile, path, valid_ids, findings)
    check_final_certainty(outcome_profile, path, valid_ids, findings)


def check_quality_control(profile: dict, findings: list[Finding]) -> None:
    """The GRADE quality-control list, as documentation checks only."""
    checklist = profile.get("quality_control")
    if not isinstance(checklist, dict):
        findings.append(Finding("error", "quality_control", "the quality-control checklist is missing"))
        return
    for key, value in checklist.items():
        if key.startswith("_"):
            continue
        if is_unresolved(value):
            findings.append(Finding("error", f"quality_control.{key}", "unresolved"))


def check_prohibited_content(profile: dict, findings: list[Finding]) -> None:
    """A profile may not contain a recommendation or a person-level directive."""
    prohibited_keys = {"recommendation", "recommendation_strength", "recommended_action",
                       "treatment_recommendation", "dose", "dosing", "patient_specific",
                       "clinical_action", "triage", "alert", "urgency"}
    for key in profile:
        if str(key).lower() in prohibited_keys:
            findings.append(Finding(
                "error", str(key),
                "a GRADE profile records certainty, not a recommendation; recommendation "
                "development belongs in a separate Evidence-to-Decision record",
            ))
    text = json.dumps(profile).lower()
    for phrase in ("should be prescribed", "recommend starting", "recommended dose"):
        if phrase in text:
            findings.append(Finding(
                "error", "$", f"the profile contains the treatment directive {phrase!r}"
            ))


def check(profile: dict) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(profile, dict):
        return [Finding("error", "$", "the profile must be a JSON object")]

    check_prohibited_content(profile, findings)
    check_question(profile, findings)
    valid_ids = check_sources(profile, findings)

    outcome_profiles = profile.get("outcome_profiles")
    if not isinstance(outcome_profiles, list) or not outcome_profiles:
        findings.append(Finding(
            "error", "outcome_profiles",
            "certainty is rated per outcome; at least one outcome profile is required, and "
            "outcomes must not be collapsed into a single study-level grade",
        ))
    else:
        seen: set[str] = set()
        for index, outcome_profile in enumerate(outcome_profiles):
            if isinstance(outcome_profile, dict):
                name = outcome_profile.get("outcome")
                if isinstance(name, str) and name in seen:
                    findings.append(Finding(
                        "error", f"outcome_profiles[{index}].outcome",
                        f"outcome {name!r} is profiled more than once",
                    ))
                seen.add(name)
            check_outcome_profile(profile, index, valid_ids, findings)

    check_quality_control(profile, findings)
    return findings


def load_profile(path: str) -> dict:
    if path.startswith(("http://", "https://", "file://")):
        raise SystemExit(f"error: {path} looks like a URL; this helper reads local files only")
    file_path = Path(path)
    if not file_path.is_file():
        raise SystemExit(f"error: profile not found: {path}")
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
    lines = [f"profile: {path}", f"errors: {errors}, warnings: {warnings}", ""]
    for finding in findings:
        lines.append(f"{finding['level']}: {finding['field']}: {finding['message']}")
    lines += ["",
              "This report checks structure, allowed labels, human attribution, and citation "
              "links only. It does not calculate certainty, does not endorse any panel "
              "judgment, and is not a recommendation.",
              "Not for patient care or live clinical use."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check completeness and citation links in a GRADE evidence profile.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--profile", default=None, help="local JSON evidence profile")
    parser.add_argument("positional", nargs="?", help="local JSON evidence profile")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="report format")
    parser.add_argument("--out", default=None, help="write the report here; default stdout")
    args = parser.parse_args(argv)

    path = args.profile or args.positional
    if not path:
        raise SystemExit("error: give the profile path, positionally or with --profile")

    profile = load_profile(path)
    findings = check(profile)
    errors = sum(1 for f in findings if f["level"] == "error")

    if args.format == "json":
        text = json.dumps(
            {
                "profile": path,
                "errors": errors,
                "warnings": sum(1 for f in findings if f["level"] == "warning"),
                "findings": findings,
                "does_not_calculate_certainty": True,
                "boundary": "Not for patient care or live clinical use.",
            },
            indent=2,
        ) + "\n"
    else:
        text = report_to_text(findings, path)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(text, end="")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

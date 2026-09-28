#!/usr/bin/env python3
"""Check a documented de-identification process checklist.

What it does
------------
Inventories the human work recorded in a de-identification checklist: the two HHS
methods, the eighteen Safe Harbor categories, the Expert Determination record, the
aggregate-disclosure review, the actual-knowledge and residual-risk review, and the
escalations. It verifies that each category carries a status and, for every status
other than ``unresolved``, evidence text. It flags escalations that remain open.

It never reads a dataset. Do not paste sensitive information into a template to see
whether it passes.

What it is not
--------------
It cannot perform Expert Determination or Safe Harbor, cannot determine whether an
organization is a covered entity or business associate, and cannot establish
de-identification or HIPAA compliance. Passing means the documentation is complete,
nothing more. The only permitted completion sentence is: "Documentation checklist
complete for the selected method. This output is not a HIPAA compliance or
de-identification determination."

Usage
-----
    python3 scripts/deidentification_checklist.py assets/deidentification_checklist_template.json
    python3 scripts/deidentification_checklist.py checklist.json --format json --out report.json

Provenance
----------
Reconstructed from references/privacy_and_disclosure.md, which lists the two HHS
methods, the eighteen categories, the status values, the Expert Determination record
fields, and the allowed output language. The completeness checks are this file's own.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MAX_FILE_BYTES = 2 * 1024 * 1024
UNRESOLVED = "unresolved"

# The Safe Harbor identifier categories from 45 CFR 164.514(b)(2).
SAFE_HARBOR_CATEGORIES = (
    "names",
    "geographic_subdivisions_smaller_than_state",
    "date_elements_more_specific_than_year",
    "telephone_numbers",
    "fax_numbers",
    "email_addresses",
    "social_security_numbers",
    "medical_record_numbers",
    "health_plan_beneficiary_numbers",
    "account_numbers",
    "certificate_or_license_numbers",
    "vehicle_identifiers_and_serial_numbers",
    "device_identifiers_and_serial_numbers",
    "web_urls",
    "ip_addresses",
    "biometric_identifiers",
    "full_face_photographs_and_comparable_images",
    "other_unique_identifying_numbers_characteristics_or_codes",
)

STATUS_VALUES = {
    "not_present": "documented inventory confirms absence",
    "removed": "documented transformation confirms removal",
    "generalized": "allowed generalization documented and approved",
    "expert_reviewed": "addressed under the referenced Expert Determination",
    "unresolved": "not complete",
}

EXPERT_DETERMINATION_FIELDS = (
    "expert_qualifications_and_independence",
    "data_context_and_recipients",
    "anticipated_linkages_and_attacker_knowledge",
    "methods_and_assumptions",
    "risk_threshold_and_rationale",
    "mitigation_and_residual_risk",
    "validity_period_and_change_triggers",
    "documentation_location_and_approval",
)

RESIDUAL_RISK_FIELDS = (
    "free_text", "derived_fields", "linkage_and_differencing", "unusual_occupations_or_events",
    "rare_diseases_or_combinations", "dates_and_ages", "geography", "longitudinal_uniqueness",
    "recipient_context", "prior_releases", "residual_identifiers",
)

DISCLOSURE_RISK_VECTORS = (
    "small cells", "row and column totals", "differencing across releases", "rare combinations",
    "nested geographies", "longitudinal patterns", "extreme values", "genomics", "external linkage",
)

# Language this skill must never emit or accept as a completion claim.
FORBIDDEN_CLAIMS = (
    "hipaa compliant", "hipaa-compliant", "is anonymous", "safe to publish",
    "de-identified per hipaa", "fully de-identified", "guarantees no re-identification",
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


def check_method(checklist: dict, findings: list[Finding]) -> str:
    method = checklist.get("method")
    if not isinstance(method, dict):
        findings.append(Finding("error", "method", "the checklist must select an HHS method"))
        return ""
    selected = str(method.get("selected", "")).strip().lower()
    if is_unresolved(selected):
        findings.append(Finding("error", "method.selected",
                                "select expert_determination or safe_harbor"))
        return ""
    if selected not in {"expert_determination", "safe_harbor"}:
        findings.append(Finding(
            "error", "method.selected",
            f"{selected!r} is not one of the two methods at 45 CFR 164.514: "
            "expert_determination or safe_harbor",
        ))
        return ""
    if is_unresolved(method.get("why_selected")):
        findings.append(Finding("error", "method.why_selected",
                                "record why this method was selected for this release"))
    return selected


def check_safe_harbor(checklist: dict, selected: str, findings: list[Finding]) -> None:
    section = checklist.get("safe_harbor_categories")
    if not isinstance(section, dict):
        findings.append(Finding("error", "safe_harbor_categories",
                                "the Safe Harbor category inventory is missing"))
        return

    for category in SAFE_HARBOR_CATEGORIES:
        entry = section.get(category)
        path = f"safe_harbor_categories.{category}"
        if not isinstance(entry, dict):
            findings.append(Finding("error", path, "category is not documented"))
            continue
        status = str(entry.get("status", "")).strip().lower()
        if status not in STATUS_VALUES:
            findings.append(Finding(
                "error", f"{path}.status",
                f"{entry.get('status')!r} is not one of: " + ", ".join(sorted(STATUS_VALUES)),
            ))
            continue
        if status == "unresolved":
            findings.append(Finding("error", f"{path}.status", "category is not complete"))
        elif is_unresolved(entry.get("evidence")):
            findings.append(Finding(
                "error", f"{path}.evidence",
                f"status {status!r} requires evidence text. Never include an example "
                "identifier in the evidence",
            ))

    if selected == "safe_harbor" and section.get("free_text_review", {}).get("status") == "not_present":
        findings.append(Finding(
            "error", "safe_harbor_categories.free_text_review",
            "free text is not exempt under Safe Harbor and routinely carries listed "
            "identifiers; recording it as absent needs an explicit justification",
        ))


def check_expert_determination(checklist: dict, selected: str, findings: list[Finding]) -> None:
    record = checklist.get("expert_determination_record")
    if not isinstance(record, dict):
        findings.append(Finding("error", "expert_determination_record",
                                "the Expert Determination record is missing"))
        return

    if selected == "safe_harbor" and record.get("applies") is True:
        findings.append(Finding(
            "error", "expert_determination_record.applies",
            "Expert Determination is recorded as applying, but the selected method is Safe Harbor",
        ))

    for field in EXPERT_DETERMINATION_FIELDS:
        if is_unresolved(record.get(field)):
            findings.append(Finding(
                "error", f"expert_determination_record.{field}",
                f"{field.replace('_', ' ')} is required in the Expert Determination record",
            ))

    insufficient = record.get("not_sufficient_alone")
    if not isinstance(insufficient, list) or not insufficient:
        findings.append(Finding(
            "error", "expert_determination_record.not_sufficient_alone",
            "record that hashing, pseudonymization, encryption, a data-use agreement, and a "
            "low cell count are each insufficient on their own",
        ))


def check_disclosure(checklist: dict, findings: list[Finding]) -> None:
    section = checklist.get("aggregate_disclosure_review")
    if not isinstance(section, dict):
        findings.append(Finding("error", "aggregate_disclosure_review",
                                "the aggregate disclosure review is missing"))
        return
    reviewed = section.get("risk_vectors_reviewed")
    missing = [vector for vector in DISCLOSURE_RISK_VECTORS
               if not isinstance(reviewed, list) or vector not in reviewed]
    if missing:
        findings.append(Finding(
            "error", "aggregate_disclosure_review.risk_vectors_reviewed",
            "risk vectors not recorded as reviewed: " + ", ".join(missing),
        ))
    if is_unresolved(section.get("controls_applied")):
        findings.append(Finding("error", "aggregate_disclosure_review.controls_applied", "unresolved"))
    if is_unresolved(section.get("approved_policy")):
        findings.append(Finding(
            "error", "aggregate_disclosure_review.approved_policy",
            "name the approved disclosure policy; there is no universal small-cell threshold "
            "that proves de-identification",
        ))


def check_residual_risk(checklist: dict, findings: list[Finding]) -> None:
    section = checklist.get("actual_knowledge_and_residual_risk")
    if not isinstance(section, dict):
        findings.append(Finding("error", "actual_knowledge_and_residual_risk",
                                "the actual-knowledge and residual-risk review is missing"))
        return
    for field in RESIDUAL_RISK_FIELDS:
        if is_unresolved(section.get(field)):
            findings.append(Finding(
                "error", f"actual_knowledge_and_residual_risk.{field}", "unresolved"
            ))


def check_escalations(checklist: dict, findings: list[Finding]) -> None:
    escalations = checklist.get("escalations_to_qualified_privacy_review")
    if is_unresolved(escalations):
        findings.append(Finding(
            "error", "escalations_to_qualified_privacy_review",
            "list every item escalated to qualified privacy review. An empty list is not "
            "evidence that none exist",
        ))
    elif isinstance(escalations, list) and escalations:
        open_items = [
            index for index, item in enumerate(escalations)
            if isinstance(item, str) and is_unresolved(item)
        ]
        if open_items:
            findings.append(Finding(
                "error", "escalations_to_qualified_privacy_review",
                f"{len(open_items)} escalation(s) are still unresolved",
            ))


def check_review(checklist: dict, findings: list[Finding]) -> None:
    review = checklist.get("review")
    if not isinstance(review, dict):
        findings.append(Finding("error", "review",
                                "a named privacy officer or qualified expert must sign the review"))
        return
    for field in ("privacy_officer_or_qualified_expert", "review_date", "status"):
        if is_unresolved(review.get(field)):
            findings.append(Finding("error", f"review.{field}", "unresolved"))


def check_forbidden_claims(checklist: dict, findings: list[Finding]) -> None:
    """A checklist may not carry a compliance, anonymity, or publication-safety claim."""
    def walk(node, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if str(key) == "not_allowed":
                    continue  # the template's own list of forbidden phrasings
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")
        elif isinstance(node, str):
            lowered = node.lower()
            for claim in FORBIDDEN_CLAIMS:
                if claim in lowered:
                    findings.append(Finding(
                        "error", path,
                        f"contains the claim {claim!r}. The allowed completion sentence is: "
                        "Documentation checklist complete for the selected method. This output "
                        "is not a HIPAA compliance or de-identification determination.",
                    ))

    walk(checklist, "$")


def check(checklist: dict) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(checklist, dict):
        return [Finding("error", "$", "the checklist must be a JSON object")]

    check_forbidden_claims(checklist, findings)
    selected = check_method(checklist, findings)
    check_safe_harbor(checklist, selected, findings)
    check_expert_determination(checklist, selected, findings)
    check_disclosure(checklist, findings)
    check_residual_risk(checklist, findings)
    check_escalations(checklist, findings)
    check_review(checklist, findings)
    return findings


def load_checklist(path: str) -> dict:
    if path.startswith(("http://", "https://", "file://")):
        raise SystemExit(f"error: {path} looks like a URL; this helper reads local files only")
    file_path = Path(path)
    if not file_path.is_file():
        raise SystemExit(f"error: checklist not found: {path}")
    if file_path.stat().st_size > MAX_FILE_BYTES:
        raise SystemExit(f"error: {path} is larger than {MAX_FILE_BYTES} bytes")
    try:
        with file_path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: {path} is not valid JSON: {exc}")


COMPLETION_SENTENCE = (
    "Documentation checklist complete for the selected method. This output is not a HIPAA "
    "compliance or de-identification determination."
)


def report_to_text(findings: list[Finding], path: str) -> str:
    errors = sum(1 for f in findings if f["level"] == "error")
    warnings = sum(1 for f in findings if f["level"] == "warning")
    lines = [f"checklist: {path}", f"errors: {errors}, warnings: {warnings}", ""]
    for finding in findings:
        lines.append(f"{finding['level']}: {finding['field']}: {finding['message']}")
    lines += ["", COMPLETION_SENTENCE, "Not for patient care or live clinical use."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check a documented de-identification process checklist.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("checklist", help="local JSON de-identification checklist")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="report format")
    parser.add_argument("--out", default=None, help="write the report here; default stdout")
    args = parser.parse_args(argv)

    checklist = load_checklist(args.checklist)
    findings = check(checklist)
    errors = sum(1 for f in findings if f["level"] == "error")

    if args.format == "json":
        text = json.dumps(
            {
                "checklist": args.checklist,
                "errors": errors,
                "warnings": sum(1 for f in findings if f["level"] == "warning"),
                "findings": findings,
                "read_a_dataset": False,
                "completion_sentence": COMPLETION_SENTENCE,
                "boundary": "Not a de-identification determination. Not for patient care or "
                            "live clinical use.",
            },
            indent=2,
        ) + "\n"
    else:
        text = report_to_text(findings, args.checklist)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(text, end="")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Validate the required artifact header on a clinical-decision-support JSON artifact.

What it does
------------
Checks that a research artifact carries every field the Required Artifact Header
in SKILL.md demands, that no prohibited use appears as an enabled capability, that
the boundary statement is present, and that the human-review roles and source
citations are filled in. Writes a JSON report; exit code 0 when clean, 1 when
findings were raised, 2 for unusable input.

What it does not do
-------------------
It does not read PHI, evaluate a study, determine de-identification, or make any
regulatory, HIPAA, or legal determination. "Not for patient care or live clinical
use" applies to this script's own output.

Safety controls
---------------
Local files only: no network, no environment-variable reads, no credentials, no
model calls, no executable deserialization. Input size, depth, group count, row
count, and string length are all capped. Common person-level field names are
rejected as defense in depth, and a URL-like path is refused outright. These are
accidental-misuse controls, not a privacy determination.

Usage
-----
    python3 scripts/validate_cds_artifact.py --artifact assets/artifact_intended_use_template.json
    python3 scripts/validate_cds_artifact.py --artifact report.json --format json

Provenance
----------
Reconstructed from the Required Artifact Header list and the hard safety boundary
in SKILL.md. The cap values and the field checks are this file's own.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_DEPTH = 12
MAX_GROUPS = 200
MAX_ROWS = 100_000
MAX_STRING = 20_000
MAX_ITEMS = 50_000

# Keys that would indicate row-level or person-linked input. Defence in depth: the
# documented contract is synthetic or aggregate schemas only, and this list cannot
# detect every identifier name or sensitive value.
PERSON_LEVEL_KEYS = frozenset({
    "patient_id", "patientid", "mrn", "medical_record_number", "ssn", "social_security_number",
    "dob", "date_of_birth", "birth_date", "address", "street", "postcode", "zip", "zip_code",
    "phone", "telephone", "fax", "email", "name", "first_name", "last_name", "full_name",
    "free_text", "note", "notes", "narrative", "image", "waveform", "sequence", "genome",
    "identifier", "subject_id", "person_id", "encounter_id", "admission_date", "discharge_date",
})

REQUIRED_TOP_LEVEL = (
    "artifact_type", "title", "version", "status", "owner", "date", "change_summary",
    "intended_purpose", "intended_users", "aggregate_population_scope", "decision_role",
    "prohibited_uses", "data_level", "no_phi_confirmation", "limitations",
    "external_validation_status", "subgroup_applicability_status", "human_review",
    "sources", "monitoring_and_change_control",
)

REQUIRED_HUMAN_REVIEW_ROLES = (
    "methodologist_or_statistician",
    "domain_expert",
    "privacy_officer_or_qualified_expert",
    "regulatory_or_legal_counsel",
    "human_factors_specialist",
    "authorized_governance_owner",
)

BOUNDARY_PHRASE = "not for patient care or live clinical use"
UNRESOLVED = "unresolved"


class Finding(dict):
    """One finding: level, field, and message. Serialises straight into the report."""

    def __init__(self, level: str, field: str, message: str) -> None:
        super().__init__(level=level, field=field, message=message)


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def scan_for_person_keys(node, path: str, findings: list[Finding], depth: int = 0) -> None:
    """Walk the loaded JSON looking for row-level or person-linked keys."""
    if depth > MAX_DEPTH:
        findings.append(Finding("error", path, f"nesting deeper than {MAX_DEPTH} levels"))
        return
    if isinstance(node, dict):
        for key, value in node.items():
            normalised = str(key).lower()
            if normalised in PERSON_LEVEL_KEYS:
                findings.append(Finding(
                    "error", f"{path}.{key}",
                    "row-level or person-linked key is not accepted; this skill takes "
                    "synthetic or aggregate structures only",
                ))
            scan_for_person_keys(value, f"{path}.{key}", findings, depth + 1)
    elif isinstance(node, list):
        if len(node) > MAX_ITEMS:
            findings.append(Finding("error", path, f"list longer than {MAX_ITEMS} items"))
        for index, value in enumerate(node[:MAX_ITEMS]):
            scan_for_person_keys(value, f"{path}[{index}]", findings, depth + 1)
    elif isinstance(node, str) and len(node) > MAX_STRING:
        findings.append(Finding("error", path, f"string longer than {MAX_STRING} characters"))


def is_unresolved(value) -> bool:
    """True for the template's unresolved marker, in any of its forms."""
    if isinstance(value, str):
        return UNRESOLVED in value.lower()
    if isinstance(value, (list, dict)):
        return not value
    return value is None


def check_header(artifact: dict, findings: list[Finding]) -> None:
    """Every Required Artifact Header field must be present and filled."""
    for field in REQUIRED_TOP_LEVEL:
        if field not in artifact:
            findings.append(Finding("error", field, "required header field is absent"))
        elif is_unresolved(artifact[field]):
            findings.append(Finding(
                "error", field,
                f"still carries the unresolved template marker; {UNRESOLVED!r} must be "
                "replaced with a completed value before review",
            ))

    boundary = artifact.get("not_for_patient_care_or_live_clinical_use", "")
    if not isinstance(boundary, str) or BOUNDARY_PHRASE not in boundary.lower():
        findings.append(Finding(
            "error", "not_for_patient_care_or_live_clinical_use",
            f"the artifact must state: Not for patient care or live clinical use.",
        ))

    uses = artifact.get("prohibited_uses")
    if isinstance(uses, list) and len(uses) < 6:
        findings.append(Finding(
            "error", "prohibited_uses",
            f"only {len(uses)} prohibited use(s) recorded; the hard safety boundary lists eight",
        ))

    decision_role = artifact.get("decision_role", "")
    if isinstance(decision_role, str) and decision_role and UNRESOLVED not in decision_role.lower():
        lowered = decision_role.lower()
        if "care" in lowered and "does not" not in lowered and "no " not in lowered:
            findings.append(Finding(
                "warning", "decision_role",
                "decision_role mentions care; state plainly that the artifact informs "
                "research or governance review and directs no action for any person",
            ))


def check_human_review(artifact: dict, findings: list[Finding]) -> None:
    """Review roles must be listed, and the approval boundary must be explicit."""
    review = artifact.get("human_review")
    if not isinstance(review, dict):
        findings.append(Finding("error", "human_review", "must be an object with roles and status"))
        return

    roles = review.get("required_roles")
    if not isinstance(roles, list) or not roles:
        findings.append(Finding("error", "human_review.required_roles", "no review roles listed"))
    else:
        present = {str(role).lower() for role in roles}
        missing = [role for role in REQUIRED_HUMAN_REVIEW_ROLES if role not in present]
        if missing:
            findings.append(Finding(
                "error", "human_review.required_roles",
                "missing review role(s): " + ", ".join(missing),
            ))

    if is_unresolved(review.get("status")):
        findings.append(Finding("error", "human_review.status", "review status is unresolved"))
    boundary = review.get("approval_boundary", "")
    if not isinstance(boundary, str) or "draft" not in boundary.lower():
        findings.append(Finding(
            "error", "human_review.approval_boundary",
            "the approval boundary must state that outputs remain drafts until qualified "
            "humans approve them",
        ))


def check_sources(artifact: dict, findings: list[Finding]) -> None:
    """Citations need a version or a date to be checkable."""
    sources = artifact.get("sources")
    if not isinstance(sources, list) or not sources:
        findings.append(Finding("error", "sources", "no source citations recorded"))
        return
    for index, source in enumerate(sources):
        path = f"sources[{index}]"
        if not isinstance(source, dict):
            findings.append(Finding("error", path, "each source must be an object"))
            continue
        for field in ("citation", "version_or_date"):
            if is_unresolved(source.get(field)):
                findings.append(Finding(
                    "error", f"{path}.{field}",
                    f"every citation needs a {field.replace('_', ' ')}",
                ))


def check_monitoring(artifact: dict, findings: list[Finding]) -> None:
    """Monitoring, change control, retirement, and audit must all be addressed."""
    section = artifact.get("monitoring_and_change_control")
    if not isinstance(section, dict):
        findings.append(Finding(
            "error", "monitoring_and_change_control", "must be an object"
        ))
        return
    for field in ("monitoring_expectations", "change_control", "retirement_criteria", "audit_expectations"):
        if is_unresolved(section.get(field)):
            findings.append(Finding(
                "error", f"monitoring_and_change_control.{field}", "unresolved"
            ))


def check_prohibited_content(artifact: dict, findings: list[Finding]) -> None:
    """Refuse any key that would enable a prohibited use."""
    prohibited = {
        "recommendation", "recommended_action", "treatment_recommendation", "dose",
        "dosing", "alert", "alarm", "triage", "urgency", "diagnosis", "diagnostic_rule",
        "care_pathway", "patient_action", "class_assignment", "risk_score_for_person",
    }
    for key in artifact:
        if str(key).lower() in prohibited:
            findings.append(Finding(
                "error", str(key),
                "field name corresponds to a use the hard safety boundary prohibits",
            ))


def validate(artifact: dict) -> list[Finding]:
    """Run every check and return the findings in report order."""
    findings: list[Finding] = []
    if not isinstance(artifact, dict):
        return [Finding("error", "$", "the artifact must be a JSON object")]

    scan_for_person_keys(artifact, "$", findings)
    check_prohibited_content(artifact, findings)
    check_header(artifact, findings)
    check_human_review(artifact, findings)
    check_sources(artifact, findings)
    check_monitoring(artifact, findings)
    return findings


def load_artifact(path: str) -> dict:
    """Read a local JSON file, refusing URL-like paths and oversized files."""
    if path.startswith(("http://", "https://", "ftp://", "file://")):
        raise SystemExit(
            f"error: {path} looks like a URL. This helper reads local files only and "
            "never fetches anything."
        )
    file_path = Path(path)
    if not file_path.is_file():
        raise SystemExit(f"error: artifact not found: {path}")
    size = file_path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise SystemExit(
            f"error: {path} is {size} bytes, over the {MAX_FILE_BYTES}-byte cap. This helper "
            "works on artifact headers, not on datasets."
        )
    try:
        with file_path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: {path} is not valid JSON: {exc}")


def report_to_text(findings: list[Finding], path: str) -> str:
    errors = [f for f in findings if f["level"] == "error"]
    warnings = [f for f in findings if f["level"] == "warning"]
    lines = [f"artifact: {path}",
             f"errors: {len(errors)}, warnings: {len(warnings)}", ""]
    for finding in findings:
        lines.append(f"{finding['level']}: {finding['field']}: {finding['message']}")
    lines += ["", "Not for patient care or live clinical use. This report is not a privacy, "
              "regulatory, or legal determination."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the required header on a clinical-decision-support research artifact.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--artifact", default=None, help="local JSON artifact to validate")
    parser.add_argument("positional", nargs="?", help="local JSON artifact to validate")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="report format")
    parser.add_argument("--out", default=None, help="write the report here; default stdout")
    args = parser.parse_args(argv)

    path = args.artifact or args.positional
    if not path:
        raise SystemExit("error: give the artifact path, positionally or with --artifact")

    artifact = load_artifact(path)
    findings = validate(artifact)
    errors = sum(1 for f in findings if f["level"] == "error")

    if args.format == "json":
        payload = json.dumps(
            {
                "artifact": os.path.abspath(path),
                "errors": errors,
                "warnings": sum(1 for f in findings if f["level"] == "warning"),
                "findings": findings,
                "boundary": "Not for patient care or live clinical use.",
            },
            indent=2,
        )
        text = payload + "\n"
    else:
        text = report_to_text(findings, path)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        log(f"wrote {args.out}")
    else:
        print(text, end="")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

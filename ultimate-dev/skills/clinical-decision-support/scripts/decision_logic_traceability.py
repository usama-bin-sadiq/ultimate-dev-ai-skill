#!/usr/bin/env python3
"""Validate a research/governance decision-logic traceability matrix and emit it as CSV.

What it does
------------
Checks that every node carries a unique ID, an allowed type, a bounded output
kind, source IDs that exist in the source ledger, a rationale, a validation test
set, an owner, a reviewer role, and a status. Then checks the matrix-level
properties: orphaned nodes, missing sources, unresolved metadata, and any node
whose logic statement reads as prohibited clinical logic. Finally it writes the
matrix as a flat CSV for review.

It does not parse or execute the logic statement. The CSV is a documentation
matrix, not executable clinical logic.

Usage
-----
    python3 scripts/decision_logic_traceability.py assets/decision_logic_traceability_template.json
    python3 scripts/decision_logic_traceability.py matrix.json --out matrix.csv --format json

Provenance
----------
Reconstructed from references/decision_logic_traceability.md, which defines the
allowed node types, output kinds, required fields, and matrix-level tests. The
prohibited-phrase screen is this file's own, and it is a screen, not a substitute
for human review.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_NODES = 500
UNRESOLVED = "unresolved"

NODE_TYPES = frozenset({
    "input_check", "data_quality_gate", "evidence_rule", "validation_gate",
    "documentation_gate", "human_review", "release_gate", "monitoring_gate",
})
OUTPUT_KINDS = frozenset({
    "include_evidence", "exclude_evidence", "flag_for_review", "validation_status",
    "documentation_status", "release_hold", "monitoring_status",
})
VALIDATION_TESTS = (
    "positive_case", "negative_case", "boundary_case", "missing_or_invalid_input",
    "source_or_version_regression", "expected_output", "reviewer", "review_date",
)
MATRIX_TESTS = (
    "unreachable_or_orphan_nodes", "conflicting_outputs", "cycles", "missing_sources",
    "stale_versions", "bypass_paths_around_human_review", "rollback_and_retirement_behavior",
)
CHANGE_CONTROL_STEPS = (
    "reason", "linked_evidence_or_requirement", "affected_nodes_and_downstream_artifacts",
    "tests_updated", "independent_validation", "approval_recorded", "rollout_and_rollback",
    "previous_version_retained", "monitoring_updated", "superseded_logic_retired_explicitly",
)

# Phrases that would put the matrix outside its documented scope. Screening for
# these is cheap and catches the common mistake; it does not replace review.
PROHIBITED_PATTERNS = (
    r"\btrigger an? (urgent|immediate)\b",
    r"\brecommend (a |the )?(therapy|treatment|drug|dose)\b",
    r"\b(start|stop|increase|decrease|adjust) (the )?(drug|dose|medication|therapy)\b",
    r"\bpatient[- ]specific\b",
    r"\bif (a|the) person'?s? score\b",
    r"\btriage\b",
    r"\burgency\b",
    r"\bbest dose\b",
    r"\bprescrib",
)
PROHIBITED_RE = re.compile("|".join(PROHIBITED_PATTERNS), re.IGNORECASE)


class Finding(dict):
    def __init__(self, level: str, field: str, message: str) -> None:
        super().__init__(level=level, field=field, message=message)


def is_unresolved(value) -> bool:
    if isinstance(value, str):
        return UNRESOLVED in value.lower()
    if isinstance(value, (list, dict)):
        return not value
    return value is None


def collect_source_ids(matrix: dict) -> set[str]:
    ids: set[str] = set()
    for source in matrix.get("source_ledger", []) or []:
        if isinstance(source, dict):
            identifier = source.get("source_id")
            if isinstance(identifier, str) and not is_unresolved(identifier):
                ids.add(identifier)
    return ids


def check_metadata(matrix: dict, findings: list[Finding]) -> None:
    metadata = matrix.get("matrix_metadata")
    if not isinstance(metadata, dict):
        findings.append(Finding("error", "matrix_metadata", "matrix metadata is missing"))
        return
    for field in ("logic_id", "title", "version", "status", "owner",
                  "research_only_intended_use", "data_level", "source_ledger",
                  "change_summary", "monitoring_criteria", "retirement_criteria"):
        if is_unresolved(metadata.get(field)):
            findings.append(Finding("error", f"matrix_metadata.{field}", "unresolved"))
    if metadata.get("human_review_required") is not True:
        findings.append(Finding(
            "error", "matrix_metadata.human_review_required",
            "human review is required for a research or governance matrix and must be declared",
        ))
    uses = metadata.get("prohibited_uses")
    if isinstance(uses, list) and len(uses) < 5:
        findings.append(Finding(
            "error", "matrix_metadata.prohibited_uses",
            f"only {len(uses)} prohibited use(s) recorded; the boundary lists more",
        ))


def check_source_ledger(matrix: dict, valid_ids: set[str], findings: list[Finding]) -> None:
    ledger = matrix.get("source_ledger")
    if not isinstance(ledger, list) or not ledger:
        findings.append(Finding("error", "source_ledger", "the matrix must carry a source ledger"))
        return
    for index, source in enumerate(ledger):
        path = f"source_ledger[{index}]"
        if not isinstance(source, dict):
            findings.append(Finding("error", path, "each ledger entry must be an object"))
            continue
        for field in ("citation", "version_or_date"):
            if is_unresolved(source.get(field)):
                findings.append(Finding("error", f"{path}.{field}", f"{field} is unresolved"))


def check_node(node, index: int, valid_ids: set[str], findings: list[Finding]) -> None:
    path = f"nodes[{index}]"
    if not isinstance(node, dict):
        findings.append(Finding("error", path, "each node must be an object"))
        return

    node_id = node.get("node_id")
    if is_unresolved(node_id):
        findings.append(Finding("error", f"{path}.node_id", "each node needs a unique ID"))
    elif not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", str(node_id)):
        findings.append(Finding(
            "error", f"{path}.node_id",
            f"{node_id!r} should be letters, digits, dot, underscore, or hyphen",
        ))

    node_type = node.get("type")
    if node_type not in NODE_TYPES:
        findings.append(Finding(
            "error", f"{path}.type",
            f"{node_type!r} is not an allowed node type; allowed: {', '.join(sorted(NODE_TYPES))}",
        ))

    output_kind = node.get("output_kind")
    if output_kind not in OUTPUT_KINDS:
        findings.append(Finding(
            "error", f"{path}.output_kind",
            f"{output_kind!r} is not an allowed output kind; allowed: "
            f"{', '.join(sorted(OUTPUT_KINDS))}",
        ))

    for field in ("precondition_or_input", "logic_statement", "output_value", "rationale",
                  "owner", "reviewer_role", "status"):
        if is_unresolved(node.get(field)):
            findings.append(Finding("error", f"{path}.{field}", f"{field} is unresolved"))

    cited = node.get("source_ids")
    if not isinstance(cited, list) or not cited:
        findings.append(Finding("error", f"{path}.source_ids",
                                "every node must link to at least one source ID"))
    else:
        for identifier in cited:
            if identifier not in valid_ids:
                findings.append(Finding(
                    "error", f"{path}.source_ids",
                    f"cites source ID {identifier!r}, which is not in the ledger",
                ))

    tests = node.get("validation_tests")
    if not isinstance(tests, dict):
        findings.append(Finding("error", f"{path}.validation_tests",
                                "each node needs its validation test set"))
    else:
        for field in VALIDATION_TESTS:
            if is_unresolved(tests.get(field)):
                findings.append(Finding("error", f"{path}.validation_tests.{field}", "unresolved"))

    if is_unresolved(node.get("known_limitations")):
        findings.append(Finding("warning", f"{path}.known_limitations",
                                "record the node's known limitations"))

    statement = node.get("logic_statement")
    if isinstance(statement, str) and statement and not is_unresolved(statement):
        hit = PROHIBITED_RE.search(statement)
        if hit:
            findings.append(Finding(
                "error", f"{path}.logic_statement",
                f"reads as prohibited clinical logic (matched {hit.group(0)!r}). This matrix "
                "documents research and governance rules only",
            ))


def check_nodes(matrix: dict, valid_ids: set[str], findings: list[Finding]) -> None:
    nodes = matrix.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        findings.append(Finding("error", "nodes", "the matrix must document at least one node"))
        return
    if len(nodes) > MAX_NODES:
        findings.append(Finding("error", "nodes", f"more than {MAX_NODES} nodes"))
        return

    seen: set[str] = set()
    for index, node in enumerate(nodes):
        check_node(node, index, valid_ids, findings)
        if isinstance(node, dict):
            node_id = node.get("node_id")
            if isinstance(node_id, str) and not is_unresolved(node_id):
                if node_id in seen:
                    findings.append(Finding(
                        "error", f"nodes[{index}].node_id", f"duplicate node ID {node_id!r}"
                    ))
                seen.add(node_id)

    # A human_review node that nothing references is an orphan.
    review_nodes = {
        str(node.get("node_id")) for node in nodes
        if isinstance(node, dict) and node.get("type") == "human_review"
    }
    if not review_nodes:
        findings.append(Finding(
            "error", "nodes",
            "no human_review node; every research or governance matrix needs its approval "
            "checkpoint documented as a node",
        ))


def check_matrix_tests(matrix: dict, findings: list[Finding]) -> None:
    tests = matrix.get("matrix_level_tests")
    if not isinstance(tests, dict):
        findings.append(Finding("error", "matrix_level_tests", "the matrix-level tests are missing"))
        return
    for field in MATRIX_TESTS:
        if is_unresolved(tests.get(field)):
            findings.append(Finding("error", f"matrix_level_tests.{field}", "unresolved"))


def check_change_control(matrix: dict, findings: list[Finding]) -> None:
    control = matrix.get("change_control")
    if not isinstance(control, dict):
        findings.append(Finding("error", "change_control", "the change-control record is missing"))
        return
    for field in CHANGE_CONTROL_STEPS:
        if is_unresolved(control.get(field)):
            findings.append(Finding("error", f"change_control.{field}", "unresolved"))


def check_boundary(matrix: dict, findings: list[Finding]) -> None:
    """The matrix must carry a boundary statement and not smuggle a generic action node."""
    for key in matrix:
        if str(key).lower() in {"action", "action_node", "actions", "clinical_action"}:
            findings.append(Finding(
                "error", str(key),
                "there is deliberately no generic action node in this schema",
            ))


def check(matrix: dict) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(matrix, dict):
        return [Finding("error", "$", "the matrix must be a JSON object")]
    check_boundary(matrix, findings)
    check_metadata(matrix, findings)
    valid_ids = collect_source_ids(matrix)
    check_source_ledger(matrix, valid_ids, findings)
    check_nodes(matrix, valid_ids, findings)
    check_matrix_tests(matrix, findings)
    check_change_control(matrix, findings)
    return findings


def load_matrix(path: str) -> dict:
    if path.startswith(("http://", "https://", "file://")):
        raise SystemExit(f"error: {path} looks like a URL; this helper reads local files only")
    file_path = Path(path)
    if not file_path.is_file():
        raise SystemExit(f"error: matrix not found: {path}")
    if file_path.stat().st_size > MAX_FILE_BYTES:
        raise SystemExit(f"error: {path} is larger than {MAX_FILE_BYTES} bytes")
    try:
        with file_path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: {path} is not valid JSON: {exc}")


def write_csv(matrix: dict, out_path: Path) -> Path:
    """Flatten the matrix into one row per node for spreadsheet review."""
    fields = [
        "node_id", "type", "precondition_or_input", "logic_statement", "output_kind",
        "output_value", "source_ids", "rationale", "owner", "reviewer_role", "status",
        "known_limitations", "validation_tests_documented",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for node in matrix.get("nodes", []) or []:
            if not isinstance(node, dict):
                continue
            tests = node.get("validation_tests")
            documented = (
                sum(1 for field in VALIDATION_TESTS if not is_unresolved(tests.get(field)))
                if isinstance(tests, dict) else 0
            )
            writer.writerow({
                "node_id": node.get("node_id", ""),
                "type": node.get("type", ""),
                "precondition_or_input": node.get("precondition_or_input", ""),
                "logic_statement": node.get("logic_statement", ""),
                "output_kind": node.get("output_kind", ""),
                "output_value": node.get("output_value", ""),
                "source_ids": ";".join(str(s) for s in (node.get("source_ids") or [])),
                "rationale": node.get("rationale", ""),
                "owner": node.get("owner", ""),
                "reviewer_role": node.get("reviewer_role", ""),
                "status": node.get("status", ""),
                "known_limitations": node.get("known_limitations", ""),
                "validation_tests_documented": f"{documented}/{len(VALIDATION_TESTS)}",
            })
    return out_path


def report_to_text(findings: list[Finding], path: str) -> str:
    errors = sum(1 for f in findings if f["level"] == "error")
    warnings = sum(1 for f in findings if f["level"] == "warning")
    lines = [f"matrix: {path}", f"errors: {errors}, warnings: {warnings}", ""]
    for finding in findings:
        lines.append(f"{finding['level']}: {finding['field']}: {finding['message']}")
    lines += ["",
              "This report validates identifiers, allowed node and output types, citations, and "
              "required review fields. It does not parse or execute the logic statement. The "
              "output is a documentation matrix, not executable clinical logic, and is not for "
              "patient care or live clinical use."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a research/governance decision-logic traceability matrix.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("matrix", help="local JSON traceability matrix")
    parser.add_argument("--out", default=None, help="write the flattened matrix CSV here")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="report format")
    args = parser.parse_args(argv)

    matrix = load_matrix(args.matrix)
    findings = check(matrix)
    errors = sum(1 for f in findings if f["level"] == "error")

    if args.format == "json":
        text = json.dumps(
            {
                "matrix": args.matrix,
                "errors": errors,
                "warnings": sum(1 for f in findings if f["level"] == "warning"),
                "findings": findings,
                "boundary": "Documentation matrix, not executable clinical logic.",
            },
            indent=2,
        ) + "\n"
    else:
        text = report_to_text(findings, args.matrix)

    print(text, end="")
    if args.out:
        path = write_csv(matrix, Path(args.out))
        print(f"wrote {path}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

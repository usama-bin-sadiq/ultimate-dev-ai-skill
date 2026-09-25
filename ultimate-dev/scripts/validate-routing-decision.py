#!/usr/bin/env python3
"""Validate one structured routing decision without calling a model or service."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DELIVERABLES = {
    "answer", "research", "comparison", "recommendation", "plan", "requirements",
    "specification", "decision", "code", "bug-fix", "review", "security-review",
    "audit", "financial-analysis", "data-analysis", "document", "spreadsheet",
    "presentation", "communication", "workflow", "creative", "learning", "unknown",
}
SIZES = {"atomic", "moderate", "complex", "ambiguous"}
RISKS = {"none", "data", "security", "compliance"}
CLARITIES = {"clear", "resolvable", "blocked"}
GAPS = {"none", "partial", "blocking"}


def canonical_domains() -> set[str]:
    text = (ROOT / "config" / "capability-index.yaml").read_text(encoding="utf-8")
    match = re.search(r"^domains:\s*$([\s\S]*?)(?=^[A-Za-z_][\w-]*:\s*$|\Z)", text, re.MULTILINE)
    if not match:
        return set()
    return set(re.findall(r"^  - id:\s*([A-Za-z0-9_-]+)\s*$", match.group(1), re.MULTILINE))


def routable_names() -> set[str]:
    """Skills and agents that a route may legitimately name."""
    names = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
    names.update(path.stem for path in (ROOT / "agents").rglob("*.md"))
    names.update({"universal-task", "inline"})
    return names


def validate(decision: Any) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(decision, dict):
        return {"ok": False, "errors": ["decision must be a mapping"], "warnings": []}
    for field in ("deliverable", "size", "domains", "risk", "clarity", "capability_gap", "route"):
        if field not in decision:
            errors.append(f"missing field: {field}")
    if decision.get("deliverable") not in DELIVERABLES:
        errors.append(f"invalid deliverable: {decision.get('deliverable')!r}")
    if decision.get("size") not in SIZES:
        errors.append(f"invalid size: {decision.get('size')!r}")
    if decision.get("risk") not in RISKS:
        errors.append(f"invalid risk: {decision.get('risk')!r}")
    if decision.get("clarity") not in CLARITIES:
        errors.append(f"invalid clarity: {decision.get('clarity')!r}")
    gap = decision.get("capability_gap")
    if isinstance(gap, dict):
        gap = gap.get("level")
    if gap not in GAPS:
        errors.append(f"invalid capability_gap: {gap!r}")
    domains = decision.get("domains")
    if not isinstance(domains, list) or not domains:
        errors.append("domains must be a non-empty list")
    else:
        allowed = canonical_domains()
        unknown = sorted({str(item) for item in domains} - allowed)
        if unknown:
            errors.append(f"non-canonical domain(s): {', '.join(unknown)}")
    route = decision.get("route")
    if not isinstance(route, str) or not route.strip():
        errors.append("route must be a non-empty string")
    elif route.strip() not in routable_names():
        errors.append(f"route '{route}' does not resolve to a shipped skill or agent")
    activated = decision.get("activated_forbidden_domains", [])
    if not isinstance(activated, list):
        errors.append("activated_forbidden_domains must be a list")
    else:
        forbidden = set(map(str, decision.get("expected_forbidden_domains", []) or []))
        overlap = sorted(forbidden.intersection(map(str, activated)))
        if overlap:
            errors.append(f"forbidden domain activated: {', '.join(overlap)}")
    self_check = decision.get("self_check")
    if self_check is not None:
        if not isinstance(self_check, dict):
            errors.append("self_check must be a mapping")
        else:
            passes = self_check.get("passes", 1)
            if not isinstance(passes, int) or isinstance(passes, bool) or passes < 0:
                errors.append("self_check.passes must be a non-negative integer")
            elif passes > 1:
                errors.append(f"self_check is bounded to one pass, got {passes}")
            unresolved = self_check.get("unresolved", [])
            if not isinstance(unresolved, list):
                errors.append("self_check.unresolved must be a list")
    if decision.get("clarity") == "blocked" and decision.get("capability_gap") == "none":
        warnings.append("blocked clarity usually requires a named capability or decision gap")
    if isinstance(decision.get("domains"), list) and len(decision["domains"]) > 3:
        warnings.append("more than three domains may indicate over-broad routing")

    # Coherence: an unfamiliar domain must report the knowledge gap it implies.
    gap_level = gap if isinstance(gap, str) else None
    if isinstance(domains, list) and "unknown-unclassified" in {str(item) for item in domains}:
        if gap_level == "none":
            errors.append(
                "unknown-unclassified domain requires capability_gap partial or blocking, not none"
            )

    # Coherence: a raised risk must name the actual impact, not a topic.
    risk = decision.get("risk")
    risk_basis = decision.get("risk_basis")
    if risk in {"data", "security", "compliance"}:
        if not isinstance(risk_basis, str) or not risk_basis.strip():
            errors.append(f"risk '{risk}' requires a non-empty risk_basis naming the actual impact")
        elif len(risk_basis.split()) > 25:
            errors.append("risk_basis must be a short impact clause, not a narrative")
    elif isinstance(risk_basis, str) and risk_basis.strip():
        warnings.append("risk 'none' with a risk_basis usually means the risk should be raised")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decision", type=Path, help="JSON decision file, or - for stdin")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.read() if str(args.decision) == "-" else args.decision.read_text(encoding="utf-8")
        result = validate(json.loads(raw))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"validate-routing-decision: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"{'PASS' if result['ok'] else 'FAIL'}: routing decision")
        for error in result["errors"]:
            print(f"  ERROR: {error}")
        for warning in result["warnings"]:
            print(f"  WARN: {warning}")
    return 1 if args.strict and not result["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

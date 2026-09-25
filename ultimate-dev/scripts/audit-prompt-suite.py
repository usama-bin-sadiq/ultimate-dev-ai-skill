#!/usr/bin/env python3
"""Audit Ultimate-Dev as a portable prompt skill, not as a runtime system.

The audit is deliberately local and deterministic. It measures packaging,
metadata, routing discoverability, progressive disclosure, evaluation coverage,
and prompt/runtime boundary consistency. It does not call a model, provider,
browser, container, MCP server, or external API.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment dependent
    raise SystemExit("audit-prompt-suite: PyYAML is required") from exc

ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SKILL_DESCRIPTION = 1024
MAX_SKILL_WORDS = 700
MAX_AGENT_DESCRIPTION = 1024
BROAD_TRIGGER_THRESHOLD = 5
MIN_GOLDEN_CASES = 150
MIN_NEGATIVE_RATIO = 0.40
REQUIRED_CONTRACT_FILES = (
    "contracts/README.md",
    "contracts/four-channels.md",
    "contracts/task-envelope.yaml",
)
NORMALIZED_SKILLS = {
    "coding", "research", "testing", "review", "architecture", "security",
    "debugging", "devops", "documentation", "data",
}
CROSS_FUNCTIONAL_AUDIT_DOMAINS = {
    "internal-communications": ("status update", "meeting notes", "decision memo", "stakeholder"),
    "legal-privacy-contracts": ("contract", "privacy", "legal hold", "retention"),
    "people-operations": ("hiring", "onboarding", "employee", "workforce"),
    "procurement-vendors": ("procurement", "vendor", "supplier", "rfp"),
    "accounting-controls": ("accounting", "ledger", "reconciliation", "close"),
    "office-knowledge-artifacts": ("pdf", "docx", "xlsx", "pptx", "spreadsheet"),
    "strategy-operating-model": ("strategy", "operating model", "okr", "kpi tree"),
    "data-bi": ("dashboard", "data analysis", "metric definition", "business intelligence"),
    "audit-risk-assurance": ("internal audit", "control test", "evidence request"),
}
RUNTIME_CLAIM_PATTERNS = (
    (re.compile(r"runtime\.[a-z_]+", re.I), "direct Runtime API call"),
    (re.compile(r"before any task.{0,120}(runtime|jev|state\.json)", re.I | re.S), "mandatory runtime wording"),
    (re.compile(r"mandatory.{0,120}(runtime|jev|state\.json)", re.I | re.S), "mandatory runtime/state wording"),
    (re.compile(r"call .*runtime", re.I), "imperative Runtime call"),
    (re.compile(r"state\.json.{0,80}authoritative", re.I | re.S), "state.json treated as universally authoritative"),
)


def read_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
    if not match:
        return {}, text
    value = yaml.safe_load(match.group(1)) or {}
    return (value if isinstance(value, dict) else {}), text


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def audit() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    unsafe_generation_claims: list[str] = []
    agents: list[dict[str, Any]] = []
    skills: list[dict[str, Any]] = []
    modules: list[dict[str, Any]] = []

    for path in sorted((ROOT / "agents").rglob("*.md")):
        if "_shared" in path.parts or path.name.startswith("."):
            continue
        metadata, text = read_frontmatter(path)
        entry = {
            "path": relative(path),
            "id": metadata.get("name"),
            "domain": metadata.get("domain"),
            "description": str(metadata.get("description") or ""),
            "triggers": [str(item).lower() for item in (metadata.get("triggers") or [])],
            "anti_triggers": [str(item).lower() for item in (metadata.get("anti_triggers") or [])],
            "words": len(text.split()),
        }
        agents.append(entry)
        if re.search(r"auto-generate|automatically create|create the agent file|auto-generation enabled", text, re.I):
            unsafe_generation_claims.append(relative(path))
        if not SKILL_NAME_RE.fullmatch(str(entry["id"] or "")):
            errors.append(f"{entry['path']}: invalid agent id")
        if not entry["description"] or len(entry["description"]) > MAX_AGENT_DESCRIPTION:
            errors.append(f"{entry['path']}: description must be 1-{MAX_AGENT_DESCRIPTION} characters")
        if not entry["triggers"] or not entry["anti_triggers"]:
            errors.append(f"{entry['path']}: triggers and anti_triggers are required")

    for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
        metadata, text = read_frontmatter(path)
        name = str(metadata.get("name") or "")
        description = str(metadata.get("description") or "")
        entry = {
            "path": relative(path),
            "id": name,
            "description": description,
            "triggers": [str(item).lower() for item in (metadata.get("triggers") or [])],
            "provides": metadata.get("provides"),
            "words": len(text.split()),
        }
        skills.append(entry)
        if not SKILL_NAME_RE.fullmatch(name):
            errors.append(f"{entry['path']}: invalid skill name")
        if name != path.parent.name:
            errors.append(f"{entry['path']}: skill name must match directory name")
        if not description or len(description) > MAX_SKILL_DESCRIPTION:
            errors.append(f"{entry['path']}: description must be 1-{MAX_SKILL_DESCRIPTION} characters")
        if not isinstance(metadata.get("triggers"), list) or not metadata["triggers"]:
            errors.append(f"{entry['path']}: triggers must be a non-empty list")
        if not metadata.get("provides"):
            errors.append(f"{entry['path']}: provides is required")
        if name in NORMALIZED_SKILLS and "## Operating Contract" not in text:
            errors.append(f"{entry['path']}: normalized skill lacks ## Operating Contract")
        if entry["words"] > MAX_SKILL_WORDS:
            warnings.append(f"{entry['path']}: {entry['words']} words; consider progressive disclosure")

    for path in sorted((ROOT / "modules").rglob("*.md")):
        _, text = read_frontmatter(path)
        modules.append({"path": relative(path), "words": len(text.split())})

    for contract_relative in REQUIRED_CONTRACT_FILES:
        if not (ROOT / contract_relative).is_file():
            errors.append(f"required contract is missing: {contract_relative}")
    if not (ROOT / "skills" / "universal-task" / "SKILL.md").is_file():
        errors.append("skills/universal-task/SKILL.md is missing")
    if unsafe_generation_claims:
        errors.append("unsafe automatic specialist creation claims: " + ", ".join(sorted(unsafe_generation_claims)))

    trigger_index: dict[str, list[str]] = collections.defaultdict(list)
    for agent in agents:
        for trigger in agent["triggers"]:
            trigger_index[trigger].append(agent["id"] or agent["path"])
    collisions = [
        {"trigger": trigger, "count": len(ids), "agents": sorted(ids)}
        for trigger, ids in sorted(trigger_index.items())
        if len(ids) >= BROAD_TRIGGER_THRESHOLD
    ]

    capability_path = ROOT / "config" / "capability-index.yaml"
    capability_domains: list[dict[str, Any]] = []
    deliverable_types: list[dict[str, Any]] = []
    if capability_path.exists():
        try:
            capability = yaml.safe_load(capability_path.read_text(encoding="utf-8")) or {}
            capability_domains = capability.get("domains") or []
            deliverable_types = capability.get("deliverable_types") or []
        except yaml.YAMLError as exc:
            errors.append(f"config/capability-index.yaml: {exc}")
    else:
        errors.append("config/capability-index.yaml is missing")
    for domain in capability_domains:
        if not isinstance(domain, dict):
            errors.append("capability index contains a non-mapping domain")
            continue
        for field in ("id", "status", "signals", "skills", "agents", "fallback", "risk"):
            if field not in domain:
                errors.append(f"capability domain {domain.get('id', '<unknown>')}: missing {field}")
    deliverable_ids: set[str] = set()
    if not isinstance(deliverable_types, list) or not deliverable_types:
        errors.append("config/capability-index.yaml: deliverable_types must be a non-empty list")
    else:
        for deliverable in deliverable_types:
            if not isinstance(deliverable, dict):
                errors.append("capability deliverable_types contains a non-mapping entry")
                continue
            identifier = str(deliverable.get("id") or "")
            if not identifier:
                errors.append("capability deliverable has an empty id")
            elif identifier in deliverable_ids:
                errors.append(f"duplicate capability deliverable: {identifier}")
            deliverable_ids.add(identifier)
            for field in ("signals", "primary_skills", "output_contract"):
                if not deliverable.get(field):
                    errors.append(f"capability deliverable {identifier or '<unknown>'}: missing {field}")
        if "unknown" not in deliverable_ids:
            errors.append("capability deliverable_types must include unknown")
    unknown_domain = next(
        (domain for domain in capability_domains if isinstance(domain, dict) and domain.get("id") == "unknown-unclassified"),
        None,
    )
    if unknown_domain is None:
        errors.append("capability index must include unknown-unclassified")
    elif unknown_domain.get("fallback_skill") != "universal-task":
        errors.append("unknown-unclassified must use universal-task as fallback_skill")

    eval_path = ROOT / "evals" / "golden-cases.yaml"
    cases: list[dict[str, Any]] = []
    if eval_path.exists():
        try:
            eval_data = yaml.safe_load(eval_path.read_text(encoding="utf-8")) or {}
            cases = eval_data.get("cases") or []
        except yaml.YAMLError as exc:
            errors.append(f"evals/golden-cases.yaml: {exc}")
    else:
        errors.append("evals/golden-cases.yaml is missing")
    case_domains = {str(domain) for case in cases for domain in (case.get("expected_domains") or [])}
    case_text = " ".join(str(case.get("task") or "") for case in cases).lower()
    case_categories = collections.Counter(
        str(case.get("category") or ("near-miss" if "nearmiss" in str(case.get("id") or "").lower() else "positive"))
        for case in cases
    )
    negative_count = sum(
        count for category, count in case_categories.items()
        if category.lower().replace("_", "-") in {"near-miss", "nearmiss", "negative"}
    )
    negative_ratio = negative_count / len(cases) if cases else 0.0
    deliverable_count = sum(1 for case in cases if case.get("expected_deliverable"))
    ambiguous_without_clarity = sum(
        1 for case in cases
        if str(case.get("expected_size") or "") == "ambiguous" and not case.get("expected_clarity")
    )
    uncovered_domains = [
        domain
        for domain, signals in CROSS_FUNCTIONAL_AUDIT_DOMAINS.items()
        if domain not in case_domains and not any(signal in case_text for signal in signals)
    ]
    if len(cases) < MIN_GOLDEN_CASES:
        warnings.append(f"golden cases: {len(cases)} (target >= {MIN_GOLDEN_CASES})")
    if negative_ratio < MIN_NEGATIVE_RATIO:
        errors.append(f"golden negative/near-miss ratio {negative_ratio:.1%} is below {MIN_NEGATIVE_RATIO:.0%}")
    if cases and deliverable_count / len(cases) < 0.80:
        warnings.append(
            f"legacy fixture migration pending: {len(cases) - deliverable_count} case(s) predate expected_deliverable"
        )
    if ambiguous_without_clarity:
        warnings.append(
            f"{ambiguous_without_clarity} case(s) use size=ambiguous without expected_clarity=blocked"
        )
    if uncovered_domains:
        warnings.append("golden cases do not cover: " + ", ".join(sorted(uncovered_domains)))

    boundary_claims: list[dict[str, Any]] = []
    for path in (ROOT / "SKILL.md", ROOT / "AGENTS.md"):
        text = path.read_text(encoding="utf-8")
        for pattern, label in RUNTIME_CLAIM_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                boundary_claims.append({"file": relative(path), "kind": label, "count": len(matches)})
                warnings.append(f"{relative(path)}: {len(matches)} {label} reference(s) need prompt-only qualification")

    prompt_only_profile = any(
        "prompt-only jev profile" in path.read_text(encoding="utf-8").lower()
        for path in (ROOT / "SKILL.md", ROOT / "AGENTS.md")
    )
    if not prompt_only_profile:
        errors.append("SKILL.md/AGENTS.md must document a prompt-only JEV profile")

    common_skill_names = {
        skill_name
        for domain in capability_domains
        if isinstance(domain, dict)
        for skill_name in (domain.get("skills") or [])
    }
    return {
        "scope": "portable prompt skill only",
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "agents": len(agents),
            "skills": len(skills),
            "modules": len(modules),
            "agent_body_words": sum(item["words"] for item in agents),
            "skill_body_words": sum(item["words"] for item in skills),
            "module_body_words": sum(item["words"] for item in modules),
            "common_skills_referenced": len(common_skill_names & {item["id"] for item in skills}),
            "golden_cases": len(cases),
            "golden_case_domains": len(case_domains),
            "golden_deliverable_types": len({str(case.get("expected_deliverable")) for case in cases if case.get("expected_deliverable")}),
            "golden_negative_or_near_miss_cases": negative_count,
            "golden_negative_or_near_miss_ratio": round(negative_ratio, 4),
            "golden_cases_with_expected_deliverable": deliverable_count,
            "golden_ambiguous_without_clarity": ambiguous_without_clarity,
            "capability_domains": len(capability_domains),
            "deliverable_types": len(deliverable_ids),
        },
        "trigger_collisions": collisions,
        "boundary_claims": boundary_claims,
        "uncovered_cross_functional_domains": sorted(uncovered_domains),
        "unsafe_generation_claims": sorted(unsafe_generation_claims),
        "long_skills": [item for item in skills if item["words"] > MAX_SKILL_WORDS],
    }


def render_markdown(result: dict[str, Any]) -> str:
    metrics = result["metrics"]
    lines = [
        "# Prompt-Suite Audit",
        "",
        "**Scope:** portable prompt skill only; no provider, runtime, browser, container, MCP, or external API claims.",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key, value in metrics.items():
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## Errors", ""])
    lines.extend([f"- `{item}`" for item in result["errors"]] or ["- None"])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {item}" for item in result["warnings"]] or ["- None"])
    lines.extend(["", "## Trigger collisions", ""])
    if result["trigger_collisions"]:
        for item in result["trigger_collisions"]:
            lines.append(f"- `{item['trigger']}`: {item['count']} agents")
    else:
        lines.append("- None")
    lines.extend(["", "## Uncovered cross-functional eval domains", ""])
    lines.extend([f"- {item}" for item in result["uncovered_cross_functional_domains"]] or ["- None"])
    lines.extend(["", "## Prompt/runtime boundary claims", ""])
    if result["boundary_claims"]:
        for item in result["boundary_claims"]:
            lines.append(f"- `{item['file']}`: {item['count']} {item['kind']} reference(s)")
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--strict", action="store_true", help="exit nonzero for errors")
    args = parser.parse_args(argv)
    result = audit()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_markdown(result), end="")
    return 1 if args.strict and result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

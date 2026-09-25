#!/usr/bin/env python3
"""Run a provider-free prompt-routing fixture benchmark.

This tool validates the golden case contract and, when explicitly supplied with
a local classifier callable, compares that callable's structured output with the
fixture expectations. It never discovers or calls a model, provider, browser,
container, MCP server, or external API. Without a local classifier, execution
is reported as ``not_run`` rather than being presented as a model benchmark.
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from runtime.evaluation import load_cases
except Exception as exc:  # pragma: no cover - environment-dependent import failure
    raise SystemExit(f"benchmark-prompt-routing: unable to load evaluation reader: {exc}")

VALID_SIZES = {"atomic", "moderate", "complex", "ambiguous"}
VALID_RISKS = {"none", "data", "security", "compliance"}
VALID_DELIVERABLES = {
    "answer", "research", "comparison", "recommendation", "plan", "requirements",
    "specification", "decision", "code", "bug-fix", "review", "security-review",
    "audit", "financial-analysis", "data-analysis", "document", "spreadsheet",
    "presentation", "communication", "workflow", "creative", "learning", "unknown",
}
CASE_REQUIRED = {"id", "task", "expected_size", "expected_domains", "expected_risk"}
CATEGORY_RE = re.compile(r"(near[-_ ]?miss|negative|unknown|multilingual|capability[-_ ]?gap)", re.I)


def _domain_alias_policy() -> tuple[dict[str, str], set[str]]:
    try:
        data = json.loads((ROOT / "evals" / "domain-aliases.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, set()
    safe = data.get("safe_aliases") if isinstance(data, dict) else {}
    ambiguous = data.get("ambiguous_labels") if isinstance(data, dict) else []
    return (
        {str(key): str(value) for key, value in (safe or {}).items()},
        {str(value) for value in (ambiguous or [])},
    )


def _canonical_domain_ids() -> set[str]:
    """Read canonical domain IDs without adding a YAML dependency."""
    index_path = ROOT / "config" / "capability-index.yaml"
    try:
        text = index_path.read_text(encoding="utf-8")
    except OSError:
        return set()
    match = re.search(r"^domains:\s*$([\s\S]*?)(?=^[A-Za-z_][\w-]*:\s*$|\Z)", text, re.MULTILINE)
    if not match:
        return set()
    return set(re.findall(r"^  - id:\s*([A-Za-z0-9_-]+)\s*$", match.group(1), re.MULTILINE))


def _case_category(case: dict[str, Any]) -> str:
    explicit = str(case.get("category") or "").strip().lower()
    if explicit:
        return explicit
    identifier = str(case.get("id") or "")
    match = CATEGORY_RE.search(identifier)
    return match.group(1).lower().replace(" ", "-") if match else "positive"


def _expected_fields(case: dict[str, Any]) -> dict[str, Any]:
    expected: dict[str, Any] = {}
    nested = case.get("expected")
    if isinstance(nested, dict):
        expected.update(nested)
    for key in (
        "expected_size", "expected_domains", "expected_risk", "expected_deliverable",
        "expected_route", "expected_forbidden_domains", "expected_clarity",
        "expected_capability_gap",
    ):
        if key in case:
            expected[key.removeprefix("expected_")] = case[key]
    return expected


def _load_local_classifier(spec: str) -> Callable[[dict[str, Any]], Any]:
    """Load ``path.py:function`` without importing anything outside the repo."""

    if ":" not in spec:
        raise ValueError("--classifier must use path.py:function syntax")
    raw_path, function_name = spec.rsplit(":", 1)
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError("classifier must be inside the Ultimate-Dev repository") from exc
    if not path.is_file() or path.suffix != ".py":
        raise ValueError("classifier must be an existing repository Python file")
    module_spec = importlib.util.spec_from_file_location("ud_local_prompt_classifier", path)
    if module_spec is None or module_spec.loader is None:
        raise ValueError("unable to load classifier module")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    function = getattr(module, function_name, None)
    if not callable(function):
        raise ValueError(f"classifier function not found: {function_name}")
    return function


def _comparison_value(value: Any) -> Any:
    if isinstance(value, dict) and "level" in value:
        return value.get("level")
    return value


def _compare(
    expected: dict[str, Any],
    actual: Any,
    safe_aliases: dict[str, str] | None = None,
    ambiguous_labels: set[str] | None = None,
) -> tuple[bool, list[str]]:
    if not isinstance(actual, dict):
        return False, ["classifier_output_not_mapping"]
    reasons: list[str] = []
    for key in ("size", "risk", "deliverable", "route", "clarity", "capability_gap"):
        if key in expected and str(_comparison_value(actual.get(key, ""))).lower() != str(expected[key]).lower():
            reasons.append(f"{key}_mismatch")
    if "domains" in expected:
        expected_values = {str(item) for item in (expected["domains"] or [])}
        ambiguous_labels = ambiguous_labels or set()
        safe_aliases = safe_aliases or {}
        if expected_values and not expected_values.intersection(ambiguous_labels):
            expected_domains = {safe_aliases.get(item, item) for item in expected_values}
            actual_domains = {
                safe_aliases.get(str(item), str(item))
                for item in (actual.get("domains") or [])
            }
            if expected_domains != actual_domains:
                reasons.append("domains_mismatch")
    if "forbidden_domains" in expected:
        activated = actual.get("activated_forbidden_domains")
        if not isinstance(activated, list):
            reasons.append("forbidden_domains_not_reported")
        else:
            forbidden = {str(item) for item in expected["forbidden_domains"]}
            if forbidden.intersection(str(item) for item in activated):
                reasons.append("forbidden_domain_activated")
    return not reasons, reasons


def benchmark(cases: list[dict[str, Any]], classifier: Callable[[dict[str, Any]], Any] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    ids: set[str] = set()
    categories: collections.Counter[str] = collections.Counter()
    domains: set[str] = set()
    deliverables: set[str] = set()
    risks: set[str] = set()
    missing_deliverable = 0
    negative_count = 0
    unknown_count = 0
    forbidden_count = 0
    multilingual_count = 0
    legacy_ambiguous_count = 0
    ambiguous_without_clarity = 0
    canonical_domain_ids = _canonical_domain_ids()
    safe_aliases, ambiguous_labels = _domain_alias_policy()
    noncanonical_fixture_domains: set[str] = set()
    safe_alias_fixture_domains: set[str] = set()
    ambiguous_fixture_domains: set[str] = set()
    domain_comparison_unscored_cases = 0
    executed = 0
    passed = 0
    failed = 0
    uncertain = 0

    for index, case in enumerate(cases, 1):
        if not isinstance(case, dict):
            errors.append(f"case {index}: case must be a mapping")
            continue
        missing = sorted(CASE_REQUIRED - set(case))
        if missing:
            errors.append(f"case {index}: missing {', '.join(missing)}")
        identifier = str(case.get("id") or f"case-{index}")
        if identifier in ids:
            errors.append(f"duplicate case id: {identifier}")
        ids.add(identifier)
        if not str(case.get("task") or "").strip():
            errors.append(f"{identifier}: task must be non-empty")
        size = str(case.get("expected_size") or "")
        risk = str(case.get("expected_risk") or "")
        if size not in VALID_SIZES:
            errors.append(f"{identifier}: invalid expected_size {size!r}")
        if risk not in VALID_RISKS:
            errors.append(f"{identifier}: invalid expected_risk {risk!r}")
        if not isinstance(case.get("expected_domains"), list):
            errors.append(f"{identifier}: expected_domains must be a list")
        else:
            domains.update(str(item) for item in case["expected_domains"])
            if canonical_domain_ids:
                noncanonical_fixture_domains.update(
                    str(item) for item in case["expected_domains"]
                    if str(item) not in canonical_domain_ids
                )
                safe_alias_fixture_domains.update(
                    str(item) for item in case["expected_domains"]
                    if str(item) in safe_aliases
                )
                ambiguous_fixture_domains.update(
                    str(item) for item in case["expected_domains"]
                    if str(item) in ambiguous_labels
                )
                if any(str(item) in ambiguous_labels for item in case["expected_domains"]):
                    domain_comparison_unscored_cases += 1
        risks.add(risk)
        category = _case_category(case)
        categories[category] += 1
        normalized_category = category.lower().replace("_", "-")
        if normalized_category in {"near-miss", "nearmiss", "negative"}:
            negative_count += 1
            forbidden = case.get("expected_forbidden_domains")
            if not isinstance(forbidden, list) or not forbidden:
                errors.append(f"{identifier}: near-miss case must declare expected_forbidden_domains")
            else:
                forbidden_count += 1
        if category == "unknown" or "unknown" in identifier.lower():
            unknown_count += 1
            if not case.get("expected_capability_gap"):
                errors.append(f"{identifier}: unknown case must declare expected_capability_gap")
        if category == "multilingual" or case.get("output_language"):
            multilingual_count += 1
            if not case.get("output_language"):
                errors.append(f"{identifier}: multilingual case must declare output_language")
        if size == "ambiguous":
            legacy_ambiguous_count += 1
            if not case.get("expected_clarity"):
                ambiguous_without_clarity += 1
        deliverable = case.get("expected_deliverable")
        if deliverable is None:
            missing_deliverable += 1
        else:
            deliverable = str(deliverable)
            if deliverable not in VALID_DELIVERABLES:
                errors.append(f"{identifier}: unknown expected_deliverable {deliverable!r}")
            deliverables.add(deliverable)

        if classifier is not None:
            executed += 1
            try:
                actual = classifier(case)
                ok, reasons = _compare(
                    _expected_fields(case), actual, safe_aliases, ambiguous_labels
                )
                if ok:
                    passed += 1
                else:
                    failed += 1
                    errors.append(f"{identifier}: classifier mismatch ({', '.join(reasons)})")
            except Exception as exc:  # noqa: BLE001 - report local backend failures
                uncertain += 1
                errors.append(f"{identifier}: classifier error: {exc}")

    total = len(cases)
    negative_ratio = negative_count / total if total else 0.0
    if total < 150:
        warnings.append(f"golden suite has {total} cases; target is at least 150")
    if negative_ratio < 0.40:
        errors.append(f"negative/near-miss ratio {negative_ratio:.1%} is below 40%")
    if missing_deliverable:
        warnings.append(
            f"legacy fixture migration pending: {missing_deliverable} case(s) predate expected_deliverable"
        )
    if ambiguous_without_clarity:
        warnings.append(
            f"{ambiguous_without_clarity} case(s) use size=ambiguous without expected_clarity=blocked"
        )
    if not any(domain in domains for domain in ("unknown-unclassified", "universal-task")):
        warnings.append("no explicit unknown/unclassified domain case found")
    if safe_alias_fixture_domains:
        warnings.append(
            f"golden fixture domain aliases available for comparison: "
            f"{len(safe_alias_fixture_domains)} legacy label(s); aliases are not routing replacements"
        )
    if ambiguous_fixture_domains:
        preview = ", ".join(sorted(ambiguous_fixture_domains))
        warnings.append(
            "golden fixture domain comparison unscored for ambiguous labels "
            f"({preview}); review each case before migration"
        )
    remaining = sorted(noncanonical_fixture_domains - safe_alias_fixture_domains - ambiguous_fixture_domains)
    if remaining:
        preview = ", ".join(remaining[:8])
        suffix = "..." if len(remaining) > 8 else ""
        warnings.append(
            "golden fixture domain taxonomy drift: expected_domains contains unmapped labels "
            f"outside capability-index IDs ({preview}{suffix})"
        )

    return {
        "provenance": {
            "mode": "injected_local_classifier" if classifier else "provider_free_fixture_audit",
            "is_model_benchmark": False,
            "external_calls": 0,
            "limitations": [
                "This does not measure model answer quality or real-host tool execution.",
                "A local classifier, when supplied, is test code and is not a provider benchmark.",
            ],
        },
        "metrics": {
            "total_cases": total,
            "unique_ids": len(ids),
            "categories": dict(sorted(categories.items())),
            "negative_or_near_miss_cases": negative_count,
            "negative_or_near_miss_ratio": round(negative_ratio, 4),
            "unknown_cases": unknown_count,
            "forbidden_route_cases": forbidden_count,
            "multilingual_cases": multilingual_count,
            "legacy_ambiguous_size_cases": legacy_ambiguous_count,
            "ambiguous_without_clarity": ambiguous_without_clarity,
            "domains_covered": len(domains),
            "noncanonical_fixture_domains": len(noncanonical_fixture_domains),
            "safe_alias_fixture_domains": len(safe_alias_fixture_domains),
            "ambiguous_fixture_domains": len(ambiguous_fixture_domains),
            "domain_comparison_unscored_cases": domain_comparison_unscored_cases,
            "deliverables_covered": len(deliverables),
            "missing_expected_deliverable": missing_deliverable,
            "executed_cases": executed,
            "classifier_passed": passed,
            "classifier_failed": failed,
            "classifier_uncertain": uncertain,
            "scored": classifier is not None,
        },
        "errors": errors,
        "warnings": warnings,
        "status": (
            "fail"
            if errors
            else "pass"
            if classifier is not None
            else "fixture_audit_pass"
        ),
    }


def render_markdown(result: dict[str, Any]) -> str:
    metrics = result["metrics"]
    lines = [
        "# Provider-Free Prompt Routing Benchmark",
        "",
        "**This is a fixture/contract benchmark, not a model benchmark.**",
        f"Execution status: `{result['status']}`; no classifier means `scored: false`.",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key in (
        "total_cases", "unique_ids", "negative_or_near_miss_cases",
        "negative_or_near_miss_ratio", "unknown_cases", "domains_covered",
        "noncanonical_fixture_domains", "safe_alias_fixture_domains", "ambiguous_fixture_domains",
        "domain_comparison_unscored_cases", "deliverables_covered", "missing_expected_deliverable", "executed_cases",
        "classifier_passed", "classifier_failed", "classifier_uncertain", "scored",
    ):
        lines.append(f"| {key} | {metrics[key]} |")
    lines.extend(["", "## Categories", ""])
    for category, count in metrics["categories"].items():
        lines.append(f"- `{category}`: {count}")
    lines.extend(["", "## Errors", ""])
    lines.extend(f"- {item}" for item in result["errors"] or ["- None"])
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result["warnings"] or ["- None"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "evals" / "golden-cases.yaml")
    parser.add_argument("--classifier", help="local path.py:function classifier; no provider calls")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--strict", action="store_true", help="fail on contract/threshold errors")
    parser.add_argument("--require-classifier", action="store_true", help="fail unless a local classifier is supplied")
    args = parser.parse_args(argv)

    classifier = None
    if args.classifier:
        try:
            classifier = _load_local_classifier(args.classifier)
        except ValueError as exc:
            print(f"benchmark-prompt-routing: {exc}", file=sys.stderr)
            return 2
    cases = list(load_cases(args.cases))
    result = benchmark(cases, classifier)
    if args.require_classifier and classifier is None:
        result["errors"].append("--require-classifier was supplied but no classifier was loaded")
        result["status"] = "fail"
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_markdown(result), end="")
    return 1 if args.strict and result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())

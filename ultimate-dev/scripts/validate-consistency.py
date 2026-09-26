#!/usr/bin/env python3
"""Validate Ultimate-Dev manifest, version, agent, and skill consistency.

This is a repository quality gate, not a runtime dependency. It uses PyYAML
when available because the existing manifest generator and CI validation use
that optional maintenance dependency.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment dependent
    raise SystemExit("validate-consistency: PyYAML is required for repository validation") from exc

ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ROOT.parent
VERSION_FILE = REPO_ROOT / "VERSION"
MANIFEST_FILE = ROOT / "skill-manifest.yaml"
INSTALL_TARGETS_FILE = ROOT / "config" / "install-targets.yaml"
AGENT_CATALOG_FILE = ROOT / "config" / "agent-catalog.yaml"
AGENT_REGISTRY_FILE = ROOT / "config" / "agent_registry.yaml"
CAPABILITY_INDEX_FILE = ROOT / "config" / "capability-index.yaml"
TASK_ENVELOPE_FILE = ROOT / "contracts" / "task-envelope.yaml"
WORKFLOW_FILE = ROOT / "config" / "workflow.yaml"
SKILL_FILE = ROOT / "SKILL.md"
ENTRYPOINT_FILES = (
    ROOT / "AGENT.md",
    ROOT / "AGENTS.md",
    ROOT / "CLAUDE.md",
)
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
AGENT_REQUIRED = ("name", "domain", "description", "triggers", "anti_triggers", "tools", "model", "last_verified")
SKILL_REQUIRED = ("name", "description", "triggers", "provides")
ADAPTER_REQUIRED = ("tool", "support", "last_verified")
CAPABILITY_REQUIRED = ("id", "status", "signals", "skills", "agents", "fallback", "risk")
DELIVERABLE_REQUIRED = ("id", "signals", "primary_skills", "output_contract")
CAPABILITY_STATUSES = {"strong", "partial", "missing"}
REQUIRED_CONTRACTS = (
    "contracts/README.md",
    "contracts/four-channels.md",
    "contracts/task-envelope.yaml",
    "contracts/task-state-machine.yaml",
    "contracts/middleware-hooks.yaml",
    "contracts/capability-manifest.yaml",
    "contracts/subagent-contract.yaml",
    "contracts/handoff-contract.yaml",
    "contracts/memory-provenance.yaml",
    "contracts/hitl-interrupt.yaml",
    "contracts/host-instruction-provisioning.yaml",
)
DEVELOPMENT_REQUIREMENTS_FILE = ROOT / "requirements-dev.txt"
REQUIRED_GUIDES = ("INSTALLATION.md",)
MAX_METADATA_AGE_DAYS = 180
VERSIONED_CONFIGS = (
    ROOT / "config" / "agent-catalog.yaml",
    ROOT / "config" / "agent_registry.yaml",
    ROOT / "config" / "capability-index.yaml",
    ROOT / "config" / "context_budgets.yaml",
    ROOT / "config" / "models.yaml",
    ROOT / "config" / "permissions.yaml",
    ROOT / "config" / "security.yaml",
    ROOT / "config" / "workflow.yaml",
)


def frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
    if not match:
        raise ValueError("missing YAML frontmatter")
    value = yaml.safe_load(match.group(1))
    if not isinstance(value, dict):
        raise ValueError("frontmatter is not a mapping")
    return value


def canonical_version() -> str:
    value = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(value):
        raise ValueError(f"invalid canonical VERSION: {value!r}")
    return value


def validate_freshness(metadata: dict[str, Any], label: str, errors: list[str]) -> None:
    value = metadata.get("last_verified")
    try:
        verified = date.fromisoformat(str(value))
    except (TypeError, ValueError):
        errors.append(f"{label}: last_verified must be an ISO date")
        return
    today = date.today()
    if verified > today:
        errors.append(f"{label}: last_verified is in the future")
    elif (today - verified).days > MAX_METADATA_AGE_DAYS:
        errors.append(f"{label}: metadata is older than {MAX_METADATA_AGE_DAYS} days")


def actual_agents() -> list[str]:
    return sorted(
        str(path.relative_to(ROOT))
        for path in (ROOT / "agents").rglob("*.md")
        if "_shared" not in path.parts and not path.name.startswith(".")
    )


def actual_skills() -> list[str]:
    return sorted(
        str(path.relative_to(ROOT))
        for path in (ROOT / "skills").glob("*/SKILL.md")
        if path.parent.name != "_learned"
    )


def actual_modules() -> list[str]:
    return sorted(
        str(path.relative_to(ROOT))
        for path in (ROOT / "modules").rglob("*.md")
        if not path.name.startswith(".")
    )


def actual_adapters() -> list[str]:
    return sorted(
        str(path.relative_to(ROOT))
        for path in (ROOT / "adapters").glob("*.md")
        if not path.name.startswith(".")
    )


def actual_contracts() -> list[str]:
    return sorted(
        str(path.relative_to(ROOT))
        for path in (ROOT / "contracts").rglob("*")
        if path.is_file() and not path.name.startswith(".")
    )


def collect_workflow_agent_references(value: Any) -> set[str]:
    references: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "agent" and isinstance(child, str):
                references.add(child)
            else:
                references.update(collect_workflow_agent_references(child))
    elif isinstance(value, list):
        for child in value:
            references.update(collect_workflow_agent_references(child))
    return references


def check() -> list[str]:
    errors: list[str] = []
    try:
        version = canonical_version()
    except (OSError, ValueError) as exc:
        return [str(exc)]

    try:
        manifest = yaml.safe_load(MANIFEST_FILE.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        return [f"skill-manifest.yaml: {exc}"]
    if not isinstance(manifest, dict):
        return ["skill-manifest.yaml: root is not a mapping"]

    try:
        catalog = yaml.safe_load(AGENT_CATALOG_FILE.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        catalog = {}
        errors.append(f"config/agent-catalog.yaml: {exc}")
    if not isinstance(catalog, dict):
        errors.append("config/agent-catalog.yaml: root is not a mapping")
        catalog = {}
    if catalog.get("version") != version:
        errors.append(f"agent catalog version {catalog.get('version')!r} != {version}")
    if catalog.get("source") != "skill-manifest.yaml":
        errors.append("agent catalog source must be skill-manifest.yaml")

    try:
        catalog_check = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate-agent-catalog.py"), "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if catalog_check.returncode != 0:
            detail = (catalog_check.stdout + catalog_check.stderr).strip()
            errors.append(f"agent catalog is stale: {detail}")
    except OSError as exc:
        errors.append(f"agent catalog generator: {exc}")

    try:
        registry = yaml.safe_load(AGENT_REGISTRY_FILE.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        registry = {}
        errors.append(f"config/agent_registry.yaml: {exc}")
    if not isinstance(registry, dict):
        errors.append("config/agent_registry.yaml: root is not a mapping")
        registry = {}
    if registry.get("registry_kind") != "abstract-runtime-roles":
        errors.append("config/agent_registry.yaml: registry_kind must be abstract-runtime-roles")
    if registry.get("concrete_agent_source") != "../skill-manifest.yaml":
        errors.append("config/agent_registry.yaml: concrete_agent_source must be ../skill-manifest.yaml")
    workflow_roles = registry.get("workflow_roles")
    if not isinstance(workflow_roles, dict) or not workflow_roles:
        errors.append("config/agent_registry.yaml: workflow_roles must be a non-empty mapping")
        workflow_roles = {}

    try:
        capability_index = yaml.safe_load(CAPABILITY_INDEX_FILE.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        capability_index = {}
        errors.append(f"config/capability-index.yaml: {exc}")
    if not isinstance(capability_index, dict):
        errors.append("config/capability-index.yaml: root is not a mapping")
        capability_index = {}
    task_envelope: dict[str, Any] = {}
    try:
        task_envelope = yaml.safe_load(TASK_ENVELOPE_FILE.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        errors.append(f"contracts/task-envelope.yaml: {exc}")
    if not isinstance(task_envelope, dict):
        errors.append("contracts/task-envelope.yaml: root is not a mapping")
        task_envelope = {}
    if capability_index.get("version") != version:
        errors.append(f"capability index version {capability_index.get('version')!r} != {version}")
    routing_policy = capability_index.get("routing_policy")
    if not isinstance(routing_policy, dict):
        errors.append("capability index routing_policy must be a mapping")
    else:
        for key in (
            "common_first",
            "skills_before_agents",
            "max_primary_agents_per_domain",
            "broad_triggers_are_hints",
            "require_intent_and_context_for_ambiguous_routes",
            "deliverable_first",
            "unknown_fallback_skill",
            "capability_gap_report",
            "prompt_only_supported",
            "do_not_load_full_registry_for_every_task",
        ):
            if key not in routing_policy:
                errors.append(f"capability index routing_policy is missing {key}")
        if routing_policy.get("max_primary_agents_per_domain") != 1:
            errors.append("routing policy must allow one primary agent per domain")
        for key in (
            "common_first",
            "skills_before_agents",
            "broad_triggers_are_hints",
            "require_intent_and_context_for_ambiguous_routes",
            "deliverable_first",
            "prompt_only_supported",
            "do_not_load_full_registry_for_every_task",
        ):
            if key in routing_policy and routing_policy[key] is not True:
                errors.append(f"routing policy {key} must be true")
        if routing_policy.get("capability_gap_report") != "required":
            errors.append("routing policy capability_gap_report must be required")
        if routing_policy.get("unknown_fallback_skill") != "universal-task":
            errors.append("routing policy unknown_fallback_skill must be universal-task")
    capability_domains = capability_index.get("domains")
    if not isinstance(capability_domains, list) or not capability_domains:
        errors.append("config/capability-index.yaml: domains must be a non-empty list")
        capability_domains = []

    try:
        workflow = yaml.safe_load(WORKFLOW_FILE.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        workflow = {}
        errors.append(f"config/workflow.yaml: {exc}")
    workflow_references = collect_workflow_agent_references(workflow)

    try:
        install_targets = yaml.safe_load(INSTALL_TARGETS_FILE.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        install_targets = {}
        errors.append(f"config/install-targets.yaml: {exc}")
    profiles = install_targets.get("profiles") if isinstance(install_targets, dict) else None
    if not isinstance(profiles, dict):
        errors.append(f"config/install-targets.yaml: profiles must be a mapping")
        profiles = {}
    for name, profile in profiles.items():
        if not isinstance(name, str) or not name or not isinstance(profile, dict):
            errors.append(f"config/install-targets.yaml: invalid profile entry")
            continue
        relative_path = profile.get("relative_path")
        if not isinstance(relative_path, str) or not relative_path or relative_path.startswith("/") or ".." in Path(relative_path).parts:
            errors.append(f"install target {name}: relative_path must be a safe relative path")
        if profile.get("support") not in {"generic", "native", "generic-fallback"}:
            errors.append(f"install target {name}: support is invalid")

    if manifest.get("version") != version:
        errors.append(f"manifest version {manifest.get('version')!r} != {version}")
    try:
        skill_meta = frontmatter(SKILL_FILE)
    except (OSError, ValueError) as exc:
        errors.append(f"SKILL.md: {exc}")
        skill_meta = {}
    if skill_meta.get("version") != version:
        errors.append(f"SKILL.md version {skill_meta.get('version')!r} != {version}")

    for path in ENTRYPOINT_FILES:
        try:
            metadata = frontmatter(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        if metadata.get("version") != version:
            errors.append(f"{path.relative_to(ROOT)} version {metadata.get('version')!r} != {version}")

    for path in VERSIONED_CONFIGS:
        try:
            metadata = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        if not isinstance(metadata, dict):
            errors.append(f"{path.relative_to(ROOT)}: root is not a mapping")
            continue
        if metadata.get("version") != version:
            errors.append(f"{path.relative_to(ROOT)} version {metadata.get('version')!r} != {version}")

    for relative in REQUIRED_CONTRACTS:
        if not (ROOT / relative).is_file():
            errors.append(f"required contract is missing: {relative}")
    for relative in REQUIRED_GUIDES:
        if not (ROOT / relative).is_file():
            errors.append(f"required guide is missing: {relative}")
    if not DEVELOPMENT_REQUIREMENTS_FILE.is_file():
        errors.append("requirements-dev.txt is missing")
    development = manifest.get("development")
    if not isinstance(development, dict):
        errors.append("skill manifest development metadata is missing")
    else:
        if development.get("requirements") != "requirements-dev.txt":
            errors.append("manifest development.requirements must be requirements-dev.txt")
        if development.get("prompt_only_dependencies") != []:
            errors.append("manifest prompt_only_dependencies must be empty")

    expected = {
        "agents": actual_agents(),
        "skills": actual_skills(),
        "modules": actual_modules(),
        "adapters": actual_adapters(),
        "contracts": actual_contracts(),
    }
    for key, paths in expected.items():
        listed = manifest.get(key)
        if listed != paths:
            errors.append(f"manifest {key} list is stale or unordered")

    stats = manifest.get("stats")
    if not isinstance(stats, dict):
        errors.append("manifest stats is missing or not a mapping")
    else:
        expected_stats = {
            "total_agents": len(expected["agents"]),
            "total_skills": len(expected["skills"]),
            "total_modules": len(expected["modules"]),
        }
        for key, value in expected_stats.items():
            if stats.get(key) != value:
                errors.append(f"manifest stats.{key}={stats.get(key)!r} != {value}")
        try:
            generated = date.fromisoformat(str(stats.get("last_generated")))
            if generated > date.today():
                errors.append("manifest stats.last_generated is in the future")
        except ValueError:
            errors.append("manifest stats.last_generated is not an ISO date")

    names: dict[str, str] = {}
    for relative in expected["agents"]:
        path = ROOT / relative
        try:
            metadata = frontmatter(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{relative}: {exc}")
            continue
        for key in AGENT_REQUIRED:
            if key not in metadata:
                errors.append(f"{relative}: missing agent field {key}")
        name = metadata.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{relative}: agent name must be non-empty")
        elif name in names:
            errors.append(f"duplicate agent name {name!r}: {names[name]} and {relative}")
        else:
            names[name] = relative
        for key in ("triggers", "anti_triggers", "tools"):
            value = metadata.get(key)
            if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value):
                errors.append(f"{relative}: {key} must be a non-empty string list")
        if not isinstance(metadata.get("model"), str) or not metadata["model"].strip():
            errors.append(f"{relative}: model must be a non-empty string")
        validate_freshness(metadata, relative, errors)

    catalog_entries = catalog.get("agents")
    if not isinstance(catalog_entries, list):
        errors.append("agent catalog agents must be a list")
        catalog_entries = []
    catalog_ids: set[str] = set()
    catalog_paths: list[str] = []
    for entry in catalog_entries:
        if not isinstance(entry, dict):
            errors.append("agent catalog contains a non-mapping entry")
            continue
        identifier = entry.get("id")
        path = entry.get("path")
        if not isinstance(identifier, str) or not identifier:
            errors.append("agent catalog contains an invalid id")
        else:
            catalog_ids.add(identifier)
        if not isinstance(path, str) or not path:
            errors.append(f"agent catalog entry {identifier!r} has no path")
        else:
            catalog_paths.append(path)
    if sorted(catalog_paths) != expected["agents"]:
        errors.append("agent catalog paths are stale or unordered")
    if catalog.get("agent_count") != len(expected["agents"]):
        errors.append("agent catalog agent_count is stale")
    missing_catalog_ids = sorted(set(names) - catalog_ids)
    unknown_catalog_ids = sorted(catalog_ids - set(names))
    if missing_catalog_ids:
        errors.append(f"agent catalog missing concrete agents: {', '.join(missing_catalog_ids)}")
    if unknown_catalog_ids:
        errors.append(f"agent catalog has unknown concrete agents: {', '.join(unknown_catalog_ids)}")
    unknown_workflow_refs = sorted(workflow_references - set(names) - set(workflow_roles) - {"auto"})
    if unknown_workflow_refs:
        errors.append(f"workflow references unknown agent/role: {', '.join(unknown_workflow_refs)}")

    for relative in expected["skills"]:
        path = ROOT / relative
        try:
            metadata = frontmatter(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{relative}: {exc}")
            continue
        for key in SKILL_REQUIRED:
            if key not in metadata:
                errors.append(f"{relative}: missing skill field {key}")
        if metadata.get("name") != path.parent.name:
            errors.append(
                f"{relative}: skill name {metadata.get('name')!r} must match directory {path.parent.name!r}"
            )
        if not isinstance(metadata.get("triggers"), list) or not metadata["triggers"]:
            errors.append(f"{relative}: triggers must be a non-empty list")

    skill_names = {Path(relative).parent.name for relative in expected["skills"]}
    for domain in capability_domains:
        if isinstance(domain, dict) and domain.get("fallback_skill") is not None:
            if domain["fallback_skill"] not in skill_names:
                errors.append(
                    f"capability index domain {domain.get('id', '<unknown>')}: unknown fallback_skill {domain['fallback_skill']}"
                )
    capability_ids: set[str] = set()
    for domain in capability_domains:
        if not isinstance(domain, dict):
            errors.append("capability index contains a non-mapping domain")
            continue
        for key in CAPABILITY_REQUIRED:
            if key not in domain:
                errors.append(f"capability index domain is missing {key}")
        domain_id = domain.get("id")
        if not isinstance(domain_id, str) or not domain_id:
            errors.append("capability index contains an invalid domain id")
            continue
        if domain_id in capability_ids:
            errors.append(f"duplicate capability index domain: {domain_id}")
        capability_ids.add(domain_id)
        if domain.get("status") not in CAPABILITY_STATUSES:
            errors.append(f"capability index domain {domain_id}: invalid status")
        if not isinstance(domain.get("signals"), list) or not domain["signals"]:
            errors.append(f"capability index domain {domain_id}: signals must be a non-empty list")
        if not isinstance(domain.get("risk"), str) or not domain["risk"]:
            errors.append(f"capability index domain {domain_id}: risk must be a non-empty string")
        for field, valid in (("skills", skill_names), ("agents", set(names))):
            values = domain.get(field)
            if not isinstance(values, list):
                errors.append(f"capability index domain {domain_id}: {field} must be a list")
                continue
            unknown = sorted(set(values) - valid)
            if unknown:
                errors.append(f"capability index domain {domain_id}: unknown {field}: {', '.join(unknown)}")
        fallback = domain.get("fallback")
        if not isinstance(fallback, str) or fallback not in set(names):
            errors.append(f"capability index domain {domain_id}: fallback is not a concrete agent")
        fallback_skill = domain.get("fallback_skill")
        if fallback_skill is not None and (not isinstance(fallback_skill, str) or not fallback_skill):
            errors.append(f"capability index domain {domain_id}: fallback_skill must be a non-empty string")

    unknown_domain = next(
        (domain for domain in capability_domains if isinstance(domain, dict) and domain.get("id") == "unknown-unclassified"),
        None,
    )
    if unknown_domain is None or unknown_domain.get("fallback_skill") != "universal-task":
        errors.append("unknown-unclassified must use universal-task as fallback_skill")

    deliverable_types = capability_index.get("deliverable_types")
    if not isinstance(deliverable_types, list) or not deliverable_types:
        errors.append("config/capability-index.yaml: deliverable_types must be a non-empty list")
        deliverable_types = []
    deliverable_ids: set[str] = set()
    for deliverable in deliverable_types:
        if not isinstance(deliverable, dict):
            errors.append("capability index deliverable_types contains a non-mapping entry")
            continue
        for key in DELIVERABLE_REQUIRED:
            if key not in deliverable:
                errors.append(f"capability deliverable {deliverable.get('id', '<unknown>')}: missing {key}")
        deliverable_id = deliverable.get("id")
        if not isinstance(deliverable_id, str) or not deliverable_id:
            errors.append("capability index contains an invalid deliverable id")
        elif deliverable_id in deliverable_ids:
            errors.append(f"duplicate capability deliverable: {deliverable_id}")
        else:
            deliverable_ids.add(deliverable_id)
        if not isinstance(deliverable.get("signals"), list) or not deliverable["signals"]:
            errors.append(f"capability deliverable {deliverable_id}: signals must be a non-empty list")
        primary_skills = deliverable.get("primary_skills")
        if not isinstance(primary_skills, list) or not primary_skills:
            errors.append(f"capability deliverable {deliverable_id}: primary_skills must be a non-empty list")
        else:
            unknown_skills = sorted(set(primary_skills) - skill_names)
            if unknown_skills:
                errors.append(
                    f"capability deliverable {deliverable_id}: unknown skills: {', '.join(unknown_skills)}"
                )
    if "unknown" not in deliverable_ids:
        errors.append("capability index deliverable_types must include unknown")
    if "unknown-unclassified" not in capability_ids:
        errors.append("capability index domains must include unknown-unclassified")

    contract_deliverables = task_envelope.get("deliverable_types")
    if not isinstance(contract_deliverables, dict) or not contract_deliverables:
        errors.append("contracts/task-envelope.yaml: deliverable_types must be a non-empty mapping")
        contract_deliverables = {}
    capability_by_id = {
        item.get("id"): item for item in deliverable_types if isinstance(item, dict) and item.get("id")
    }
    for deliverable_id, contract_value in contract_deliverables.items():
        index_value = capability_by_id.get(deliverable_id)
        if index_value is None:
            errors.append(f"deliverable {deliverable_id} is missing from capability index")
            continue
        if not isinstance(contract_value, dict):
            errors.append(f"contract deliverable {deliverable_id} must be a mapping")
            continue
        if contract_value.get("signals") != index_value.get("signals"):
            errors.append(f"deliverable {deliverable_id}: signals differ between contract and capability index")
        if not index_value.get("output_contract"):
            errors.append(f"deliverable {deliverable_id}: capability output_contract is empty")
    for deliverable_id in capability_by_id:
        if deliverable_id not in contract_deliverables:
            errors.append(f"deliverable {deliverable_id} is missing from task envelope contract")

    adapter_names: set[str] = set()
    for relative in expected["adapters"]:
        path = ROOT / relative
        try:
            metadata = frontmatter(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{relative}: {exc}")
            continue
        for key in ADAPTER_REQUIRED:
            if key not in metadata:
                errors.append(f"{relative}: missing adapter field {key}")
        tool = metadata.get("tool")
        if not isinstance(tool, str) or not tool.strip():
            errors.append(f"{relative}: tool must be a non-empty string")
        elif tool in adapter_names:
            errors.append(f"duplicate adapter tool profile: {tool}")
        else:
            adapter_names.add(tool)
        validate_freshness(metadata, relative, errors)

    declared_tools = set(manifest.get("compatible_tools", []))
    normalized_adapter_names = {"generic" if name == "generic-cli" else name for name in adapter_names}
    missing_profiles = sorted(declared_tools - normalized_adapter_names)
    if missing_profiles:
        errors.append(f"manifest compatible_tools lacks adapter profiles: {', '.join(missing_profiles)}")
    unknown_profiles = sorted(set(profiles) - normalized_adapter_names)
    if unknown_profiles:
        errors.append(f"install target profiles lack adapter docs: {', '.join(unknown_profiles)}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable results")
    args = parser.parse_args(argv)
    errors = check()
    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors}, sort_keys=True))
    elif errors:
        for error in errors:
            print(f"consistency: ERROR: {error}", file=sys.stderr)
    else:
        print("consistency: manifest, catalog, workflow roles, versions, agents, skills, and adapters are consistent")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

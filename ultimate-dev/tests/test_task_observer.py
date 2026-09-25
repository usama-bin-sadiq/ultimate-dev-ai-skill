#!/usr/bin/env python3
"""Focused contract tests for the Task Observer skill and agent."""
from pathlib import Path
import re

import yaml


BASE = Path(__file__).resolve().parents[1]
SKILL = BASE / "skills" / "task-observer" / "SKILL.md"
AGENT = BASE / "agents" / "meta" / "task-observer.md"
MANIFEST = BASE / "skill-manifest.yaml"
README = BASE / "README.md"
AGENTS = BASE / "AGENTS.md"
EVALS = BASE / "evals" / "golden-cases.yaml"


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert match, f"missing frontmatter: {path}"
    value = yaml.safe_load(match.group(1))
    assert isinstance(value, dict), f"frontmatter is not a mapping: {path}"
    return value


def test_task_observer_artifacts_exist_and_have_expected_frontmatter():
    assert SKILL.is_file()
    assert AGENT.is_file()

    skill = frontmatter(SKILL)
    assert skill["name"] == "task-observer"
    assert "observation" in skill["description"].lower()
    assert "task observer" in [str(item).lower() for item in skill["triggers"]]
    assert skill["provides"] == "task_observation_ability"

    agent = frontmatter(AGENT)
    for field in ("name", "domain", "description", "triggers", "anti_triggers", "tools", "model"):
        assert field in agent, f"agent missing {field}"
    assert agent["name"] == "task-observer"
    assert agent["domain"] == "meta"
    assert agent["model"] == "inherit"


def test_agent_keeps_methodology_in_the_skill():
    text = AGENT.read_text(encoding="utf-8")
    assert "skills/task-observer/SKILL.md" in text
    for heading in ("## Taxonomy", "## Observation Record", "## Numbering Rules", "## Confidentiality Rules"):
        assert heading not in text, f"agent duplicates skill section: {heading}"


def test_skill_preserves_local_observation_contract():
    text = SKILL.read_text(encoding="utf-8")
    for required in (
        "### Observation N:",
        "**Status:** OPEN",
        "ACTIONED (YYYY-MM-DD)",
        "DECLINED (YYYY-MM-DD)",
        "last-review-date.txt",
        "skill-observations/",
        "log and defer",
    ):
        assert required in text, f"skill missing contract text: {required}"


def test_manifest_registers_each_artifact_exactly_once():
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["agents"].count("agents/meta/task-observer.md") == 1
    assert manifest["skills"].count("skills/task-observer/SKILL.md") == 1
    assert manifest["stats"]["total_agents"] == len(manifest["agents"])
    assert manifest["stats"]["total_skills"] == len(manifest["skills"])


def test_skill_directory_contains_core_and_progressive_references():
    files = sorted(path.name for path in SKILL.parent.iterdir() if path.is_file())
    assert files == ["SKILL.md"]
    references = sorted(path.name for path in (SKILL.parent / "references").glob("*.md"))
    assert references == ["confidentiality-and-review.md", "observation-protocol.md"]
    core = SKILL.read_text(encoding="utf-8")
    assert len(core.split()) < 500
    for reference in references:
        assert reference in core
        assert (SKILL.parent / "references" / reference).is_file()


def test_task_observer_references_are_safe_and_operational():
    references = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (SKILL.parent / "references").glob("*.md")
    )
    combined = SKILL.read_text(encoding="utf-8") + "\n" + references
    for required in ("Append protocol", "Confidentiality", "review", "log.md"):
        assert required.lower() in combined.lower()
    assert not re.search(
        r"\b(playwright|puppeteer|selenium|docker|podman|openai|anthropic|ollama|npm|pip|package manager|mcp server)\b",
        combined.lower(),
    )


def test_documentation_and_routing_surfaces_include_task_observer():
    assert "task-observer" in README.read_text(encoding="utf-8")
    assert "task-observer" in AGENTS.read_text(encoding="utf-8")
    evaluations = EVALS.read_text(encoding="utf-8")
    assert "task-observer" in evaluations
    assert "task-observer-001" in evaluations


def test_artifacts_do_not_require_external_runtime_providers():
    text = (SKILL.read_text(encoding="utf-8") + "\n" + AGENT.read_text(encoding="utf-8")).lower()
    forbidden = r"\b(playwright|puppeteer|selenium|docker|podman|openai|anthropic|ollama|npm|pip|package manager|mcp server)\b"
    assert not re.search(forbidden, text), "Task Observer artifacts must remain host-native"

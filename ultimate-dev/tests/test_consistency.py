import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent


def test_supported_installer_profiles_have_adapters_and_menu_entries():
    expected = {
        "generic": "generic-cli",
        "opencode": "opencode",
        "claude-code": "claude-code",
        "codex": "codex",
        "windsurf": "windsurf",
        "cline": "cline",
        "copilot": "copilot",
        "aider": "aider",
    }
    posix = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
    powershell = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")
    for tool, adapter in expected.items():
        assert (ROOT / "adapters" / f"{adapter}.md").is_file()
        assert tool in posix
        assert tool in powershell
    assert "Tool-specific" in posix
    assert "Tool-specific" in powershell
    assert "Global" in posix and "Project" in posix
    assert "Global" in powershell and "Project" in powershell


def test_prompt_suite_audit_has_no_structural_errors_or_broad_trigger_collisions():
    import json

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "audit-prompt-suite.py"), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["trigger_collisions"] == []


def test_prompt_suite_audit_has_no_structural_errors():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "audit-prompt-suite.py"), "--strict"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_skill_names_follow_agent_skills_spec():
    import yaml

    for path in (ROOT / "skills").glob("*/SKILL.md"):
        text = path.read_text(encoding="utf-8")
        metadata = yaml.safe_load(text.split("---", 2)[1])
        assert metadata["name"] == path.parent.name


def test_agent_catalog_is_generated_and_current():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate-agent-catalog.py"), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_cross_functional_skills_stay_progressive_disclosure():
    names = (
        "discovery-requirements",
        "planning-execution",
        "internal-communications",
        "business-analysis",
        "strategy-operating-model",
        "data-analysis-bi",
        "accounting-finance",
        "legal-privacy",
        "people-operations",
        "procurement-vendors",
        "office-artifacts",
        "audit-controls",
        "prompt-evaluation",
        "universal-task",
    )
    for name in names:
        path = ROOT / "skills" / name / "SKILL.md"
        assert path.is_file()
        assert len(path.read_text(encoding="utf-8").split()) < 700


def test_high_use_skills_have_standard_operating_contracts():
    names = (
        "coding", "research", "testing", "review", "architecture", "security",
        "debugging", "devops", "documentation", "data",
    )
    for name in names:
        text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        assert "## Operating Contract" in text, f"{name} lacks a standard operating contract"
        for field in ("Inputs", "Output", "Verification", "When not to use"):
            assert field in text, f"{name} lacks {field} contract"


def test_behavioral_calibration_is_single_source():
    calibration = (ROOT / "router" / "behavioral-calibration.md").read_text(encoding="utf-8")
    assert "Decision order" in calibration
    assert "Deliverable calibration" in calibration
    assert "Risk calibration" in calibration
    for entrypoint in (ROOT / "SKILL.md", ROOT / "AGENTS.md"):
        text = entrypoint.read_text(encoding="utf-8")
        assert "routing/behavioral-calibration.md" in text
        assert "Do not emit legacy labels" not in text


def test_capability_index_has_bounded_entrypoints():
    import yaml

    index = yaml.safe_load((ROOT / "config" / "capability-index.yaml").read_text(encoding="utf-8"))
    assert index["version"] == "3.0.2"
    assert len(index["domains"]) >= 12
    assert index["routing_policy"]["common_first"] is True
    assert index["routing_policy"]["skills_before_agents"] is True
    assert index["routing_policy"]["deliverable_first"] is True
    assert index["routing_policy"]["unknown_fallback_skill"] == "universal-task"
    assert index["routing_policy"]["capability_gap_report"] == "required"
    assert index["routing_policy"]["prompt_only_supported"] is True
    assert index["routing_policy"]["max_primary_agents_per_domain"] == 1
    assert any(domain["id"] == "unknown-unclassified" for domain in index["domains"])
    assert any(item["id"] == "unknown" for item in index["deliverable_types"])
    for domain in index["domains"]:
        assert domain["status"] in {"strong", "partial", "missing"}
        assert domain["signals"]
        assert isinstance(domain["skills"], list)
        assert isinstance(domain["agents"], list)
        assert domain["fallback"]
    for deliverable in index["deliverable_types"]:
        assert deliverable["signals"]
        assert deliverable["primary_skills"]
        assert deliverable["output_contract"]


def test_portable_contracts_and_provider_free_benchmark_are_registered():
    import yaml

    manifest = yaml.safe_load((ROOT / "skill-manifest.yaml").read_text(encoding="utf-8"))
    assert manifest["contracts"] == [
        "contracts/README.md",
        "contracts/four-channels.md",
        "contracts/task-envelope.yaml",
    ]
    assert "scripts/benchmark-prompt-routing.py" in manifest["scripts"]
    assert "scripts/generate-project-context.py" in manifest["scripts"]
    assert "scripts/measure-install.py" in manifest["scripts"]
    assert "scripts/validate-company-context.py" in manifest["scripts"]
    assert "scripts/benchmark-project-context.py" in manifest["scripts"]
    assert manifest["development"]["requirements"] == "requirements-dev.txt"
    assert manifest["development"]["prompt_only_dependencies"] == []
    assert (ROOT / "requirements-dev.txt").is_file()
    requirements = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    for package in ("PyYAML==6.0.2", "pytest==8.3.5", "requests==2.32.3"):
        assert package in requirements
    for relative in manifest["contracts"]:
        assert (ROOT / relative).is_file()
    envelope = yaml.safe_load((ROOT / "contracts" / "task-envelope.yaml").read_text(encoding="utf-8"))
    assert envelope["runtime_required"] is False
    assert set(envelope["channels"]) == {"intent", "knowledge", "action", "evidence"}
    assert envelope["result_status_values"] == ["completed", "partial", "failed", "blocked", "not_run"]
    assert envelope["size_values"] == ["atomic", "moderate", "complex"]
    assert "unknown" in envelope["deliverable_types"]
    assert envelope["jev_profiles"]["prompt_only"]["execution"] == "forbidden"


def test_universal_task_skill_declares_safe_fallback_contract():
    text = (ROOT / "skills" / "universal-task" / "SKILL.md").read_text(encoding="utf-8").lower()
    assert "contracts/task-envelope.yaml" in text
    assert "capability_gap" in text
    assert "unknown" in text
    assert "do not claim" in text
    assert "one focused question" in text


def test_prompt_only_jev_boundary_is_conditional():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
    orchestrator = (ROOT / "agents" / "orchestrator.md").read_text(encoding="utf-8").lower()
    assert "prompt-only jev profile" in skill
    assert "prompt-only jev profile" in agents
    assert "prompt-only profile" in orchestrator
    assert "before an execution transition, request" not in orchestrator
    assert "do not claim a jev packet" in orchestrator


def test_workflow_roles_are_declared_separately():
    import yaml

    registry = yaml.safe_load((ROOT / "config" / "agent_registry.yaml").read_text(encoding="utf-8"))
    assert registry["registry_kind"] == "abstract-runtime-roles"
    assert registry["concrete_agent_source"] == "../skill-manifest.yaml"
    for role in ("planner", "architect", "backend", "frontend", "tester", "reviewer", "security", "debugger", "writer"):
        assert role in registry["workflow_roles"]


def test_manifest_versions_agents_skills_and_adapters_are_consistent():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate-consistency.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_supported_tool_adapters_are_present():
    manifest = (ROOT / "skill-manifest.yaml").read_text(encoding="utf-8")
    for tool in ("opencode", "claude-code", "codex", "cursor", "windsurf", "cline", "copilot", "aider", "generic"):
        assert f"adapters/{tool if tool != 'generic' else 'generic-cli'}.md" in manifest

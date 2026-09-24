from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
README = ROOT / "README.md"


def test_readme_has_no_accidental_placeholder_tail():
    text = README.read_text(encoding="utf-8")
    assert not re.search(r"(?m)^# (?:sync fix|test)$", text)


def test_release_workflow_handles_main_pushes_without_recursive_releases():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert re.search(r"(?m)^  push:\n    branches: \[main\]$", text)
    assert "github.event_name == 'push'" in text
    assert "chore: release v" in text
    assert "chore: auto-sync manifest and docs" in text
    assert "pull-requests: read" in text
    assert "secrets.ULTIMATE_DEV_TOKEN" in text
    assert "github.api_url" in text
    assert "github.token" in text
    assert "environment: release" in text
    assert "environment: CICD" in text

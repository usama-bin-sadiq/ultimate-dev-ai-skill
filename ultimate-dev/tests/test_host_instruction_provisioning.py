#!/usr/bin/env python3
"""Tests for host-instruction provisioning."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "provision-host-instructions.py"
CONTRACT = ROOT / "contracts" / "host-instruction-provisioning.yaml"


def _load():
    spec = importlib.util.spec_from_file_location("provision", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_declares_every_target_path():
    module = _load()
    spec = module._yaml_paths()
    assert len(spec["targets"]) >= 8
    for tool, target in spec["targets"].items():
        assert target["path"], tool
        assert not target["path"].startswith("/"), f"{tool} target must be project-relative"


def test_env_signals_outrank_marker_files(tmp_path):
    """A live host must win over a project that merely carries another tool's file."""
    module = _load()
    (tmp_path / "CLAUDE.md").write_text("marker from a previous tool\n", encoding="utf-8")
    # No environment signal: file presence is all there is.
    assert module.detect_tool(tmp_path, env={}) == ["claude-code"]
    # A live host outranks the stale marker file.
    tools = module.detect_tool(tmp_path, env={"CURSOR_TRACE_ID": "1"})
    assert tools[0] == "cursor"
    tool, target = module.resolve_target(tmp_path, None, env={"CURSOR_TRACE_ID": "1"})
    assert (tool, target.name) == ("cursor", ".cursorrules")


def test_detection_falls_back_to_generic(tmp_path):
    module = _load()
    assert module.detect_tool(tmp_path, env={}) == ["generic"]
    tool, target = module.resolve_target(tmp_path, None, env={})
    assert tool == "generic"
    assert target.name == "AGENTS.md"


def test_detection_prefers_an_env_signal_over_a_generic_fallback(tmp_path):
    module = _load()
    tools = module.detect_tool(tmp_path, env={"CLAUDECODE": "1"})
    assert "claude-code" in tools
    tool, target = module.resolve_target(tmp_path, None, env={"CLAUDECODE": "1"})
    assert (tool, target.name) == ("claude-code", "CLAUDE.md")


def test_provision_creates_a_missing_file(tmp_path):
    module = _load()
    target = tmp_path / "AGENTS.md"
    assert module.apply_block(target, module.render_block()) == "created"
    assert module.check_block(target)
    assert module.BEGIN in target.read_text(encoding="utf-8")


def test_provision_appends_without_destroying_existing_content(tmp_path):
    module = _load()
    target = tmp_path / "AGENTS.md"
    original = "# My project\n\nHand-written rules the user cares about.\n"
    target.write_text(original, encoding="utf-8")
    assert module.apply_block(target, module.render_block()) == "updated"
    text = target.read_text(encoding="utf-8")
    assert "Hand-written rules the user cares about." in text
    assert module.BEGIN in text


def test_provision_is_idempotent(tmp_path):
    module = _load()
    target = tmp_path / "AGENTS.md"
    target.write_text("# Mine\n", encoding="utf-8")
    assert module.apply_block(target, module.render_block()) == "updated"
    first = target.read_text(encoding="utf-8")
    assert module.apply_block(target, module.render_block()) == "unchanged"
    assert target.read_text(encoding="utf-8") == first


def test_reprovision_replaces_only_the_marked_region(tmp_path):
    module = _load()
    target = tmp_path / "AGENTS.md"
    target.write_text("# Top\n", encoding="utf-8")
    old_block = f"{module.BEGIN}\nold block\n{module.END}"
    new_block = f"{module.BEGIN}\nnew block\n{module.END}"
    assert module.apply_block(target, old_block) == "updated"
    assert "old block" in target.read_text(encoding="utf-8")
    # A user edit outside the markers must survive re-provisioning.
    text = target.read_text(encoding="utf-8").replace("# Top", "# Top\nuser edit above the block")
    target.write_text(text, encoding="utf-8")
    assert module.apply_block(target, new_block) == "updated"
    after = target.read_text(encoding="utf-8")
    assert "user edit above the block" in after
    assert "new block" in after
    assert "old block" not in after


def test_check_fails_when_the_block_is_absent(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--project", str(tmp_path), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    target = tmp_path / "AGENTS.md"
    target.write_text("no markers here\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--project", str(tmp_path), "--check", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert json.loads(result.stdout)["has_block"] is False


def test_dry_run_writes_nothing(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--project", str(tmp_path), "--dry-run"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "AGENTS.md").exists()


def test_block_states_the_precedence_rule_and_the_invocation_forms():
    module = _load()
    block = module.render_block()
    lowered = block.lower()
    assert "@ultimate-dev" in block
    assert "/ultimate-dev" in block
    assert "keep that persona" in lowered
    assert "never claim" in lowered
    assert "not_run" in block


def test_unknown_tool_is_reported_not_guessed(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--project", str(tmp_path), "--tool", "not-a-tool"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "unknown tool" in (result.stdout + result.stderr).lower()

#!/usr/bin/env python3
"""Agent validation tests for ultimate-dev skill."""
import os
import re
import pytest


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(BASE, "agents")


def get_agent_files():
    """Get all agent markdown files."""
    agents = []
    for root, dirs, files in os.walk(AGENTS_DIR):
        for f in files:
            if f.endswith(".md") and not f.startswith(".") and "_shared" not in root:
                agents.append(os.path.join(root, f))
    return agents


class TestAgents:
    """Test agent definitions."""

    @pytest.mark.parametrize("agent_file", get_agent_files())
    def test_agent_has_frontmatter(self, agent_file):
        """Each agent should have YAML frontmatter."""
        with open(agent_file) as f:
            content = f.read()
        assert content.startswith("---"), f"{agent_file} missing frontmatter"
        assert content.count("---") >= 2, f"{agent_file} frontmatter not closed"

    @pytest.mark.parametrize("agent_file", get_agent_files())
    def test_agent_has_required_frontmatter_fields(self, agent_file):
        """Each agent should have required frontmatter fields."""
        with open(agent_file) as f:
            content = f.read()
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        assert match, f"{agent_file} frontmatter not parseable"
        fm_text = match.group(1)
        # Check for key fields
        required = ["name:", "domain:", "description:", "triggers:", "tools:"]
        for field in required:
            assert field in fm_text, f"{agent_file} missing frontmatter field: {field}"

    @pytest.mark.parametrize("agent_file", get_agent_files())
    def test_agent_has_anti_triggers(self, agent_file):
        """Each agent should have anti_triggers to prevent overlap."""
        with open(agent_file) as f:
            content = f.read()
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        assert match, f"{agent_file} frontmatter not parseable"
        fm_text = match.group(1)
        assert "anti_triggers:" in fm_text, f"{agent_file} missing anti_triggers"

    def test_no_duplicate_agent_names(self):
        """Agent names (from filename) should be unique."""
        names = []
        for f in get_agent_files():
            name = os.path.basename(f).replace(".md", "")
            names.append(name)
        assert len(names) == len(set(names)), "Duplicate agent names found"

    def test_agent_name_matches_filename(self):
        """Agent name in frontmatter should match filename."""
        for agent_file in get_agent_files():
            filename = os.path.basename(agent_file).replace(".md", "")
            with open(agent_file) as f:
                content = f.read()
            match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if match:
                fm_text = match.group(1)
                name_match = re.search(r'^name:\s*(.+)$', fm_text, re.MULTILINE)
                if name_match:
                    fm_name = name_match.group(1).strip().strip('"\'')
                    assert fm_name == filename, \
                        f"Agent name mismatch: file={filename}, frontmatter={fm_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
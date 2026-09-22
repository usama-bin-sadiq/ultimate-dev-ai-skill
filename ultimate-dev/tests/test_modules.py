#!/usr/bin/env python3
"""Module validation tests for ultimate-dev skill."""
import os
import re
import pytest


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES_DIR = os.path.join(BASE, "modules")


def get_module_files():
    """Get all module markdown files."""
    modules = []
    for root, dirs, files in os.walk(MODULES_DIR):
        for f in files:
            if f.endswith(".md") and not f.startswith(".") and not f.startswith("_"):
                modules.append(os.path.join(root, f))
    return modules


class TestModules:
    """Test module definitions."""

    @pytest.mark.parametrize("module_file", get_module_files())
    def test_module_has_frontmatter(self, module_file):
        """Each module should have YAML frontmatter."""
        with open(module_file) as f:
            content = f.read()
        assert content.startswith("---"), f"{module_file} missing frontmatter"
        assert content.count("---") >= 2, f"{module_file} frontmatter not closed"

    @pytest.mark.parametrize("module_file", get_module_files())
    def test_module_has_required_frontmatter_fields(self, module_file):
        """Each module should have required frontmatter fields."""
        with open(module_file) as f:
            content = f.read()
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        assert match, f"{module_file} frontmatter not parseable"
        fm_text = match.group(1)
        required = ["name:", "description:", "triggers:", "anti_triggers:"]
        for field in required:
            assert field in fm_text, f"{module_file} missing frontmatter field: {field}"

    @pytest.mark.parametrize("module_file", get_module_files())
    def test_module_has_last_verified(self, module_file):
        """Each module should have last_verified date."""
        with open(module_file) as f:
            content = f.read()
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        assert match, f"{module_file} frontmatter not parseable"
        fm_text = match.group(1)
        assert "last_verified:" in fm_text, f"{module_file} missing last_verified"

    def test_no_duplicate_module_names(self):
        """Module names should be unique."""
        names = []
        for f in get_module_files():
            name = os.path.basename(f).replace(".md", "")
            names.append(name)
        assert len(names) == len(set(names)), "Duplicate module names found"

    def test_module_has_anti_patterns_section(self):
        """Each module should have Anti-Patterns section."""
        for module_file in get_module_files():
            with open(module_file) as f:
                content = f.read()
            # Skip shared/private modules
            if os.path.basename(module_file).startswith("_"):
                continue
            assert "## Anti-Patterns" in content or "## Anti-Patterns" in content, \
                f"{module_file} missing Anti-Patterns section"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
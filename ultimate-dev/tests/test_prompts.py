#!/usr/bin/env python3
"""Prompt completeness tests for ultimate-dev skill."""
import os
import pytest


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_DIR = os.path.join(BASE, "prompts")

REQUIRED_PROMPTS = [
    "system.md",
    "handoff.md",
    "reflection.md",
    "verification.md",
    "delegation.md",
]


def get_prompt_files():
    """Get all markdown files in prompts directory."""
    if not os.path.exists(PROMPTS_DIR):
        return []
    return [f for f in os.listdir(PROMPTS_DIR) if f.endswith('.md')]


class TestPrompts:
    """Test prompt completeness."""

    @pytest.mark.parametrize("prompt_file", REQUIRED_PROMPTS)
    def test_required_prompt_exists(self, prompt_file):
        """Each required prompt should exist."""
        path = os.path.join(PROMPTS_DIR, prompt_file)
        assert os.path.exists(path), f"Required prompt {prompt_file} missing"

    @pytest.mark.parametrize("prompt_file", get_prompt_files())
    def test_prompt_not_empty(self, prompt_file):
        """No prompt file should be empty or only headers."""
        path = os.path.join(PROMPTS_DIR, prompt_file)
        with open(path) as f:
            content = f.read().strip()
        assert len(content) > 50, f"{prompt_file} should have substantial content"

    @pytest.mark.parametrize("prompt_file", get_prompt_files())
    def test_prompt_has_title(self, prompt_file):
        """Each prompt should have a clear title."""
        path = os.path.join(PROMPTS_DIR, prompt_file)
        with open(path) as f:
            content = f.read()
        # Check for markdown title or frontmatter title
        has_title = content.startswith('# ') or 'title:' in content[:200]
        assert has_title, f"{prompt_file} should have a title"

    def test_cross_references_valid(self):
        """Cross-references between prompts should be valid."""
        # This would check for references to other prompts
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
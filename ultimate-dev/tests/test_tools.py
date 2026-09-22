#!/usr/bin/env python3
"""Tool registry validation tests for ultimate-dev skill."""
import os
import yaml
import pytest


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL_REGISTRY = os.path.join(BASE, "tools", "tool_registry.yaml")


class TestToolRegistry:
    """Test tool registry."""

    def test_tool_registry_exists(self):
        """Tool registry file should exist."""
        assert os.path.exists(TOOL_REGISTRY), "tool_registry.yaml missing"

    def test_tool_registry_parses(self):
        """Tool registry should parse as valid YAML."""
        with open(TOOL_REGISTRY) as f:
            content = yaml.safe_load(f)
        assert content is not None, "tool_registry.yaml should not be empty"
        assert "tools" in content, "tool_registry.yaml must have 'tools' key"
        assert isinstance(content["tools"], list), "tools must be a list"

    def test_each_tool_has_required_fields(self):
        """Each tool must have required fields."""
        with open(TOOL_REGISTRY) as f:
            content = yaml.safe_load(f)
        for tool in content["tools"]:
            assert "id" in tool, "Tool missing 'id'"
            assert "name" in tool, f"Tool {tool.get('id')} missing 'name'"
            assert "description" in tool, f"Tool {tool.get('id')} missing 'description'"
            assert "category" in tool, f"Tool {tool.get('id')} missing 'category'"
            assert "permissions" in tool, f"Tool {tool.get('id')} missing 'permissions'"
            assert "parameters" in tool, f"Tool {tool.get('id')} missing 'parameters'"
            assert "returns" in tool, f"Tool {tool.get('id')} missing 'returns'"
            assert "restrictions" in tool, f"Tool {tool.get('id')} missing 'restrictions'"
            assert "usage" in tool, f"Tool {tool.get('id')} missing 'usage'"

    def test_tool_ids_unique(self):
        """Tool IDs must be unique."""
        with open(TOOL_REGISTRY) as f:
            content = yaml.safe_load(f)
        ids = [tool["id"] for tool in content["tools"]]
        assert len(ids) == len(set(ids)), "Duplicate tool IDs found"

    def test_tool_id_naming_convention(self):
        """Tool IDs should follow snake_case convention."""
        with open(TOOL_REGISTRY) as f:
            content = yaml.safe_load(f)
        for tool in content["tools"]:
            tool_id = tool["id"]
            # Should be lowercase with underscores
            assert tool_id == tool_id.lower(), f"Tool ID '{tool_id}' should be lowercase"
            assert " " not in tool_id, f"Tool ID '{tool_id}' should not contain spaces"

    def test_tool_categories_known(self):
        """Tool categories should be from known set."""
        with open(TOOL_REGISTRY) as f:
            content = yaml.safe_load(f)
        known_categories = {
            "filesystem", "search", "execution", "information", "interaction"
        }
        for tool in content["tools"]:
            cat = tool["category"]
            assert cat in known_categories, f"Unknown category '{cat}' for tool {tool['id']}"

    def test_browser_tool_has_full_capabilities(self):
        """Browser tool should have full automation capabilities."""
        with open(TOOL_REGISTRY) as f:
            content = yaml.safe_load(f)
        browser_tool = next((t for t in content["tools"] if t["id"] == "browser"), None)
        assert browser_tool is not None, "Browser tool missing"
        caps = browser_tool.get("capabilities", [])
        expected_caps = [
            "Click elements", "Fill forms", "Execute JavaScript",
            "Wait for elements", "Extract attributes"
        ]
        for exp in expected_caps:
            assert any(exp.lower() in c.lower() for c in caps), \
                f"Browser tool missing capability: {exp}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
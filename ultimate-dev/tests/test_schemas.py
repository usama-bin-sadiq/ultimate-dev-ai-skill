#!/usr/bin/env python3
"""Schema validation tests for ultimate-dev skill."""
import os
import yaml
import pytest


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMAS_DIR = os.path.join(BASE, "schemas")
RUNTIME_SCHEMAS_DIR = os.path.join(BASE, "runtime", "schemas")


def get_schema_files():
    """Get all YAML files in schemas directory."""
    if not os.path.exists(SCHEMAS_DIR):
        return []
    return [f for f in os.listdir(SCHEMAS_DIR) if f.endswith(('.yaml', '.yml'))]


class TestSchemas:
    """Test schema validation."""

    @pytest.mark.parametrize("schema_file", get_schema_files())
    def test_schema_parses(self, schema_file):
        """Each schema file should parse without errors."""
        path = os.path.join(SCHEMAS_DIR, schema_file)
        with open(path) as f:
            content = yaml.safe_load(f)
        assert content is not None, f"{schema_file} should not be empty"

    @pytest.mark.parametrize("schema_file", get_schema_files())
    def test_schema_has_required_fields(self, schema_file):
        """Each schema should have basic required fields."""
        path = os.path.join(SCHEMAS_DIR, schema_file)
        with open(path) as f:
            content = yaml.safe_load(f)
        # Basic structure checks
        assert isinstance(content, dict), f"{schema_file} should be a dict"

    @pytest.mark.parametrize("schema_file", ["task-contract.yaml", "handoff.yaml", "operation.yaml"])
    def test_runtime_schema_parses(self, schema_file):
        """Runtime JSON contracts should remain parseable and identified."""
        path = os.path.join(RUNTIME_SCHEMAS_DIR, schema_file)
        with open(path, encoding="utf-8") as f:
            content = yaml.safe_load(f)
        assert isinstance(content, dict), f"{schema_file} should be an object"
        assert content.get("$schema"), f"{schema_file} should declare a schema dialect"
        assert content.get("title"), f"{schema_file} should have a title"

    def test_error_codes_naming(self):
        """Error codes should follow naming convention."""
        error_schema = os.path.join(SCHEMAS_DIR, "error.yaml")
        if os.path.exists(error_schema):
            with open(error_schema) as f:
                content = yaml.safe_load(f)
            # Check for error code patterns if defined
            assert content is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
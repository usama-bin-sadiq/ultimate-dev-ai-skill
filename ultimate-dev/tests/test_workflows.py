#!/usr/bin/env python3
"""Workflow integrity tests for ultimate-dev skill."""
import os
import yaml
import pytest


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOWS_DIR = os.path.join(BASE, "workflows")


def get_workflow_files():
    """Get all YAML files in workflows directory."""
    if not os.path.exists(WORKFLOWS_DIR):
        return []
    return [f for f in os.listdir(WORKFLOWS_DIR) if f.endswith(('.yaml', '.yml'))]


class TestWorkflows:
    """Test workflow integrity."""

    @pytest.mark.parametrize("workflow_file", get_workflow_files())
    def test_workflow_parses(self, workflow_file):
        """Each workflow file should parse without errors."""
        path = os.path.join(WORKFLOWS_DIR, workflow_file)
        with open(path) as f:
            content = yaml.safe_load(f)
        assert content is not None, f"{workflow_file} should not be empty"

    @pytest.mark.parametrize("workflow_file", get_workflow_files())
    def test_workflow_has_required_fields(self, workflow_file):
        """Each workflow should have name, description, and steps."""
        path = os.path.join(WORKFLOWS_DIR, workflow_file)
        with open(path) as f:
            content = yaml.safe_load(f)
        assert 'name' in content, f"{workflow_file} missing 'name'"
        assert 'description' in content, f"{workflow_file} missing 'description'"
        assert 'steps' in content, f"{workflow_file} missing 'steps'"

    @pytest.mark.parametrize("workflow_file", get_workflow_files())
    def test_steps_have_unique_ids(self, workflow_file):
        """Each step within a workflow should have a unique ID."""
        path = os.path.join(WORKFLOWS_DIR, workflow_file)
        with open(path) as f:
            content = yaml.safe_load(f)
        steps = content.get('steps', [])
        step_ids = [s.get('id') for s in steps if s.get('id')]
        assert len(step_ids) == len(set(step_ids)), f"{workflow_file} has duplicate step IDs"

    @pytest.mark.parametrize("workflow_file", get_workflow_files())
    def test_steps_have_required_fields(self, workflow_file):
        """Each step should have required fields."""
        path = os.path.join(WORKFLOWS_DIR, workflow_file)
        with open(path) as f:
            content = yaml.safe_load(f)
        for step in content.get('steps', []):
            assert 'id' in step, f"Step in {workflow_file} missing 'id'"
            assert 'name' in step, f"Step {step.get('id')} in {workflow_file} missing 'name'"
            assert 'agent' in step or 'tool' in step or 'action' in step, \
                f"Step {step.get('id')} in {workflow_file} missing agent/tool/action"

    @pytest.mark.parametrize("workflow_file", get_workflow_files())
    def test_error_handling_defined(self, workflow_file):
        """Each workflow should have error handling."""
        path = os.path.join(WORKFLOWS_DIR, workflow_file)
        with open(path) as f:
            content = yaml.safe_load(f)
        # Check for error handling at workflow or step level
        has_error_handling = (
            'error_handling' in content or
            any('error_handling' in s or 'on_error' in s for s in content.get('steps', []))
        )
        assert has_error_handling, f"{workflow_file} should define error handling"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
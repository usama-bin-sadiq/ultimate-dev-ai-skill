#!/usr/bin/env python3
"""Rules validation tests for ultimate-dev skill."""
import os
import pytest


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_DIR = os.path.join(BASE, "rules")

REQUIRED_RULES = [
    "validation.md",
    "security.md",
    "coding-standards.md",
    "error-handling.md",
    "delegation.md",
    "three-tier-boundaries.md",
]


class TestRules:
    """Test rules completeness and consistency."""

    @pytest.mark.parametrize("rule_file", REQUIRED_RULES)
    def test_required_rule_exists(self, rule_file):
        """Each required rule file should exist."""
        path = os.path.join(RULES_DIR, rule_file)
        assert os.path.exists(path), f"Required rule {rule_file} missing"

    @pytest.mark.parametrize("rule_file", REQUIRED_RULES)
    def test_rule_not_empty(self, rule_file):
        """No rule file should be empty."""
        path = os.path.join(RULES_DIR, rule_file)
        with open(path) as f:
            content = f.read().strip()
        assert len(content) > 100, f"{rule_file} should have substantial content"

    def test_security_rules_cover_owasp_top10(self):
        """Security rules should cover OWASP Top 10 categories."""
        security_path = os.path.join(RULES_DIR, "security.md")
        with open(security_path) as f:
            content = f.read().lower()
        owasp_categories = [
            "injection", "broken auth", "sensitive data",
            "xml external", "broken access control", "security misconfiguration",
            "xss", "insecure deserialization", "known vulnerabilities",
            "insufficient logging"
        ]
        for cat in owasp_categories:
            assert cat in content, f"Security rules missing OWASP category: {cat}"

    def test_validation_has_test_pyramid(self):
        """Validation rules should enforce test pyramid."""
        validation_path = os.path.join(RULES_DIR, "validation.md")
        with open(validation_path) as f:
            content = f.read()
        assert "test pyramid" in content.lower() or "testing pyramid" in content.lower(), \
            "Validation rules must enforce test pyramid"
        assert "unit" in content.lower() and "integration" in content.lower() and "e2e" in content.lower(), \
            "Validation rules must define all three test layers"

    def test_no_contradictory_rules(self):
        """Rules should not contradict each other."""
        # This is a placeholder - real implementation would cross-reference rules
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
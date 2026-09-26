#!/usr/bin/env python3
"""The runtime must not name a model, and must say why a provider is absent.

Model Independence is a stated non-negotiable: never branch on hardcoded model
names, use capabilities. A literal model name in the runtime pins the product to
one vendor's lineup and ages badly, because model names churn faster than code.

These tests enforce the rule and the honest-reporting requirement that makes
"no model configured" visible instead of silent.
"""
from __future__ import annotations

import os
import re
import sys

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from runtime.core.model_adapter import (  # noqa: E402
    AnthropicProvider,
    ModelAdapter,
    OllamaProvider,
    OpenAIProvider,
)

# Names that must never appear as a literal in runtime code.
FORBIDDEN = (
    "gpt-3", "gpt-4", "gpt-5", "gpt-",
    "claude-2", "claude-3", "claude-4", "claude-",
    "llama2", "llama3",
    "gemini-", "mistral-", "mixtral",
)


def runtime_sources() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    root = os.path.join(BASE, "runtime")
    for directory, _dirs, names in os.walk(root):
        if "__pycache__" in directory:
            continue
        for name in names:
            if not name.endswith((".py", ".mjs")):
                continue
            path = os.path.join(directory, name)
            with open(path, encoding="utf-8") as handle:
                out.append((os.path.relpath(path, BASE), handle.read()))
    return out


class TestNoModelNameLiterals:
    def test_runtime_contains_no_model_name_literal(self):
        offenders = []
        for relative, text in runtime_sources():
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("*"):
                    continue
                for token in FORBIDDEN:
                    if token in stripped:
                        offenders.append(f"{relative}: {stripped[:80]}")
        assert not offenders, (
            "the runtime must not name a model. Model identity comes from "
            "configuration:\n  " + "\n  ".join(offenders)
        )

    def test_providers_default_to_no_model(self):
        for cls in (OllamaProvider, OpenAIProvider, AnthropicProvider):
            instance = cls()
            assert instance.model is None, (
                f"{cls.__name__} must not default to a model name"
            )


class TestUnconfiguredProviderIsReportedNotDefaulted:
    def test_missing_model_config_is_recorded(self):
        adapter = ModelAdapter(config={})
        assert "ollama" in adapter.unavailable_reasons
        assert "no ollama_model configured" in adapter.unavailable_reasons["ollama"]

    def test_absent_api_key_is_recorded(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        adapter = ModelAdapter(config={})
        assert "OPENAI_API_KEY not set" in adapter.unavailable_reasons.get("openai", "")
        assert "ANTHROPIC_API_KEY not set" in adapter.unavailable_reasons.get("anthropic", "")

    def test_no_provider_is_registered_without_configuration(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        adapter = ModelAdapter(config={})
        assert adapter.providers == [], (
            "a provider must not register itself without configured model identity"
        )

    def test_configured_model_is_used_verbatim(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        adapter = ModelAdapter(config={"ollama_model": "some-local-build"})
        # Availability depends on a running endpoint, but the configured name
        # must be the one carried, never a substituted default.
        for provider in adapter.providers:
            assert provider.model == "some-local-build"

    def test_unavailable_reasons_cover_every_known_provider(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        adapter = ModelAdapter(config={})
        assert set(adapter.unavailable_reasons) >= {"ollama", "openai", "anthropic"}


class TestRuleCannotBeSilentlyReintroduced:
    def test_a_reintroduced_literal_is_detected(self):
        """Sanity-check the detector against the pattern it forbids."""
        sample = '    model=self.config.get("openai_model", "gpt-4o-mini"),'
        assert any(token in sample for token in FORBIDDEN), (
            "the detector must flag a model literal in an assignment"
        )

    def test_comments_may_mention_a_name_without_triggering(self):
        sample = '        # prefer a strong reasoning model over gpt-4o-mini'
        offenders = [token for token in FORBIDDEN if token in sample]
        assert offenders, "the raw detector flags names; the test ignores comments"

    def test_config_file_is_the_legal_home_for_model_identity(self):
        import yaml

        with open(os.path.join(BASE, "config", "models.yaml"), encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
        assert "tiers" in config, "models.yaml must remain the tier/capability source"
        # A concrete model may be configured; it just may not be compiled in.
        assert isinstance(config, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

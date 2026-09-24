import importlib

import pytest

from runtime.core.model_adapter import AnthropicProvider, OllamaProvider, OpenAIProvider


def test_provider_transport_is_optional(monkeypatch):
    module = importlib.import_module("runtime.core.model_adapter")
    monkeypatch.setattr(module, "requests", None)
    assert OllamaProvider().is_available() is False
    for provider in (OpenAIProvider(api_key="x"), AnthropicProvider(api_key="x")):
        try:
            provider.complete("hello")
        except RuntimeError as exc:
            assert "optional requests" in str(exc)
        else:
            raise AssertionError("provider should fail closed without requests")


def test_cloud_key_presence_does_not_imply_health(monkeypatch):
    module = importlib.import_module("runtime.core.model_adapter")
    monkeypatch.setenv("OPENAI_API_KEY", "present-but-unverified")
    adapter = module.ModelAdapter()
    assert all(provider.get_capabilities().get("provider") != "openai" for provider in adapter.providers)


def test_host_fallback_requires_an_explicit_callback(monkeypatch):
    module = importlib.import_module("runtime.core.model_adapter")
    monkeypatch.setattr(module, "requests", None)
    adapter = module.ModelAdapter()
    assert adapter.get_best_provider() is None
    with pytest.raises(RuntimeError):
        adapter.complete("hello")

    explicit = module.ModelAdapter({
        "allow_host_fallback": True,
        "host_callback": lambda prompt, options: "host answer",
    })
    result = explicit.complete_with_provenance("hello")
    assert result["text"] == "host answer"
    assert result["provider"] == "host_fallback"
    assert result["fallback"] is False

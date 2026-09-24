#!/usr/bin/env python3
"""
Built-in Model Adapter — Standalone LLM execution.
Supports multiple providers with auto-fallback.
"""
import os
import json
import subprocess
try:
    import requests
except ImportError:  # optional provider transport
    requests = None
from typing import Dict, Any, Optional, List, Callable
from abc import ABC, abstractmethod
from pathlib import Path


class ModelProvider(ABC):
    """Abstract base for model providers."""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass
    
    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Return model capabilities."""
        pass


class OllamaProvider(ModelProvider):
    """Ollama local models."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1"):
        self.base_url = base_url.rstrip("/")
        self.model = model
    
    def is_available(self) -> bool:
        if requests is None:
            return False
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return r.status_code == 200
        except:
            return False
    
    def complete(self, prompt: str, **kwargs) -> str:
        if requests is None:
            raise RuntimeError("optional requests dependency is unavailable")
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.3),
                    "num_predict": kwargs.get("max_tokens", 4096),
                }
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json().get("response", "")
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "provider": "ollama",
            "model": self.model,
            "reasoning": "strong",
            "context_window": 32768,
            "supports_temperature": True,
            "max_output_tokens": 4096,
            "local": True
        }


class OpenAIProvider(ModelProvider):
    """OpenAI API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini", *, assume_available: bool = False):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.assume_available = bool(assume_available)
    
    def is_available(self) -> bool:
        return bool(self.api_key) and self.assume_available
    
    def complete(self, prompt: str, **kwargs) -> str:
        if requests is None:
            raise RuntimeError("optional requests dependency is unavailable")
        if not self.api_key:
            raise RuntimeError("OpenAI API key not set")
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", 0.3),
                "max_tokens": kwargs.get("max_tokens", 4096),
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def get_capabilities(self) -> Dict[str, Any]:
        model_caps = {
            "gpt-4o": {"reasoning": "deep", "context": 128000},
            "gpt-4o-mini": {"reasoning": "strong", "context": 128000},
            "gpt-3.5-turbo": {"reasoning": "standard", "context": 16384},
        }
        caps = model_caps.get(self.model, {"reasoning": "strong", "context": 32768})
        return {
            "provider": "openai",
            "model": self.model,
            "reasoning": caps["reasoning"],
            "context_window": caps["context"],
            "supports_temperature": True,
            "max_output_tokens": 4096,
        }


class AnthropicProvider(ModelProvider):
    """Anthropic Claude API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022", *, assume_available: bool = False):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.assume_available = bool(assume_available)
    
    def is_available(self) -> bool:
        return bool(self.api_key) and self.assume_available
    
    def complete(self, prompt: str, **kwargs) -> str:
        if requests is None:
            raise RuntimeError("optional requests dependency is unavailable")
        if not self.api_key:
            raise RuntimeError("Anthropic API key not set")
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", 0.3),
                "max_tokens": kwargs.get("max_tokens", 4096),
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "provider": "anthropic",
            "model": self.model,
            "reasoning": "deep",
            "context_window": 200000,
            "supports_temperature": True,
            "max_output_tokens": 8192,
        }


class LocalCLIProvider(ModelProvider):
    """Local CLI-based models (llama.cpp, etc.)."""
    
    def __init__(self, command: List[str], model_name: str = "local"):
        self.command = command
        self.model_name = model_name
    
    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                self.command + ["--help"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def complete(self, prompt: str, **kwargs) -> str:
        # Write prompt to temp file, run CLI
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            temp_path = f.name
        
        try:
            cmd = self.command + [temp_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            return result.stdout
        finally:
            os.unlink(temp_path)
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "provider": "local_cli",
            "model": self.model_name,
            "reasoning": "standard",
            "context_window": 8192,
            "supports_temperature": False,
            "max_output_tokens": 2048,
        }


class HostFallbackProvider(ModelProvider):
    """Explicit host callback provider; never fabricates a completion."""

    def __init__(self, callback: Optional[Callable[[str, Dict[str, Any]], str]] = None):
        self.callback = callback

    def is_available(self) -> bool:
        return callable(self.callback)

    def complete(self, prompt: str, **kwargs) -> str:
        if not callable(self.callback):
            raise RuntimeError("host fallback requires an explicit host callback")
        value = self.callback(prompt, dict(kwargs))
        if not isinstance(value, str) or not value:
            raise RuntimeError("host fallback callback returned no completion")
        return value

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "provider": "host_fallback",
            "model": "host_model",
            "reasoning": "unknown",
            "context_window": 0,
            "supports_temperature": False,
            "max_output_tokens": 0,
            "host_native": True,
        }


class ModelAdapter:
    """
    Unified model adapter with auto-discovery and fallback.
    """
    
    PROVIDER_CLASSES = [
        OllamaProvider,
        OpenAIProvider,
        AnthropicProvider,
        LocalCLIProvider,
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.providers: List[ModelProvider] = []
        self.current_provider: Optional[ModelProvider] = None
        self._discover_providers()
    
    @property
    def capabilities(self) -> Dict[str, Any]:
        """Backward compatibility: capabilities as property."""
        return self.get_capabilities()
    
    def _discover_providers(self) -> None:
        """Auto-discover available providers in priority order."""
        # 1. Ollama (local, free)
        ollama = OllamaProvider(
            base_url=self.config.get("ollama_url", "http://localhost:11434"),
            model=self.config.get("ollama_model", "llama3.1")
        )
        if ollama.is_available():
            self.providers.append(ollama)
        
        # 2. OpenAI (cloud)
        if os.environ.get("OPENAI_API_KEY"):
            provider = OpenAIProvider(
                model=self.config.get("openai_model", "gpt-4o-mini"),
                assume_available=bool(self.config.get("assume_cloud_available", False)),
            )
            if provider.is_available():
                self.providers.append(provider)
        
        # 3. Anthropic (cloud)
        if os.environ.get("ANTHROPIC_API_KEY"):
            provider = AnthropicProvider(
                model=self.config.get("anthropic_model", "claude-3-5-sonnet-20241022"),
                assume_available=bool(self.config.get("assume_cloud_available", False)),
            )
            if provider.is_available():
                self.providers.append(provider)
        
        # 4. Local CLI (custom)
        local_cmd = self.config.get("local_command")
        if local_cmd:
            self.providers.append(LocalCLIProvider(local_cmd, "custom"))
        
        # Host fallback is opt-in and must be backed by a real callback.  A
        # placeholder string is never a valid model completion.
        host_callback = self.config.get("host_callback")
        if self.config.get("allow_host_fallback") and callable(host_callback):
            self.providers.append(HostFallbackProvider(host_callback))
        
        # Select best available provider
        if self.providers:
            self.current_provider = self.providers[0]
    
    def get_best_provider(self) -> Optional[ModelProvider]:
        """Get the best available provider."""
        return self.current_provider
    
    def complete(self, prompt: str, **kwargs) -> str:
        """Generate a completion, failing rather than fabricating a fallback."""
        return self.complete_with_provenance(prompt, **kwargs)["text"]

    def complete_with_provenance(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Return text plus explicit provider/fallback provenance."""
        if not self.current_provider:
            raise RuntimeError("No model provider available. Configure an explicit host or provider callback.")
        errors = []
        for provider in self.providers:
            if not provider.is_available():
                continue
            try:
                text = provider.complete(prompt, **kwargs)
                self.current_provider = provider
                return {
                    "text": text,
                    "provider": provider.get_capabilities().get("provider", "unknown"),
                    "fallback": provider is not self.providers[0],
                    "status": "success",
                }
            except Exception as exc:
                errors.append(f"{type(provider).__name__}:{type(exc).__name__}")
        raise RuntimeError("All configured model providers failed: " + ", ".join(errors))
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of current provider."""
        if self.current_provider:
            return self.current_provider.get_capabilities()
        return {
            "provider": "none",
            "reasoning": "unknown",
            "context_window": 0,
            "supports_temperature": False,
            "max_output_tokens": 0,
        }
    
    def select_tier_for_task(self, complexity: str = "medium") -> str:
        """Select model tier based on capabilities."""
        caps = self.get_capabilities()
        reasoning = caps.get("reasoning", "standard")
        context = caps.get("context_window", 0)
        
        if reasoning == "deep" and context >= 32000:
            return "high"
        elif reasoning in ("standard", "strong") and context >= 16000:
            return "medium"
        return "low"


def create_model_adapter(config: Optional[Dict] = None) -> ModelAdapter:
    """Factory function."""
    return ModelAdapter(config)


# Backward compatibility
_default_adapter: Optional[ModelAdapter] = None

def get_adapter(config: Optional[Dict] = None) -> ModelAdapter:
    """Backward compatibility: get default adapter."""
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = ModelAdapter(config)
    return _default_adapter


# Convenience function for simple usage
def quick_complete(prompt: str, **kwargs) -> str:
    """Quick completion with auto-discovery."""
    adapter = create_model_adapter()
    return adapter.complete(prompt, **kwargs)


# Backward compatibility class
class ModelAdapterLegacy:
    """Legacy ModelAdapter for backward compatibility with tests."""
    
    def __init__(self, endpoint: Optional[str] = None, config: Optional[Dict] = None):
        self.endpoint = endpoint
        self.config = config or {}
        # Use provided config as capabilities override
        self._capabilities_override = self.config.copy()
    
    def get_tier_for_task(self, complexity: str = "medium") -> str:
        caps = self._get_capabilities()
        reasoning = caps.get("reasoning", "standard")
        context = caps.get("context_window", 0)
        
        if reasoning == "deep" and context >= 32000:
            return "high"
        elif reasoning in ("standard", "strong") and context >= 16000:
            return "medium"
        return "low"
    
    def _get_capabilities(self) -> Dict[str, Any]:
        caps = {
            "provider": "configured",
            "model": self.config.get("model", "unknown"),
            "reasoning": self.config.get("reasoning", "standard"),
            "context_window": self.config.get("context_window", 0),
            "supports_temperature": self.config.get("supports_temperature", True),
            "max_output_tokens": self.config.get("max_output_tokens", 4096),
        }
        caps.update(self._capabilities_override)
        return caps
    
    def degrade_for_missing_capability(self, required: str) -> str:
        caps = self._get_capabilities()
        if required == "long_context" and caps.get("context_window", 0) < 32000:
            return "medium_context_fallback"
        if required == "deep_reasoning" and caps.get("reasoning") != "deep":
            return "standard_reasoning_fallback"
        return "none"
    
    def invoke(self, model_input: Dict) -> Dict:
        if self.endpoint:
            return {"status": "invoked", "adapter": "model-independent", "endpoint": self.endpoint}
        tier = self.get_tier_for_task(model_input.get("complexity", "medium"))
        return {
            "status": "delegated_to_host",
            "adapter": "model-independent",
            "tier": tier,
            "capabilities": self._get_capabilities(),
            "degradation_applied": tier
        }
    
    @property
    def capabilities(self) -> Dict[str, Any]:
        return self._get_capabilities()


# Convenience function for simple usage
def quick_complete(prompt: str, **kwargs) -> str:
    """Quick completion with auto-discovery."""
    adapter = create_model_adapter()
    return adapter.complete(prompt, **kwargs)
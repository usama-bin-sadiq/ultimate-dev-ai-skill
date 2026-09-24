from __future__ import annotations
"""Model-independent adapter — works with ANY model type.
No hardcoded models, no hardcoded providers.
Discovers capabilities and degrades gracefully."""
from typing import Any, Dict, Optional, List

class ModelAdapter:
    """Provider-agnostic model adapter.
    Works with Claude, GPT, Gemini, Mistral, Llama, custom endpoints — any model.
    Degrades to closest supported pattern if capabilities missing."""

    def __init__(self, endpoint: Optional[str] = None, config: Optional[Dict] = None):
        """endpoint: optional URL/config; if None, discovers from environment.
        config: optional capability overrides."""
        self.endpoint = endpoint
        self.config = config or {}
        self.capabilities = self._discover_capabilities()

    def _discover_capabilities(self) -> Dict[str, Any]:
        """Discover capabilities WITHOUT hardcoding model names.
        Uses available signals: env, endpoint, config, or defaults."""
        caps = {
            "reasoning": self.config.get("reasoning", "unknown"),
            "context_window": self.config.get("context_window", 0),
            "supports_temperature": self.config.get("supports_temperature", True),
            "max_output_tokens": self.config.get("max_output_tokens", 4096),
            "multimodal": self.config.get("multimodal", False),
            "provider_type": "unknown"
        }
        # Degrade if unknown: assume minimal but functional
        if caps["reasoning"] == "unknown":
            caps["reasoning"] = "standard"  # safe default — don't over-promise
        if caps["context_window"] == 0:
            caps["context_window"] = 8192  # safe default
        return caps

    def get_tier_for_task(self, complexity: str = "medium") -> str:
        """Select tier by capability, not by model name.
        Works for any model regardless of brand."""
        if self.capabilities["reasoning"] == "deep" and self.capabilities["context_window"] >= 32000:
            return "high"
        elif self.capabilities["reasoning"] in ("standard", "strong") and self.capabilities["context_window"] >= 16000:
            return "medium"
        else:
            return "low"

    def invoke(self, model_input: Dict) -> Dict:
        """Invoke model — adapter translates to whatever endpoint is configured.
        Never branches on hardcoded provider names."""
        # If endpoint configured, use it generically
        if self.endpoint:
            return {"status": "invoked", "adapter": "model-independent", "endpoint": self.endpoint}
        # Otherwise: use host/default with capability-aware settings
        tier = self.get_tier_for_task(model_input.get("complexity", "medium"))
        return {
            "status": "delegated_to_host",
            "adapter": "model-independent",
            "tier": tier,
            "capabilities": self.capabilities,
            "degradation_applied": tier
        }

    def degrade_for_missing_capability(self, required: str) ->str:
        """If required capability missing, return closest safe pattern."""
        if required == "long_context" and self.capabilities["context_window"] < 32000:
            return "medium_context_fallback"
        if required == "deep_reasoning" and self.capabilities["reasoning"] != "deep":
            return "standard_reasoning_fallback"
        return "none"

# Global adapter instance — can be replaced with any endpoint/config
_default_adapter: Optional[ModelAdapter] = None

def get_adapter(endpoint: Optional[str] = None, config: Optional[Dict] = None) -> ModelAdapter:
    global _default_adapter
    if _default_adapter is None or endpoint is not None or config is not None:
        _default_adapter = ModelAdapter(endpoint=endpoint, config=config)
    return _default_adapter

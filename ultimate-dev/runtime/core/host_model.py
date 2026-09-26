"""Delegation to the host's own model, with provenance.

This is the only model access the runtime has. There is no provider client here
and there must not be one: no API key is read, no endpoint is contacted, and no
vendor is named. When the runtime needs a completion, it asks the host for one
through a callback the host supplies, and records which host answered.

A host fallback that fabricates a completion would defeat the entire evidence
model, so an unconfigured fallback is unavailable and raises rather than
inventing text.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional


class HostFallbackProvider:
    """Delegates completion to a host-supplied callable.

    ``callback`` receives ``(prompt, options)`` and returns the completion text.
    Without one this provider is unavailable, and calling ``complete`` raises:
    a silent, fabricated answer is worse than no answer.
    """

    provider_id = "host_fallback"

    def __init__(self, callback: Optional[Callable[[str, Dict[str, Any]], str]] = None):
        if callback is not None and not callable(callback):
            raise TypeError("host fallback callback must be callable")
        self.callback = callback

    def is_available(self) -> bool:
        return self.callback is not None

    def complete(self, prompt: str, **options: Any) -> str:
        if self.callback is None:
            raise RuntimeError(
                "no host model callback is configured; the runtime does not "
                "call a provider itself, so a completion cannot be produced"
            )
        return self.callback(prompt, options)

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_id,
            "host_native": True,
            "reasoning": "host_defined",
            "context_window": None,
            "supports_temperature": True,
            "max_output_tokens": None,
        }

    def complete_with_provenance(self, prompt: str, **options: Any) -> Dict[str, Any]:
        """Return the completion together with where it came from."""
        text = self.complete(prompt, **options)
        return {
            "text": text,
            "provider": self.provider_id,
            "host_native": True,
            "evidence_grade": "TOOL_ATTESTED" if text else "SELF_REPORTED",
        }


def get_capabilities() -> Dict[str, Any]:
    """Describe the host-delegated path without naming a model."""
    return HostFallbackProvider().get_capabilities()


__all__ = ["HostFallbackProvider", "get_capabilities"]

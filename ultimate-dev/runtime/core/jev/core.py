"""Retired Python JEV core compatibility surface.

This module intentionally contains no classifier, routing, or execution logic.
The old implementation could return a permissive executable result without
using the canonical host-native decision contract.  Keep the names importable,
but reject every public entry point with a stable typed error before reading a
context or invoking another component.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .types import (
    JevAggregatedDecision,
    JevContext,
    JevDecisionPacket,
    LegacyUnavailableError,
)


class JevInput:
    """Compatibility constructor for the old three-argument ``JevInput``."""

    def __init__(
        self,
        user_input: str,
        langchain_state: Dict[str, Any],
        available_tools: list[Dict[str, Any]],
        session_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        raise LegacyUnavailableError("runtime.core.jev.core", "JevInput")


class JevCore:
    """Legacy JEV orchestrator; unavailable by design."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        raise LegacyUnavailableError("runtime.core.jev.core", "JevCore")

    def classify(self, context: JevContext) -> JevAggregatedDecision:
        raise LegacyUnavailableError("runtime.core.jev.core", "JevCore.classify")

    def process(self, context: JevContext) -> Dict[str, Any]:
        raise LegacyUnavailableError("runtime.core.jev.core", "JevCore.process")

    def get_stats(self) -> Dict[str, Any]:
        raise LegacyUnavailableError("runtime.core.jev.core", "JevCore.get_stats")


def create_jev_core(config: Optional[Dict[str, Any]] = None) -> JevCore:
    raise LegacyUnavailableError("runtime.core.jev.core", "create_jev_core")


__all__ = [
    "LegacyUnavailableError",
    "JevContext",
    "JevDecisionPacket",
    "JevInput",
    "JevCore",
    "create_jev_core",
]

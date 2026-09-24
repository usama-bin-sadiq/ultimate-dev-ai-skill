"""Retired Python JEV tool-slimming compatibility surface."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .types import JevAggregatedDecision, LegacyUnavailableError


@dataclass
class SlimmingResult:
    pruned_tools: List[str] = field(default_factory=list)
    retained_tools: List[str] = field(default_factory=list)
    slimming_reason: str = ""
    slimming_confidence: float = 0.0


class ToolSlimmer:
    """Legacy tool slimmer that cannot make routing decisions."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        raise LegacyUnavailableError("runtime.core.jev.tool_slimmer", "ToolSlimmer")

    def slim(
        self, tools: List[Dict[str, Any]], agg_decision: JevAggregatedDecision
    ) -> List[Dict[str, Any]]:
        raise LegacyUnavailableError("runtime.core.jev.tool_slimmer", "ToolSlimmer.slim")

    def _slim_for_execution(
        self, tools: List[Dict[str, Any]], agg_decision: JevAggregatedDecision
    ) -> List[Dict[str, Any]]:
        raise LegacyUnavailableError("runtime.core.jev.tool_slimmer", "ToolSlimmer._slim_for_execution")

    def _slim_for_lightweight(
        self, tools: List[Dict[str, Any]], agg_decision: JevAggregatedDecision
    ) -> List[Dict[str, Any]]:
        raise LegacyUnavailableError("runtime.core.jev.tool_slimmer", "ToolSlimmer._slim_for_lightweight")

    def _slim_for_backend(
        self, tools: List[Dict[str, Any]], agg_decision: JevAggregatedDecision
    ) -> List[Dict[str, Any]]:
        raise LegacyUnavailableError("runtime.core.jev.tool_slimmer", "ToolSlimmer._slim_for_backend")

    def _slim_for_review(
        self, tools: List[Dict[str, Any]], agg_decision: JevAggregatedDecision
    ) -> List[Dict[str, Any]]:
        raise LegacyUnavailableError("runtime.core.jev.tool_slimmer", "ToolSlimmer._slim_for_review")

    def _filter_by_categories(
        self, tools: List[Dict[str, Any]], allowed_categories: set[str]
    ) -> List[Dict[str, Any]]:
        raise LegacyUnavailableError("runtime.core.jev.tool_slimmer", "ToolSlimmer._filter_by_categories")

    def _categorize_tool(self, tool_name: str) -> str:
        raise LegacyUnavailableError("runtime.core.jev.tool_slimmer", "ToolSlimmer._categorize_tool")

    def get_slimming_stats(
        self, original: List[Dict[str, Any]], pruned: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        raise LegacyUnavailableError(
            "runtime.core.jev.tool_slimmer", "ToolSlimmer.get_slimming_stats"
        )


class ToolSlimmerAdvanced:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        raise LegacyUnavailableError(
            "runtime.core.jev.tool_slimmer", "ToolSlimmerAdvanced"
        )

    def slim_with_semantics(
        self,
        tools: List[Dict[str, Any]],
        task: str,
        decision: JevAggregatedDecision,
    ) -> List[Dict[str, Any]]:
        raise LegacyUnavailableError(
            "runtime.core.jev.tool_slimmer", "ToolSlimmerAdvanced.slim_with_semantics"
        )

    def get_tool_relevance(self, tool: Dict[str, Any], task: str) -> float:
        raise LegacyUnavailableError(
            "runtime.core.jev.tool_slimmer", "ToolSlimmerAdvanced.get_tool_relevance"
        )


def create_tool_slimmer(config: Optional[Dict[str, Any]] = None) -> ToolSlimmer:
    raise LegacyUnavailableError("runtime.core.jev.tool_slimmer", "create_tool_slimmer")


def create_advanced_slimmer(
    config: Optional[Dict[str, Any]] = None
) -> ToolSlimmerAdvanced:
    raise LegacyUnavailableError(
        "runtime.core.jev.tool_slimmer", "create_advanced_slimmer"
    )


__all__ = [
    "LegacyUnavailableError",
    "SlimmingResult",
    "ToolSlimmer",
    "ToolSlimmerAdvanced",
    "create_tool_slimmer",
    "create_advanced_slimmer",
]

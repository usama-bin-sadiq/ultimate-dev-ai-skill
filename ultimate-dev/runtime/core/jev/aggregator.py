"""Retired Python JEV aggregation compatibility surface."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .types import (
    ChoiceResult,
    JevAggregatedDecision,
    LegacyUnavailableError,
    NOULResult,
    ScoreResult,
)


class DeterministicAggregator:
    """Legacy aggregator that cannot produce an executable decision."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        raise LegacyUnavailableError(
            "runtime.core.jev.aggregator", "DeterministicAggregator"
        )

    def aggregate(
        self,
        noul_result: NOULResult,
        choice_result: ChoiceResult,
        score_result: ScoreResult,
    ) -> JevAggregatedDecision:
        raise LegacyUnavailableError(
            "runtime.core.jev.aggregator", "DeterministicAggregator.aggregate"
        )

    def build_decision(
        self,
        noul_result: NOULResult,
        choice_result: ChoiceResult,
        score_result: ScoreResult,
    ) -> JevAggregatedDecision:
        raise LegacyUnavailableError(
            "runtime.core.jev.aggregator", "DeterministicAggregator.build_decision"
        )


__all__ = ["DeterministicAggregator", "JevAggregatedDecision", "LegacyUnavailableError"]

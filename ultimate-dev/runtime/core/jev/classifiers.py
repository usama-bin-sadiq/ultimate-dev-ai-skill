"""Retired Python JEV classifier compatibility surface.

The old classifiers were independently implemented policy logic and could
approve work without the host-native decision contract.  Keep the public names
for import compatibility, but make every entry point fail closed before it can
inspect input or perform work.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .types import (
    ChoiceResult,
    LegacyUnavailableError,
    NOULResult,
    ScoreResult,
)


class NOULClassifier:
    """Legacy classifier that is intentionally unavailable."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        raise LegacyUnavailableError("runtime.core.jev.classifiers", "NOULClassifier")

    def _load_rules(self) -> None:
        raise LegacyUnavailableError("runtime.core.jev.classifiers", "NOULClassifier._load_rules")

    def _rule_safety_deny(self, task: str, context: Dict[str, Any]) -> tuple:
        raise LegacyUnavailableError("runtime.core.jev.classifiers", "NOULClassifier._rule_safety_deny")

    def _rule_urgency_approve(self, task: str, context: Dict[str, Any]) -> tuple:
        raise LegacyUnavailableError("runtime.core.jev.classifiers", "NOULClassifier._rule_urgency_approve")

    def _rule_complexity_deny(self, task: str, context: Dict[str, Any]) -> tuple:
        raise LegacyUnavailableError("runtime.core.jev.classifiers", "NOULClassifier._rule_complexity_deny")

    def _rule_simple_approve(self, task: str, context: Dict[str, Any]) -> tuple:
        raise LegacyUnavailableError("runtime.core.jev.classifiers", "NOULClassifier._rule_simple_approve")

    def classify(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> NOULResult:
        raise LegacyUnavailableError("runtime.core.jev.classifiers", "NOULClassifier.classify")


class ChoiceClassifier:
    """Legacy classifier that is intentionally unavailable."""

    ROUTING_CLASSES = (
        "execute_tool",
        "human_review",
        "lightweight_backend",
        "backend",
        "flagship_llm",
    )

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        raise LegacyUnavailableError("runtime.core.jev.classifiers", "ChoiceClassifier")

    def _load_patterns(self) -> None:
        raise LegacyUnavailableError("runtime.core.jev.classifiers", "ChoiceClassifier._load_patterns")

    def classify(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> ChoiceResult:
        raise LegacyUnavailableError("runtime.core.jev.classifiers", "ChoiceClassifier.classify")


class ScoreClassifier:
    """Legacy classifier that is intentionally unavailable."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        raise LegacyUnavailableError("runtime.core.jev.classifiers", "ScoreClassifier")

    def classify(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> ScoreResult:
        raise LegacyUnavailableError("runtime.core.jev.classifiers", "ScoreClassifier.classify")


__all__ = [
    "LegacyUnavailableError",
    "NOULClassifier",
    "ChoiceClassifier",
    "ScoreClassifier",
]

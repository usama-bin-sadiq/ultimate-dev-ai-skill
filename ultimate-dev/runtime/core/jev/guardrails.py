"""Retired Python JEV guardrail compatibility surface."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .types import LegacyUnavailableError, NOULResult


class GuardrailDecision(Enum):
    APPROVE = "approve"
    DENY = "deny"
    HUMAN_REVIEW = "human_review"


@dataclass
class GuardrailResult:
    decision: str
    confidence: float
    reason: str
    triggered_rules: List[str] = field(default_factory=list)


class Guardrails:
    """Legacy guardrails that always fail closed before evaluating input."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        raise LegacyUnavailableError("runtime.core.jev.guardrails", "Guardrails")

    def evaluate(
        self, noul_result: NOULResult, task: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        raise LegacyUnavailableError("runtime.core.jev.guardrails", "Guardrails.evaluate")

    def evaluate_simple(self, probability: float, task: str) -> Dict[str, Any]:
        raise LegacyUnavailableError(
            "runtime.core.jev.guardrails", "Guardrails.evaluate_simple"
        )


def create_guardrails(config: Optional[Dict[str, Any]] = None) -> Guardrails:
    raise LegacyUnavailableError("runtime.core.jev.guardrails", "create_guardrails")


__all__ = [
    "LegacyUnavailableError",
    "GuardrailDecision",
    "GuardrailResult",
    "Guardrails",
    "create_guardrails",
]

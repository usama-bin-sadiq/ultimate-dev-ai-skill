"""Typed compatibility definitions for the retired Python JEV implementation.

The Python JEV package is a compatibility surface only.  It is intentionally
kept importable so old callers receive a useful, typed error instead of a
partially functioning decision engine.  The supported decision kernel lives in
``runtime/jev/engine.mjs`` (or an equivalent host-native implementation).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class LegacyUnavailableError(RuntimeError):
    """Raised when a retired compatibility entry point is reached.

    ``code`` is deliberately stable for callers that need to distinguish this
    boundary from an ordinary programming or provider failure.
    """

    code = "legacy_unavailable"
    error_code = code

    def __init__(
        self,
        component: str = "runtime.core.jev",
        operation: str = "legacy entry point",
    ) -> None:
        self.component = component
        self.operation = operation
        message = (
            f"{self.code}: {component}.{operation} is unavailable; use the "
            "host-native JEV contract or runtime/jev/engine.mjs"
        )
        super().__init__(message)

    def to_dict(self) -> Dict[str, str]:
        return {
            "code": self.code,
            "component": self.component,
            "operation": self.operation,
            "message": str(self),
        }


class UnsafeDevelopmentError(RuntimeError):
    """Stable error code for explicitly unsafe development-only operations."""

    code = "unsafe-development"
    error_code = code

    def __init__(
        self,
        component: str = "runtime.core",
        operation: str = "unsafe development operation",
    ) -> None:
        self.component = component
        self.operation = operation
        message = (
            f"{self.code}: {component}.{operation} is disabled; this legacy "
            "surface is not a supported execution boundary"
        )
        super().__init__(message)

    def to_dict(self) -> Dict[str, str]:
        return {
            "code": self.code,
            "component": self.component,
            "operation": self.operation,
            "message": str(self),
        }


# Compatibility aliases used by older integrations.
LegacyUnavailable = LegacyUnavailableError
UnsafeDevelopment = UnsafeDevelopmentError
LegacyJevUnavailableError = LegacyUnavailableError
JevLegacyUnavailableError = LegacyUnavailableError


class JevDecisionType(Enum):
    APPROVE = "approve"
    DENY = "deny"
    HUMAN_REVIEW = "human_review"


class RoutingTarget(Enum):
    EXECUTE_TOOL = "execute_tool"
    HUMAN_REVIEW = "human_review"
    LIGHTWEIGHT_BACKEND = "lightweight_backend"
    BACKEND = "backend"
    FLAGSHIP_LLM = "flagship_llm"


class RiskLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskComplexity(Enum):
    ATOMIC = "atomic"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ClarityLevel(Enum):
    CLEAR = "clear"
    RESOLVABLE = "resolvable"
    BLOCKED = "blocked"


class PatternHint(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    COMPOSE = "compose"


@dataclass
class NOULResult:
    decision: bool
    probability: float
    reasoning: str
    rule_id: str


@dataclass
class ChoiceResult:
    selected: str
    probabilities: Dict[str, float]
    reasoning: str
    rule_id: str


@dataclass
class ScoreResult:
    value: float
    level: RiskLevel
    reasoning: str
    rule_id: str


@dataclass
class JevClassification:
    size: str
    domains: List[str]
    risk: str
    clarity: str
    agents: List[str]
    pattern: str
    confidence: float


@dataclass
class JevAggregatedDecision:
    """Legacy data shape retained for import compatibility.

    Constructing this data object does not execute a decision.  All legacy
    classifiers and routing entry points refuse to produce one.
    """

    guardrail_decision: str
    routing_target: str
    selected_backend: str
    guardrail_confidence: float = 0.0
    guardrail_reason: str = ""
    human_review_required: bool = False
    routing_confidence: float = 0.0
    routing_reason: str = ""
    pruned_tools: List[str] = field(default_factory=list)
    retained_tools: List[str] = field(default_factory=list)
    slimming_reason: str = ""
    slimming_confidence: float = 0.0
    size: str = "moderate"
    domains: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    clarity: str = "clear"
    pattern_hint: str = "A"
    domain_hints: List[str] = field(default_factory=list)
    specialist_hints: List[str] = field(default_factory=list)
    ambiguity_flags: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)
    raw_noul: Optional[Dict[str, Any]] = None
    raw_choice: Optional[Dict[str, Any]] = None
    raw_score: Optional[Dict[str, Any]] = None


@dataclass
class JevInput:
    user_input: str
    langchain_state: Dict[str, Any]
    available_tools: List[Dict[str, Any]]
    session_config: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        raise LegacyUnavailableError("runtime.core.jev.types", "JevInput")


@dataclass
class JevContext:
    user_input: str
    langchain_state: Dict[str, Any]
    available_tools: List[Dict[str, Any]]
    session_config: Dict[str, Any]
    project_root: str
    session_id: Optional[str] = None

    def __post_init__(self) -> None:
        raise LegacyUnavailableError("runtime.core.jev.types", "JevContext")


@dataclass
class JevDecisionPacket:
    aggregated: JevAggregatedDecision
    guardrail_result: Dict[str, Any]
    routing_decision: Dict[str, Any]
    slimming_result: Dict[str, Any]
    processing_time_ms: float
    should_execute: bool
    should_escalate: bool

    def __post_init__(self) -> None:
        raise LegacyUnavailableError("runtime.core.jev.types", "JevDecisionPacket")


__all__ = [
    "LegacyUnavailableError",
    "LegacyUnavailable",
    "UnsafeDevelopment",
    "LegacyJevUnavailableError",
    "JevLegacyUnavailableError",
    "UnsafeDevelopmentError",
    "JevDecisionType",
    "RoutingTarget",
    "RiskLevel",
    "TaskComplexity",
    "ClarityLevel",
    "PatternHint",
    "NOULResult",
    "ChoiceResult",
    "ScoreResult",
    "JevClassification",
    "JevAggregatedDecision",
    "JevInput",
    "JevContext",
    "JevDecisionPacket",
]

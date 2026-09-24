"""Retired Python JEV compatibility package.

The package remains importable for old callers, but all executable legacy
entry points fail closed.  Use the host-native JEV contract instead.
"""
from .types import (
    ChoiceResult,
    ClarityLevel,
    JevAggregatedDecision,
    JevClassification,
    JevContext,
    JevDecisionPacket,
    JevDecisionType,
    JevInput,
    LegacyJevUnavailableError,
    LegacyUnavailable,
    LegacyUnavailableError,
    NOULResult,
    PatternHint,
    RiskLevel,
    RoutingTarget,
    ScoreResult,
    TaskComplexity,
    UnsafeDevelopment,
    UnsafeDevelopmentError,
)
from .classifiers import ChoiceClassifier, NOULClassifier, ScoreClassifier
from .aggregator import DeterministicAggregator
from .guardrails import GuardrailResult, Guardrails, create_guardrails
from .routing import PathRouter, RoutingDecision, create_path_router
from .tool_slimmer import SlimmingResult, ToolSlimmer, create_tool_slimmer
from .core import JevCore, create_jev_core

__all__ = [
    "LegacyUnavailableError",
    "LegacyUnavailable",
    "LegacyJevUnavailableError",
    "UnsafeDevelopment",
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
    "NOULClassifier",
    "ChoiceClassifier",
    "ScoreClassifier",
    "DeterministicAggregator",
    "Guardrails",
    "GuardrailResult",
    "PathRouter",
    "RoutingDecision",
    "ToolSlimmer",
    "SlimmingResult",
    "create_guardrails",
    "create_path_router",
    "create_tool_slimmer",
    "JevCore",
    "create_jev_core",
]

"""
Jev Core Types - System One Decision Layer
Type-safe enums and dataclasses for Jev decision layer.
"""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


class JevDecisionType(Enum):
    """Guardrail decision types"""
    APPROVE = "approve"
    DENY = "deny"
    HUMAN_REVIEW = "human_review"


class RoutingTarget(Enum):
    """Where to route the task for execution"""
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
    A = "A"  # Skills - single domain, inline
    B = "B"  # Subagents - parallel independent domains
    C = "C"  # Handoffs - sequential dependent stages
    D = "D"  # Router - classification and dispatch
    COMPOSE = "compose"  # Multiple patterns combined


class JevDecisionType(Enum):
    """Guardrail decision types"""
    APPROVE = "approve"
    DENY = "deny"
    HUMAN_REVIEW = "human_review"


class RoutingTarget(Enum):
    """Where to route the task for execution"""
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


# Core result types
@dataclass
class NOULResult:
    """Boolean decision result from NOUL classifier."""
    decision: bool
    probability: float
    reasoning: str
    rule_id: str

@dataclass
class ChoiceResult:
    """Multi-class classification result."""
    selected: str
    probabilities: Dict[str, float]
    reasoning: str
    rule_id: str

@dataclass
class ScoreResult:
    """Risk/scale scoring result."""
    value: float
    level: RiskLevel
    reasoning: str
    rule_id: str


# Core result types
@dataclass
class NOULResult:
    """Boolean decision result from NOUL classifier."""
    decision: bool
    probability: float
    reasoning: str
    rule_id: str

@dataclass
class ChoiceResult:
    """Multi-class classification result."""
    selected: str
    probabilities: Dict[str, float]
    reasoning: str
    rule_id: str

@dataclass
class ScoreResult:
    """Risk/scale scoring result."""
    value: float
    level: RiskLevel
    reasoning: str
    rule_id: str


# Complete classification result
@dataclass
class JevClassification:
    """Complete classification result from Jev."""
    size: str
    domains: List[str]
    risk: str
    clarity: str
    agents: List[str]
    pattern: str
    confidence: float


# Aggregated decision from Jev pipeline
@dataclass
class JevAggregatedDecision:
    """Deterministic aggregation of NOUL + CHOICE + SCORE."""
    # Required fields first (no defaults)
    guardrail_decision: str
    routing_target: str
    selected_backend: str

    # Guardrails
    guardrail_confidence: float = 0.0
    guardrail_reason: str = ""
    human_review_required: bool = False

    # Dynamic Routing
    routing_confidence: float = 0.0
    routing_reason: str = ""
    selected_backend: str = "backend"

    # Context Slimming
    pruned_tools: List[str] = field(default_factory=list)
    retained_tools: List[str] = field(default_factory=list)
    slimming_reason: str = ""
    slimming_confidence: float = 0.0

    # Classification Output
    size: str = "moderate"
    domains: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    clarity: str = "clear"
    pattern_hint: str = "A"
    domain_hints: List[str] = field(default_factory=list)
    specialist_hints: List[str] = field(default_factory=list)
    ambiguity_flags: List[str] = field(default_factory=list)

    # Metadata
    processing_time_ms: float = 0.0
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)
    raw_noul: Optional[Dict] = None
    raw_choice: Optional[Dict] = None
    raw_score: Optional[Dict] = None


# Context and input types
@dataclass
class JevInput:
    """Input to Jev classifier."""
    user_input: str
    langchain_state: Dict[str, Any]
    available_tools: List[Dict[str, Any]]
    session_config: Dict[str, Any]


@dataclass
class JevContext:
    """Context passed through Jev pipeline."""
    user_input: str
    langchain_state: Dict[str, Any]
    available_tools: List[Dict[str, Any]]
    session_config: Dict[str, Any]
    project_root: str
    session_id: Optional[str] = None


@dataclass
class JevDecisionPacket:
    """Complete decision packet from Jev Core."""
    aggregated: 'JevAggregatedDecision'
    guardrail_result: Dict
    routing_decision: Dict
    slimming_result: Dict
    processing_time_ms: float
    should_execute: bool
    should_escalate: bool


# Re-export for backward compatibility
__all__ = [
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
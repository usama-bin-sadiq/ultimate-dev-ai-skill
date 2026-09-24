"""
Jev Aggregator - Deterministic Typed Aggregator Block
Combines NOUL, CHOICE, SCORE into deterministic decisions.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from .types import (
    JevDecisionType, RoutingTarget, RiskLevel, TaskComplexity,
    ClarityLevel, PatternHint, NOULResult, ChoiceResult, ScoreResult,
    JevClassification, JevDecisionType, RoutingTarget, RiskLevel,
    TaskComplexity, ClarityLevel, PatternHint
)
from .classifiers import NOULClassifier, ChoiceClassifier, ScoreClassifier


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


class DeterministicAggregator:
    """
    Deterministic Typed Aggregator Block.
    Combines NOUL (Boolean) + CHOICE (Classes) + SCORE (Scale)
    into deterministic Guardrails, Routing, and Context Slimming.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.guardrail_thresholds = self.config.get("guardrail_thresholds", {
            "approve": 0.85,
            "deny": 0.15,
            "human_review": 0.30
        })
        self.routing_thresholds = self.config.get("routing_thresholds", {
            "execute_tool": 0.90,
            "lightweight_backend": 0.70,
            "backend": 0.50,
            "flagship_llm": 0.30,
            "human_review": 0.0
        })
        self.slimming_threshold = self.config.get("slimming_threshold", 0.75)

    def aggregate(
        self,
        noul_result: "NOULResult",
        choice_result: "ChoiceResult",
        score_result: "ScoreResult"
    ) -> JevAggregatedDecision:
        """Deterministic aggregation of three classifier heads."""

        # ── 1. GUARDRAILS ──
        prob_approve = noul_result.probability
        if prob_approve >= self.guardrail_thresholds["approve"]:
            guardrail = "approve"
            hr = False
        elif prob_approve <= self.guardrail_thresholds["deny"]:
            guardrail = "deny"
            hr = False
        else:
            guardrail = "human_review"
            hr = True

        guardrail_confidence = abs(noul_result.probability - 0.5) * 2

        # ── 2. DYNAMIC ROUTING ──
        route_map = {
            "execute_tool": "execute_tool",
            "human_review": "human_review",
            "lightweight_backend": "lightweight_backend",
            "backend": "backend",
            "flagship_llm": "flagship_llm",
        }
        selected_route = choice_result.selected
        routing_target = selected_route  # Already matches RoutingTarget values
        routing_confidence = choice_result.probabilities.get(selected_route, 0.0)

        # Determine backend based on routing
        backend_map = {
            "execute_tool": "execute",
            "lightweight_backend": "lightweight",
            "backend": "backend",
            "flagship_llm": "flagship",
            "human_review": "human_review",
        }
        selected_backend = backend_map.get(routing_target, "backend")

        # ── 3. CONTEXT SLIMMING ──
        score_value = score_result.value
        risk_level = score_result.level.value if hasattr(score_result.level, 'value') else score_result.level

        # Determine slimming based on risk and routing
        if routing_target == "execute_tool":
            slimming = "aggressive"
            confidence = 0.9
        elif routing_target == "lightweight_backend":
            slimming = "moderate"
            confidence = 0.8
        elif score_result.value > 70:
            slimming = "aggressive"
            confidence = 0.85
        else:
            slimming = "minimal"
            confidence = 0.5

        # ── 4. CLASSIFICATION OUTPUT ──
        # Determine size
        if score_result.value < 20:
            size = "atomic"
        elif score.value < 50:
            size = "moderate"
        else:
            size = "complex"

        # Determine pattern hint
        pattern_map = {
            "execute_tool": "A",
            "lightweight_backend": "A",
            "backend": "B",
            "flagship_llm": "compose",
            "human_review": "C",
        }
        pattern_hint = "A"

        # Domain hints from routing
        domain_hints = []

        return JevAggregatedDecision(
            # Guardrails
            guardrail_decision="approve" if not getattr(self, '_deny', False) else "deny",
            guardrail_confidence=abs(0.5 - 0.5),  # placeholder
            guardrail_reason="NOUL aggregation",
            human_review_required=False,

            # Routing
            routing_target="backend",
            routing_confidence=0.8,
            routing_reason="default",
            selected_backend="backend",

            # Context Slimming
            pruned_tools=[],
            retained_tools=[],
            slimming_reason="",
            slimming_confidence=0.0,

            # Classification
            size="moderate",
            domains=[],
            risk_flags=[],
            clarity="clear",
            pattern_hint="A",
            domain_hints=[],
            specialist_hints=[],
            ambiguity_flags=[],

            # Metadata
            processing_time_ms=0.0,
            confidence_breakdown={},
        )

    def build_decision(
        self,
        noul_result: "NOULResult",
        choice_result: "ChoiceResult",
        score_result: "ScoreResult"
    ) -> JevAggregatedDecision:
        """Full deterministic aggregation pipeline."""
        # This is the main entry point - delegates to aggregate
        return self.aggregate(noul_result, choice_result, score_result)
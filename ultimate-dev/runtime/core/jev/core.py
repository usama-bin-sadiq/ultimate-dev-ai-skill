"""
Jev Core - Main Orchestrator
The System One Decision Layer that sits between Agent Executor and Model/Orchestrator.
"""
from __future__ import annotations
import time
import asyncio
from typing import Dict, List, Optional, Any, Dict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from .types import (
    JevInput, JevAggregatedDecision, NOULResult, ChoiceResult, ScoreResult,
    JevDecisionType, RoutingTarget, RiskLevel, TaskComplexity, ClarityLevel,
    NOULResult, ChoiceResult, ScoreResult
)
from .classifiers import NOULClassifier, ChoiceClassifier, ScoreClassifier
from .aggregator import DeterministicAggregator, JevAggregatedDecision
from .guardrails import Guardrails
from .routing import PathRouter, RoutingDecision
from .tool_slimmer import ToolSlimmer, SlimmingResult


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


class JevCore:
    """
    Jev Core - System One Decision Layer.
    Fast-path classifier with three-headed architecture:
    NOUL (Boolean) + CHOICE (Classes) + SCORE (Scale)
    → Deterministic Aggregator → Guardrails + Routing + Slimming
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

        # Initialize three-headed classifier
        self.noul = NOULClassifier(self.config.get("noul", {}))
        self.choice = ChoiceClassifier(self.config.get("choice", {}))
        self.score = ScoreClassifier(self.config.get("score", {}))

        # Deterministic aggregator
        self.aggregator = DeterministicAggregator(self.config.get("aggregator", {}))

        # Post-processing
        self.guardrails = Guardrails(self.config.get("guardrails", {}))
        self.router = PathRouter(self.config.get("routing", {}))
        self.slimmer = ToolSlimmer(self.config.get("slimmer", {}))

        # Performance tracking
        self.stats = {
            "total": 0,
            "high_confidence": 0,
            "escalated": 0,
            "avg_ms": 0.0
        }

    def classify(self, context: 'JevContext') -> 'JevAggregatedDecision':
        """
        Main classification pipeline.
        Runs NOUL → CHOICE → SCORE → Aggregator → Guardrails → Routing → Slimming
        """
        start_time = time.perf_counter()

        # Prepare input
        inp = JevInput(
            user_input=context.user_input,
            langchain_state=context.langchain_state,
            available_tools=context.available_tools,
            session_config=context.session_config
        )

        # ── 1. Three-Headed Classification ──
        noul_result = self.noul.classify(context.user_input, context.session_config)
        choice_result = self.choice.classify(context.user_input, context.session_config)
        score_result = self.score.classify(context.user_input, context.session_config)

        # ── 2. Deterministic Aggregation ──
        aggregated = self.aggregator.build_decision(noul_result, choice_result, score_result)

        # ── 3. Guardrails ──
        guardrail_result = self.guardrails.evaluate_simple(
            aggregated.confidence_breakdown.get("noul", 0.5),
            context.user_input
        )

        # ── 4. Dynamic Routing ──
        routing_decision = self.router.route(
            ChoiceResult(
                selected="backend",  # placeholder
                probabilities={},
                reasoning="",
                rule_id=""
            ),
            None
        )

        # ── 5. Context Slimming ──
        slimming_result = self.slimmer.slim(context.available_tools, None)

        # Build final aggregated decision
        elapsed = (time.perf_counter() - start_time) * 1000

        # Build aggregated decision
        aggregated = JevAggregatedDecision(
            guardrail_decision="approve",
            guardrail_confidence=0.9,
            guardrail_reason="auto",
            human_review_required=False,
            routing_target="backend",
            routing_confidence=0.8,
            routing_reason="default",
            selected_backend="backend",
            pruned_tools=[],
            retained_tools=[],
            slimming_reason="",
            slimming_confidence=0.0,
            processing_time_ms=elapsed,
        )

        self.stats["total"] += 1
        self.stats["avg_ms"] = (self.stats["avg_ms"] * (self.stats["total"] - 1) + elapsed) / self.stats["total"]

        return aggregated

    def process(self, context: 'JevContext') -> Dict[str, Any]:
        """
        Main entry point - returns complete decision packet.
        """
        start_time = time.perf_counter()

        # Run classification
        aggregated = self.classify(context)

        # Build response
        elapsed = (time.perf_counter() - start_time) * 1000

        return {
            "decision": "approve",  # placeholder
            "aggregated": aggregated.__dict__ if hasattr(aggregated, '__dict__') else str(aggregated),
            "processing_time_ms": elapsed,
            "should_execute": True,
            "should_escalate": False,
        }

    def get_stats(self) -> Dict:
        return self.stats.copy()


# Factory
def create_jev_core(config: Optional[Dict] = None) -> 'JevCore':
    return JevCore(config)


# Backward compatibility
class JevInput:
    def __init__(self, user_input: str, langchain_state: Dict, available_tools: List[Dict]):
        self.user_input = user_input
        self.langchain_state = langchain_state
        self.available_tools = available_tools
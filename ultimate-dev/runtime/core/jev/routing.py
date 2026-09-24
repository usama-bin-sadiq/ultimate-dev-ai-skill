"""
Jev Dynamic Routing - Path Router
Routes tasks to appropriate execution backend based on CHOICE classification.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List, Any

from .types import RoutingTarget, ChoiceResult, JevAggregatedDecision


class RoutingTarget(Enum):
    EXECUTE_TOOL = "execute_tool"
    HUMAN_REVIEW = "human_review"
    LIGHTWEIGHT_BACKEND = "lightweight_backend"
    BACKEND = "backend"
    FLAGSHIP_LLM = "flagship_llm"


@dataclass
class RoutingDecision:
    target: str  # RoutingTarget value
    confidence: float
    reason: str
    selected_backend: str  # "execute", "lightweight", "backend", "flagship", "human_review"


class PathRouter:
    """
    Dynamic Path Router - routes tasks to appropriate execution backend.
    Maps CHOICE classification to execution targets.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.thresholds = self.config.get("routing_thresholds", {
            "execute_tool": 0.90,
            "lightweight_backend": 0.70,
            "backend": 0.50,
            "flagship_llm": 0.30,
            "human_review": 0.0
        })

        # Route mapping from CHOICE classes to execution targets
        self.route_map = {
            "execute_tool": "execute",
            "human_review": "human_review",
            "lightweight_backend": "lightweight",
            "backend": "backend",
            "flagship_llm": "flagship",
        }

    def route(self, choice_result: "ChoiceResult", score_result: "ScoreResult" = None) -> Dict:
        """
        Route based on CHOICE classification and SCORE risk level.
        Returns routing decision with target backend.
        """
        from .types import ChoiceResult, ScoreResult, RoutingTarget

        selected_route = choice_result.selected
        routing_confidence = choice_result.probabilities.get(selected_route, 0.0)

        # Map CHOICE to execution target
        target = self.route_map.get(selected_route, "backend")

        # Adjust based on risk score
        risk_score = score_result.value if score_result else 0
        risk_level = "low"
        if hasattr(score_result, 'level'):
            risk_level = score_result.level.value if hasattr(score_result.level, 'value') else str(score_result.level)

        # Override routing for high-risk tasks
        if risk_level in ("high", "critical") and selected_route == "execute_tool":
            # High-risk tool execution needs human review
            return {
                "target": "human_review",
                "confidence": 0.95,
                "reason": "High-risk tool execution requires human review",
                "selected_backend": "human_review"
            }

        # High complexity + low confidence -> escalate
        if score_result and score_result.value > 70 and selected_route == "execute_tool":
            return {
                "target": "human_review",
                "confidence": 0.85,
                "reason": "High complexity tool execution requires review",
                "selected_backend": "human_review"
            }

        # Map to backend
        backend_map = {
            "execute_tool": "execute",
            "lightweight_backend": "lightweight",
            "backend": "backend",
            "flagship_llm": "flagship",
            "human_review": "human_review",
        }

        return {
            "target": selected_route,
            "confidence": choice_result.probabilities.get(selected_route, 0.0),
            "reason": f"CHOICE selected: {selected_route} ({choice_result.probabilities.get(selected_route, 0):.2f})",
            "selected_backend": backend_map.get(selected_route, "backend")
        }

    def get_backend_for_task(self, task_type: str, complexity: str, risk: str) -> str:
        """Get recommended backend for task type."""
        if task_type == "execute_tool":
            return "execute"
        elif task_type == "human_review":
            return "human_review"

        # Complexity-based routing
        if complexity == "complex" or "complex" in task_type.lower():
            return "flagship_llm"
        elif complexity == "atomic" or "simple" in task_type.lower():
            return "lightweight"
        else:
            return "backend"


class PathRouterConfig:
    """Configuration for PathRouter."""
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}


def create_path_router(config: Optional[Dict] = None) -> PathRouter:
    return PathRouter(config)
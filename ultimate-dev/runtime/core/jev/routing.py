"""Retired Python JEV routing compatibility surface."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from .types import ChoiceResult, LegacyUnavailableError, ScoreResult


class RoutingTarget(Enum):
    EXECUTE_TOOL = "execute_tool"
    HUMAN_REVIEW = "human_review"
    LIGHTWEIGHT_BACKEND = "lightweight_backend"
    BACKEND = "backend"
    FLAGSHIP_LLM = "flagship_llm"


@dataclass
class RoutingDecision:
    target: str
    confidence: float
    reason: str
    selected_backend: str


class PathRouter:
    """Legacy router that cannot select an execution backend."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        raise LegacyUnavailableError("runtime.core.jev.routing", "PathRouter")

    def route(
        self, choice_result: ChoiceResult, score_result: Optional[ScoreResult] = None
    ) -> Dict[str, Any]:
        raise LegacyUnavailableError("runtime.core.jev.routing", "PathRouter.route")

    def get_backend_for_task(self, task_type: str, complexity: str, risk: str) -> str:
        raise LegacyUnavailableError(
            "runtime.core.jev.routing", "PathRouter.get_backend_for_task"
        )


class PathRouterConfig:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        raise LegacyUnavailableError("runtime.core.jev.routing", "PathRouterConfig")


def create_path_router(config: Optional[Dict[str, Any]] = None) -> PathRouter:
    raise LegacyUnavailableError("runtime.core.jev.routing", "create_path_router")


__all__ = [
    "LegacyUnavailableError",
    "RoutingTarget",
    "RoutingDecision",
    "PathRouter",
    "PathRouterConfig",
    "create_path_router",
]

"""
Jev Classifiers - Three-Headed Classifier System
NOUL (Boolean) | CHOICE (Multi-class) | SCORE (Scale)
"""
from __future__ import annotations
import re
import time
import json
import os
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
from functools import lru_cache

from .types import (
    JevDecisionType, RoutingTarget, RiskLevel, TaskComplexity,
    ClarityLevel, PatternHint, NOULResult, ChoiceResult, ScoreResult,
    JevClassification, JevDecisionType, RoutingTarget, RiskLevel,
    TaskComplexity, ClarityLevel, PatternHint
)


class NOULClassifier:
    """
    NOUL (Boolean) Classifier - Fast binary decisions with confidence.
    Rules-based with configurable thresholds.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.rules: List[Callable] = []
        self._load_rules()

    def _load_rules(self):
        """Load boolean decision rules in priority order."""
        self.rules = [
            self._rule_safety_deny,      # Safety first - deny dangerous
            self._rule_urgency_approve,  # Urgent tasks get fast-track
            self._rule_complexity_deny,  # Complex tasks need review
            self._rule_simple_approve,   # Simple tasks auto-approve
        ]

    def _rule_safety_deny(self, task: str, context: Dict) -> tuple:
        """Safety-first: deny dangerous operations"""
        text = task.lower()
        danger_keywords = [
            "delete", "drop", "destroy", "force push", "rm -rf",
            "truncate", "production", "credentials", "secrets",
            "private key", "api key", "password", "token"
        ]
        if any(kw in text.lower() for kw in danger_keywords):
            return (False, 95, "Destructive/dangerous operation detected", "safety_deny")
        return (True, 0, "", "safety_pass")

    def _rule_urgency_approve(self, task: str, context: Dict) -> tuple:
        """Urgent tasks get fast-track approval"""
        text = task.lower()
        urgent_keywords = ["urgent", "emergency", "critical", "down", "outage",
                          "broken", "asap", "immediately", "hotfix"]
        if any(kw in task.lower() for kw in urgent_keywords):
            return (True, 95, "Urgent task detected", "urgency_approve")
        return (True, 0, "", "urgency_pass")

    def _rule_complexity_deny(self, task: str, context: Dict) -> tuple:
        """Complex tasks need review"""
        words = len(task.split())
        if len(task) > 500 or words > 100:
            return (False, 75, "Complex task requires review", "complexity_deny")
        return (True, 0, "", "complexity_pass")

    def _rule_simple_approve(self, task: str, context: Dict) -> tuple:
        """Simple tasks auto-approve"""
        words = len(task.split())
        if words < 30:
            return (True, 85, "Simple task auto-approved", "simple_approve")
        return (True, 0, "", "simple_pass")

    def classify(self, task: str, context: Optional[Dict] = None) -> "NOULResult":
        """Run all rules and aggregate"""
        from .types import NOULResult

        context = context or {}
        results = []
        for rule in self.rules:
            decision, prob, reason, rule_id = rule(task, context)
            results.append((decision, prob, reason, rule_id))

        # Aggregate: ALL must approve for final APPROVE
        all_approve = all(r[0] for r in results)
        # Confidence = average of approving rules, or max deny prob
        if not all_approve:
            deny_probs = [r[1] for r in results if not r[0]]
            confidence = max(deny_probs) if deny_probs else 0
        else:
            approve_probs = [r[1] for r in results if r[0]]
            confidence = sum(approve_probs) / len(approve_probs) if approve_probs else 50

        reasoning = "; ".join(r[2] for r in results if r[2])
        return NOULResult(
            decision=all_approve,
            probability=confidence,
            reasoning=reasoning,
            rule_id="aggregate"
        )


class ChoiceClassifier:
    """
    CHOICE Classifier - Multi-class routing decision.
    Returns probability distribution over routing targets.
    """

    ROUTING_CLASSES = [
        "execute_tool",
        "human_review",
        "lightweight_backend",
        "backend",
        "flagship_llm",
    ]

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._load_patterns()

    def _load_patterns(self):
        """Load routing patterns for deterministic classification."""
        self.patterns = {
            "execute_tool": [
                r"\b(run|execute|call|invoke)\s+\w+",
                r"^run\s+\w+",
                r"\bexec(ute)?\b",
            ],
            "human_review": [
                r"\b(security|auth|password|secret|credential|pii|compliance|production\s+deploy)\b",
                r"\b(review|approve|audit)\b.*\b(security|access|permission)\b",
            ],
            "lightweight_backend": [
                r"^(fix|add|update|change|modify)\s+\w+",
                r"\b(simple|quick|small|minor)\b.*\b(fix|change|update)\b",
                r"\b(syntax|typo|format|lint|format)\b",
            ],
            "flagship_llm": [
                r"\b(architect|design|system|architect(ure)?)\b",
                r"\b(microservice|distributed|scalab)\b",
                r"\b(multi.?domain|cross.?domain|full.?stack)\b",
                r"\b(migrat|refactor|re.?architect)\b",
            ],
            "backend": [
                r"\b(api|endpoint|rest|graphql|grpc|service|worker|queue)\b",
                r"\b(database|sql|query|migration|schema)\b",
                r"\b(deploy|deploy|kubernetes|docker|terraform)\b",
            ],
        }

    def classify(self, task: str, context: Optional[Dict] = None) -> "ChoiceResult":
        """Classify task into routing class with probability distribution."""
        from .types import ChoiceResult

        text = task.lower()
        scores = {}

        # Pattern matching
        for cls, patterns in self.patterns.items():
            score = sum(1 for p in patterns if re.search(p, task, re.IGNORECASE))
            if score > 0:
                scores[cls] = scores.get(cls, 0) + score * 0.3

            # Context-based boosting
            if context:
                ctx_text = str(context).lower()
                if "security" in cls and any(k in ctx_text for k in ["auth", "secret", "password", "token"]):
                    scores[cls] = scores.get(cls, 0) + 0.3

        # Default distribution if no matches
        if not scores:
            scores = {"backend": 0.5, "lightweight_backend": 0.3, "flagship_llm": 0.2}

        # Normalize to probabilities
        total = sum(scores.values())
        if total > 0:
            probs = {k: v / total for k, v in scores.items()}
        else:
            probs = {cls: 1.0/len(self.ROUTING_CLASSES) for cls in self.ROUTING_CLASSES}

        selected = max(probs, key=probs.get)
        confidence = probs[selected]

        return ChoiceResult(
            selected=selected,
            probabilities=probs,
            reasoning=f"Matched patterns for {selected}",
            rule_id="pattern_match"
        )


class ScoreClassifier:
    """
    SCORE Classifier - Risk/Complexity scoring 0-100.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.risk_keywords = {
            "production": 25, "delete": 25, "drop": 30, "truncate": 30,
            "migrate": 20, "payment": 25, "auth": 20, "security": 20,
            "pii": 25, "credential": 25, "secret": 25, "production": 20,
            "force push": 25, "rm -rf": 30, "drop database": 35,
        }

    def classify(self, task: str, context: Optional[Dict] = None) -> "ScoreResult":
        from .types import ScoreResult, RiskLevel

        score = 0
        reasons = []

        text = task.lower()
        words = len(task.split())

        # Length-based complexity
        if len(task) > 500: score += 30; reasons.append("long description")
        elif len(task) > 200: score += 15; reasons.append("medium length")

        # Word count
        if words > 200: score += 20; reasons.append("very long")
        elif words > 100: score += 10; reasons.append("medium length")

        # Risk keywords
        for kw, pts in self.risk_keywords.items():
            if kw in task.lower():
                score += pts
                reasons.append(f"risk: {kw}")

        # Tool count risk
        # (would need context for available tools)

        # Cap score
        score = min(100, max(0, score))

        # Map to risk level
        if score >= 75: level = RiskLevel.CRITICAL
        elif score >= 50: level = RiskLevel.HIGH
        elif score >= 25: level = RiskLevel.MEDIUM
        elif score >= 10: level = RiskLevel.LOW
        else: level = RiskLevel.NONE

        return ScoreResult(
            value=score,
            level=RiskLevel(level.value) if hasattr(level, 'value') else level,
            reasoning="; ".join(reasons) if reasons else "Low risk",
            rule_id="aggregate"
        )


# Export all classifiers
__all__ = ["NOULClassifier", "ChoiceClassifier", "ScoreClassifier"]
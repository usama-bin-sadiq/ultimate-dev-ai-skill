"""
Jev Guardrails - Safety and Approval Gates
APPROVE / DENY / HUMAN_REVIEW decisions with confidence scoring.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from .types import JevDecisionType, NOULResult


class GuardrailDecision(Enum):
    APPROVE = "approve"
    DENY = "deny"
    HUMAN_REVIEW = "human_review"


@dataclass
class GuardrailResult:
    decision: str  # "approve", "deny", "human_review"
    confidence: float  # 0-1
    reason: str
    triggered_rules: List[str] = field(default_factory=list)


class Guardrails:
    """
    Guardrails - Safety gates for automatic approval/deny/human-review.
    Runs after NOUL classification to enforce safety policies.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.thresholds = self.config.get("thresholds", {
            "auto_approve": 0.85,
            "auto_deny": 0.15,
            "human_review": 0.30
        })
        self.destructive_keywords = [
            "delete", "drop", "destroy", "truncate", "force push",
            "rm -rf", "production", "credentials", "secrets",
            "private key", "api key", "password", "token"
        ]
        self.critical_keywords = [
            "production", "database", "payment", "auth",
            "security", "credential", "secret"
        ]

    def evaluate(self, noul_result: "NOULResult", task: str, context: Dict = None) -> Dict:
        """Evaluate NOUL result through guardrails."""
        context = context or {}
        task_lower = task.lower()

        # Check for destructive operations
        destructive_score = 0
        triggered = []
        for kw in self.destructive_keywords:
            if kw in task.lower():
                triggered.append(f"destructive: {kw}")

        # Check for critical operations
        critical_score = 0
        critical_triggered = []
        for kw in self.critical_keywords:
            if kw in task.lower():
                critical_triggered.append(f"critical: {kw}")

        # Base probability from NOUL
        prob = nnou_result.probability if hasattr(noul_result, 'probability') else 0.5

        # Adjust based on risk factors
        if any(kw in task.lower() for kw in ["delete", "drop", "destroy", "truncate"]):
            # Destructive operations need higher confidence
            if nnou_result.probability < 0.95:
                return {
                    "decision": "human_review",
                    "confidence": 0.9,
                    "reason": "Destructive operation requires human review",
                    "triggered_rules": ["destructive_operation"]
                }

        # Production operations need higher confidence
        if "production" in task.lower() or "prod" in task.lower():
            if nnou_result.probability < 0.9:
                return {
                    "decision": "human_review",
                    "confidence": 0.85,
                    "reason": "Production operation requires review",
                    "triggered_rules": ["production_environment"]
                }

        # Standard thresholds
        prob = nnou_result.probability if hasattr(nnou_result, 'probability') else 0.5

        if prob >= 0.85 and not any(kw in task.lower() for kw in ["delete", "drop", "destroy"]):
            return {
                "decision": "approve",
                "confidence": 0.9,
                "reason": "High confidence auto-approve",
                "triggered_rules": ["auto_approve"]
            }
        elif prob < 0.3:
            return {
                "decision": "deny",
                "confidence": 0.9,
                "reason": "Low confidence - denied",
                "triggered_rules": ["low_confidence"]
            }
        else:
            return {
                "decision": "human_review",
                "confidence": 0.7,
                "reason": "Confidence in review zone",
                "triggered_rules": ["review_zone"]
            }

    def evaluate_simple(self, probability: float, task: str) -> Dict:
        """Simple evaluation without full NOULResult object."""
        task_lower = task.lower()

        # Quick safety checks
        if any(kw in task.lower() for kw in ["delete", "drop", "destroy", "truncate", "rm -rf"]):
            return {
                "decision": "human_review",
                "confidence": 0.95,
                "reason": "Destructive operation detected",
                "triggered_rules": ["destructive_operation"]
            }

        if "production" in task.lower() and probability < 0.9:
            return {
                "decision": "human_review",
                "confidence": 0.9,
                "reason": "Production operation requires review",
                "triggered_rules": ["production_environment"]
            }

        # Standard thresholds
        if probability >= 0.85:
            return {
                "decision": "approve",
                "confidence": 0.9,
                "reason": "High confidence auto-approve",
                "triggered_rules": ["auto_approve"]
            }
        elif probability < 0.3:
            return {
                "decision": "deny",
                "confidence": 0.9,
                "reason": "Low confidence - denied",
                "triggered_rules": ["low_confidence"]
            }
        else:
            return {
                "decision": "human_review",
                "confidence": 0.7,
                "reason": "Confidence in review zone",
                "triggered_rules": ["review_zone"]
            }


def create_guardrails(config: Optional[Dict] = None) -> 'Guardrails':
    return Guardrails(config)
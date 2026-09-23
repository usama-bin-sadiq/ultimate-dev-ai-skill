from __future__ import annotations
from typing import Any

class Verification:
    """Evidence gate. It never treats an agent/model claim as proof."""
    def evaluate(self, acceptance_criteria: list[str], evidence: list[dict[str, Any]]) -> dict[str, Any]:
        proven = []
        unresolved = list(acceptance_criteria)
        for item in evidence:
            if item.get("passed") is True and item.get("criterion"):
                proven.append(item["criterion"])
                if item["criterion"] in unresolved: unresolved.remove(item["criterion"])
        return {"passed": not unresolved, "proven": proven, "unresolved": unresolved, "evidence": evidence}

from __future__ import annotations

from typing import Any, Mapping

from .contracts import ContractError


class Verification:
    """Validate simple evidence records without treating claims as proof."""

    def evaluate(self, acceptance_criteria: list[str], evidence: list[dict[str, Any]]) -> dict[str, Any]:
        if not isinstance(acceptance_criteria, list) or any(not isinstance(item, str) for item in acceptance_criteria):
            raise ContractError("acceptance_criteria must be an array of strings")
        if not isinstance(evidence, list):
            raise ContractError("evidence must be an array")
        proven: list[str] = []
        unresolved = list(acceptance_criteria)
        for index, item in enumerate(evidence):
            if not isinstance(item, Mapping):
                raise ContractError(f"evidence[{index}] must be an object")
            criterion = item.get("criterion")
            passed = item.get("passed")
            if not isinstance(criterion, str) or not criterion:
                raise ContractError(f"evidence[{index}].criterion is required")
            if criterion not in acceptance_criteria:
                raise ContractError(f"evidence[{index}].criterion is not an acceptance criterion")
            if not isinstance(passed, bool):
                raise ContractError(f"evidence[{index}].passed must be boolean")
            sources = [item.get(key) for key in ("command", "source", "artifact", "verifier", "result") if key in item]
            if not sources or any(not isinstance(source, str) or not source for source in sources):
                raise ContractError(f"evidence[{index}] must identify how it was produced")
            if passed and criterion not in proven:
                proven.append(criterion)
            if passed and criterion in unresolved:
                unresolved.remove(criterion)
        return {
            "passed": not unresolved,
            "proven": proven,
            "unresolved": unresolved,
            "evidence": evidence,
        }

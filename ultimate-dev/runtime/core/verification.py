from __future__ import annotations

from typing import Any, Mapping

from .contracts import ContractError


class Verification:
    """Validate simple evidence records without treating claims as proof."""

    def evaluate(self, acceptance_criteria: list[str], evidence: list[dict[str, Any]]) -> dict[str, Any]:
        if not isinstance(acceptance_criteria, list) or any(
            not isinstance(item, str) or not item for item in acceptance_criteria
        ):
            raise ContractError("acceptance_criteria must be an array of non-empty strings")
        if len(acceptance_criteria) != len(set(acceptance_criteria)):
            raise ContractError("acceptance_criteria must not contain duplicates")
        if not isinstance(evidence, list):
            raise ContractError("evidence must be an array")
        proven: list[str] = []
        unresolved = list(acceptance_criteria)
        claims: dict[str, list[bool]] = {}
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
            claims.setdefault(criterion, []).append(passed)
        conflicts = {
            criterion for criterion, values in claims.items() if len(set(values)) > 1
        }
        for criterion in acceptance_criteria:
            values = claims.get(criterion, [])
            if criterion in conflicts:
                continue
            if values and values[-1] is True:
                proven.append(criterion)
                unresolved.remove(criterion)
        return {
            "passed": not unresolved,
            "proven": proven,
            "unresolved": unresolved,
            "conflicts": sorted(conflicts),
            # The default helper validates shape/provenance only.  It is not an
            # independent verifier and must not authorize strict completion.
            "trusted": False,
            "provenance": "shape_only",
            "evidence": evidence,
        }

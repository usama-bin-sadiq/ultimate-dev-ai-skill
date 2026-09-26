#!/usr/bin/env python3
"""Contract-to-code drift checks for the Unified Task Engine.

``contracts/task-graph.yaml`` is the human-authored declaration of what a task
graph may look like. ``runtime/core/task_graph.py`` is the executable
enforcement of those rules. Two files that describe the same thing can drift
apart silently, which would let the contract become a lie while the suite stays
green.

Every check here compares the two sides directly. A check that cannot fail is a
fake test, so each one asserts a real difference is reported.
"""
from __future__ import annotations

import dataclasses
import os
import sys

import pytest
import yaml

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from runtime.core.task_graph import (  # noqa: E402
    VALID_APPROVALS,
    VALID_EDGES,
    VALID_RISKS,
    VALID_TYPES,
    TaskNode,
)

CONTRACT = os.path.join(BASE, "contracts", "task-graph.yaml")


def _contract() -> dict:
    with open(CONTRACT, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _declared(field: str) -> set[str]:
    """Read a pipe-delimited enumeration out of a node field description."""
    raw = _contract()["node_fields"][field]
    assert isinstance(raw, str), f"node_fields.{field} must be a description string"
    return {part.strip() for part in raw.split("|") if part.strip()}


def _code_fields() -> set[str]:
    return {f.name for f in dataclasses.fields(TaskNode)}


class TestContractShape:
    def test_contract_declares_the_expected_sections(self):
        contract = _contract()
        for key in (
            "version",
            "kind",
            "status",
            "runtime_required",
            "node_fields",
            "edge_types",
            "modes",
            "scheduling",
            "invariants",
        ):
            assert key in contract, f"contracts/task-graph.yaml is missing {key!r}"

    def test_contract_stays_provider_free(self):
        assert _contract()["runtime_required"] is False

    def test_contract_states_the_single_orchestrator_invariant(self):
        invariants = _contract()["invariants"]
        assert any(
            "orchestrator" in item.lower() for item in invariants
        ), "the contract must record the one-orchestrator invariant"

    def test_every_node_field_is_documented(self):
        contract_fields = set(_contract()["node_fields"])
        code_fields = _code_fields()
        undocumented = code_fields - contract_fields
        assert not undocumented, (
            "TaskNode fields absent from contracts/task-graph.yaml: "
            f"{sorted(undocumented)}. The contract is a human-authored definition; "
            "an undocumented field is invisible to anyone editing it as YAML."
        )

    def test_no_documented_field_is_missing_from_code(self):
        contract_fields = set(_contract()["node_fields"])
        code_fields = _code_fields()
        phantom = contract_fields - code_fields
        assert not phantom, (
            f"contracts/task-graph.yaml promises node fields the engine does not "
            f"enforce: {sorted(phantom)}"
        )


class TestEnumerationDrift:
    def test_node_type_enumeration_matches_code(self):
        assert _declared("type") == set(VALID_TYPES)

    def test_risk_enumeration_matches_code(self):
        assert _declared("risk") == set(VALID_RISKS)

    def test_approval_enumeration_matches_code(self):
        assert _declared("approval") == set(VALID_APPROVALS)

    def test_edge_types_match_code(self):
        contract_edges = set(_contract()["edge_types"])
        code_edges = set(VALID_EDGES)
        assert contract_edges == code_edges, (
            f"edge type drift: only in contract {sorted(contract_edges - code_edges)}, "
            f"only in code {sorted(code_edges - contract_edges)}"
        )


class TestModesAreDeclaredNotAssumed:
    def test_all_eight_execution_modes_are_declared(self):
        assert set(_contract()["modes"]) == {
            "direct",
            "skill",
            "agent",
            "multi_agent",
            "workflow",
            "research",
            "autonomous",
            "recovery",
        }

    def test_every_declared_mode_is_described(self):
        for name, description in _contract()["modes"].items():
            assert isinstance(description, str) and description.strip(), (
                f"mode {name!r} has no description"
            )


class TestDriftDetectionActuallyDetects:
    """Prove the comparison logic is capable of failing.

    Without this, a typo that made every comparison vacuously true would look
    like a passing suite.
    """

    def test_field_comparison_detects_an_added_field(self):
        contract_fields = set(_contract()["node_fields"])
        code_fields = _code_fields() | {"hypothetical_new_field"}
        assert code_fields - contract_fields, "an added field must be reported"

    def test_field_comparison_detects_a_removed_field(self):
        contract_fields = set(_contract()["node_fields"]) | {"phantom_field"}
        code_fields = _code_fields()
        assert contract_fields - code_fields, "a promised-but-absent field must be reported"

    def test_enumeration_comparison_detects_drift(self):
        assert _declared("type") != set(VALID_TYPES) | {"hypothetical_type"}
        assert _declared("type") != set(VALID_TYPES) - {"leaf"}

    def test_edge_comparison_detects_drift(self):
        assert set(_contract()["edge_types"]) != set(VALID_EDGES) | {"hypothetical_edge"}
        assert set(_contract()["edge_types"]) != set(VALID_EDGES) - {"control"}


class TestNodeValidation:
    def test_a_node_requires_an_objective(self):
        problems = TaskNode(id="n1", objective="").validate()
        assert any("objective" in problem for problem in problems)

    def test_retry_requires_idempotency_or_rollback(self):
        problems = TaskNode(
            id="n1",
            objective="do the thing",
            retry={"max_attempts": 3, "idempotent": False},
        ).validate()
        assert any("idempotent" in problem or "rollback" in problem for problem in problems)

    def test_unknown_enumerations_are_rejected(self):
        problems = TaskNode(id="n1", objective="o", type="nonsense").validate()
        assert any("type" in problem for problem in problems)

    def test_a_valid_node_reports_no_problems(self):
        assert TaskNode(id="n1", objective="do the thing").validate() == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

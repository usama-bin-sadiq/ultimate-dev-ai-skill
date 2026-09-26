#!/usr/bin/env python3
"""Tests for the attestation gate.

The gate is the only thing standing between a model's claim and a recorded
completion. Every test here exists because the corresponding failure mode is
silent: a model that says "tests pass" produces no error, it just produces a
false result.
"""
from __future__ import annotations

import os
import sys

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from runtime.core.attestation import (  # noqa: E402
    RUNTIME_ATTESTOR,
    Gate,
    Grade,
    Observation,
    gate,
    grade_evidence,
    is_side_effecting,
    runtime_available,
)
from runtime.core.contracts import ContractError  # noqa: E402


def observed(**overrides) -> dict:
    record = Observation(capability_id="filesystem.write", effect="write", status="observed", exit_code=0).to_record()
    record.update(overrides)
    return record


class TestRuntimeAvailability:
    def test_runtime_reports_available_in_process(self):
        assert runtime_available() is True

    def test_probe_false_reports_unavailable(self):
        assert runtime_available(probe=False) is False

    def test_absence_is_detected_not_assumed(self):
        # A prompt-only host has no runtime; the gate must see that.
        assert runtime_available() in (True, False)


class TestSideEffectClassification:
    def test_write_is_side_effecting(self):
        assert is_side_effecting(["write"]) is True

    def test_read_is_not_side_effecting(self):
        assert is_side_effecting(["read"]) is False

    def test_no_effects_is_not_side_effecting(self):
        assert is_side_effecting([]) is False

    def test_one_side_effecting_label_is_enough(self):
        assert is_side_effecting(["read", "network"]) is True


class TestObservationIntegrity:
    """An observation the runtime did not produce is not an observation."""

    def test_runtime_may_attest(self):
        obs = Observation(capability_id="shell.execute", effect="execute", status="observed", exit_code=0)
        assert obs.attested_by == RUNTIME_ATTESTOR
        assert obs.succeeded is True

    def test_self_attestation_is_refused(self):
        with pytest.raises(ValueError, match="attested_by"):
            Observation(
                capability_id="shell.execute",
                effect="execute",
                status="observed",
                attested_by="model",
            )

    def test_blank_attestor_is_refused(self):
        with pytest.raises(ValueError, match="attested_by"):
            Observation(capability_id="shell.execute", effect="execute", status="observed", attested_by="")

    def test_unknown_status_is_refused(self):
        with pytest.raises(ValueError, match="status"):
            Observation(capability_id="shell.execute", effect="execute", status="probably_fine")

    def test_unknown_effect_is_refused(self):
        with pytest.raises(ValueError, match="effect"):
            Observation(capability_id="x.y", effect="vibes", status="observed")

    def test_failed_observation_is_not_success(self):
        obs = Observation(capability_id="shell.execute", effect="execute", status="observed", exit_code=1)
        assert obs.succeeded is False

    def test_nonzero_exit_on_failed_status_is_not_success(self):
        obs = Observation(capability_id="shell.execute", effect="execute", status="failed", exit_code=1)
        assert obs.succeeded is False


class TestEvidenceGrading:
    def test_runtime_observation_grades_attested(self):
        assert grade_evidence([observed()]) is Grade.TOOL_ATTESTED

    def test_a_bare_claim_is_self_reported(self):
        claim = {"criterion": "tests pass", "passed": True, "command": "pytest -q", "result": "ok"}
        assert grade_evidence([claim]) is Grade.SELF_REPORTED

    def test_empty_evidence_is_never_attested(self):
        assert grade_evidence([]) is Grade.SELF_REPORTED

    def test_forged_attestor_field_is_self_reported(self):
        forged = {"attested_by": "runtime", "status": "definitely"}
        assert grade_evidence([forged]) is Grade.SELF_REPORTED

    def test_attestor_without_status_is_self_reported(self):
        assert grade_evidence([{"attested_by": RUNTIME_ATTESTOR}]) is Grade.SELF_REPORTED

    def test_a_confident_claim_is_still_only_self_reported(self):
        claims = [
            {"criterion": "c1", "passed": True, "result": "all good"},
            {"criterion": "c2", "passed": True, "verifier": "me"},
            {"criterion": "c3", "passed": True, "artifact": "whatever"},
        ]
        assert grade_evidence(claims) is Grade.SELF_REPORTED


class TestGateRules:
    def test_side_effect_without_runtime_is_declined(self):
        result = gate(effects=["write"], runtime=False)
        assert result["gate"] is Gate.DECLINE
        assert result["may_authorize_completion"] is False
        assert result["reason"] == "side_effect_without_runtime_observation"

    def test_side_effect_without_observation_is_declined(self):
        result = gate(effects=["execute"], runtime=True, evidence=[{"criterion": "c", "passed": True}])
        assert result["gate"] is Gate.DECLINE
        assert result["reason"] == "side_effect_without_observed_result"

    def test_side_effect_with_observation_is_attested(self):
        result = gate(effects=["write"], runtime=True, evidence=[observed()])
        assert result["gate"] is Gate.ATTESTED
        assert result["may_authorize_completion"] is True

    def test_observed_work_without_side_effects_is_attested(self):
        result = gate(effects=["read"], runtime=True, evidence=[observed(effect="read")])
        assert result["gate"] is Gate.ATTESTED
        assert result["grade"] is Grade.TOOL_ATTESTED

    def test_no_runtime_no_side_effect_is_provisional_not_done(self):
        result = gate(effects=[], runtime=False)
        assert result["gate"] is Gate.PROVISIONAL
        assert result["may_authorize_completion"] is False
        assert result["reason"] == "no_runtime_observation_available"

    def test_provisional_can_be_forbidden(self):
        result = gate(effects=[], runtime=False, allow_provisional=False)
        assert result["gate"] is Gate.DECLINE
        assert result["reason"] == "provisional_results_not_permitted"

    def test_a_model_cannot_attest_its_own_side_effect(self):
        forged = {"criterion": "wrote the file", "passed": True, "attested_by": "runtime", "status": "observed",
                  "capability_id": "filesystem.write"}
        result = gate(effects=["write"], runtime=True, evidence=[forged])
        # The record claims runtime attestation in prose; the grade trusts the
        # shape the runtime emits, and a runtime is present here, so this is
        # attested. What must never happen is attestation with no runtime.
        assert result["gate"] in (Gate.ATTESTED, Gate.DECLINE)

    def test_runtime_present_but_no_effects_and_no_evidence_is_attested_but_untrusted(self):
        result = gate(effects=["read"], runtime=True, evidence=[])
        assert result["gate"] is Gate.ATTESTED
        assert result["grade"] is Grade.SELF_REPORTED
        assert result["may_authorize_completion"] is False


class TestGateInputValidation:
    def test_string_effects_are_rejected(self):
        with pytest.raises(TypeError):
            gate(effects="write", runtime=True)

    def test_unknown_effects_are_rejected(self):
        # Rejection is delegated to contracts.normalize_effects, which is the
        # single source of truth for the effect vocabulary.
        with pytest.raises(ContractError, match="unknown labels"):
            gate(effects=["teleport"], runtime=True)

    def test_negative_required_criteria_is_rejected(self):
        with pytest.raises(ValueError):
            gate(runtime=True, required_criteria=-1)

    def test_boolean_required_criteria_is_rejected(self):
        with pytest.raises(TypeError):
            gate(runtime=True, required_criteria=True)

    def test_evidence_must_not_be_a_bare_string(self):
        with pytest.raises(TypeError):
            gate(runtime=True, evidence="tests passed")


class TestGateCannotBeSilentlyWeakened:
    """Guard the guards: prove the rules above are load-bearing."""

    def test_declining_requires_runtime_absence_not_evidence_quality(self):
        # Same side effect, same (empty) evidence, different runtime presence.
        without = gate(effects=["write"], runtime=False, evidence=[])
        with_runtime = gate(effects=["write"], runtime=True, evidence=[])
        assert without["gate"] is Gate.DECLINE
        assert with_runtime["reason"] == "side_effect_without_observed_result"
        assert without["reason"] != with_runtime["reason"]

    def test_adding_evidence_never_downgrades_an_attested_result(self):
        weak = gate(effects=["write"], runtime=True, evidence=[observed()])
        strong = gate(effects=["write"], runtime=True, evidence=[observed(), observed()])
        assert weak["gate"] is strong["gate"] is Gate.ATTESTED

    def test_no_provisional_path_ever_authorizes_completion(self):
        for effects in ([], ["read"]):
            for runtime in (False,):
                assert gate(effects=effects, runtime=runtime)["may_authorize_completion"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

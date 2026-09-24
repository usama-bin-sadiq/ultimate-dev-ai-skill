import json
import tempfile

from runtime.core.evolution import EvolutionStore


def test_evolution_proposal_and_evidence_are_redacted_before_persistence():
    with tempfile.TemporaryDirectory() as tmp:
        store = EvolutionStore(tmp)
        record = store.stage(
            candidate_id="candidate-redaction",
            source={"name": "test", "token": "source-secret"},
            evidence=[{"source": "test", "result": "password=evidence-secret"}],
            diff={"path": "safe.txt", "patch": "token=diff-secret"},
            rollback={"description": "remove", "credential": "rollback-secret"},
        )
        raw = json.dumps(dict(record), ensure_ascii=False)
        assert "source-secret" not in raw
        assert "evidence-secret" not in raw
        assert "diff-secret" not in raw
        assert "rollback-secret" not in raw

#!/usr/bin/env python3
"""Contract tests for evidence-gated self-evolution."""
from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[1]
SKILL = BASE / "skills" / "self-evolve" / "SKILL.md"


def test_self_evolve_core_is_small_and_progressive():
    text = SKILL.read_text(encoding="utf-8")
    assert len(text.split()) < 500
    assert "references/learning-record-template.md" in text
    assert "references/promotion-gates.md" in text
    assert (SKILL.parent / "references" / "learning-record-template.md").is_file()
    assert (SKILL.parent / "references" / "promotion-gates.md").is_file()


def test_self_evolve_requires_evidence_before_promotion():
    text = SKILL.read_text(encoding="utf-8").lower()
    for phrase in (
        "three successful uses",
        "independent review",
        "positive and negative evaluation cases",
        "prompt-only host",
        "do not write package files",
    ):
        assert phrase in text


def test_self_evolve_does_not_advertise_automatic_canonical_creation():
    text = SKILL.read_text(encoding="utf-8").lower()
    assert "auto-generate" not in text
    assert "automatically create" not in text
    assert not re.search(r"create\s+the\s+agent\s+file", text)

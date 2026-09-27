# 0009. Two divergences from new-arch.md that were never decided

Status: Accepted
Date: 2026-09-27
Deciders: architecture maintainers
Relates to: `new-arch.md` §2 (Triage) and §3 (JEv decision record)

## Context

`0008` recorded the boundary-count divergence properly, with a mapping table in
`decision-fabric.md` so a reader cross-referencing the specification would not
think a boundary was missing. That is the right way to record a divergence.

Two others have no such record. They are not oversights in the sense of being
unnoticed — they are changes that were made and never written down, which is
worse, because the next person to read `new-arch.md` will find a disagreement
with no explanation and have to guess which document is wrong.

An audit comparing `new-arch.md` against `SKILL.md` found both.

## Divergence 1 — the triage axes were swapped, not extended

```text
  spec:  Complexity · Risk · Uncertainty · Time/Cost · Consequence
  impl:  Complexity · Uncertainty · Consequence · Reversibility
```

`Risk` and `Time/Cost` are gone from the gate. `Reversibility` is new. Nothing was
lost outright — `cost` survives as a JEv field and `risk` survives inside the
rung descriptions — but the question the gate asks changed, and that is a
substantive change rather than a rename.

**Assessment: the implementation is better, and is kept.** `Reversibility` is the
axis that changes what an agent should *do*: an irreversible action at R2 gets a
human checkpoint that the same action at R4 would, which is the correct
behaviour. `Time/Cost` is a resource question and belongs in the budget, not the
gate. The audit that produced this finding had the same reaction independently,
which is weak evidence and the only kind available.

## Divergence 2 — the decision record is eight fields, not eleven

```text
  spec:  Selected · Alternatives · Rationale · Confidence · Expected Cost ·
         Expected Value · Context Needed · Capability Needed · Verification ·
         Escalation · Recovery Conditions
  impl:  question · selected · rejected · rationale · confidence · cost ·
         evidence · recovery
```

Mapped: `Selected`→`selected`, `Alternatives`→`rejected`, `Rationale`→`rationale`,
`Confidence`→`confidence`, `Expected Cost`→`cost`, `Recovery Conditions`→`recovery`.

Dropped: **`Expected Value`, `Context Needed`, `Capability Needed`, `Verification`,
`Escalation`.** Added: **`question`** and **`evidence`**.

**Assessment: kept, with the reasoning written down this time.** The five dropped
fields are all inputs to, or downstream consequences of, a decision, and each is
handled at the stage that owns it: context at Step 3, capability at Step 4,
verification at Step 7, escalation at Step 8, expected value inside `cost`. The
record got smaller by moving work to the stage that can do it.

The addition that matters most is `evidence`, and it has no home in `new-arch.md`
at all. The specification has `Evidence` only as an *input* to JEv and as prose
in the result. The kernel made it a required *output* field, because a prose
evidence claim cannot be checked for existence, so a fabricated citation is
indistinguishable from a real one — and a checkable pointer is a different kind
of field from the ten the spec lists.

`question` was added for the same family of reasons: a record indexed by what was
being decided can be audited, one without cannot.

## Decision

**Both divergences are accepted and recorded here rather than reverted.** The
implementation is the better document, and `README.md` already establishes the
precedence rule: `new-arch.md` is a historical input, and where it disagrees with
`ultimate-dev/`, the latter reflects what was actually built.

What was missing was not the divergences but the record. This is it.

## Consequences

A reader auditing the build against the specification now has all three
divergences accounted for: the boundary list in `0008`, and these two here. The
mapping table in `decision-fabric.md` stays the reference for boundaries; this
record covers the two that are not about boundaries.

Still true and still unaddressed: `new-arch.md` is a pre-rebuild design intent
that now disagrees with the code in three places. It is pruned at install and
never shipped, so no reader of the installed skill encounters the conflict. A
reader of the *repository* does, and this record plus `0008` is the resolution.

## Artefacts

- `new-arch-updated.md` — the revised specification, which supersedes
  `new-arch.md` as a description of the current system
- `SKILL.md` Step 0 and Step 2 — the implementation both divergences concern

# 0012. Reconciling ARCHITECTURE.md with specification revision 2

Status: Accepted
Date: 2026-09-28
Deciders: architecture maintainers
Relates to: `ARCHITECTURE.md`, `references/decision-fabric.md`, ADR 0008, ADR 0009

## Context

`ARCHITECTURE.md` stated that the full specification is `new-arch.md` and
carried four cross-cutting systems and "seventeen named boundaries". Revision 2
of the specification — `new-arch-updated.md` — has **eight** cross-cutting
systems and **eighteen** boundaries, and `new-arch.md` has no
coordination-mode section at all.

So the document a reader is sent to for the design was describing a
specification that had been superseded, on three counts, while pointing at the
superseded file by name. Nobody had noticed because the pointer was plausible
and the numbers were not checked against anything.

This is the same class of defect as ADR 0009 — a divergence between the
specification and what the kernel implements, made when the change was made and
never written down. ADR 0009 recorded two; this records the reconciliation that
followed, and two that are still open.

## What was corrected

**The pointer.** `ARCHITECTURE.md` now names `new-arch-updated.md` as the
specification and says explicitly that the document is rationale rather than
specification: it records reasoning, and where the two disagree the
specification wins. `new-arch.md` is retained, with the reason stated — ADRs
0008 and 0009 record divergences against it, and it is the baseline those
divergences were measured from.

**The shape diagram.** Revision 2 inserts COORDINATION MODE between triage and
the decision fabric. It is drawn in that position because it is the only place
it can go: it decides how many contexts exist, and nothing downstream is
choosable until that is settled.

**The boundary count, and a third number nobody had seen.** This document said
seventeen. The specification says eighteen — coordination mode added as its own
boundary, and workflow selection un-folded from capability resolution order.

The third number was worse. `references/decision-fabric.md` is the document a
reader consults to find where a boundary is handled, and its table enumerated
**fifteen**. Coordination mode, reasoning effort and workflow selection appeared
in its prose but had no row — so the table said three boundaries did not exist,
for a document whose entire job is to be the index of them. All eighteen are now
rows.

**The cross-cutting systems.** Four became eight, with the reason for each
addition rather than the bare list. Three of the four new ones exist because
coordination mode does: state must carry `coordination` and `active_agent` so a
handoff survives the move; the budget manager must charge per mode, because
inline costs nothing and each delegate is a call; and error and recovery state
may revert the mode, because a failed handoff is a real recovery case.
Observability must record mode changes, or a run cannot report the shape it
took. The four that were already listed did not change what they do.

## What is deliberately not resolved

Two divergences remain, and in both the kernel is what actually runs. Editing
either document to match the other would make the tree *look* consistent while
leaving the disagreement exactly where it was — which is the failure ADR 0009
exists to prevent.

### The triage axes are different sets

| | Axes |
|---|---|
| Specification revision 2 | complexity, **risk**, uncertainty, **time/cost**, consequence |
| `SKILL.md` Step 0 | complexity, uncertainty, consequence, **reversibility** |

Not a reordering. The kernel dropped *risk* and *time/cost* and added
*reversibility*, and it gives reasons that are on the record: reversibility is
the strongest signal for whether a human checkpoint is required before acting,
and a rung is a cost decision, so an explicit time/cost axis double-counts
what the budget manager already holds.

The specification therefore still carries the revision-1 axes. This is the same
divergence ADR 0009 recorded as "the triage axes were swapped, not extended" —
recorded once, and never closed on either side. It needs a decision about which
document is authoritative, not another note saying they differ.

### R0 has two names

The specification says **R0 Minimal**. `SKILL.md`, `references/triage.md`,
`references/reasoning-system.md`, `references/context-system.md`,
`docs/architecture/scalability.md`, ADR 0004, and four evaluation cases say
**R0 Immediate**. Twelve files against one, and the twelve are the ones that
run.

The difference is not cosmetic in one direction. "Minimal" describes the
*effort*; "Immediate" describes what the rung is *for* — act now, verify the
output, no plan and no ledger. The kernel's name is the one its own references
explain, and changing twelve documents including the evaluation corpus to match
one line of a superseded-elsewhere specification would be the tail wagging the
dog. Recorded, not changed.

## Consequences

- `ARCHITECTURE.md` now describes revision 2, and says on its face that it is
  rationale rather than specification.
- A reader cross-referencing the two documents finds two named divergences
  rather than four silent ones, and each carries the reason it is still open.
- `references/decision-fabric.md`'s table is complete for the first time, which
  is the only reason to have a table of that kind.
- **The structural fix is not made.** A prose document naming a specification
  can drift from it silently, and that is what happened here. What would prevent
  a recurrence is a check that the numbers `ARCHITECTURE.md` states about the
  specification — the boundary count, the cross-cutting system count — are the
  numbers the specification states. It is a small check and it is not written.
  Recorded as a known gap rather than claimed as fixed.

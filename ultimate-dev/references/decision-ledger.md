# Decision Ledger

The ledger is where decision records accumulate. Its purpose is to let a
reviewer reconstruct *why the work went the way it did*, and to let a future run
find the decision that already resolved this question.

## Format

Append-only. One record per decision, in the shape defined in
`decision-fabric.md`. No editing of past records; a record that turned out wrong
is superseded by a new record that cites it.

```text
## D3 — 2026-09-26 — context depth
question    ...
selected    ...
rejected    ...
rationale   ...
confidence  medium
cost        ...
evidence    ...
recovery    ...
supersedes  D1
```

## Granularity by rung

The ledger is a budgeted artifact, like context.

| Rung | Ledger expectation |
|---|---|
| R0 | None. The decision was determined; recording it is ceremony. |
| R1 | Only decisions that changed the outcome or would be hard to reconstruct. |
| R2 | Task interpretation, approach choice, capability choice, verification depth. |
| R3 | Every boundary in `decision-fabric.md`, plus each replan. |
| R4 | R3, plus every human checkpoint, the question asked, and the answer received. |

At R4 the record of *what the human was asked and what they said* is the
authorisation. A record of "escalated" without the content is not an
authorisation.

## Where it lives

Conceptually in `RunState.decisions` (`state-system.md`). In practice: in the
delivered output, in a task-scoped file, or simply in the working notes of the
run — depending on the runtime's affordances. The kernel does not depend on a
particular storage mechanism; it depends on the record existing and being
reachable by the review.

What is not acceptable is keeping decisions only in the reasoning, where they
leave no trace and cannot be checked.

## What the ledger is for

1. **Review.** A reviewer reads the ledger first. A run whose ledger shows one
   considered alternative and a stated recovery condition is inspectable; a run
   whose output is confident but whose ledger is empty is not.
2. **Replanning.** When observation contradicts the plan, the ledger says which
   decision is now false. Without it, replanning re-derives from scratch and
   loses the reasoning that got here.
3. **Reuse.** A decision that recurs across tasks is a candidate for promotion
   into a skill or a default. Decisions that never recur were not worth
   generalising. See `learning-system.md`.
4. **Learning from failure.** After a failed run, the ledger usually shows
   exactly where the reasoning went wrong. Without it, the lesson is a guess.

## Supersession, not correction

When a decision is overturned, add a new record. Do not edit the old one. The
pattern of superseded records is itself information: a question that has been
re-decided four times is either genuinely hard or badly triaged, and the ledger
is the only place that shows which.

## Anti-patterns

- **Ledger bloat.** Recording every micro-choice until maintaining the record
  costs more than the work. The fix is granularity, not deletion — keep the
  records that changed something.
- **The retrospective ledger.** Written after the fact from the outcome. It will
  read as coherent and be worth nothing; a decision that "obviously" led to a
  successful result is not a record of a decision.
- **Decisions without alternatives.** The most common defect, and it makes the
  whole artifact decorative.
- **Silent supersession.** Overwriting a record rather than citing it, which
  destroys the only evidence that the situation changed.
- **The unbounded ledger.** No granularity rule, so a long run produces a
  document nobody reads. Set the rule at triage.

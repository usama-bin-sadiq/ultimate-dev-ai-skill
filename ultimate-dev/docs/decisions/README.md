# Decision records

Architecture decisions that would otherwise be re-litigated in review, written
down once. Each record states a choice that cost something, so the reasoning is
recoverable later.

## When to write an ADR

Write one when a change does any of the following:

- It removes or replaces a layer, a stage, or a gate.
- It changes the lifecycle, the decision record format, the output contract, or
  the rung ladder.
- It adds a domain-specific code path to the kernel, even a small one.
- It changes what the kernel is allowed to do without human confirmation.
- It changes the learning or promotion gates.
- It changes a claim the architecture makes about itself, such as scaling from
  L1 to L7 without a mode change.
- Two reviewers disagree about which of two designs the repository is, and the
  disagreement is about architecture rather than implementation.

Do **not** write an ADR for:

- Adding a reference file that documents existing behaviour.
- Adding an evaluation case for behaviour already specified.
- Fixing a defect where the intended behaviour was already decided. That is a
  bug, and the fix restores the decision.
- Wording changes, renames of files, or additions that only add examples.

If you cannot tell which kind of change you are making, ask whether the
question is "what should this do?" or "what should this be?". The first is a
bug. The second is an ADR.

## Format

```text
# NNNN. Title in the form of a decision

Status: Proposed | Accepted | Superseded by NNNN | Rejected
Date:    YYYY-MM-DD
Deciders: names or roles

## Context
The forces at play. What made a decision necessary. Include the constraint
that ruled out the obvious answer.

## Decision
What was decided, in the present tense, stated as a rule that could be
checked.

## Consequences
What becomes easier, what becomes harder, and what must now be watched.
Include the failure mode this decision makes more likely, if there is one.

## Alternatives considered
Each with why it was rejected. This section is why the record exists.

## Revisit when
Observable conditions. Not "if it becomes a problem".
```

Rules:

- One decision per record. If you are writing "and also", split it.
- The title states the decision, not the topic. "Adopt R0 to R4 rungs" beats
  "Reasoning depth".
- Write the record before merging. A record written afterwards rationalises.
- If a decision is reversed, supersede the old record rather than editing it.
  The history of a wrong belief is more useful than a clean file.
- Never use "TBD", "to be decided", or a placeholder status. A proposed
  decision without a status is not a decision; make it one.

## Numbering

Four digits, sequential, never reused. `0001` through the current set. A
superseded number is retired permanently, so links never change meaning.

## Index

| # | Title | Status | Why it matters |
|---|---|---|---|
| [0001](0001-jev-as-decision-fabric.md) | JEv as the decision fabric | Accepted | Makes the kernel a decision procedure rather than a pipeline |
| [0002](0002-skills-are-resources-not-agents.md) | Skills are resources, not agents | Accepted | Prevents the architecture from becoming a swarm of specialists |
| [0003](0003-gated-learning-lifecycle.md) | Gated learning lifecycle | Accepted | Stops self-improvement becoming self-corruption |
| [0004](0004-explicit-effort-ladder.md) | An explicit effort ladder | Accepted | Makes cost a recorded decision rather than a habit |

## Reviewing an ADR

Reviewers check four things:

1. **Is the context honest?** Does it name the constraint that made the
   alternatives expensive? A context written to justify a predetermined answer
   is the common failure.
2. **Is the decision checkable?** Could someone verify compliance without
   reading the rationale? If not, it is a principle, not a decision.
3. **Are the alternatives real?** Were they genuinely available, and was a real
   one rejected for a real reason? A record with one token alternative was not a
   decision.
4. **Are the consequences both-sided?** Every decision makes something worse.
   A record that lists only benefits is marketing.

## Relationship to other documents

- The architecture the records describe: `../architecture/`.
- The vocabulary the records use: `../concepts/README.md`.
- The threats the decisions partly address: `../security/threat-model.md`.
- The open questions the records do **not** resolve: `../../research/`, in each
  area's "Open problems" section. An ADR that hides an unresolved tension
  belongs in research, not here.

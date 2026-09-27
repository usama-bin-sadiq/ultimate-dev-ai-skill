# Compose or create

The decision this engine makes most often, and the one it most often makes
wrong. Composing existing capabilities beats creating a new one; the cost of
composing is a seam, and the cost of creating is permanent.

This file is about the decision **inside the engine**. The composition rung of
the kernel's capability resolution ladder — why it outranks creation at all, and
what a chain costs to validate — is in the kernel's
`references/capability-composition.md`. Read that for the argument; read this for
the judgement call.

## When composition is the answer

Composition, not creation, when:

- Two or more existing skills between them cover the gap, with a small amount of
  sequencing.
- The gap is a *variation* of an existing skill's purpose rather than a
  different purpose.
- The new need is best expressed as "do A, then B, checking C between them" and
  that ordering is genuinely reusable.
- The gap is in how existing capabilities are wired, not in what they can do.

Creation is the answer when the gap is in *what can be done*, not in how
existing things are sequenced.

## The three forms

**Sequential** — run A to completion, then B. The simplest and most common.
The composition adds value only if the *boundary* is reusable: what to check
between A and B, and what to do if A's output does not satisfy B's input.

**Conditional** — run A, and on a specific observable condition run B. The
condition must be observable, or the composition is unreproducible.

**Composed capability** — a thin new artifact that references existing skills
rather than restating them. This is the preferred form: it adds the sequencing
knowledge without duplicating the procedural knowledge, and it stays correct
when the component skills are revised.

## What composition is for

The value is almost never the steps. It is the **transitions**:

- The precondition B needs, and how to check it.
- The interpretation of A's output that determines whether B is applicable.
- The rollback if B fails after A succeeded.
- The evidence that must be gathered across the boundary.

A composition that only says "do A then B" has added nothing. One that says
"run A; if it reports `<status>`, run B with `<field>`; if B fails, A's output is
still valid and must not be rolled back" has encoded real knowledge.

## Composition versus extension

| Question | If yes |
|---|---|
| Does the existing skill simply not handle this case? | **Extend** the existing skill |
| Do the existing skills handle their parts, but nobody knows the order and the boundary conditions? | **Compose** |
| Is this the same job with a different trigger? | **Merge** into one skill with two triggers |
| Does the existing skill need to *change behaviour* to cover it? | Extend, carefully, and version |

Composition is preferred over extension when the added knowledge is genuinely
about the *relationship* between capabilities. Extension is preferred when one
capability is genuinely under-powered. Merging two skills with overlapping
descriptions fixes the split-trigger problem that composition cannot.

## Failure modes of composition

- **The hidden precondition.** B is run on A's output without checking that it
  qualifies, and the failure surfaces as a confusing error inside B.
- **The unrecoverable boundary.** A succeeded, B failed, and there is no recorded
  answer to what state the world is in now.
- **The duplicated instructions.** The composition restates A's procedure instead
  of calling it, and now there are two copies that drift.
- **The unowned seam.** Nobody is responsible for behaviour that emerges only at
  the boundary, which is usually where the interesting bugs are.
- **The composition that should have been a plan step.** Sequencing used once,
  recorded as a capability. Apply the recurrence test.

## Recording

A composition is a decision, and gets a decision record like any other: which
skills are composed, what the boundary conditions are, what the rollback is, and
the condition under which the composition should be split into a real skill.

The last field matters. A composition that keeps growing is a skill that has not
admitted what it is yet.

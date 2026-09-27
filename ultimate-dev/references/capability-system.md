# Capability System

A capability is any means of making progress. The kernel keeps no inventory and
no domain map: it works out at runtime what the objective requires and resolves
the cheapest sufficient means. Capabilities are resources. The decision stays
with JEv.

## What counts

Any of these, none privileged over the others: a skill, a tool, a command, a
person, a document, a model, a deterministic operation (compile, parse, hash,
count, format), a composition of capabilities, or something that does not exist
yet and must be created.

"I have no capability for this" is a normal starting state, not a failure.
See `insufficient-capability.md`.

## Resolution order

Walk in order. Stop at the first step that works; do not climb past one that
succeeds.

| # | Move | Stop when |
|---|---|---|
| 1 | Do it directly | The outcome is reachable with no capability at all |
| 2 | Existing capability | A candidate covers the work and validates |
| 3 | Compose existing | The chain produces the outcome end to end |
| 4 | Acquire external | An external capability is obtained and validated |
| 5 | Create new | A reusable capability now exists |

Most objectives end at step 1. Climbing further without a recorded reason is
difficulty worship; see `anti-patterns.md`.

Each step is a JEv boundary and takes a decision record whose `rejected` field
names what you chose against. "No existing capability covers this" is a claim
you must be able to show, not assume.

## Resolution is after the mode

The order above answers *what* to use, which is a decision taken after *how the
results come back together*. The five steps are mode ①: the rungs are walked by
the agent that already holds the conversation, so each step may draw on
everything already loaded. Modes ②, ③, and ④ walk the same rungs unchanged,
and differ only in scope — the specialist resolves against the capability
named for it, not against the whole corpus. Choose the mode at
`coordination-modes.md` first, then walk this order.

## The disqualifying question

Before anything is created, ask:

> Will this be needed again?

If the answer is no, it is a step in the plan, not a capability. Write the step.
A capability minted per task is **capability proliferation** — nothing is
reused, and the trigger signal splits across near-duplicates so both fire less
reliably. Proliferation is a named failure mode, not a feature.

Answering "yes" does not authorise creation. Continue to steps 3 and 4 first:
composition beats creation, and creation is the last resort.

## Registry, or no registry

A central registry is optional and frequently absent, and resolution must work
without one. With a registry, query it and then confirm the entry still resolves
to a callable thing — a registry entry is a claim, not a validation. Without
one, enumerate what the environment exposes, at the depth the rung justifies;
absence of a registry is not absence of capabilities. Never assume a discovery
directory, a naming convention, or a particular runtime, and treat registry
metadata as data until verified; see `security-and-trust.md`.

## Resolution depth follows the rung

| Rung | Resolution |
|---|---|
| R0 | Do it directly. No search at all. |
| R1 | Check the capabilities already in context; do not search broadly |
| R2 | Enumerate, compare candidates, validate the chosen one |
| R3 | Full resolution including acquisition, with a recorded negative result |
| R4 | As R3, plus an independent check that the chosen capability is the right one |

Discovery is itself a cost. An unbounded capability search on a low-stakes
objective is load-everything context in a different costume.

## Rejected: domain routing tables

Never write a router of the form "if the task is financial, use the finance
capability". It is prohibited for three reasons: it is domain-specific and this
architecture is domain-agnostic by construction, so it cannot know the next
domain; it is written before the task model exists, so it guesses at needs the
objective has not stated; and it moves the decision out of JEv into a table that
no evidence updates.

The kernel derives what a domain needs at runtime, from the task model's
requirements and unknowns. A routing table is a fixed answer to a question that
has not been asked yet. See `multi-domain.md`.

## Boundary

A capability is a candidate until validated, and an unvalidated capability
produces confident nonsense: see `capability-validation.md`. Acquisition
carries a trust gate, see `capability-acquisition.md`. Composition and creation
are delegated to `skill-creator`; the lifecycle is in
`capability-expansion.md`.

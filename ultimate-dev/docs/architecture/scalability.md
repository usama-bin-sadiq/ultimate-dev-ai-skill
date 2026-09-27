# Scalability: one kernel from L1 to L7

This is the central architectural claim of the repository:

> There is no Level 7 mode.

The same kernel, the same lifecycle, the same decision boundaries, and the same
output contract operate on a one-line change and on a multi-year programme. What
changes is the amount of resource spent, the depth of planning, the strength of
verification, and the number of capabilities composed.

The claim is falsifiable. A new level must be reachable by changing quantities,
never by adding a branch that says "if very large, behave differently". If a new
level needs a new mode, the architecture is a family of workflows with a shared
name.

## The two ladders

Effort rung and scale level are independent, and confusing them causes both
over-orchestration and under-structuring.

| Rung | Reasoning effort for one unit |
|---|---|
| R0 Immediate | act, verify the output, no plan |
| R1 Structured | short plan, verify each step |
| R2 Analytical | task model, real plan, per-unit verification |
| R3 Deep | full kernel, parallelism where independent, independent verification |
| R4 Assurance | R3 plus a named human checkpoint before acting, and an independent check of the result |

| Scale | Shape of the work |
|---|---|
| L1 | one task |
| L2 | multi-step, a few units |
| L3 | professional, decomposition and per-unit verification |
| L4 | multi-domain project, workstreams, integration |
| L5 | large programme, hierarchical planning, checkpoints |
| L6 | extremely complex, unfamiliar, long-horizon |
| L7 | civilisational scale, staged delivery, explicit risk retirement |

The pair is a product, not a ladder with one axis:

- One irreversible action on a production database is **R4 and L1**.
- A thousand low-stakes edits across a repository are **R1 and L4**.
- A research programme with one open question is **L6 and R2**.

Escalate the rung when reality is harder than triage found. De-escalate when it
is easier. Carrying R3 on an R0 task is the most common defect in this system and
the one users pay for most directly.

## What changes between levels

**Resources.** Concurrency, budget, elapsed time, and simultaneous capabilities. At
L1 the whole plan fits in one context. At L5 it does not, so state moves to disk
and every unit must be resumable.

**Planning depth.** L1 to L2: a list. L3: atomic units with preconditions. L4: a
dependency graph with integration points. L5 and above: hierarchical plans where
subplans are themselves kernel runs.

**Verification strength.** L1: check the output. L2: check each step. L3: verify
per unit against its declared result. L4: add cross-unit and integration
verification. L5: continuous verification, so regressions surface at the unit
that introduced them. L6 and L7: independent re-derivation on the claims that
carry the programme, staged acceptance, and named human checkpoints before
irreversible milestones.

**Capability composition.** L1: one capability, often none. L3: several, resolved
per unit. L4: composed chains, and at least one acquired rather than shipped. L5
and above: the library grows during the run, which makes learning and
deprecation part of delivery rather than a later concern.

**Coordination.** Below L4 the kernel coordinates its own units. At L4 and above
it coordinates workstreams, and the integration between them becomes its own
workstream with its own verification.

## What does not change

This list is the test. If any of these change with scale, the claim is broken.

- **The lifecycle.** Fourteen layers, entered at the same point, exited at the
  same condition.
- **The decision record.** Same fields at every level. A workstream decision is
  recorded like a single-unit decision, and rejected alternatives are just as
  mandatory.
- **Triage.** Rungs mean the same thing at L1 and L7.
- **Verification.** Never optional. Only its strength scales.
- **Observation.** A result that was not observed is unknown at every level.
- **The output contract.** Outcome, evidence, assumptions, limitations,
  confidence, verification status. A programme report omits none of them.
- **The learning gates.** A lesson from one L7 unit is a candidate, not a rule.
- **Human control.** R4 means a named human checkpoint before acting, at every
  level, for the same reasons.

## Level by level

**L1 — one task.** RECEIVE, UNDERSTAND, TRIAGE at R0 or R1, act, observe, verify,
deliver. No plan, no ledger. You cannot tell from the outside whether the kernel
is running L1 or skipping steps, and that is the point: L1 must not feel
different from answering directly. The common failure here is orchestrating a
trivial task, visible only as delay and process nobody asked for.

**L2 — multi-step.** A short plan of a few units, each verified. The unit is the
new object: precondition, expected result, its own resume point. If work cannot
be resumed from its own state, it is not yet a unit.

**L3 — professional.** Real decomposition, capability resolution per unit,
verification per unit. This is where the kernel starts earning its keep: it
acquires what it lacks, verifies each piece, and delivers a result whose parts
were checked independently.

**L4 — multi-domain project.** Workstreams appear, each a bounded objective with
its own requirements, plan, and verification, reporting upward through the output
contract. Integration becomes explicit work. The most common L4 defect is
treating workstreams as independent and discovering at the end that they were
not: name the shared assumptions across workstreams in the task model, and verify
them.

**L5 — large programme.** Hierarchical planning, where subplans are kernel runs in
their own right. That is what makes the claim recursive rather than rhetorical.

```text
programme
├── programme plan  (kernel run: triage, workstream definition, integration order)
│   ├── workstream A  (kernel run: own model, plan, units, verification)
│   │   ├── unit
│   │   └── unit
│   ├── workstream B  (kernel run)
│   └── integration   (kernel run: cross-workstream verification)
└── programme verification
```

Three properties make the recursion real rather than a diagram:

1. Each level receives the output contract from its parent, not a raw transcript.
   The context a subplan starts with is bounded by that contract.
2. Each level can be interrupted. Parent state plus child state reconstruct the
   programme, so losing a session is a delay and not a restart.
3. Each level can fail upward. A workstream that cannot meet its requirements
   reports a block to the parent, which re-decides: change the plan, change the
   rung, reduce scope, or stop and report. The parent does not pretend the gap is
   closed.

Checkpoints enter here: named points where the programme is verified as a whole,
not only unit by unit. Continuous evaluation also enters, because at this scale
discovering a design error at the end costs more than the whole execution budget.

**L6 — extremely complex, unfamiliar, long-horizon.** All of L5, plus explicit
risk retirement (each major risk gets an owner, a test that would retire it, and
a date by which it must be retired or escalated — untested risks are carried, not
managed); staged delivery, so a stop between stages leaves value rather than
nothing; C6 used sparingly, for the handful of decisions per stage that are
novel, contested, and load-bearing; and acquired capabilities carrying more
weight, since a generated skill that turns out wrong here can affect hundreds of
downstream units.

**L7 — civilisational scale.** The same machinery at the largest scale the
resources allow. What is added is duration, number of workstreams, number of
human checkpoints, and the discipline of stating limits honestly. The kernel does
not claim to complete an L7 objective; it claims to manage the work
transparently, verify what it claims to have produced, and report the rest as
unestablished. That is the honest ceiling: the architecture scales the process,
and no amount of decomposition substitutes for a check that was never run.

## Hierarchical planning, concretely

Four rules keep the recursion sound.

**Decompose by dependency, not by size.** An OS programme decomposes into boot
path, memory management, scheduling, drivers, filesystem, networking, and
integration, because those are the real dependencies. Splitting "half the work"
into two workstreams produces two units that cannot be verified separately.

**Every workstream is independently verifiable.** If a workstream can only be
checked after integration, it is not a workstream; it is a fragment of one.

**Interfaces are work.** Shared assumptions between workstreams get their own
units, their own evidence, and their own verification. They are the first thing
to go wrong and the last thing anyone checks.

**The parent holds the integration plan.** Workstreams report through the output
contract. The parent reconciles their evidence, notices contradictions between
two workstreams that both claim success, and re-decides. Contradictory success
claims are a signal, not noise to be smoothed over.

## The test for a new level

Before adding a level, or handling a case that feels like a new level:

1. Can it be expressed as a rung plus a scale level? If yes, it is not new.
2. Does it change the lifecycle, the decision record, the output contract, or
   the verification obligation? If yes, the claim is broken, and the change is
   an architectural decision requiring an ADR.
3. Does it introduce a branch that switches architecture by size? If yes, you
   have written a second kernel. Merge it, or document why the claim no longer
   holds.

A new level that passes all three is just a bigger run, and the run mechanics in
`../operations/budget-and-limits.md` already cover it.

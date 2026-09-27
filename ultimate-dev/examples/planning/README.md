# Planning traces

Two plans. One is a cutover with a rollback window, a 3.2M-row data migration, and
a deadline that cannot move, where the first plan is invalidated by a constraint
discovered in a customer's own code. The other is an itinerary, where the correct
answer is to state the reading you proceeded under, deliver it, and name the one
question that would change it.

The shared discipline is that a plan is a set of **atomic, independently verifiable
units with declared preconditions**, and that a plan which cannot be revised
against evidence is worse than no plan.

## Kernel mechanisms stressed

- **The plan as a portfolio of decidable units.** Every unit has a precondition, an
  expected result, and a verification, and the verification is runnable by someone
  who did not write the plan.
- **A plan that is expected to change.** The cutover's gate design was replaced after
  a workstream owner disclosed an architectural fact. That is the system working.
- **The rollback cost as a function of time.** The cutover's abort criteria are
  derived from how expensive rollback is at each minute, not from a generic
  "if it's broken, roll back". That derivation is the plan's actual content.
- **R1 discipline on a bounded question.** The itinerary needs a hard-constraint
  check per leg and a maximum-per-day calculation, and it needs one question asked
  in one sentence — not a clarification dialogue before any work is done.
- **Interruption-safe units.** Each unit can be resumed from its own state, which is
  what `planning-system.md` requires and what makes the cutover plan usable by a
  team that did not write it.

## Traces

| File | Objective | Scale / Rung | Verdict | Load it for |
|---|---|---|---|---|
| [`billing-api-cutover-plan.md`](billing-api-cutover-plan.md) | Write the cutover plan for moving `billing-api` to EKS on 2026-10-13 | L4 / **R3** | VERIFIED | A rollback cost function, a gate design, and a workstream owner's disclosure that invalidates half the plan |
| [`r1-japan-itinerary-constraints.md`](r1-japan-itinerary-constraints.md) | Plan 6 days in Japan under hard constraints | L2 / **R1** | VERIFIED (under a stated reading) | A bounded planning task at R1, and an ambiguity that is handled with a recommendation instead of a stall |

## Reading notes

**`billing-api-cutover-plan.md` is the one with the real content.** Its most useful
section is the rollback cost function: at T+0 rollback is a 90-second target-group
weight flip, at T+30 it is a forward-fix, and at T+60 the old stack can no longer
be restored without a data reconciliation. Every abort criterion in the plan falls
out of that table, and the plan's most important property is that it says *when* it
will stop.

**`r1-japan-itinerary-constraints.md` demonstrates the low end properly.** The
request is ambiguous in a way that changes the deliverable — "fly out on the 14th"
gives either 13 nights or an impossible trip — and the response is to pick a
reading, deliver a complete plan under it, and state in one line what changes under
the other. That is cheaper than a clarification round-trip and more useful than
asking first.

## Adjacent examples

- [`../operating-system/os-capability-benchmark.md`](../operating-system/os-capability-benchmark.md)
  — the same hierarchical plan structure at L7, with seven stage gates.
- [`../recovery/`](../recovery/) — the two plan units that did not survive contact
  with reality.
- [`../mathematics/rota-scheduling-infeasibility.md`](../mathematics/rota-scheduling-infeasibility.md)
  — a plan that turned out to have no solution, which is the same failure at a
  smaller scale.

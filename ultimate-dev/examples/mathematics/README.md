# Mathematics traces

Two objectives. One is a known procedure on a known integral, and the correct
answer is one command and one sentence — a demonstration that the machinery
switches off when the next action is already determined. The other is a
constraint-satisfaction problem over 84 shift slots that turns out to be
**infeasible**, and the interesting work is what the kernel does with a problem
that has no solution.

Both are about the same underlying discipline: stating the problem in a form that
can be *checked*, and refusing to produce an answer that the form does not
support.

## Kernel mechanisms stressed

- **The effort gate at its lowest.** `r0-gaussian-integral-substitution.md` runs
  at R0 with one unit and one deterministic check, and the trace spends most of its
  length showing what it declined to do.
- **A wrong derivation is not a wrong answer.** In the R0 trace, confirming the
  number alone would have left the user's actual confusion untouched, so the kernel
  checks the *step* — a one-line widening that is still R0, because widening by one
  deterministic step is not an escalation.
- **Infeasibility as a finding.** The rota problem has no solution under the stated
  constraints. The kernel does not loosen a constraint to produce a feasible model;
  it prices the infeasibility, enumerates the minimal relaxations with their costs,
  and escalates with a recommendation.
- **Verification by re-derivation.** The rota's correctness is checked against
  hand-enumerable invariants — coverage, no double-booking, hour bounds — rather
  than by inspecting the solver's output.
- **Capability resolution stopping at rung 3.** OR-Tools is an existing dependency
  and the modelling is composition. Nothing is acquired and nothing is created.

## Traces

| File | Objective | Scale / Rung | Verdict | Load it for |
|---|---|---|---|---|
| [`r0-gaussian-integral-substitution.md`](r0-gaussian-integral-substitution.md) | Check an integral and find where the derivation loses its ½ | L1 / **R0** | VERIFIED | The kernel doing almost nothing, and the one place it correctly widens by a single step |
| [`rota-scheduling-infeasibility.md`](rota-scheduling-infeasibility.md) | Build a 4-week, 6-person, 84-slot rota under stated working-time rules | L3 / **R2** | PARTIAL (deliberately infeasible) | An infeasible model reported honestly, with priced alternatives and a recommendation, instead of a quietly loosened constraint |

## Reading notes

**`rota-scheduling-infeasibility.md` is the one worth the time.** The failure mode
it demonstrates is the one that is hardest to notice in review: an agent that
loosens a constraint to make a solver return `OPTIMAL` has produced a schedule
that looks solved and violates a legal limit. The trace refuses to do that, works
out which constraint is binding, and hands the decision to a person with the cost
of each option.

**`r0-gaussian-integral-substitution.md` is short on purpose.** It is the counterweight
to the rest of this repository. A kernel that elaborates here is broken, and the
trace's job is to show the check that would notice.

## Adjacent examples

- [`../planning/r1-japan-itinerary-constraints.md`](../planning/r1-japan-itinerary-constraints.md)
  — the same constraint-satisfaction shape with hard human constraints and a much
  lower rung.
- [`../science/xrd-cubic-lattice-indexing.md`](../science/xrd-cubic-lattice-indexing.md)
  — where the arithmetic is real and the interpretation is not the kernel's to make.
- [`../unknown-domain/`](../unknown-domain/) — where there is no reference to lean
  on and the honest output is a stated limit.

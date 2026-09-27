# Parallelism

Parallelise work units that are genuinely independent, and only those. Two units
that share mutable state are sequential however they are scheduled; a scheduler
that runs them together has not made them independent, it has made them racy.

Parallelism trades latency against coordination cost and review burden. It wins
when units are substantial and independent. It loses when units are cheap, when
they touch the same state, or when the merge costs more than the waiting saved.

**Sequential execution is always available and is never a degradation to apologise
for.** If the runtime cannot issue concurrent calls, run the units in order. The
result is identical and slower. Do not report work as parallel when it was
sequential. See `runtime-portability.md`.

## Test independence before fanning out

For each pair, ask:

- Does either write anything the other reads or writes?
- Does one depend on the other's output?
- Do they change the same file, index, configuration, or environment?
- Would one failing leave the other reasoning on false premises?

Any yes means sequential, or means isolating the shared state first. A read-only
check that observes what a concurrent write will change is not read-only in
effect.

## The upper bound

Fan-out is not free. Independent units still have to be specified, dispatched,
merged, and verified, and a merge that costs more than the waiting saved makes
the run worse rather than slower. Parallelism helps when units are substantial
and genuinely independent, and reverses when they are neither.

Two stop conditions:

- **The merge is the work.** If combining the results costs as much as producing
  them, the units were not independent in the way that mattered. Re-scope them
  or run them in sequence.
- **Coordination exceeds execution.** If most of the run is spent deciding what
  to run in what order, the decomposition was wrong, not the scheduler.

## Good candidates

- **Independent retrievals** — several sources, none depending on another.
- **Independent read-only checks** — validating separate claims that mutate nothing.
- **Disjoint work units** — no shared input, no shared output, no ordering constraint.

Keep the fan-out narrow. Five independent units is a plan. Fifty is a dispatch
you cannot review.

## The merge point

Parallel results must be reconciled, and reconciliation is a step, not a
cleanup. Two independent derivations that disagree is a signal to investigate:
find out which is wrong before proceeding. Averaging a disagreement destroys the
information that something was wrong. If the disagreement cannot be resolved,
report both and the uncertainty, and do not present a reconciled value you did
not verify.

## Losing track

The characteristic failure is firing everything at once and then being unable
to say which unit produced which result. Tag every result with the unit that
produced it, the state it observed, and when it ran. A result that cannot be
traced to a unit cannot be verified, and an unverifiable result does not get
used.

## Parallel or sequential

| Situation | Call | Why |
|---|---|---|
| Several independent lookups, nothing depends on the result | Parallel | Latency falls, no shared state |
| Read-only checks on disjoint claims | Parallel | No writes, no ordering constraint |
| One unit's output is the next unit's input | Sequential | A real dependency |
| Two units edit the same file or state | Sequential, or isolate first | Shared mutable state |
| Each unit takes under a second | Sequential | Coordination exceeds the saving |
| Many cheap units feeding one merged answer | Sequential with batching | The merge is the real work |
| Failure in one unit invalidates the rest | Sequential | Later units would run on false premises |
| Unrelated high-cost work, user waiting | Parallel | Latency is the dominant cost |

## When to stop fanning out

Serialise when units begin sharing state, when the review burden of merged results exceeds the latency saved, or when you can no longer state what each result came from.

Cross-reference `delegation.md`, `execution-system.md`, `state-system.md`, and `anti-patterns.md`.

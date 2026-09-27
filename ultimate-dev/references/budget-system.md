# Budget System

Budget is the resource that makes every other adaptive choice possible. Without
it, "scale effort to risk" has nothing to scale against, and the kernel drifts
either towards doing everything or towards stopping as soon as anything is
awkward.

## What counts against budget

Effort, not tokens. A kernel that counts tokens optimises for the wrong thing.

| Draw | Notes |
|---|---|
| **Work units executed** | The primary unit. Comparable across tasks. |
| **Capability acquisitions** | Including validation. An unvalidated capability is worse than none. |
| **Context loaded** | Weighted by rung, since C6 costs far more than C2. |
| **Decisions taken** | Cheap individually; churning decisions are expensive in aggregate. |
| **Retries** | Charged at full rate, because a retry is a new attempt. |
| **Delegations** | Charged plus the parent's coordination cost. |
| **Wall-clock and user attention** | The scarcest resource, and the one users actually notice. |

## The measurement rule

**A budget figure you could not measure is reported as unmeasured.** Not zero,
not an estimate, not a plausible number. If the environment reports no token usage
or no cost, the budget record says so.

This is not pedantry. A kernel that invents a budget number will tune against it,
and the tuning is then optimising a fiction. Every other rule in this skill about
provenance and evidence applies to budget figures too — a fabricated cost figure is
the same failure as a fabricated tool result, just less visible.

## Spending rules

1. **The cheapest adequate rung wins.** Stop at the lowest rung that is
   adequate, not the lowest that is possible. Adequacy is set by consequence and
   uncertainty, never by habit.
2. **Budget is spent on decisions, not on motion.** A task that spends its budget
   executing a plan nobody examined has bought nothing. Re-deciding is cheap and
   usually positive-value.
3. **Front-load the decisions, back-load the execution.** Understanding,
   capability resolution, and strategy are cheap and prevent expensive work. A
   cheap early decision that saves an expensive late step is the best trade
   available.
4. **Verification is never the thing to cut first.** It is the only thing standing
   between an unverified result and a delivered one. If budget forces a cut, cut
   scope, not verification depth — and record the cut.
5. **An exhausted budget triggers a decision, not a silent stop.** Reduce scope,
   lower the rung, split the objective, or report the block. Finishing at 90% and
   labelling it done is the failure mode.

## When budget forces a choice

| Situation | Response |
|---|---|
| Budget nearly spent, criteria not met | Report PARTIAL, state precisely what is unmet, do not claim success |
| Budget nearly spent, work not started | Reduce scope to what is affordable, confirm the reduction |
| Budget exhausted mid-unit | Finish or reverse the unit, then re-decide — do not abandon it half-applied |
| Budget spent on a path now known wrong | Stop immediately; remaining budget cannot rescue a rejected approach |
| Budget insufficient for the objective | Say so, with what the objective would cost |

## Budget and rung

Rung governs *how* effort is spent; budget governs *how much*. They interact in
one direction only: a higher rung costs more, so a task does not escalate because
budget is available. It escalates because triage found the work harder, and it
de-escalates when the work turns out easier — even mid-task, even after effort is
committed. Sunk cost is not a reason to continue; it is a reason to have stopped
sooner.

## Recording

```text
BUDGET
  basis          work units | time | both
  spent          <n> units, <n> acquisitions, <n> retries
  remaining      <n> units, or "unmeasured"
  measurement    measured | unmeasured — <why, if unmeasured>
  cut made       <what was reduced, and when>   <- omit if none
  stop condition <the event that ends spending>
```

The `cut made` line is the one that matters later. It tells a reader that a
result is narrower than the objective, and it is the difference between a
deliberate scope decision and an unexplained gap.

See `triage.md` for how the rung is set, `reasoning-system.md` for what each rung
costs, and `caching-and-reuse.md` for reclaiming budget without cutting scope.

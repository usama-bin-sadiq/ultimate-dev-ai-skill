# Recovery traces

Two failures, classified before they were responded to, and in both the recorded
alternative is **blind retry** — the same action, the same inputs, the same state,
repeated in the hope that this time it works. `retry-policy.md` puts both of these
outside the retryable class, and in both cases retrying would have produced a
failure that looked like progress.

Recovery is a kernel property rather than a domain, and that is why both traces
here are drawn from ordinary infrastructure work. The interesting part is not the
failure; it is what the classification *excludes*. One of these is a resource
failure where the correct response is to do less, and one is a verification failure
where the correct response is to treat the check as wrong rather than the work —
which is the hardest distinction in `recovery-system.md` and the one most often got
backwards.

## Kernel mechanisms stressed

- **Classify, then respond.** Each failure gets a classification from the Step 8
  table, a named cause in one line, and a response the table mandates. Neither
  response is "try it again".
- **One failure is an event, two is a signal.** The OOM trace records two identical
  prior failures and treats them as evidence about the plan, not as bad luck.
- **A failure of the check is not a failure of the work.** The staging trace's
  subtlety: the criterion "CI is green" was *falsified*, which is a different finding
  from a check failing against good work, and it goes back through JEv as a
  task-model correction.
- **Bounded retry with a recorded count.** Both traces state the bound and what
  happens at it. Neither reaches it.
- **Blind retry named explicitly.** Each trace has a section on the response
  avoided, and in each the avoided response is the one that looks like effort.

## Traces

| File | Objective | Scale / Rung | Verdict | Load it for |
|---|---|---|---|---|
| [`backfill-oom-resource-failure.md`](backfill-oom-resource-failure.md) | Make a 3.2M-row backfill stop getting OOM-killed | L3 / **R2** | VERIFIED | A resource failure correctly answered by doing less, and the third restart that was cancelled before it wasted another night |
| [`staging-only-failure-verification-depth.md`](staging-only-failure-verification-depth.md) | Fix 40% staging 500s while CI is green | L2 / **R2** | VERIFIED | A falsified criterion, and the three tempting wrong answers (rerun CI, add a retry, mark it flaky) |

## Reading notes

**`backfill-oom-resource-failure.md` is the one about doing less.** The plan was a
single unbounded UPDATE over 412M rows. The recovery is a batched, checkpointed
backfill that runs in 144 seconds at 1.4GB peak instead of 3 hours until death. The
scheduled third restart was cancelled, and that cancellation is the most valuable
act in the trace — it is the retry that the classification forbids, stopped in
advance.

**`staging-only-failure-verification-depth.md` is the one about a lying check.** CI
was green and staging was returning 500s, and the instinct is to treat one of them
as the problem. It is neither: CI was not lying, it was testing a configuration
that staging does not use, and the criterion "tests are green" was the thing that
was wrong. Loosening it — a longer timeout, a retry around the failing call, a flaky
marker — would have shipped the defect.

## Adjacent examples

- [`../software-engineering/postgres-add-column-412m-rows.md`](../software-engineering/postgres-add-column-412m-rows.md)
  — the same table, the same lock-timeout discipline, and a recovery where the
  failing check was replaced rather than trusted.
- [`../distributed-system/redis-lock-without-fencing.md`](../distributed-system/redis-lock-without-fencing.md)
  — a failure that was not an error at all: a lease that expired silently.
- [`../data-analysis/srm-before-reading-an-ab-result.md`](../data-analysis/srm-before-reading-an-ab-result.md)
  — a validity failure found before anyone acted on the number.

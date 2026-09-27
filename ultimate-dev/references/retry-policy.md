# Retry Policy

A retry is a decision, not a reflex. It is permitted only after a cause is
identified and something has been changed. Its purpose is to absorb a transient
failure; it is not a route to a result the environment is refusing to give.

## The rules

1. A retry requires a named cause. No cause, no retry.
2. At most **two** attempts at the same action with the same inputs. The second
   failure means the cause was not understood — stop and change something.
3. An identical retry after an identical failure is guaranteed to fail identically.
   Identical means the same action, the same inputs, and the same state, which is
   why "try it again" is not a neutral act.
4. Every attempt and its outcome is recorded, so the count is observable rather than
   remembered. A count held in memory is wrong under pressure; the run state is not.
5. A retry that succeeded once does not license a retry policy. One pass is an
   observation, not a pattern — see `learning-system.md`.

## Why identical retries are waste

The failure was deterministic under the conditions you observed. Repeating the action
under those conditions reproduces the result and spends the attempt. A run of
identical failures also looks like work in progress while consuming the budget a real
fix needs. Treat the second identical failure as evidence that your classification was
wrong: re-classify before you spend attempt three.

## The retry escalation ladder

| Rung | Change | Use when | Stop when |
|---|---|---|---|
| R1 | Retry the action | Cause identified and transient, or the first effect was partial | One clean success, or the same failure twice |
| R2 | Change inputs | The failure depends on an input: path, format, version, flag | The new inputs produce a new failure |
| R3 | Change method | The approach is sound, the mechanism is not | A different mechanism fails the same way |
| R4 | Change strategy | The approach itself is wrong | No new strategy can be justified at JEv |
| R5 | Change rung | Reality is harder or easier than triage said | The rung ceiling is reached |
| R6 | Escalate | Only the user can supply what is missing | Terminal |

Each rung needs a decision record. Descending this ladder without recording what
changed is how a run reaches R5 having burned four attempts and learned nothing.

## Which failures are retryable

| Class | Examples | Retryable |
|---|---|---|
| Transient | Timeout, rate limit, lock contention, temporary unavailability, reclaimable space | Yes, with backoff |
| Deterministic | Syntax error, missing dependency, bad argument, absent file, type mismatch, failed assertion, unmet criterion | No — fix the cause first |
| Environmental | Permission denied, offline, wrong host, quota exhausted | No — change the environment or escalate |
| Wrong-reason failure | The action was never going to work, because of missing context, wrong capability, or a bad assumption | No — this is not an execution failure |

Only the transient class is retryable. Everything else is recovered through
`recovery-system.md`, not through repetition.

## Backoff

For a genuinely transient resource failure, wait, and grow the wait: first retry
immediately, second after a short fixed delay, then either escalate or switch to
reduced scope. Cap the number of attempts, not the elapsed time. Never back off a
deterministic failure — nothing about the environment changes while you wait.

## Record every attempt

```text
ATTEMPT
  unit      work unit
  action    what was run
  inputs    the inputs, listed or hashed
  attempt   n, against the unit's bound
  changed   what differs from attempt n-1, or "nothing"
  observed  the actual result
  outcome   success | transient | deterministic | stop
  cost      time, calls, budget consumed
```

If `changed` reads "nothing" and `outcome` is a failure, the policy is violated: take
it to JEv as a classification error, not as attempt three. Bounds belong in
`budget-system.md`; promotion of the resulting pattern belongs in
`learning-safety.md`.

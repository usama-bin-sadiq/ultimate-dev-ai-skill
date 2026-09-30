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
| R6 | Prove absence | You believe only the user can supply what is missing | Absence is **proved**, not assumed — see below |
| R7 | Escalate | The routes below were tried and did not produce it | Terminal |

Each rung needs a decision record. Descending this ladder without recording what
changed is how a run reaches R5 having burned four attempts and learned nothing.

## A capability you did not find is a hypothesis, not a fact

The single most common way a run ends early is a sentence like *"this tool is
unavailable, so I have left that part untouched"* — and the sentence is almost
never true, because **not having looked for a route is not the same as there
being none.** Treating absence as an environmental fact is what turns a task into
a report about a task.

So an absent capability is a claim, and a claim has to be earned before it can end
the work. Before R6 (prove absence) or R7 (escalate) is reached, do all of this:

1. **Search, do not assume.** The catalogue is large and the tools are not named
   the way you would guess. Search it (`tools/index-tree.py --search <term>`),
   check what the host actually exposes, and look for the *capability* rather than
   the tool you had in mind. A different tool with the same effect is a route.
2. **Change the level.** If one route is refused, a different mode usually is not:
   inline vs delegate, a specialist vs the general procedure, a script vs a
   manual sequence, a narrower scope done for real vs a broad scope declared.
3. **Re-resolve the unit.** Go back through capability resolution (do it → use an
   existing one → compose → acquire → create) for *this unit*, not for the plan
   you started with. The plan was written before you knew this part was hard.
4. **Do the part that is possible, for real.** A partially-completed unit that
   genuinely changed something on disk or in the output is worth more than a
   complete report that nothing was attempted.

Only when every one of those has genuinely been tried is absence a finding. "I
did not find it" becomes "it is not there" here, and never before.

**And the mirror error, which the rule above does not fix.** Benchmarks built to
measure premature give-up report that the models most likely to give up are also
the ones that *over*-block: one evaluation found a model unsafe on due diligence
while still declining to answer 21% of the questions it was safe to answer. So
"never give up" is not the correction either — it trades a false-completion rate
for a refusal rate, and both are ways of not doing the work.

Both errors have one cure, and it is the same test: **was the boundary carried, or
was it abandoned?** A task where the agent used what it had, did the achievable
part for real, and reported the remainder factually is right in both directions.
It fails neither test — which is why `deliver --path` and `satisfy --evidence`
exist. They require the artifact to exist and the evidence to resolve, so neither a
fabricated success nor a comfortable refusal satisfies the state. An over-blocker
cannot pass the gate by declining, any more than an under-claimer passes it by
explaining.

**The asymmetry, stated so it is not traded away.** This rule makes *early* giving
up expensive, and deliberately does not make *claiming success* cheap. Persisting
is not the same as finishing: a run that exhausts every route and then reports a
genuine block has succeeded at the task of finding out what is true, even though
it did not deliver the feature. Both halves are required —

- never stop at the first obstacle (**this section**), and
- never claim a result you did not observe (`anti-hallucination.md`,
  `execution-system.md`).

A run that does the first and skips the second is worse than either failure alone,
because it converts a block into a fabrication. The order matters: **exhaust the
routes, then report honestly what is left.** The failure this prevents is not
giving up — it is the comfortable substitution of *writing about* the task for
doing it, wearing the costume of rigour.

## Which failures are retryable

| Class | Examples | Retryable |
|---|---|---|
| Transient | Timeout, rate limit, lock contention, temporary unavailability, reclaimable space | Yes, with backoff |
| Deterministic | Syntax error, missing dependency, bad argument, absent file, type mismatch, failed assertion, unmet criterion | No — fix the cause first |
| Environmental | Permission denied, offline, wrong host, quota exhausted | No — change the environment, find another route, or escalate. A *missing tool* is not environmental: it is R6 |
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

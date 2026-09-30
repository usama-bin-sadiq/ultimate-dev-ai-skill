# Recovery System

A failure is not a disruption to the work. It is the cheapest information you will
get about the work, because a fact that was a guess a moment ago is now observed.
Classify every failure before you respond to it, and record it before you act on it.

## Classify before responding

Blind retry is prohibited. Repeating an action whose cause is unknown reproduces
the failure, burns budget, and produces the appearance of effort — the worst of the
three. Before any second attempt, name the cause in one line. If you cannot, the
cause is missing context or wrong capability, and both are recoverable.

| Classification | Mandated response | Stop condition |
|---|---|---|
| Missing context | Acquire it, then resume. Do not retry blind. | Context unobtainable → escalate |
| Wrong capability | Re-resolve; compose or create one, then validate it. | Two resolutions fail → escalate |
| Wrong strategy | Re-decide at JEv, with a new decision record. | Two strategies fail on one unit → re-triage |
| Bad assumption | Correct it, then re-plan every unit that depended on it. | Correction invalidates the task model → re-triage |
| Execution failure | Fix the identified cause, then retry within the bound. | Bound reached → change rung or escalate |
| Resource failure | Reduce scope, lower effort, or report the block. | No slack left → report the block |
| Verification failure | Treat as a real failure of the work, not of the check. | Same criterion fails twice → re-decide |
| Unsupported objective | Say so plainly, with what is missing. Stop — **but only after the routes in `retry-policy.md` §"A capability you did not find" are exhausted.** "Unsupported" is a conclusion reached by looking, not the first thing you notice. | Terminal; do not hunt for a workaround |
| Coordination failure | Re-choose the mode; a mode error is not a capability error. | Two mode changes → re-triage |

Recovery may change `coordination`, and the change is recorded like any other
field. A delegate that fails twice where a route would have covered the ground
is a mode error, and recording it is what makes the correction reviewable
instead of invisible.

## Failures are data

Every failure enters the run state as structured information: what was attempted, the
observed error, the classification, the cause, and the response taken. A failure that
lives only in your reasoning is one you will repeat, because the next unit will hit
the same wall with no memory of it. Record first, then act.

```text
FAILURE
  unit            work unit and action that failed
  observed        the actual error or result, quoted rather than paraphrased
  classification  missing context | wrong capability | wrong strategy
                  | bad assumption | execution | resource
                  | verification | unsupported objective | coordination
  cause           the identified reason, in one line
  response        acquire | re-resolve | re-decide | replan | retry | reduce | stop
  attempts        attempt count for this unit so far
  blocked         what else is waiting on this
  evidence        what proves the cause: the error, a diff, a check
  recovery        what would make it recur, and what would prevent it
```

## One failure is an event; repeated failures are a signal

A failure inside one work unit is local: fix the cause and move on. The same
classification across two or more units, or across two tasks, is systemic — it names
something wrong above the unit: the plan, the capability set, the task model, or the
rung. A per-unit fix will not clear it. Stop fixing units, re-decide at JEv, and if
the pattern survives that, escalate. Treating a systemic failure as noise is how the
same class of error gets rediscovered at every level of the programme.

## A failure of the work is not a failure of the check

A verification failure means the criteria are not met, so the work is wrong. The
first response is never to loosen the check. Only when the check itself is falsified
— a misstated criterion, a wrong measurement, a lying tool — does that become the
finding, and it goes back through JEv as a task-model correction. Loosening a check
because it failed converts a detected defect into a shipped one.

## When to stop

Recovery is bounded. Take it to `escalation.md` when the classification is
unsupported objective, when the rung has nowhere lower to go, or when the cause is
known, fixed, and still failing.

A bound on recovery is a bound on *repetition*, not on *routes*. Running out of retries
on one approach means change the approach, not that the work is finished: the ladder
in `retry-policy.md` has six rungs below escalation, and a run that climbed none of
them has not tried to recover, it has retried. The block you report must name the
routes already taken, because "this was blocked" and "I stopped looking" are
indistinguishable to a reader and only one of them is true. Retry arithmetic is in `retry-policy.md`; the state
that must survive a stop is in `state-system.md`; verification verdicts are in
`verification-system.md`.

A recovered run is a normal run, not a degraded one. Report what failed, what it
cost, and the evidence that the recovery worked — not a caveat about having
recovered.

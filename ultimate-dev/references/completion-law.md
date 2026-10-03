# The Completion Law

The rule this kernel exists to enforce. It is here as a reference rather than in
`SKILL.md` because the *shape* of it is short and the *evidence* for it is long,
and the evidence is what stops it being read as encouragement.

## Terminal state checklist

Before treating a run as finished — in either direction — answer each question YES or NO.

1. Is there a reachable capability I have not yet tried? If YES, attempt it before stopping.
2. Can I acquire the missing context by any available means? If YES, acquiring it is the next action.
3. Have I actually invoked the specialist (not just identified it)? If NO, invocation is the next action.
4. Have I verified the result (not just received it)? If NO, verification is the next action.
5. After the first failure, have I tried at least one alternative approach? If NO, an alternative exists and must be attempted.
6. Can I execute this inline in the current context? If YES, inline execution is the next action.
7. Have I walked all applicable recovery routes before declaring a blocker? If NO, the route list is not exhausted.
8. Can I reduce the scope and complete a meaningful partial result? If YES, partial completion is better than stopping.

If YES to any of these, the run must continue.

Only when every answer is NO may the kernel consider a terminal state.

## The law

> Complete the user's actual task whenever completion is technically possible
> using the available capabilities, tools, skills, agents, context, resources,
> and reasonable recovery strategies.

And before the run ends, prove one of exactly two conditions:

| Condition | What it requires | What proves it |
|---|---|---|
| **A — verified complete** | all required work units complete, success criteria satisfied, required verification passed, no required action remains | `satisfy --what "<criterion>" --evidence OBS-n` for each criterion, and `dispatch` on every capability at `observed` or beyond |
| **B — genuine blocker** | the required action has no reachable capability, no alternative capability, no available context path, no viable recovery, and no valid replan — all five | `blocked --what --reason --tried ... --next-action ...` with non-empty routes, and a delivery audited clean |

There is no third terminal state. A run that ends having done neither has not
finished; it has stopped, and stopping is only legitimate as one of the two.

## The invariant

```text
IF the task is not complete
AND a viable next action exists
THEN execute the next action.
```

Held at every point, the kernel continuously answers: what remains incomplete,
what is blocking it, whether that blocker can be removed, what capability removes
it, whether that capability is reachable, what context it requires, whether that
context can be acquired, what alternative strategy exists, and what the next
executable action is. If there is an executable next action, execute it.

## What is not completion

Planning is not completion. Skill discovery is not. Agent selection is not.
Delegation is not. Partial execution is not. A proposed solution is not. A
blocker statement is not. Only a **verified completed outcome** is.

## The phrasings a run may not end on

These are enumerated, which is what makes them checkable — `run-state.py audit`
refuses a delivery that opens on one of them.

| Phrasing | Why it is a terminal state in disguise |
|---|---|
| "I didn't touch this task." | The unit was never opened. |
| "I only planned it." | A plan is not execution. |
| "I identified the required skill but did not use it." | `candidate_found` is never `task_completed`, and never `blocked` either. |
| "I found the agent." | Discovery stopped one step short of invocation. |
| "This would require another agent." | If that agent is reachable, the answer is to invoke it. |
| "I need more context." | If the context can be acquired, acquiring it is route 2. |
| "The first approach failed." | If alternatives exist, they are the next action. |
| "This is complex." | Complexity is a rung, and a rung is revised by evidence. |
| "I cannot guarantee success." | Not a reason to stop while useful execution remains. |
| "I wasn't sure." | Uncertainty is a trigger to acquire, not a verdict. |

And the blocker constructions, which are worse than the above because they assert
a fact about the world that is not true:

> "I did not use the skill, therefore blocked."
> "I did not call the agent, therefore unavailable."
> "I need more information, therefore blocked."
> "The task is complex, therefore blocked."
> "The first method failed, therefore blocked."

A capability that was not looked for is a **hypothesis**, not a finding about the
host. This is the one that runs in both directions: it is the same error whether
it ends a run early or reports a capability as absent.

## Why this is a mechanism and not a paragraph

Because prose does not work here, and that is measured rather than assumed:

- An explicit "do not give up" or checklist line in a system prompt **does not
  improve paired success** (PushBench, arXiv:2605.23574). Verifier gating alone
  completed **zero** backlogs that progress-state control finished 25–50% of.
- A model asked to judge its own completeness **anchors on confident closing
  language** and scores a trajectory "completed" regardless of what happened —
  AUROC ≤ 0.65 across five judge models and five prompt conditions
  (arXiv:2606.09863).
- Fail-and-report is *strong* on a different axis: it scored **1.000** on both
  answer quality and gap quality (Partial Evidence Bench, arXiv:2605.05379) —
  and the same work found a model **over-blocked at 21.4%** of safe questions.

That last point is the reason both directions are gated. A rule that only says
"keep going" trades a false-completion rate for a refusal rate, and the refusal
rate is invisible until someone needs the answer. Here, a decline satisfies no
criterion and produces no deliverable, so an over-blocker cannot pass either.

Which is also the honest account of the failure this kernel has. The dominant
violation is **under-action** — 48.4% of violations, an elicitation gap rather
than a capability limit (ACL 2026, "Action Boundary Blindness"), and an explicit
boundary prompt recovers 42–47% of it. A kernel that nudges harder is treating a
symptom. A kernel that makes the omission *visible in state* is treating the
cause: an unattempted action and a proven impossibility leave different traces,
so the report can no longer pass for the work.

## The route list

If the objective is not met, walk these in order and take the first `yes`. It is
`references/recovery-system.md` — the classification — read as a checklist,
because the classification is what you consult once you have already decided to
stop.

| # | Route | What it means here |
|---|---|---|
| 1 | `retry` | The cause is identified and transient; attempt again, bounded |
| 2 | `acquire-context` | Something needed was never loaded → `context --ref` |
| 3 | `other-skill` | The capability exists as a skill, not as a tool |
| 4 | `other-agent` | Another mode or another agent can hold it → `set-mode` |
| 5 | `inline` | Runnable in the context already in hand, and correctly so |
| 6 | `delegate` | Specialisation clearly beats doing it → `set-mode --mode delegate` |
| 7 | `route` | Spans several sources → `set-mode --mode route` |
| 8 | `reorder` | A different order of the same units |
| 9 | `decompose` | The objective splits into more, smaller units |
| 10 | `other-resource` | Something exists that this route did not consider |
| 11 | `replan` | The strategy was wrong → back to JEv and re-decide |
| 12 | `recover` | Recover from the failed state rather than restarting it |
| 13 | `continue-partially` | Do what is possible now, resolving the rest as a dependency |
| 14 | `reduce-scope` | The objective reduces to what is already done |
| 15 | `no-path-remains` | Every answer above is `no` — and only now may the run stop |

The names are a closed vocabulary, not prose, because `blocked --routes` draws
from them and a free-text route would mean whatever the run needed it to mean.
`tools/test-run-state.py` asserts that this table and the `ROUTES` constant hold
the same fifteen names in the same order, so the two cannot drift — which is the
whole reason the list is written down.

```sh
python3 tools/run-state.py blocked --what "<the blocked part>" --reason "<why>" \
  --tried "<what you actually looked for>" --routes <one of the fifteen>
```

`--routes` is the checkable half and `--tried` is the evidence, and they are
separate because they fail in opposite directions: a block with a route and no
detail asserts a category without showing any work, and a block with detail and
no route asserts that nothing systematic was tried — the claim that most needs
support and is least often given it.

**Two of these are machine-checkable** and `check` decides them alone: route 1 is
the dispatch gate, and route 5 is the acceptance gate. The other thirteen are
judgements. A rule that stopped a run on the model's reading of its own list
would be the self-judgement failure above wearing a different hat, so they are
written down and reviewed by whoever reads the run.

## Recovery is not the end of the task

```text
FAILURE → OBSERVE → UNDERSTAND FAILURE → JEv RE-DECISION → REPLAN
        → ALTERNATIVE CAPABILITY → ALTERNATIVE COORDINATION MODE
        → ADDITIONAL CONTEXT ON DEMAND → RETRY → VERIFY → CONTINUE
```

Never stop because the first plan failed, the first capability failed, context is
missing, a specialist is needed, a specialist failed, the task is complex, or one
strategy failed. Change the plan. Find another capability. Acquire the context.
Invoke the specialist. Recover through JEv. Decompose it. Replan.

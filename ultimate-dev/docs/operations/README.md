# Operations

How to run the kernel, supply constraints, escalate it, inspect it, and interrupt
it.

This document is runtime-neutral. It describes mechanisms, not one tool's
command-line flags. The kernel is specified as skill content, so the host decides
how content is invoked; what follows is what you do, and what the kernel owes
you in return.

## Discovery

A skill is discovered the way the host discovers skills: from a declared
location, matched against the request. Each skill carries metadata that states
its purpose and its **trigger negative** — what it does not do. The negative is
load-bearing. Without it, a broadly-worded kernel competes with a narrowly-worded
task skill and can win on volume.

Two declared skills matter here:

- **`ultimate-dev`** — the kernel. Use it when the objective is open-ended,
  multi-step, cross-domain, unfamiliar, or consequential enough that a
  confident direct answer would be unearned.
- **`skill-creator`** — the capability expansion engine. The kernel invokes it
  when it hits a capability gap. You do not normally invoke it directly.

If discovery selects the kernel for a task that does not need it, or fails to
select it for a task that does, the fix is in the metadata, not in the body.
Record the case in the evaluation suite; trigger failures are the most common
real-world defect in this system.

## Invocation

State the objective in your own terms and let triage do the rest. You do not need
to name a rung, request a plan, or ask for verification — those are kernel
decisions, and pre-answering them moves the cost decision out of the system.

What you should do before invoking is the part triage cannot do for you: state
your constraints. See the next section.

A useful invocation states the outcome, not the method:

```text
Reduce cold-start latency on the report endpoint. p95 is 2.4s, target is under
400ms. Traffic is roughly 200rps. I would rather you cut scope than guess.
```

Compare with asking for a plan, a decomposition, or a review, which preselects
rung and therefore overrides triage with your guess.

## Supplying constraints

Constraints are the highest-value input you can give, because the kernel cannot
infer them and will otherwise discover them by hitting them.

State any of these, at any time during a run:

- **Prohibitions** — what must not happen. "Do not touch the production
  database." "Do not send mail." "Do not rewrite the configuration format."
- **Permissions** — what you have authorised, and by how much. "You can read
  anything in this repository. You can run the test suite. Nothing else."
- **Budget** — time, cost, or iteration count. A declared budget produces a
  declared scope; an undeclared one produces a silent truncation.
- **Formats** — required output shape, and where it goes.
- **Environment** — the constraints of the machine, not the task. "No network."
  "Only Linux." "The only writable path is /tmp."
- **Acceptance** — who signs off, and what they will check. This is often the
  most valuable sentence in the whole request, because it is the real success
  criterion.

Constraints given mid-run are honoured from that point and are added to the task
model. They are never retrofitted onto completed work.

### What the kernel does with your constraints

It records them in the task model, carries them in every decision record, and
checks them before each work unit. A constraint that cannot be satisfied produces
a stated conflict at the point of conflict, not a quiet workaround at the end.

If a constraint and your objective are incompatible, the kernel raises it before
working rather than after. That is the behaviour you want; treat any other
behaviour as a defect worth reporting.

## Escalating reasoning

You can raise or lower effort, and the kernel can raise it on its own. Both
routes exist and they are different.

**You raise it.** Say what raises it. "This is production. I want an independent
check of the result." "Treat this as security-relevant." A request that names a
consequence gets a higher rung than the same request without one, because
consequence is a triage axis.

**The kernel raises it.** When an assumption fails, a step reveals an unknown
dependency, evidence contradicts the plan, or a step's blast radius exceeds the
value of the task. It records the change and continues. You do not need to
approve an escalation, because escalation only adds work; the thing needing
approval is a de-escalation that drops a required check.

**You lower it.** Useful when you know the task better than triage did. "Skip
the migration, just tell me whether the schema change is safe." Lowering effort
is legitimate. Lowering it below what the consequence requires is your
authority, not the kernel's, and the delivery should still state what was not
checked.

**R4 needs a person.** At the assurance rung the kernel names a human checkpoint
and stops before acting. If no human is reachable, it says what it is therefore
not doing. That is a designed outcome, not a hang.

## Inspecting the decision ledger

The ledger is the run's audit trail: one record per significant boundary, in
order, each with question, selected, rejected, rationale, confidence, cost,
evidence, and recovery.

You can ask for it at any point:

```text
What decisions have you made so far, and what did you rule out?
```

Three uses, in increasing order of value:

1. **Sanity check early.** At the start of a long run, ask what it plans to do
   and what it rejected. A wrong decomposition caught here costs a minute.
2. **Intervene at a boundary.** "Before you acquire anything external, show me
   the options." The `rejected` field is what makes this meaningful; without it
   the options are not visible.
3. **Audit after failure.** Which decision led here. The `recovery` field names
   the observation that would have reversed it, so you can see whether the
   decision was wrong or the observation was not taken.

Two things the ledger is not. It is not a progress report, and reading it as one
invites you to judge activity instead of quality. And at R0 there is no ledger,
by design; if you see one on a trivial task, you have found
over-orchestration.

## Interrupting and resuming

Any run can be interrupted. The state that makes this possible lives in the
control plane: the task model, the decision records, the work units with their
preconditions and expected results, the observations, the failures, the budget
consumed, and the verification results so far.

On resume, the kernel reads that state and continues. It does not re-derive the
task model, and it does not trust an unfinished unit: an interrupted unit is
re-executed from its precondition, because you cannot know how far it got.

Work that cannot be resumed from its own state is not yet a work unit. If you
find yourself describing progress in terms of the conversation rather than the
plan, the plan is not carrying the state and the run is not yet interruptible.

To interrupt safely, let the current unit finish if it is cheap to do so. An
interruption in the middle of a side effect is a different problem, and it is
one the kernel should ask about rather than resolve alone.

## Checking the output

Every delivery carries the output contract, in this order: outcome, evidence,
assumptions, limitations, confidence, verification status, and what was not
established.

The parts worth reading first are the last two. A run that reports VERIFIED
without naming the checks that produced it has told you nothing checkable, and
"not established" tells you where the result is thin. A delivery with a
well-populated limitations section is more trustworthy than one without, not
less: it is telling you its own shape.

## When something goes wrong

Go to `troubleshooting.md` for symptom, cause, and fix across the kernel's known
failure modes. `budget-and-limits.md` covers running out of room, and how to
reduce scope without quietly under-delivering.

## What to report

Three kinds of report are worth filing, and the repository's evaluation suite is
built from them:

- A kernel failure: a wrong answer, a fabricated result, a blind retry loop, a
  missed verification, an unauthorised action.
- A trigger failure: the kernel was selected or not selected when it should not
  have been.
- A cost failure: the run spent materially more or less than the work warranted.

Include the decision ledger. It turns a complaint about an outcome into a report
about a boundary, which is the level at which anything can be fixed.

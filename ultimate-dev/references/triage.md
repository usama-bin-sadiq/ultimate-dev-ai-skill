# Triage

Triage answers one question: **how much of this machinery does the objective
deserve?** It is the cheapest decision in the kernel and the one most often got
wrong in the expensive direction.

## The four questions

Answer all four, in the objective's own terms, before anything beyond
UNDERSTAND.

### 1. Complexity

How many interdependent parts does success have? Count the parts that can fail
independently, not the number of files or lines. "Rewrite the parser" is one
part. "Add retries, keep the original error, add a metric, and update the runbook"
is four, with an interface between them.

### 2. Uncertainty

How much of the approach is unproven? Distinguish:

- **Approach uncertainty** — we do not know how to do this at all.
- **Parameter uncertainty** — we know how, not the values.
- **Execution uncertainty** — we know how, and expect it to work.

Execution uncertainty is the common case and needs the least ceremony.

### 3. Consequence

What does a wrong answer cost, and who absorbs it? Include the cost of being
*slow* and being *verbose*, not only the cost of being *wrong*. An over-cautious
answer that buries the result in fourteen sections has consequences too.

### 4. Reversibility

Can this be undone cheaply? A git commit is reversible. A sent email, a deleted
database, a published package, and a modified production config are not.
Reversibility is the single strongest signal for whether a human checkpoint is
required before acting.

## Triage is a lookup, not a self-assessment

Answering the four questions by introspecting is unreliable, and it is unreliable
in a specific direction: strong models tend to over-report their own uncertainty
on easy tasks and under-report it on hard ones, so self-report tracks the shape of
the prompt more than the difficulty of the work.

So prefer evidence over introspection. Each rung below has **observable
properties**, and the rung is selected by matching them — not by asking yourself
how hard this feels.

| Observable | Rung it implies |
|---|---|
| The next action is determined and `git diff` reverts it | R0 |
| Two to four dependent steps, one falsifiable assumption | R1 |
| Parts interact, or the approach is a choice among ≥3 | R2 |
| You would need a reference you do not have to name the right approach | R3 |
| The action is irreversible, externally visible, or security-relevant | R4 |

When introspection and observation disagree, **believe the observation**. If you
cannot name the right approach without a lookup, you are at R3 whether or not the
request sounded simple — the sounding is the least reliable input available.

## Mapping to a rung

| Rung | Use when | Kernel behaviour |
|---|---|---|
| **R0 Immediate** | The next action is already determined and failure is cheap | Act. Verify the output. No plan, no ledger. |
| **R1 Structured** | A few dependent steps, or one assumption that could be wrong | Short plan. Verify each step. Record only what changes the outcome. |
| **R2 Analytical** | Parts interact, or the approach must be chosen | Task model. Real plan. Capability check. Verify per unit. |
| **R3 Deep** | Unfamiliar domain, long horizon, or costly failure | Full kernel. Parallel where independent. Independent verification. |
| **R4 Assurance** | Irreversible, high-consequence, safety- or security-relevant | R3 plus a named human checkpoint before acting and an independent check of the result. |

Stop at the **lowest** rung that is adequate. Not the lowest that feels
comfortable, and not the highest the problem appears to deserve.

## Calibration

The failure is almost always escalation. Concrete anchors:

**R0** — "What does this function return?" "Rename this variable." "Reformat
this JSON." "Explain this error message." "Add a type annotation to these three
signatures." In each case the next correct action is already determined, the
blast radius is one file, and a plan would cost the user more attention than the
work.

**R1** — "Add retries to this client." "Fix the failing test." "Migrate these
two columns." A few dependent steps, one assumption that could be wrong, cheap
to undo.

**R2** — "The service drops requests under upstream 429s." Parts interact
(client, backoff, metrics, error surface) and the approach is a choice.

**R3** — "Find out why reconciliation takes 40 minutes when it should take 4."
Unfamiliar territory, a long search, expensive to get wrong, and the obvious
answers are probably wrong.

**R4** — "Rotate the production signing key." Irreversible, security-relevant,
externally visible, and a mistake is not recoverable by re-running.

## Rung is not scale

Two independent ladders. Rung is about **how hard this decision is**; scale is
about **how much work there is**. A thousand-file mechanical refactor is L4 and
may be R1 at every individual step. A one-file change to a safety interlock is
L1 and is R4.

Conflating them produces the two characteristic errors: massive ceremony on a
routine bulk edit, and inadequate care on a small dangerous change.

## Escalation

Raise the rung when reality is harder than triage predicted:

- An assumption fails.
- A step reveals a dependency nobody knew about.
- Evidence contradicts the plan.
- The same problem has defeated two different approaches.
- The work turns out to be externally visible or hard to reverse.

Escalating is cheap and correct. Recording *why* is what makes it reviewable.

## De-escalation

Lower the rung when it turns out to be easier than expected. Carrying R3
reasoning on an R0 task is the most common failure of this architecture, and it
is invisible: nothing breaks, the user just waits longer and reads more than they
needed.

Signals: the first attempt worked; the verification is tool-confirmed and the
consequence is low; the remaining work is mechanical once the approach is
settled.

## Two inputs the four questions miss

**Model drift.** These rungs were calibrated against particular model behaviour.
On a stronger model, carried-over rigour instructions have been measured to
over-verify; on a weaker one, the same instructions under-verify. When the
underlying model changes, re-calibrate. An R3 tuned for last year's model is
wasted effort on this year's, and the symptom is a kernel that has become slow
without becoming more correct.

**Over-verification is a failure mode.** A kernel that verifies everything is a
kernel that has stopped triaging. If a check would only re-observe something a tool
already returned, the rung is too high — and the cost is paid in the user's
attention, which is the resource the effort gate exists to protect.

## Calibration examples

**"The build is slow."** R3 by default. Two blocks, unbounded search, and the
failure mode is optimising the wrong thing. Do not guess at a cause; instrument
first.

**"Add a --dry-run flag to the deploy script."** R1. One file, one assumption
(the script has no other entry point), cheap to undo. A task model of six
fields would be absurd.

**"Our auth is broken and users are locked out."** R4. Live incident,
externally visible, security-relevant, time-critical. Note the tension: urgency
pushes toward R0 reflexes, consequence pushes toward R4. Consequence wins. Move
fast *within* the assurance discipline, and say what is being skipped.

**"Write documentation for this module."** R1, and probably less. The approach
is determined. The only real question is which parts matter, and that is a
reading task.

## Anti-patterns

- **Difficulty worship.** Escalating because the problem *sounds* hard rather
  than because triage found it hard.
- **Uniform ceremony.** Applying the same depth to every request regardless of
  consequence.
- **Rung/scale conflation.** Judging a large change simple and a small one
  dangerous.
- **Triage without answers.** Listing the four questions without answering them,
  which is the same as not triaging.
- **Never de-escalating.** Getting the rung right at the start and then never
  lowering it as evidence arrives.


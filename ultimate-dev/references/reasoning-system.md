# Reasoning System

The reasoning ladder R0–R4 sets a **floor on rigour, not a quota**. You set the
rung once at Step 0 from the triage answers, apply exactly the behaviours that
rung requires, and revisit it at every JEv. The ladder exists so effort is
proportional to the task, not so every task is treated as hard.

## The rungs

| Rung | Trigger condition | Required behaviours |
|---|---|---|
| **R0 Immediate** | The next action is already determined and failure is cheap | Act. Verify the output. No plan, no ledger. Stop. |
| **R1 Structured** | A few dependent steps, or one assumption that could be wrong | Short plan. Verify each step. Record only what changes the outcome. |
| **R2 Analytical** | Parts interact, or the approach must be chosen | Task model. Real plan. Capability check. Verify per work unit. |
| **R3 Deep** | Unfamiliar domain, long horizon, or costly failure | Full kernel. Parallel where independent. Independent verification. |
| **R4 Assurance** | Irreversible, high-consequence, safety- or security-relevant | R3 plus a named human checkpoint **before acting** and an independent check of the result |

## What each rung actually demands

**R0.** Name the next action, do it, and check the output. If the check fails,
that is a rung error, not a reason to expand. Do not produce a plan, a
triage record, or a capability search for work whose next step was already
determined. The test is not how big the task looks; it is whether the next
correct action is already determined.

**R1.** Two to five steps in order, each with a check. Keep records only where
they would change the outcome — a decision record per meaningful boundary, not
a diary. If a step's result cannot be checked, that is a rung or plan defect.

**R2.** Write the task model (objective, requirements, constraints, unknowns,
assumptions, success criteria), resolve capabilities before use, and verify
each work unit against its declared expected result. Interacting parts mean the
plan, not the sequence of commands, carries the work.

**R3.** Run the whole kernel, and exploit genuine independence: parallel
execution where units do not share state, and an independent check on results
you are inclined to trust. R3 is also where unknowns get labelled blocking or
not, because at this scale an unexamined unknown surfaces as a late surprise.

**R4.** Everything in R3, and two additions that are not optional. First, a
**named human checkpoint before acting** — a specific person or role, told what
is about to happen, what is irreversible, and what evidence exists. Second, an
**independent check of the result**: derived by a different route, by someone or
something that did not produce the first derivation. R4 work that was only
carefully done is not assured; it is carefully done.

## Escalate when

| Trigger | Escalate to |
|---|---|
| An assumption fails | R2 minimum — correct the assumption, re-plan dependents |
| A step reveals an unknown dependency | R2, or R3 if the horizon just grew |
| Evidence contradicts the plan | R3 — the plan is wrong, not the observation |
| The blast radius grows (more surfaces, users, money, data) | R3–R4 by consequence |
| Work becomes irreversible or externally visible | R4 — named checkpoint before acting |
| A human is about to act on your output | R4 — the risk transfers, so the assurance must too |

Escalation is a decision at JEv: record the trigger, the new rung, and what it
buys. Never escalate silently.

## De-escalate when

- The unknowns you feared are resolved and now blocking.
- The failure cost turned out to be bounded and the fix is cheap.
- A capability check proved the task is a known procedure.
- The verification is tool-confirmed and low-stakes.

De-escalation is a decision too. Record it, and drop the machinery you no
longer need: plans, ledgers, extra verifiers. **Carrying R3 reasoning on an R0
task is waste, and it is the most common failure of this kernel** — the user
pays in time and attention for nothing.

## Difficulty worship

Escalating because the problem *sounds* hard, rather than because triage found
it hard, is an anti-pattern. Complexity, uncertainty, consequence and
reversibility — the four Step 0 questions, handled in `triage.md` — are the
only legitimate basis for the rung. Novel vocabulary is not complexity. A long
prompt is not an unfamiliar domain.

The ladder is a floor, so an unlabelled task that is genuinely hard must still
reach the right rung. But "be thorough" is not a rung, and there is no rung
above R4: past assurance, the answer is a human, not more reasoning.

See `strategy-system.md` for what the rung's deliberation must produce,
`model-adaptation.md` for adapting the form of work to the executor, and
`verification-system.md` for the depth each rung implies.

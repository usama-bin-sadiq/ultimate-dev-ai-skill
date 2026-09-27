# 0004. An explicit effort ladder

Status: Accepted
Date: 2026-09-26
Deciders: architecture maintainers

## Context

The kernel is capable enough to plan, acquire capabilities, decompose work,
delegate, and verify in depth. On a general objective, all of that is available
to it all the time. Nothing in the raw capability stops a one-line change from
being executed as a nine-stage programme with a capability search and a review
panel.

This is the most likely failure of the system, and it is more likely because the
architecture is good. An agent that can do more will do more, and the user pays
in latency, in tokens, and in attention spent reading process they did not
request. The result arrives eventually and is usually correct, which is exactly
what makes the defect durable: nothing looks broken.

The opposite failure is just as real. Fixing over-orchestration by defaulting to
minimum effort means a novel, irreversible, high-consequence action gets the same
treatment as arithmetic. That is worse than over-orchestration, because the
verification is missing rather than merely excessive, and the user has no signal
that anything was skipped.

**Cost is not observable from inside the task.** The kernel cannot feel that a
plan is unnecessary. It can only be told. So the cost decision has to be written
down at the point where it is made, or nobody makes it.

**Difficulty is not measurable by the model.** A confidently-worded request for a
scheduler rewrite reads as harder than a request to fix an off-by-one, and
frequently is easier. Any mechanism that keys on the impression of difficulty
inherits the impression.

**The temptation to average.** Four axes — complexity, uncertainty, consequence,
reversibility — invite a single score. A single score is exactly wrong here: a
trivially simple action that cannot be undone is the highest-consequence case
there is, and averaging hides it.

**Escalation has to be possible after triage.** Real work reveals unknowns. A
mechanism that fixes effort at the start cannot respond, and a plan whose effort
cannot rise is a plan that fails rather than adapts.

## Decision

Adopt an **explicit effort ladder**: five named rungs, chosen at triage from
four questions, recorded, and revisable by evidence.

1. Triage answers four questions before any stage beyond understanding:
   **complexity** (how many interdependent parts does success have),
   **uncertainty** (how much of the approach is unproven), **consequence**
   (what does a wrong answer cost, and who absorbs it), **reversibility** (can it
   be undone cheaply). All four are recorded. They are not averaged.
2. The answers map to a rung: **R0 Immediate**, **R1 Structured**, **R2
   Analytical**, **R3 Deep**, **R4 Assurance**. The kernel stops at the lowest
   rung that is adequate.
3. The triage record states the **rung**, the **scale level**, the reason this
   rung and not the one below, and two triggers: the observable event that
   forces the rung up, and the observable event that lets it drop. A triage
   without triggers cannot be revised by evidence.
4. The rung determines **which decision boundaries must be crossed** and
   therefore what the run does. R0 crosses two by default and produces no
   ledger. R4 crosses all seventeen and adds a named human checkpoint *before*
   acting.
5. The rung sets the **floor for rigour, not a quota**. At R0 the task model is
   one line. The ladder does not require detail the rung cannot use.
6. **De-escalation is a first-class move**, not a failure. Carrying R3 reasoning
   on an R0 task is named as the most common defect of this system.
7. **Escalation conditions are observable events**, not impressions: an
   assumption failed, a step revealed an unknown dependency, evidence
   contradicted the plan, or a step's blast radius exceeds the value of the task.
8. **Rung does not authorise action.** An irreversible, externally visible,
   credential-bearing, or ambiguously authorised action is escalated for
   confirmation regardless of rung. R0 is not an exemption from human control.
9. Rung is recorded as a decision like any other, including at R0, so that cost
   is inspectable even when nothing else is.

## Consequences

**Easier.** Cost becomes arguable. Over-orchestration becomes visible in the
record instead of only in the user's patience. Under-reasoning on
high-consequence work becomes a violation of a stated rule rather than an
unnoticed omission. The same kernel runs at R0 and R4 without branching, which is
what makes [0001](0001-jev-as-decision-fabric.md) and the L1-to-L7 claim hold
together. New tasks need no new mode: they need a rung.

**Harder.** Triage is a mandatory step that produces no visible work, and a
kernel under time pressure will want to skip it. Four questions is more thinking
than most tasks warrant, and the rule "only to the depth the rung justifies"
has to be honoured or the mechanism becomes the thing it was meant to prevent.
Boundary-crossing tables have to be maintained as the ladder evolves, and a stale
table is worse than none. Most awkwardly: a correct triage is invisible to
review, so bad triages surface only as user irritation, which is a slow and
noisy signal.

**New failure modes this makes more likely.** **Difficulty worship** —
escalating because the problem sounds hard, which the triggers are meant to
prevent but cannot fully, because sound is all that is available before work
starts. **Ledger theatre at the low end**, where R0 runs produce a record to
prove diligence, which is the same defect in a smaller costume. **Rung inertia**,
where the initial triage holds for the whole run and the triggers are never
evaluated, so a task that turned R3 stays R3 after becoming trivial.
**Under-triage**, which is the dangerous direction and the one the evaluation
suite must watch hardest: a high-consequence action run at R0 looks identical
from the outside to a correct cheap task.

## Alternatives considered

**Always run the full kernel.** Rejected. It is the failure this decision
exists to prevent, and it is not fixable by telling the model to be brief: the
cost is in the deliberation, not in the output length.

**Always run minimum, escalate on exception.** Rejected because the first
exception is invisible, and because it makes the safe path the default for
precisely the tasks where the safe path is wrong. A production schema migration
that fails a smoke check after execution is a post-hoc check of an irreversible
act.

**Model self-assessment of difficulty.** Rejected. Self-assessment correlates
with fluency, not with difficulty, and a capable model can argue itself into any
rung. It is also unverifiable from outside, so the cost decision stays invisible.

**A composite score from the four axes.** Rejected because averaging is
destructive. Simple and irreversible is the highest-stakes case, and a composite
score places it mid-table. The axes stay separate and each is recorded.

**Continuous effort, no named rungs.** Rejected. A continuum has no anchor, so
every run picks a different interpretation of "reasonable", and comparisons
across runs are impossible. Named rungs make the decision a word, which can be
argued with.

**Let the user set the rung.** Rejected as the primary mechanism, because the
user usually does not know which rung is adequate, and asking transfers triage
cost to the person the kernel exists to help. Rung is an inference, with the
user's own constraints feeding it as inputs.

**Two modes: fast path and full path.** Rejected. This is the mode switch
`../architecture/scalability.md` claims does not exist, and a binary split puts
every real task in the wrong bucket near the boundary.

**Let the model choose a token or time budget instead of a rung.** Rejected as
the control, retained as an input. A budget is necessary and not sufficient: a
large budget on a trivial task produces exactly the over-orchestration we are
avoiding, and a small budget on a hard task produces a truncated run with no
signal that truncation happened.

## Revisit when

- The evaluation suite shows systematic under-triage: high-consequence cases
  completed at R0 with no human checkpoint. That is the failure to watch, and it
  justifies raising the floor rather than adding guidance.
- A rung is observed to be mis-set often enough that the four triage questions
  are the wrong axes, or that one question dominates. Then change the questions
  and supersede this record.
- De-escalation is never taken in practice, which would mean the triggers are
  theoretical and the ladder is only a starting estimate.
- A new level of work appears that the rung ladder cannot express, and the
  honest response is a new rung with a new ADR rather than an ad-hoc expansion
  of R4.
- Measurement makes an automatic triage rule viable, that is, a rule which
  predicts the adequate rung from the objective with acceptable error. Test it
  against human triage on the benchmark set before adopting it; the bias in
  `../../research/decision-making/` is the reason to be cautious.

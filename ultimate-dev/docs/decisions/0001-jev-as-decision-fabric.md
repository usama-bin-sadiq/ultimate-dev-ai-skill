# 0001. JEv as the decision fabric

Status: Accepted
Date: 2026-09-26
Deciders: architecture maintainers

## Context

The kernel must work on problems nobody has anticipated: a rename, a distributed
consensus bug, a literature review, a memory manager. The obvious way to serve
an open set of problems is a pipeline: a fixed sequence of stages that every
task traverses. This is what most agent frameworks are, and it is why they are
good at the tasks they were written for and brittle everywhere else.

A pipeline is cheap to specify and easy to test. It also embeds two commitments
that this architecture cannot accept.

First, a pipeline commits to an order. It decides that capability resolution
happens before planning, that context is loaded once, and that verification
happens at the end. Each of those is wrong for some real task. A task that needs
a capability discovered mid-execution, a task where the plan must change after
the first observation, and a task where the first verification failure tells you
the whole approach was misconceived, all break a pipeline.

Second, a pipeline cannot say why. When a run goes well nobody records which
choice produced the outcome, so the next run starts from defaults rather than
from understanding. When a run goes badly, there is no record to review, so the
diagnosis is reconstruction from memory by whoever is reading, and it is usually
wrong.

We also need a way to make cost a decision. Over-orchestration is the defect we
expect most often, and a pipeline cannot address it: the pipeline runs in full
regardless, so the only defence is for the operator to not invoke it, which
pushes triage out of the system and into the user's judgement.

One further constraint: whatever we adopt must work at every scale. A mechanism
that is a stage at L3 and a subroutine at L5 is two mechanisms.

## Decision

Adopt **JEv**: a decision procedure applied at every boundary where the shape of
the work could change, producing a **decision record** at each such boundary.

Concretely:

1. Seventeen boundaries exist and are fixed: task understanding, decomposition,
   context retrieval, context depth, capability selection, capability
   acquisition, strategy selection, workflow selection, reasoning effort,
   specialist delegation, parallelisation, research depth, verification depth,
   retry, replanning, escalation, learning promotion.
2. Every boundary crossing is a decision, and every decision is recorded.
3. A record contains: question, selected, rejected, rationale, confidence,
   cost, evidence, recovery. The `rejected` field is mandatory. A decision with
   no recorded alternative is an assertion and is not treated as a decision.
4. Which boundaries a run must cross is itself a decision, made from the rung.
   R0 crosses two by default. R4 crosses all seventeen and adds a named human
   checkpoint.
5. The objective of every decision is expected outcome per unit of cost, risk,
   and uncertainty. Minimising tokens, calls, or time is explicitly not the
   objective.
6. Every boundary can be re-entered from anywhere, and any boundary may return
   the run to the decision point.

## Consequences

**Easier.** Review becomes possible. A run can be audited by reading its
records, and a decision can be reversed by observing the condition its record
named. Cost becomes arguable: "why did this run take that long" has an answer,
and the answer is a decision someone can disagree with. The same procedure
applies unchanged at L1 and L7, so scale costs resources rather than
architecture.

**Harder.** Every kernel change must be justified at the boundary level, which
is slower than adding a stage. The `rejected` field is uncomfortable to write
when there genuinely was no choice, and the honest answer there is usually that
the choice was not noticed — which is itself a finding. The record format is a
tax on every significant decision, and at high volume it will be skimmed unless
the rung discipline holds. If records are skipped at R0, the same pressure will
erode them at R2.

**New failure modes this makes more likely.** Recorded decisions invite
post-hoc justification: a run that knows it must write `rejected` will invent
an alternative it did not consider. Records that are written for the reviewer
rather than for the next decision will be plausible and empty. A ledger
inspected only at the end of a run is a report, not a control, and the fix is
that records are written at the boundary, not compiled later.

## Alternatives considered

**Fixed pipeline with optional stages.** Rejected. It keeps the ordering
commitment, and optional stages reintroduce the branching the design is trying
to remove. It also cannot express "reconsider the plan from the middle of unit
four" without becoming the decision procedure under another name.

**Router: classify the task, then dispatch to a domain pipeline.** Rejected on
the architecture's central claim. It requires knowing the domain set in advance,
which is exactly the constraint the PRD forbids. It also degrades at the
boundary: an OS task that is classified as "systems" and then turns out to
require an unfamiliar hardware protocol has no route forward except a new route,
which means a new router.

**Agent swarm: many specialists, one coordinator.** Rejected. Coordination
cost grows faster than capability value, and the coordinator becomes the
architecture. A specialist can only be selected by a decision, so the decision
point survives anyway; putting the decision inside a swarm makes it harder to
inspect. See [0002](0002-skills-are-resources-not-agents.md).

**ReAct-style interleaved reasoning and acting, with no explicit decision
record.** Rejected. The loop is retained as the lifecycle, but reasoning that
is not recorded cannot be audited and cannot be re-entered deliberately. The
defect it fixes — a run that repeats the same mistake for the third time — is
precisely what the record prevents.

**Fully autonomous planning, no records, but a strong verifier.** Rejected
because the verifier then carries the entire burden of quality, and a verifier
cannot check a decision it was not told about. A model-based diagnostic is a
better tool for that, and it needs the records as input.

**Event log plus post-hoc rationale generation.** Rejected. Rationale written
after the fact is a story about what happened, not a record of what was decided
at the time, and it is systematically biased toward the outcome. Under failure
it produces exactly the plausible explanation that is hardest to disprove.

## Revisit when

- Records are demonstrably being written to satisfy the reviewer rather than the
  next decision, and a run audit shows no real use of the `recovery` field.
- The seventeen boundaries prove incomplete on real workloads, and a boundary
  keeps being crossed without a record because it is not on the list.
- The record format's cost measurably exceeds its use at high decision volume:
  track decisions per run and audit time per run against incident time saved.
- Metareasoning research in `../../research/decision-making/` produces a
  decision rule measurably better than "expected outcome per unit of cost, risk,
  and uncertainty", which is currently a stance rather than a rule.
- A benchmark shows rung-based crossing sets under-select boundaries at R2 or
  R3, and the failure mode is missed verification rather than excess cost.

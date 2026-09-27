# Concepts

The vocabulary of this architecture, defined once. If a term here conflicts with
how you are using it, the term is what this repository means. Each entry gives a
definition and a discriminating note: what the term is *not*. The notes exist
because most of these words are looser in ordinary use, and the loose meaning is
where the defects live.

Two terms here — **evidence** and **provenance** — carry a longer treatment in
[verification-and-evidence.md](verification-and-evidence.md), which sets out the
chain connecting a claim to its source and the checks that decide whether the
claim survives. Read the entries below first; that document assumes them.

## JEv

The decision fabric: the decision procedure applied at every boundary that
changes the shape of the work, plus the record it produces. It selects an action,
names the alternatives it rejected, and states confidence, cost, evidence, and the
condition that would reverse the decision.
**Not** a stage, and **not** a router. It never asks "which agent handles
finance"; it asks what the decision requires, and the answer comes from the task
model rather than a table.

## Decision record

The written output of one JEv crossing: question, selected, rejected, rationale,
confidence, cost, evidence, recovery. It is the unit of auditability here, and a
run you cannot reconstruct from its records is a run you cannot review.
**Not** a log entry. A log records that something happened; a decision record
records a choice made against named alternatives, under stated uncertainty.

## Rung

The effort level R0 to R4, chosen at triage from complexity, uncertainty,
consequence, and reversibility. It governs how much reasoning, planning, and
verification a unit receives.
**Not** a difficulty label. A rung is a cost decision, taken at the lowest level
that is adequate, and revised when evidence arrives.

## Scale level

The size of the work, L1 to L7: one task through a civilisational programme. It
governs resources, planning depth, and coordination structure.
**Not** a rung. One irreversible production action is R4 and L1. The two are
independent, and averaging them destroys the information.

## Work unit

An atomic piece of work with a declared precondition, an expected result, its own
verification, and its own resume point. The unit is what makes a plan
interruptible and progress auditable.
**Not** a task, a step, or a phase. A step is not a unit unless it can be resumed,
verified, and reported on independently.

## Capability

Any means of making progress: a skill, tool, command, person, document, model,
deterministic operation, or something that does not exist yet. Resolved in a
fixed order, and validated before use.
**Not** an agent. Capabilities are resources selected by the kernel; see
[0002](../decisions/0002-skills-are-resources-not-agents.md).

## Capability gap

A specific absence: a need with no available means, recorded precisely enough to
be closed, and routed to composition or creation rather than worked around.
**Not** difficulty, and **not** a licence to improvise. A gap that gets papered
over becomes an unvalidated capability producing confident nonsense.

## Context level

The depth of material loaded, C0 to C6, from the task state alone to specialist
depth. Chosen against a specific decision, not against the size of the available
material.
**Not** a token count or a session length. C0 is a floor and C6 a fallback; both
are selected, and both are recorded.

## Evidence

A recorded observation that bears on a specific claim, with its source and the
transformations applied to it. Evidence supports a claim or it does not; an
artifact sitting in the transcript is not evidence.
**Not** a citation, and **not** a claim. "The file exists" and "the file says
this" are different statements, and only the second supports a conclusion.

## Provenance

The record of where each item of context or evidence came from, when it was
retrieved, and what was done to it. It makes freshness checkable and claims
traceable.
**Not** attribution for its own sake. It answers two questions later: how did we
know this, and is it still true.

## Epistemic status

The label on a claim: known, inferred, assumed, unverified, uncertain, or
contradicted. It travels with the claim everywhere it goes.
**Not** model confidence, and **not** a synonym for "probably true". `assumed`
means load-bearing and unchecked; `inferred` means something was checked and the
conclusion did not follow directly.

## Promotion

The move of a candidate lesson or capability from validated to retained, with a
stated scope and evidence that it generalises. Promotion is the only way the
system changes itself.
**Not** saving a file, and **not** a cache. It changes future behaviour, which is
why it is gated; see [0003](../decisions/0003-gated-learning-lifecycle.md).

## Deprecation

The retirement of a promoted capability or lesson, with the reason recorded. A
system that can promote but not deprecate accumulates rules that were once true
and are now wrong, invisibly, until one causes a failure.
**Not** deletion. The record of why it was retired is what stops the same mistake
being promoted again.

## Trigger negative

An explicit statement of what a skill does **not** do, written into its
definition so discovery does not select it for the wrong work.
**Not** a list of future work, and **not** optional. Without it a broad
description matches everything and the trigger signal splits.

## Blind retry

Repeating an action whose cause is unknown. It reproduces the failure, consumes
budget, and produces the appearance of effort, which is worse than an honest stop
because it delays the classification.
**Not** a second attempt. A second attempt with an identified cause and a stated
bound is recovery. The question that separates them: can you name the cause in
one line?

## Over-orchestration

Running the full process on work that does not need it: a plan, a capability
search, and a verification ceremony for a one-line change.
**Not** thoroughness, and **not** a documentation preference. The test is whether
the next correct action was already determined. If it was, the elaborate path is
a defect.

## Effort ladder

The R0 to R4 set, chosen at triage, revised by evidence, with escalation and
de-escalation triggers recorded. It makes cost a decision rather than a habit.
**Not** a difficulty estimate, and **not** fixed for the run. A ladder that cannot
be climbed or descended is a label.

## Decision ledger

The accumulated decision records for a run, in order, with their evidence and
recovery conditions. It is the run's audit trail and the input to
self-evaluation.
**Not** an event log, and **not** required at every rung. R0 produces no ledger by
design; producing one anyway is over-orchestration.

## Blast radius

How much of the work an action can damage, used in triage and in recovery. An
action whose blast radius exceeds the value of the task is escalated however
simple it is.
**Not** reversibility. Reversible actions can still be expensive; irreversible ones
can still be small. Both axes are asked separately.

## Checkpoint

A named point where accumulated work is verified as a whole, not only unit by
unit, and where the run can be interrupted with its state intact. They appear at
L5 and above, and at every R4 irreversible action.
**Not** a save file. A checkpoint includes evidence and verification state, so
resuming does not re-derive what was established.

## Unsupported objective

An objective the kernel cannot pursue with the resources, capabilities, or
authority available. Reporting it plainly, with what is missing, is a successful
outcome.
**Not** a failure to be worked around. Substituting a different problem converts
an honest block into a wrong answer, and the user cannot tell which happened.

## Verification depth

How the result is checked: evidence, validation, or independent re-derivation.
Selected at JEv, scaled to risk, consequence, uncertainty, novelty, and evidence
quality.
**Not** a pipeline stage that is more thorough for large tasks. It is a decision,
and it is made every time.

## Atomicity

The property that makes a work unit safe to verify, resume, and abandon
independently. A unit that cannot be abandoned without losing everything after it
is not a unit. **Not** smallness: a unit may be large, but it must be whole.

## Handoff

The transfer of a result from one level, workstream, or delegate to the next, in
the output contract format. A handoff carries evidence, assumptions, limitations,
and confidence, not a transcript. **Not** a summary: a summary that drops the
limitations is a laundered claim, and the receiving level cannot tell.

## Words to avoid in your own writing

Confident, robust, seamless, powerful, and intelligent describe impressions, not
states. Prefer the state: "verified by X", "reproduced on Y", "not established".
If you cannot replace an adjective with a check, cut the sentence.
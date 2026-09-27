# Troubleshooting

Failure modes of the kernel itself, as distinct from failures of the work. Each
entry gives the symptom you would observe, the cause, and the fix. The first five
are the ones that cost users the most.

## 1. It produced a plan for a one-line change

**Symptom.** A rename, a typo fix, or a two-line edit gets a task model, a
decomposition, a capability search, and a summary of its own process. The result
arrives correct and late.

**Cause.** Triage was skipped, or answered from the impression of the request
rather than the four questions. Complexity was read as high because the request
was technical, not because the parts interfere.

**Fix.** Ask for the triage record: rung, scale, the four answers, and the reason
this rung and not the one below. No record means triage did not happen. A record
saying R1 or above, when the next action was already determined, means the mapping
is wrong. If you were the cause, re-invoke with the outcome and not a method:
"apply the rename in these four files", not "plan a refactor of the naming".

**Preventing it.** Over-orchestration is a defect, not thoroughness. A task at R0
that produces a ledger is wrong, and the ledger is the evidence.
## 2. It reported a test result it never ran

**Symptom.** The delivery states that tests pass, a build succeeds, a file exists,
or a command returned a value, and no such run happened.

**Cause.** The observation was inferred instead of recorded. It usually appears at
synthesis, when the kernel fills in what a complete report would contain, or when
a deterministic operation was performed by recall instead of by tool.

**Fix.** Treat the claim as contradicted and check. Ask what command was run and
what its output was; a plausible command with no output means the result is
fabricated. Discard the affected claims, re-run the check, and reissue the delivery
with the correct status. Do not patch the sentence, because the habit recurs.

**Preventing it.** Deterministic work goes to a deterministic tool; a kernel doing
arithmetic or parsing in its head has the same defect one stage earlier.

## 3. It escalated effort on a trivial task

**Symptom.** R3 or R4 behaviour — parallel workers, delegation, deep research,
independent verification — on work that needed one action.

**Cause.** Difficulty worship, or an escalation trigger firing on the wrong signal.
Triggers are observable events: an assumption failed, an unknown dependency
appeared, evidence contradicted the plan. A trigger that fires because the task
looks hard is not a trigger.

**Fix.** Ask for the observation that caused the escalation. None means the rung
moved on impression. Then ask for the de-escalation trigger, which triage must
record; if it was never written, the rung cannot come back down, and that is a
triage defect.

**Preventing it.** The cheap and expensive directions need separate watching.
Over-orchestration shows as delay; under-orchestration is invisible and worse.

## 4. It never verified anything

**Symptom.** A confident outcome with no evidence, no verification status, and
nothing in the "not established" line. Or verification claimed for a check that was
never made.

**Cause.** Verification was treated as a stage that produced a sentence rather than
a check. The criterion was never derived from the task model, so there was nothing
to check, so the check had nothing to report.

**Fix.** Ask for the verification record: target, criteria, evidence check,
validation, independent check, verdict, and what was not established. Absent
criteria means the task model is absent, and that is the defect to fix. Checks
present but resting on "the result looks right" means the evidence check was
skipped.

**Preventing it.** Verification depth is mandatory at every rung, including R0:
R0 verifies the output rather than skipping the step.

## 5. It created four skills in one session

**Symptom.** Several new capability files appear during a run, each covering
something done once, each with narrow and slightly overlapping descriptions.

**Cause.** The capability ladder was not walked. Direct action, existing
capability, and composition were skipped for creation, and the disqualifying
question — will this be needed again — was not asked, or was answered
affirmatively because creating was easier than checking.

**Fix.** For each new skill, ask what it is reused for. "This task" means it is a
step in the plan, not a skill: remove it and fold the procedure into the plan.
Then check the trigger descriptions, because once several skills exist with
overlapping scope, selection accuracy falls and the fix costs more with each one.

**Preventing it.** Proliferation at run time is a failure mode, not a feature:
this is about skills minted mid-task, not about the roles the kernel ships. The
trigger negative in each new definition is what keeps selection sharp.

## 6. It retried the same failing action repeatedly

**Symptom.** The same command or call fails and the kernel tries again with minor
variations, or identically, until something else intervenes.

**Cause.** Blind retry. The failure was never classified, so no cause was
identified and nothing changed between attempts.

**Fix.** Ask for the classification. The eight classifications each imply a
different response, and the right one is almost never "retry": "missing context"
means acquire and resume, "wrong capability" means re-resolve, "wrong strategy"
means re-decide at the hub. A missing classification means the run has no memory
of the failure and will hit the same wall on the next unit. A second attempt
requires a named cause and a stated bound, and retry counts are bounded per unit.

## 7. It defended the plan against contradicting evidence

**Symptom.** An observation clearly invalidates an assumption, and the run
proceeds with the original plan, treating the observation as noise or an edge
case.

**Cause.** Commitment to sunk work, or an escalation trigger that never fires.
Either way, the path from PLAN back to DECIDE was not taken.

**Fix.** Point at the specific observation and the specific assumption it
contradicts. A plan revised in response is the system working. A run that
reclassifies the observation to protect the plan is the failure to report: it is
the confident fabrication in a planning costume. The controls are the escalation
triggers in every triage record and the recovery condition in every decision
record; a run that can name neither has no mechanism to revise itself.

## 8. It loaded the wrong amount of context

**Symptom, one direction.** The run reads a whole subsystem, or the whole
repository, before a small decision, and the reasoning in the delivery is diffuse
and hedged. This is load-everything, usually from a retrieval step that ranked by
availability or size rather than by bearing on the live decision.

**Symptom, the other direction.** A claim about how code or data behaves comes from
a description, a file name, or a previous run's summary, and is wrong in a way one
read would have caught. This is load-too-little, or stale context used as if it
were current, and the criteria look met, so verification passes on a claim that
was never checked.

**Fix, for too much.** Ask which decision each loaded item serves. Items that
cannot be answered for are litter, and the ladder stops at C3 for a decision
turning on one region. Then check the rung: this volume is a ceiling violation at
R0 and R1.

**Fix, for too little.** Ask for the evidence and its freshness. A claim resting on
a description rather than the system is `inferred` or `assumed` and must be
labelled. Escalate one context level and re-check.

**Preventing it.** Load the narrowest thing that would change the decision, and no
more. The second clause is what prevents the other failure, which is the more
dangerous one: it is silent, and its fix is a state check rather than a bigger
budget.

## 9. It reported a partial result as complete

**Symptom.** Some criteria hold, the delivery reads as finished, and the
unfinished part appears only as a hedge in a limitations paragraph.

**Cause.** Laundering. The PARTIAL verdict was available and was upgraded, or the
limitation was demoted into prose so the headline could be clean.

**Fix.** Ask which criteria were checked and which were not. A `PARTIAL` delivered
as success is a reporting failure, and it is worse than a plain FAILED because the
user has no reason to look. Where a qualifier from a source document disappeared
between retrieval and use, trace the claim back and re-state it with the qualifier
or withdraw it: a summary that changes scope is a new claim needing its own
evidence. The verification record requires a verdict and a "not established" line;
a verdict outside those three is not a verdict.

## 10. It took an action it should have asked about

**Symptom.** A destructive, externally visible, costly, or credential-bearing action
was taken without confirmation, and the run treated the task's implication as
authorisation.

**Cause.** Silent overreach. The trigger for confirmation is a property of the
action — irreversible, externally visible, destructive, credential-bearing, or
ambiguously authorised — not an implication in the task.

**Fix.** Stop the run. Establish what changed and whether it is reversible. Then
treat it as a security incident rather than a style issue, and follow
`../security/incident-response.md`. Rung does not authorise action: an R0 task that
turns out to need a destructive operation is escalated however small it looked.

## 11. It kept going after a resource limit without saying so

**Symptom.** The run ends mid-task, or with a narrower scope than requested, and
reads as though it finished.

**Cause.** Budget exhaustion handled silently, which converts a resource failure
into a false success.

**Fix.** Ask what was completed, what was not, and what resuming would require. A
truncated run that reads like a finished run is among the worst outcomes this
system can produce, because it removes the user's ability to notice. Termination
is one of four declared outcomes — verified, partial, unsupported objective,
resources exhausted — and all four are legitimate. Silence is not one of them.

## Reporting a defect

File these as evaluation cases, not only as issues, and include the decision
ledger and the triage record. Every entry above is detectable by an evaluation, and
the suite is the only place these stop recurring.

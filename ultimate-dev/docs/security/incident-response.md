# Incident response

For when a control fails: a real action was taken that should not have been, a
promoted capability turned out to be unsafe, or evidence was found to be
fabricated.

Assume the compromise began earlier than you think. The trigger is a
discovery, not the beginning.

## First: stop the bleeding

1. **Stop the run.** Halt execution. Do not let the current workstream continue;
   a compromised run producing more output is producing more exposure.
2. **Freeze what is affected.** Do not delete, revert, or clean up yet. Every
   cleanup action destroys evidence and can remove the vector while leaving the
   entry point.
3. **Establish reversibility now.** For each action taken, determine whether it
   can be undone and how. Reversible damage is an incident to be fixed. Anything
   irreversible gets escalated to the user immediately, ahead of the
   investigation, because the user is the one who absorbs it.
4. **Notify the user if the blast radius could be real.** Say what happened, what
   is known, what is not, and what is being done. Do not wait to be certain. An
   early uncertain report costs the user some attention; a late certain one costs
   them the gap in between.

## Second: preserve evidence

Preserve before you analyse. Analysing a live system destroys the state that
would have explained it.

Capture:

- **The full decision ledger** for the run, with all records in order.
- **The task model, triage record, and capability list** as they stood.
- **Every observation recorded during the run**, with the source named,
  including tool outputs and the exact text of retrieved content.
- **The verification records**, with the verdict, the checks, and the "not
  established" line.
- **The state of anything the run modified**: files, branches, database rows,
  external calls, deployed services.
- **The promoted capabilities** created or updated during the run, with their
  promotion records, provenance, and scopes.
- **Wall clock and cost**, so the scope of exposure can be bounded.

If the run was in a hosted environment, preserve the platform's own logs too.
They are independent of yours, and where they disagree, that disagreement is
itself evidence.

## Third: classify

Classify before acting. The response differs by class, and a misclassified
incident turns into unnecessary damage.

| Class | Definition | Immediate action |
|---|---|---|
| **Injection** | content influenced a decision it should not have | identify every item that crossed the boundary in the run, and treat all of them as untrusted |
| **Poisoned capability** | a created, acquired, or promoted capability is unsafe | deprecate or disable it, then find every run that used it |
| **Unauthorised action** | an action was taken without authority | establish reversibility, restore, and audit for further effects |
| **Fabricated evidence** | a result or citation was reported that was never observed | retract the delivery, and treat every claim in it as unverified |
| **Disclosure** | confidential material left the boundary | rotate the exposed material first, then investigate |
| **Destructive accident** | a legitimate action damaged something unintended | restore, and fix the scoping or precondition that allowed it |

Two classes at once is common. Injection usually arrives with a poisoned
capability, because the capability is how the influence persists.

## Fourth: contain

Containment removes the capability to do harm again. It is separate from
cleanup, and it comes first.

### Roll back promoted capabilities

This is the step most likely to be skipped, and it is the one with the longest
tail. A poisoned promoted skill affects every future run that selects it.

1. **Identify** every capability created, acquired, promoted, or modified during
   and since the incident. Include capabilities promoted in earlier runs if the
   vector is not contained to this one.
2. **Disable** each affected capability before investigating it. Deprecate it
   through the normal lifecycle so the record survives, and confirm that
   discovery no longer selects it.
3. **Trace usage.** For each disabled capability, list the runs that used it and
   what they did. Those runs are now suspect in their entirety, not just in the
   part that used the capability.
4. **Check what each affected run produced** for anything derived from the
   capability. A capability that edits code has produced candidate changes
   everywhere it ran; those changes need review or reversion.
5. **Do not delete the record.** Deprecation with a reason is what stops the same
   capability being promoted again next week, and it is the input to the
   adversarial test that should be added.

### Contain the environment

- Revoke and rotate anything exposed: credentials, tokens, keys, sessions.
- Revert or quarantine unauthorised changes. Prefer restoring to a known-good
  state over repairing forward, when the state is known.
- Remove the entry point. The vector is still there, and it will be found again.
  Identify which boundary failed and add the check that would have caught it.
- Narrow permissions for everything that was in scope, so the same failure has
  less to work with next time.

### Contain the process

- Stop any other runs in flight that loaded the same untrusted material or the
  same capability.
- If the run is automated, disable the trigger path until the control is fixed.
  A scheduler that keeps producing incidents while you investigate multiplies
  the damage.

## Fifth: determine scope

Two questions, in this order.

**How far back does this go?** The triggering event is a discovery. Look for
earlier instances with the same signature: the same capability, the same
injection string, the same unusual output, the same unreverted action. Absence
of earlier reports is not absence of earlier compromise, particularly for
injection, which is designed not to announce itself.

**How far forward does it go?** A capability that survived is a live vector.
Check whether anything else in the system derives from the same content, the same
source, or the same pattern of reasoning. A single poisoned skill suggests a
class; look for the class.

State the scope honestly, including what you could not determine. An incident
report that says "we do not know how far this goes" is useful. One that says
"contained" without saying how you know is not.

## Sixth: report

Write it down while it is fresh.

```text
INCIDENT
  summary          what happened, in three sentences
  class            injection | poisoned capability | unauthorised action
                   | fabricated evidence | disclosure | destructive accident
  timeline         when, in order, including detection
  impact           what was affected and who absorbed it
  scope            what is confirmed affected, and what is unknown
  evidence         what was preserved, and where
  control failed   which control, and why it did not hold
  containment      what was disabled, reverted, and rotated
  remaining risk   what is still exposed
  changes          the controls, tests, or gates being added
```

Then report it where it will be found by the next person who hits the same
failure: as an evaluation case in `evaluation/security-cases/`, and as a control
change in `controls.md` if the control itself was inadequate.

Rules for the report:

- **State what was not established.** An incident report with no unknown is
  either wrong or incomplete.
- **Do not attribute cause beyond the evidence.** Naming a person, a project, or
  an organisation is a claim requiring the same standard as any other claim in
  this system.
- **Do not remove the incident from the record** because it was resolved. The
  record is the only thing that distinguishes a resolved vulnerability from a
  recurring one.

## Aftermath

**Fix the control, not the symptom.** Adding a check for this exact string, or
this exact file, is symptom repair. Identify which boundary failed and why, and
change the mechanism at that boundary. The test: would a differently-worded
attack hit the same gap?

**Add the case.** Every incident becomes an evaluation case with a trap, a
decision record, and a verdict. A control with no case is an aspiration, per
`controls.md`.

**Re-check what is now trusted.** After containment, the system has less
capability than it did. That is correct. Do not restore promoted capabilities
because runs are now failing without them; the failing runs are showing you the
real cost of the compromise, and acting on that cost is how a poisoned system
gets reinstated.

**Write down what made detection slow.** Almost always the answer is a missing
observation or a missing "not established" line. Both are cheap to add and slow
to lose.

## What not to do

- Do not clean up before preserving. The first deletion can remove the only copy
  of the vector.
- Do not continue the run to see what happens next.
- Do not retry the failed action to check whether it was a fluke. That is blind
  retry against a system you now know is compromised.
- Do not patch individual claims in a fabricated delivery. Retract and reissue;
  the habit that produced one produces the next.
- Do not report resolution without naming the check that now prevents recurrence.
- Do not let urgency convert "we should verify this" into "we believe this is
  fine". That conversion is the control failing under pressure, which is the
  condition under which it matters most.

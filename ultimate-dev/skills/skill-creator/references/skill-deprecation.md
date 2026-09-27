# Skill deprecation

**Removal must be as easy as installation.** A skill that is easy to add and
hard to remove is a permanent, unappealable claim on every future decision, and
it is the reason self-improvement becomes self-corruption. If you cannot describe
the removal in one step, you have built something you will not be able to undo.

A promoted skill that turns out wrong must be **identifiable, attributable, and
removable**. Each is a record you had to keep while the skill was working.

## Three reasons, each with its evidence

| Reason | The evidence that establishes it | Then |
|---|---|---|
| **Superseded** | A skill or composition that does the same job better, measured | Point callers at the replacement, then remove |
| **Drifted** | Description no longer matches the body, or a contract assumption has expired | Fix or remove — do not leave a skill that fires on what it can no longer do |
| **Wrong** | A case where it produced a bad result, a security finding, or a false trigger with a real cost | Remove, and record what it got wrong |

Drift is the common one and the one most often left alone, because nothing
failed yet. A skill whose description promises a capability its body no longer
implements is worse than an absent one, because the description is what future
runs match against.

## How a deprecated skill stops being used

Deprecation is a sequence, and stopping early leaves a skill that is announced
as retired and still fires.

1. **Withdraw the trigger.** Change the description so nothing selects it. This
   is the step that actually stops use.
2. **Migrate the callers.** Anything composing it, or relying on its declared
   outputs, gets pointed at the replacement or at a direct step.
3. **Record the state.** The provenance entry moves to DEPRECATED with the date,
   the reason, the evidence, and the version that was live
   (`skill-provenance.md`).
4. **Remove the files.** One deletion. No downstream edit, no shim, no redirect.
5. **Keep the record.** The provenance outlives the files, including the failures
   it recorded on the way (`skill-provenance.md`).

## The hard requirement

- **Identifiable** — the failure is named, and linked to the version that
  produced it. A defect you cannot point at a version is a defect you cannot
  bound.
- **Attributable** — the provenance names the run, the decisions, and the
  assumptions. Blame attaches to the *decision*, not to the run that carried it
  out; a run is not a person and cannot be the lesson.
- **Removable** — one deletion plus a record update. If removal requires editing
  anything outside the skill, the design was wrong and that is the finding.

## What deprecation does not do

It does not fix a live problem by deletion alone. If callers depend on the
behaviour, migrate first; a removal that breaks an active chain is a new
incident, not a cleanup.

It does not license a replacement in the same pass. A successor is a new
candidate with its own contract, its own security review, and its own gate
(`skill-promotion.md`). "Deprecate and replace" done as one decision is how an
unreviewed skill inherits a trusted name.

It does not rewrite history. Deprecation updates a state; it never removes a
finding, a failed test, or a resolved defect. A record with nothing wrong in it
is not a record.

## Stop conditions

Do not remove while: callers still select it and have not been migrated, or the
evidence for the reason is not recorded. Do not retire a skill merely because it
has not fired in a long time — that is drift in the other direction, and the
answer is a version that re-tests it, not a deletion. Do not leave a skill in
DEPRECATED state with its files still selectable; the withdrawal in step 1 is
what makes the state real.

# Observation System

An observation is a record of what actually happened. Not what you expected, not
what usually happens, not what the output pattern suggests — what you saw. If an
action was not run, there is no observation, and any account of one is
fabrication.

## The observation record

Every meaningful execution produces one entry, in this order:

```text
OBSERVATION
  action       what was actually done, concretely enough to repeat
  result       what came back, including absence of output
  state change what is different now — files, data, decisions, beliefs
  evidence     the specific artefact that supports the claim
  error        the failure text, classified (see recovery-system.md)
  unexpected   anything that does not fit the plan's model of the situation
```

The record is short. Its value is that the `unexpected` and `state change`
fields are filled honestly, not that the entry is long.

## Every meaningful execution updates the run state

State is the accumulated, checkable picture of the run: which units are done,
which assumptions are now tested, which capabilities are validated, which
unknowns remain blocking, what has been observed versus inferred. If an
execution does not change state, either it was not meaningful or you have not
finished recording it — decide which, and do not leave it ambiguous.

State is what survives interruption. A run whose state lives only in your
reasoning is a run that restarts from nothing, and one that restarts from
nothing eventually guesses.

## Observed, expected, assumed

These three are different, and collapsing them is how an assumption becomes a
fact by losing its qualifier.

| Kind | Where it comes from | How it may be used |
|---|---|---|
| **Observed** | An action you ran and a result you saw | May be relied on, cited as evidence, and extended by reasoning |
| **Expected** | A documented behaviour, a prior result, an inference | May be used as a working basis, and must be marked expected until observed |
| **Assumed** | Your model, convention, or a gap in the evidence | May not be reported as fact. Name it, and say what breaks if it is false |

Mark a claim as expected or assumed every time you carry it forward. When
observation later contradicts it, the record shows which downstream work rested
on it — that list is the re-plan scope in `planning-system.md`.

## Record the surprise explicitly

A surprise is anything you did not anticipate: a file that was not there, an
error with a different cause than the one you expected, a result that is
technically correct and useless, a tool that succeeded in a way that changes
what it means.

Write it down rather than smoothing it over, because an unrecorded surprise
silently rewrites your model of the situation while your plan keeps running on
the old model. That gap is where confident wrong answers come from. Record it,
then decide at JEv whether it changes the plan, the strategy, or only your
expectations.

Distinguish "the outcome differed from the expected result" (common, cheap) from
"the outcome was different in a way that changes the approach" (a JEv boundary,
record it as a decision).

## An error is information, not noise

Every error is classified **before any response** — missing context, wrong
capability, wrong strategy, bad assumption, execution failure, resource
failure, verification failure, unsupported objective. The classification, not
your discomfort, decides the response. Blind retry is prohibited: repeating an
action whose cause is unknown reproduces the failure and burns budget while
producing the appearance of effort. See `recovery-system.md`.

An error you cannot classify is itself a finding: say that, and treat the
obvious classification as unproven.

## Fabrication

**An unrun action produces no observation, and inferring one is fabrication.**
This includes describing a command's output, citing a test outcome, quoting a
document you did not read, or reporting a file's contents from memory. It also
includes the softer forms: "this typically returns", "the build should pass",
"based on the last run". If you did not observe it, the sentence does not go in
the deliverable.

This is the failure the rest of the system exists to prevent, and it is the one
that cannot be caught downstream.

See `execution-system.md` for the actions that produce observations,
`state-system.md` for run state, `evidence-system.md` for turning observations
into support, and `verification-system.md` for deciding what to trust.

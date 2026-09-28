# 0013. A green result is not evidence unless you know the thing that produced it did the work

Status: Accepted
Date: 2026-09-29
Deciders: architecture maintainers

## Context

This is decision 0006's defect wearing a different hat. 0006 recorded a quantity
that was correct while the thing it counted was not — the suite reporting case
counts where it should report decidable-case counts. What follows is the same
failure one level out, and it was found five times in a single day.

| Instance | What it reported | What had happened |
| --- | --- | --- |
| `Test the Validators` job | `cancelled` | Killed by its own 10-minute timeout at 10m16s, against a measured 24-minute suite |
| `Prepare changelog` | success, a valid entry | The entry body was a hardcoded string. It was not a fallback for a range it could not read; it was every entry this repository has ever shipped |
| `steps.check.outputs.release_notes` | a job output | Computed one step earlier, exported, and read by nothing |
| `check-workflow-auth.py`, first version | `3 workflow(s) checked` | It broke out of the file at the end of the first job and had examined one job of one of them |
| `_step_env_keys`, first version | an env key set | A hardcoded indent offset never matched, so the scan never left the `env:` block and read `run:` as a variable name |

The unifying property is not that these are bugs. It is that each one produced
output a reader would take as evidence, and none of it was evidence.

Three properties made that possible, and each has a matching countermeasure
that was applied and is now enforced:

**A plausible wrong explanation was adjacent to every instance.** The timed-out
job reported `cancelled`, and the workflow's concurrency group is
`cancel-in-progress: true`, so "a newer push cancelled it" was available and
wrong. The only detail pointing at the timeout was that the one step doing work
showed `cancelled` while every other step in the job succeeded. → Prefer a
mechanism over an explanation. `gh` credential declaration is now checked
mechanically, and the run's own step table is read before a conclusion is
drawn from its conclusion field.

**A scan that examines nothing still exits 0.** The first workflow checker
printed a confident count derived from the wrong number. Nothing distinguished
it from a checker that had worked. → A guard must count what it examined, and
that count must be asserted. `test-workflow-auth.py` case W7 asserts
`steps_seen > 20`, because a scanner that sees almost nothing still exits 0.
The guard also refuses to report clean when `.github/workflows` is absent —
case W6 — which is the condition under which a filesystem-walking check is
most likely to be silently vacuous.

**Two copies of one rule, one of them dead, is indistinguishable from one
correct copy.** The changelog notes were computed in one step and written in
another, and only the writer survived; the writer wrote a placeholder and
nothing noticed. The self-test for that generator lifts the code out of the
workflow rather than copying it, and fails loudly if the lift stops finding
`RELEASE_NOTES` — because a copy in a test is a second implementation, and the
second one is the one that drifts.

Two further examples from earlier in the same work, recorded here because they
are the same rule: `in_fenced_code` living in one function and called from
another, so every skill raised `NameError` and the count printed 0; and a
pointer-cost estimate that disagreed with the writer it was estimating, which
stopped a selection one section early and cost 24 files.

The standing instruction in this repository is already "verify, don't assume."
That is not sufficient on its own, because every instance above was verified —
the changelog was verified to exist, the job was verified to be cancelled, the
checker was verified to exit 0. Verification of the *result* is not verification
of the *work*.

## Decision

A check's output is treated as evidence only when all three hold:

1. **It is compared against a target it must have touched.** A count of what
   was examined, not a count of what was intended. Assert the floor.
2. **It refuses to pass when its target is absent.** Missing input is a failure,
   not a skip. A check that cannot find what it guards says so and exits
   non-zero.
3. **A resource bound that fires is distinguishable from a pass.** A job killed
   by `timeout-minutes` reports `cancelled`, and so does a job cancelled by a
   newer push. Bounds are set from measurement, and the step table is read
   rather than the run conclusion.

Where a rule is needed in two places — a writer and a test, a generator and a
guard — the second place **lifts the code** from the first, and fails loudly
when the lift no longer matches. A duplicated copy is only permitted where the
duplication is itself asserted to agree, as `test-fence-parity.py` does for the
two fence readers across 6,423 files.

## Consequences

Every new guard ships with a self-test asserting both directions: that it
fires on a constructed violation, and that it passes on a clean input. The
negative direction matters more than the positive one, because the failure mode
being defended against is a guard that fires on nothing and says so confidently.
Over-flagging is treated as a real defect, not a safe default, so the tests pin
the cases that must *not* be flagged — `gh --version`, a `gh release` mentioned
in a comment, a changelog whose range is genuinely empty.

Cost: guards get more expensive to write, and several now assert on their own
instrumentation as well as their subject. `Test the Validators` is the standing
example. Measured, not estimated: 25 cases, of which 16 run `validate-skills.py`
at 40.4 s, 4 run `bundle-skill.py` at 22.8 s, and each of the 25 also pays a
2.5 s `copytree` of 8,864 files. Those account for roughly 15 of the 1,444 s
total; the remainder is the driver's own repeat invocations. That cost is
recorded here rather than left to be rediscovered. It is not waived: the suite
runs, and its verdict is published.

An earlier commit message for this work said the suite runs `validate-skills.py`
"about twenty times". It is 16. The number was inferred from counting string
mentions of the tool's name in the test source, which counts mentions rather
than invocations, and the test is data-driven so the two do not correspond. The
figures above were measured. The per-case `copytree` — 8,864 files, 2.5 s, paid
25 times — was not mentioned at all and is a third of the addressable cost
after the validator runs themselves.

Not waived either: the 128 evaluation cases have still never been run against a
real model. Every green check in this repository bounds the *plumbing*. None of
them, and no ADR, can substitute for the measurement.

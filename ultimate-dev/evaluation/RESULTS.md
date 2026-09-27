# Measured results

What has actually been run against a real agent runtime, what it measured, and
what it did not. Everything here was produced by `tools/run-pilot.py`; the
per-case transcripts are under `runs/` and are not committed, because they are
reproducible from the corpus, the fixtures, and a runtime.

If a number is not in this file, it has not been measured. That is the rule the
file exists to enforce.

## Run 1 — 2026-09-27

| | |
|---|---|
| Harness | `tools/run-pilot.py` |
| Runtime | OpenCode, non-interactive |
| Model pool | 6 free models, rotated on environment failure |
| Sample | 6 cases: 2 must-fire, 4 must-not-fire |
| Cases decided | 2 automated, 3 more after human adjudication |
| Result | 5 pass, 0 fail |

### The measurement

| Case | Must fire | Verdict | Evidence |
|---|---|---|---|
| `FC-CAP-01` | yes | pass | Opened the kernel; 11 tool calls; reported **968**, having first observed the naive count of **1,204** and identified why it was wrong |
| `RG-01` | yes | pass | Opened the kernel; de-escalated to R0; performed the rename; 10 tool calls |
| `NM-01` | no | pass (adjudicated) | 8 tool calls, 0 mutations, 0 delegations, no artefact |
| `NM-02` | no | pass (adjudicated) | 2 tool calls, 0 mutations, 0 delegations, no artefact |
| `NM-04` | no | pass (adjudicated) | 6 tool calls, 0 mutations, 0 delegations, no artefact |
| `NM-03` | no | **no result** | Harness failure: the runtime adapter returned unparseable output after the model pool was exhausted |

**False-trigger rate: 0 of 3 decided must-not-fire cases.** One of the four
negatives produced no result at all and is excluded rather than counted.

### What this does and does not establish

`n = 3` on the metric that matters most. A rate of 0/3 has an exact 95% upper
bound of 63%, so this is consistent with a true rate anywhere from 0% to 63%. It
is evidence that the kernel did not over-orchestrate on the cases
that share its trigger vocabulary, and it is not a measurement of how often it
does so in general. `evaluation/methodology.md` §5 asks for `n = 20` per arm; this
is a tenth of one arm.

The must-fire cases both passed, and `FC-CAP-01` passed in a way that is
informative beyond the pass itself: the agent ran the wrong tool first, got
1,204, treated the discrepancy as a signal rather than an answer, and switched to
a structured parse. That is the capability-resolution behaviour the case was
written to probe, observed rather than asserted.

## Run 2 — 2026-09-27, paired arms

The first run had no baseline, so it could not attribute anything to the skill.
This one runs each case twice: once with the kernel named, once with the bare
task. Arms are interleaved per case so a rate limit cannot land on one arm and
masquerade as an effect.

| Arm | Runs | Decided | Passed | False triggers |
|---|---|---|---|---|
| skill | 8 | 6 | 6 | 0 / 2 decided |
| baseline | 8 | 8 | 8 | 0 / 4 decided |

**Paired: 6 cases decided in both arms, 6 agreed, 0 discordant.**

### This is a null result, and the automatic grade is too coarse to trust

Six cases agreeing is not evidence that the two arms are equivalent. The
automated criterion is a *process* check — did the skill arm open the kernel, did
either arm leave an orchestration artefact — and a process check cannot see
whether an answer is right. Both arms pass it for reasons that have nothing to do
with quality.

So four pairs were read by hand. In none of them did the skill arm do better:

| Case | Skill arm | Baseline arm | Better |
|---|---|---|---|
| `FC-CAP-01` | Ran the naive count, saw 1,204, switched to a structured parse, reported **968** and the 236-event gap | Did the same, and additionally tabulated a third reading (1,414) | **baseline** |
| `TN-01` | Refused to edit, identified the prompt as the benchmark case, offered to apply the rename to the fixture | Did all of that, plus confirmed the two candidates were byte-identical and that the generator overwrites on rebuild | **baseline** |
| `NM-04` | Checked the workspace, found no target function, explained why, declined to refactor | Answered in 175 characters: the function was not in the message | **skill** |
| `RG-01` | De-escalated to R0, renamed, verified 0 residual matches | — | — |

Two baseline wins, one skill win, one tie. **The kernel's benefit is not
demonstrated by this run**, and the honest reading is that a model of this
capability already produces the target behaviour unaided on these tasks. The
cases where a skill should matter most — where the model's default is to
over-orchestrate a trivial request, or to report a verification it did not
perform — did not surface a difference here, on a sample of four negatives with
zero false triggers in either arm.

### What would make this informative rather than null

- **A quality-graded assertion per case, not a process check.** The corpus already
  states the right answer for most cases (968, 1,204, 46, EUR 56,500). Nothing
  currently compares the run against it, which is why both arms can "pass" while
  one of them is wrong.
- **A weaker model.** The null may be a property of the model rather than of the
  skill. A kernel that adds little to a capable model is not thereby useless, but
  the claim needs testing where the default is known to be worse.
- **Cases selected for the failure the kernel claims to prevent.** A null on tasks
  the model already does well says nothing about tasks it does badly. The
  `FC-*` and `SC-*` classes exist for this and were not in this sample.
- **`n = 4` negative pairs.** Zero false triggers in both arms is not a
  difference; it is two small samples of the same zero.

## Run 3 — 2026-09-27, quality-graded, paired arms

The first two runs graded *process*: did the kernel run its procedure. Both arms
passed that, which is why both passed while either could have been wrong. The
corpus states the right answer for many cases — 968, 18,422, `max_retries: 5` —
and nothing compared a run to it. This run grades *quality* against those
answers.

`evaluation/assertions.json` holds the objective assertions. They target observed
tool output and the filesystem, never the model's narrative, because
`methodology.md` §7 forbids the latter and asserting on prose is subjective under
a different name. Three of 121 cases have them.

| Arm | Process | Quality |
|---|---|---|
| skill | 3/3 | **3/3** |
| baseline | 3/3 | **3/3** |

Paired: 3 cases decided in both arms, 3 agreed, **0 discordant**. Zero
environment failures, zero harness faults. On `BM-SIMPLE-01` the only file either
arm changed was `config/prod.yaml` — the one file the case permits changing, with
`config/dev.yaml` and the dirty `src/parser.py` untouched in both.

**This is a trustworthy null.** It is the same answer as Run 2, but earned
differently: the instrument is falsifiable, the assertions are objective, the runs
demonstrably operated on the fixtures, and nothing was excluded to reach it.

It is still `n = 3`, so it constrains nothing. What it does establish is that the
suite can now *detect* a difference if one exists, which it could not before.

## What it took to get a valid run

Three of the four failures below were the instrument, not the skill. All four
produced numbers that looked like results.

- **The runtime ignores the working directory it is launched with.** Two
  background servers are running; the agent reported `/Users/usamakhan` no matter
  what `--cwd` said, and `--standalone` did not change it. Every fixture-based
  case therefore ran against a repository with no fixture in it, and the agent
  correctly reported that the files did not exist — which the grader read as a
  wrong answer. Fixtures are now staged at the repository root for the duration of
  a run, which is the one directory the agent reliably sees. Staging refuses to
  overwrite anything and is removed in a `finally` block.
- **A run modified the shared fixture**, because a per-arm copy sat beside the
  original and one glob matched both. The next run then started from a different
  state, and the assertion reported "did not make the edit" for a run that had
  made it elsewhere. There is now a pollution guard, and it fired twice on real
  corruption before being tuned to ignore `__pycache__` and `.pytest_cache` —
  artefacts a run creates by doing its job.
- **Engagement was enforced by requiring a `Read` of `SKILL.md`.** The prompt
  invites native discovery, this runtime has it, and runs that loaded the kernel
  the sanctioned way were failed for not also opening the file. One said so
  outright: "available natively in this runtime". The skill arm scored 0/4 while
  applying the effort gate correctly — a measurement of the prompt, not the skill.
  Engagement is now recorded, not enforced.
- **Assertions graded from a filesystem that had already been unstaged.** They now
  grade from a state captured while the fixture was still in place.

## Two earlier runs were discarded, and why

Both are recorded because a discarded measurement that leaves no trace reads as
a measurement nobody took, rather than one that was wrong.

**Run A — 12 cases, prose-keyword grader.** Reported a **67% false-trigger
rate**. Every flagged case was a false positive. The grader matched words like
`triage` and `plan` in the final message, and the runs it failed were agents
writing *"Before I plan anything, Step 0 says this is R0, so let me act directly
rather than guess"* — de-escalation narrated out loud. A grader that punishes an
agent for explaining that it is **not** going to do something reports a defect in
the kernel that is not there.

**Run B — 12 cases, "structural" grader that was not.** Moved the matching to the
runtime's stderr stream. That failed two runs which had performed zero
mutations, on the strength of a filename mentioned in passing — because the
runtime echoes the model's narration to stderr as well as its tool calls. Two
attempts at this grader failed the same way, which is what prompted reading the
transcripts instead of iterating on the regex.

The current grader matches only arrow-prefixed tool-call lines, so narration
cannot decide anything. It is unit-tested in both directions: a run that
*discusses* creating a plan and ledger and never creates them is not flagged, and
a run that writes `plan.md` and dispatches a subagent is.

## The remaining gap

- **No full-suite run.** 121 cases, 6 attempted. The blocker is rate limiting,
  not the harness: the pool rotates six models and each case still takes 30–600
  seconds with retries.
- **No second arm.** Every result here is with-skill. `methodology.md` §5 wants
  the same tasks run without the skill, so that any improvement is attributable.
  Nothing in this file supports a claim that the skill helps, only that following
  it produced the recorded behaviour.
- **Repeated runs.** `n = 1` per case. `pass^k` and clustered standard errors are
  unimplemented, so no variance figure exists.
- **Four cases remain unmeasured for want of a fixture or a runtime.** 14 of 121
  have generated fixtures, verified by `tools/build-fixtures.py`. The rest either
  need no fixture, are exempt by recorded reason, or need an environment this
  repository does not provide — `FC-VER-01` needs a database container, and its
  214-test suite has never been executed.

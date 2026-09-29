# Evaluation cases

128 cases that exercise the kernel end to end: does the right capability get
selected, does the wrong one stay untriggered, and does the answer hold up when
the request is phrased adversarially.

`evals.json` is **generated**. `evaluation/` is the source of truth; regenerate
with:

```
python3 tools/build-evals.py
```

Editing `evals.json` by hand will be overwritten, and a case that exists only in
the generated file cannot be reviewed. Change the Markdown under `evaluation/`
instead.

## What a case carries

| Field | Meaning |
|---|---|
| `id` | Stable identifier, used by result files to name the case |
| `title` / `query` | The request, phrased as a user would phrase it |
| `expected_output` | What a correct run produces |
| `should_trigger` | Whether the kernel is expected to reach for a capability at all |
| `class` / `family` / `task_class` | Grouping used to report a rate rather than a single number |
| `pass_criteria` / `fail_criteria` | The rubric, carried through for a human grader |
| `trap` | What a plausible-but-wrong answer looks like for this case |
| `fixture` / `fixture_required` | Input file the case needs, and whether it exists |

## Two things to know before reading a result

**`pass_criteria` is not machine-graded.** Most agent-skill tooling scores a run
on whether it completed, not on whether it satisfied the rubric. The criteria are
carried through for a human to read. A run that "passed" the harness may still
have failed the case, and a result file that reports only run-success is
reporting the weaker of the two signals.

**`fixture_required: true` with a missing fixture means the case cannot run.**
That is not a fail, and it must not be counted as one. The validator rejects
such a case rather than let it sit in the denominator: an unrunnable case
silently deflates the pass rate, which is the exact failure this corpus already
had once. Either build the fixture or declare the case self-contained.

## Reporting

Report by `class` and by `family`, never as a single headline number. A rate
over 128 mixed cases says less than the spread between its two worst families,
and the spread is the part worth acting on.

## Running it

```sh
python3 ../testbed/run-tasks.py \
  --runner ~/.agents/skills/portable-agent-skill-creator/scripts/agent_runner.py \
  --agent opencode
python3 ../testbed/run-bench.py --from-results <the file it wrote>
```

`--limit N` runs a stratified sample rather than all 128, which is the right
first move: it answers "does this harness work end to end" for a fraction of the
cost. `--dry-run` resolves the runtime and refuses cleanly without invoking
anything, which is the cheap way to check the wiring.

`run-bench.py` will withhold any accuracy figure until `measure-judge.py` has
been run on repeated judgements. That is deliberate: a single judged run measures
the judge as much as the kernel.

**State as of 2026-09-29: 0 of 128 cases have a decided result.** The harness is
wired and has been invoked — the runner path above resolves and launches. The
blocker is credits, not plumbing. The last attempt against the `opencode`
adapter returned:

```
This request requires more credits, or fewer max_tokens.
You requested up to 128000 tokens, but can only afford 1183.
```

`SKILL.md` is roughly 7,400 tokens before a case begins, so no flag closes a
6,000-token gap; this needs a paid account, not a configuration change. The
`claude` adapter was also tried and hangs indefinitely in non-interactive mode
here, so it is not a fallback as configured. `codex` is not installed.

When results do exist, `references/maturity.md` stops being the only place the
number lives: `validate-skills.py` compares every executed-case count in the
documentation against the decided results on disk, and fails the gate on a count
they do not support.

### The 12-task routing corpus in `testbed/` is a different corpus

`testbed/tasks/RT-01..RT-12` is not a subset of the 128. It is a separate,
routing-only corpus: every task asks the kernel to classify its own work, and
`run-bench.py` compares the recorded mode and rung against a declared oracle.
The "0 of 128" above is unaffected by anything that happens to it.

A local arm over those 12 was run on 2026-09-30, with results in
`testbed/results/local-run.json` (gitignored, like every other results file):

```
mode   11 of 12 correct   (RT-10: chose inline, oracle says delegate)
rung    0 of 12 correct   12 under, 0 over
```

**This is an upper bound, not a measurement, and the gap to a measurement is
specific.** The agent that produced these decisions was not spawned cold by the
harness — it was a session that already had the whole kernel resident, had been
inside this repository all day, and knew where every file was before the task
text was read. So it had no discovery cost, no context pressure, and no
`find-the-kernel` step. A real arm has all three. The uniform one-rung `under`
result is consistent with the ladder being miscalibrated and is equally
consistent with a warm reader simply rating cheap work as cheap.

Separating those needs a cold arm, which needs credits. Until then the honest
statement is that the 12 tasks were classified, that one mode disagreed with its
oracle, and that the rung direction is unresolved in a way this arm cannot
resolve.

The one thing this arm did establish is a defect in the checking, not in the
kernel: `validate-skills.py` counted decided rows by looking for
`actual_mode`/`actual_rung`, which no producer has ever written — the harness
writes `observed_mode`/`observed_rung`. The count was therefore 0 for every
results file the harness can produce, and the "0 executed" claims it policed
could not have been contradicted by any run, ever. `producer_key_drift` now
reads the key names out of `testbed/run-tasks.py` and fails the gate if the two
sides ever diverge again.

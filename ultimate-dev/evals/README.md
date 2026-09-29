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

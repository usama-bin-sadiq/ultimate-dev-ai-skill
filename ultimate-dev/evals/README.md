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

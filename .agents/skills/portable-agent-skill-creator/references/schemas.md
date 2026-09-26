# JSON Schemas

Every file this skill reads or writes, and the field reference for each. The
scripts are the source of truth: `scripts/utils.py` defines the loader and
`VALID_ASSERTION_TYPES`, and `scripts/grade.py` defines the grading contract.
Where this document and the code disagree, the code is right and this document
is a bug.

---

## evals.json

Input to `run_eval.py` and `run_loop.py`. Write it to your skill's `evals/`
directory. A bare JSON array of evals is also accepted.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "query": "Create a skill called pdf-notes that summarizes a PDF to markdown.",
      "expected_output": "A valid pdf-notes skill whose description states the goal and when to use it.",
      "should_trigger": true,
      "files": ["fixtures/sample.pdf"],
      "assertions": [
        {"type": "file_exists", "path": "pdf-notes/SKILL.md"},
        {"type": "frontmatter_valid", "path": "pdf-notes"}
      ]
    }
  ]
}
```

### Eval fields

| Field | Required | Meaning |
|---|---|---|
| `query` | yes | The task handed to the runtime. |
| `expected_output` | no | Human description of success. Recorded, not asserted. |
| `id` | no | Stable identifier. Defaults to position (1-based). Must be unique. |
| `should_trigger` | no | Whether this eval *should* select the skill. Defaults to `true`. Used for precision/recall when a trigger detector is configured. |
| `files` | no | Fixture files copied into the run directory before execution. |
| `assertions` | no | Objective and subjective checks. See below. |

### Accepted aliases

Earlier drafts used different field names. They still load, and are normalized
to the canonical name on read:

| Canonical | Also accepted |
|---|---|
| `query` | `prompt`, `task`, `input` |
| `expected_output` | `expectation`, `expected` |
| `should_trigger` | `shouldTrigger`, `triggers` |
| `assertions` | `expectations`, `checks` |
| `id` | `eval_id` |

Loading fails with a specific message when `query` is missing or empty, when
`files`/`assertions` are not lists, or when two evals share an `id`.

### Assertion types

Implemented by `scripts/grade.py`. `text` is optional and is used as the
expectation label; without it, a label is derived from `value` or `path`.

| Type | Fields | Passes when |
|---|---|---|
| `file_exists` | `path` | The path is a file. |
| `file_absent` | `path` | The path does not exist. |
| `file_contains` | `path`, `value`, `ignore_case` (default true) | The file contains the string. |
| `json_valid` | `path`, `required_keys` | The file parses as JSON and has the listed top-level keys. |
| `frontmatter_valid` | `path` | The directory passes `quick_validate.py`. |
| `command_succeeds` | `command`, `timeout` | The shell command exits 0 in the run directory. |
| `output_contains` | `value`, `ignore_case` | The run's stdout/stderr or any text artifact contains the string. |
| `output_matches` | `pattern` | The same text matches the regular expression. |
| `no_placeholder` | `values` (string or list) | None of the markers appear in the run text. |
| `manual` | `text` | Never decided automatically. Always recorded as `passed: null`. |

Any other `type` fails with a message naming the valid types. A typo in a type
name is a loud failure, not a silently skipped check.

Relative paths resolve against the run directory. `command_succeeds` is the one
type that executes something: keep it cheap, and never point it at a command
with side effects outside the run directory.

---

## Run directory layout

`run_eval.py` writes this layout, and both `aggregate_benchmark.py` and
`eval-viewer/generate_review.py` read it.

```text
<results-root>/
├── eval_results.json                        aggregate of every run below
├── benchmark.json / benchmark.md            written by aggregate_benchmark.py
└── eval-<id>/
    └── <config>/                            e.g. with_skill, without_skill
        └── run-<n>/
            ├── run.json                     this run's record
            ├── stdout.txt                   the runtime's stdout
            ├── stderr.txt                   the runtime's stderr
            ├── grading.json                 verdict per assertion
            └── <artifacts the run created>  what assertions inspect
```

`<config>` is a free-form label; it is discovered by directory name, so
`with_skill` / `without_skill` and `old_skill` / `new_skill` both work. Two or
more configurations in the same results root are what makes a delta possible.

The runtime's working directory **is** its run directory, seeded with the
eval's `files`. That is what lets a `file_exists` assertion mean anything.

---

## run.json

```json
{
  "agent": "opencode",
  "exit_code": 0,
  "stdout": "...",
  "stderr": "",
  "duration_ms": 8421,
  "total_tokens": null,
  "metrics_note": "runtime did not report token usage",
  "error": null,
  "task_success": true,
  "assertions_decided": true,
  "query": "Create a skill called pdf-notes ...",
  "eval_id": 1,
  "should_trigger": true,
  "expected_output": "A valid pdf-notes skill ...",
  "assertions": [],
  "trigger_observed": null,
  "trigger_detection": "none",
  "fixture_status": []
}
```

| Field | Notes |
|---|---|
| `exit_code` | `null` on timeout or adapter failure. |
| `total_tokens` | `null` unless the runtime actually reported usage. Never estimated. |
| `error` | `Timeout`, `ExecutableNotFound`, `AdapterError`, or the exception name. |
| `task_success` | `exit_code == 0` **and** no decided assertion failed. |
| `assertions_decided` | Whether at least one assertion was decided mechanically. Distinguishes "scored" from "only exit code checked". |
| `trigger_observed` | `true`/`false` from `--trigger-detector`, else `null` (unknown). |
| `trigger_detection` | `none` or `user-detector`. |

---

## grading.json

Consumed by `aggregate_benchmark.py`, the report generator, the static viewer,
and `agents/grader.md`.

```json
{
  "expectations": [
    {
      "text": "Creates pdf-notes/SKILL.md",
      "type": "file_exists",
      "passed": true,
      "evidence": "found: /.../run-1/pdf-notes/SKILL.md",
      "manual": false
    },
    {
      "text": "Judge did not use this workflow for a plain code fix",
      "type": "manual",
      "passed": null,
      "evidence": "requires human or agent review; not decided mechanically",
      "manual": true
    }
  ],
  "summary": {
    "passed": 1,
    "failed": 0,
    "total": 1,
    "manual": 1,
    "pass_rate": 1.0
  }
}
```

| Field | Notes |
|---|---|
| `passed` | `true`, `false`, or `null` when undecided. |
| `manual` | `true` for the `manual` type. |
| `summary.total` | Counts **decided** expectations only. `manual` is reported separately. |
| `summary.pass_rate` | `null` when `total` is 0. Never `0.0` for "nothing was checked". |

A `manual` expectation is excluded from `total` and from `pass_rate`. That is
deliberate: a subjective check must never quietly inflate a score.

---

## eval_results.json

Written to the results root after every `run_eval.py` invocation.

```json
{
  "skill_path": "/abs/path/to/skill",
  "agent": "opencode",
  "model": null,
  "config": "with_skill",
  "include_skill": true,
  "command": null,
  "runs_per_query": 1,
  "results": [
    {
      "id": 1,
      "query": "...",
      "should_trigger": true,
      "runs": 1,
      "successful_runs": 1,
      "pass": true,
      "trigger_observed": null,
      "trigger_detection": "none",
      "duration_ms": 8421,
      "total_tokens": null,
      "assertions_decided": true,
      "runs_detail": [ ... one record per run ... ]
    }
  ],
  "summary": {"total": 1, "passed": 1, "failed": 0}
}
```

`pass` is the majority verdict: more than half the runs for that eval must have
succeeded. It is the number `run_loop.py` optimizes against, and it says
nothing about whether the skill was *triggered* — that is a separate question
answered only by `trigger_observed`.

---

## benchmark.json

Written by `aggregate_benchmark.py`, rendered to `benchmark.md`.

```json
{
  "metadata": {
    "skill_name": "example-skill",
    "agent": "opencode",
    "executor_model": null,
    "configurations": ["with_skill", "without_skill"],
    "timestamp": "2026-01-15T10:30:00Z",
    "evals_run": ["1", "2"],
    "runs_per_configuration": 3,
    "trigger_detection": "none"
  },
  "runs": [ ... ],
  "run_summary": {
    "with_skill": {
      "pass_rate": {"mean": 0.87, "stddev": 0.05, "min": 0.8, "max": 0.9, "measured": 3},
      "time_seconds": {"mean": 8.4, "stddev": 1.1, "min": 7.2, "max": 9.6, "measured": 3},
      "tokens": {"mean": null, "stddev": null, "min": null, "max": null, "measured": 0}
    },
    "delta": {
      "configs": ["without_skill", "with_skill"],
      "pass_rate": "+0.31",
      "pass_rate_note": null
    }
  }
}
```

Every stat carries `measured`. A metric that was never collected has
`mean: null` and `measured: 0` — it does not become `0.0`. A delta is only
computed when both sides have a real mean; otherwise `pass_rate` is `null` and
`pass_rate_note` says why.

The delta compares the first two configurations found, with the second treated
as the baseline. Name your directories so the intended comparison is the
alphabetically-first pair, or aggregate them yourself.

---

## run_loop results.json

Written by `run_loop.py` when `--results-dir` is given.

```json
{
  "skill_name": "example-skill",
  "skill_path": "/abs/path",
  "exit_reason": "all train evals passed (iteration 2)",
  "original_description": "...",
  "best_description": "...",
  "best_iteration": 2,
  "best_train": {"passed": 6, "failed": 0, "total": 6},
  "best_test": {"passed": 3, "failed": 0, "total": 3},
  "final_description": "...",
  "improved": true,
  "iterations_run": 2,
  "holdout": 0.4,
  "train_size": 6,
  "test_size": 3,
  "elapsed_ms": 918273,
  "history": [
    {
      "iteration": 1,
      "description": "...",
      "train": {"passed": 5, "failed": 1, "total": 6},
      "test": {"passed": 2, "failed": 1, "total": 3},
      "trigger_metrics": null,
      "results": [ ... per-eval records ... ]
    }
  ],
  "proposals": [
    {
      "accepted": true,
      "problems": [],
      "agent": "opencode",
      "model": null,
      "iteration": 1,
      "elapsed_ms": 4102,
      "previous_length": 71,
      "new_length": 88
    }
  ]
}
```

| Field | Notes |
|---|---|
| `exit_reason` | Why the loop stopped. Always present. |
| `best_test` | `null` when `--holdout 0`. |
| `trigger_metrics` | `null` unless a detector produced verdicts. Never fabricated. |
| `proposals[].problems` | Why a proposal was rejected, e.g. a length violation. |
| `improved` | Whether the best description differs from the original. |

The best iteration is ranked by held-out score, then train score, then
earliest iteration, so a tie keeps the earlier and simpler description.

Held-out results never reach the proposer: `run_loop.py` strips every `test*`
field from the history it passes to `improve_description`.

---

## adapters.json

Runtime adapters live in `references/adapters.json`, not in a result file. It
is read by `scripts/agent_runner.py`. See the `notes` array in that file for the
`confidence` field, which records how each invocation shape is known.

---

## Formats this skill does not produce

`history.json`, `timing.json`, `metrics.json`, `comparison.json`, and
`analysis.json` appeared in earlier drafts of this document. No script writes
them. Their contents are now carried inside `run.json` and `results.json`, and
the blind-comparison and analysis roles write free-form JSON that only a human
reads.

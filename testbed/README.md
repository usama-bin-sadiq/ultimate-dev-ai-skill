# Testbed

Route-accuracy measurement on real tasks, with a gate in front of the number.

## Why this exists

The kernel's central claim is that it picks an approach — a coordination mode
and an effort rung — according to the task. That claim had no measurement behind
it at all:

- the corpus stated a correct mode for six cases, and the label was dropped on
  projection, so **0 of 128** cases reached the grader carrying one
- the grader had no assertion type that could express a routing decision, and
  its only gate for a must-fire case was that the answer exceeded 120 characters
- the effort gate's rung was written by a tool that accepted the string
  `banana` and never re-read the field

So "accuracy of architecture selection" was not badly measured. It was
unmeasurable, and `docs/decisions/0011` names the wider pattern exactly:
*"Every check in the repository is the kernel agreeing with itself."*

That has partly been fixed in the kernel tree. This directory is where the
remaining claim gets measured on tasks rather than asserted.

## The gate, and why it is first

`measure-judge.py` must run before any accuracy figure is quoted. It measures
whether the **judge agrees with itself** across repeats — Krippendorff's alpha
for ordinal data, with missing ratings allowed, floor 0.70.

This is not ceremony. LLM-judge inter-rater reliability has been observed
ranging from **0.167 to 1.00** across runs that differed only in random seed. A
rate computed against a judge with that much variance measures the seed. So:

| state | what `run-bench.py` prints |
| --- | --- |
| no verdict file | no accuracy figure, per-task rows only |
| consistency below floor | no accuracy figure, reason stated |
| consistency at or above floor | the rate, with the n it is over |

An unmeasured gate is not a formality: with nothing supplied, the script writes
`not-measured`, exits 1, and the benchmark refuses the number. A judge that
systematically disagrees scores **alpha = -0.17** and is blocked, which is the
case that matters.

## What is measured, and what is not

**Measured** — process only:

- did the run choose the coordination mode the task's oracle declares
- did it choose the declared rung, with over- and under-escalation counted apart
- cost per task, when the runtime reports it (`null` when it does not — never a
  guess)

**Not measured** — quality. There is no answer oracle for most tasks, and
inventing one is the failure this repository keeps finding. Keeping the axes
apart is the point: `run-pilot.py` gates its `publishable` flag on the
false-trigger rate while nothing gates quality, and a run in which every case
failed is a passing invocation there.

## Coverage, stated before the rate

The twelve tasks are real work on this repository — defects found and fixed
while building the thing that measures them. They are **not** a representative
sample, and `run-bench.py` prints the gap on every run rather than letting a
rate over a skewed sample stand for the decision space:

```
COVERAGE GAP -- the sample does not exercise:
  rungs R0, R4 -- 3 of 5 represented
  modes route, handoff -- 2 of 4 represented
```

Ten of twelve are `inline`, because almost all the real work was. `route` and
`handoff` have no task at all, so nothing here says anything about them.

`dev` and `heldout` are separated for the ordinary reason: the dev split is what
a change is tuned against, and quoting both as one number is how a benchmark
stops predicting anything. Only `heldout` should be quoted outside this
directory.

## Using it

```sh
# 1. is the judge consistent? (writes judge-verdict.json)
python3 measure-judge.py --ratings repeats.json

# 2. grade a results file; accuracy is withheld unless the gate is met
python3 run-bench.py --from-results results.json

# 3. grade one split, and require the gate
python3 run-bench.py --from-results results.json --split heldout --require-gate
```

`run-bench.py` grades results; it does not invoke a model. Producing the rows
means running the kernel over `tasks/*.json` and recording the run-state each
run produced — which is the harness wiring `tools/run-pilot.py` has and this
does not yet. That gap is real and is named here rather than implied away.

## Task format

One JSON per file in `tasks/`. `expected_mode` and `expected_rung` are the
oracle; `oracle` is the reasoning behind them, so a reviewer can disagree with
a *task* rather than being handed an answer key. A task with no `expected_mode`
is scored on nothing, and reported as undecided — not as a pass.

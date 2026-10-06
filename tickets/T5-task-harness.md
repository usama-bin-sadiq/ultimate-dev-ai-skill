# T5 - task-harness

## Description

5 tasks x verifier; with vs without skill

## Acceptance

See specs/improvement-spec.md.

## Status

done: 13 tasks across 12 categories (easy/medium/hard) plus a 3-step series
task. Each has task.md, fixtures/, verifier.py and meta.json. Every grader is
proven to discriminate by `evals/selftest_tasks.py`, which runs each task twice
- reference solution must PASS, deliberately wrong answer must be REJECTED -
and that self-test is a hard CI gate. `tools/run-task-eval.py` drives real agent
CLIs with and without the target skill injected, preflighting each CLI first.
Three tasks declare no skill and act as controls for run-to-run variance.

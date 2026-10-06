# Spec — closing the gap to 10/10

## 1. Routing index freshness (R1)

Add `--check` mode to `tools/build-routing-index.py`: rebuild in memory, diff
against the committed `skills/_routing-index.json`, exit non-zero if stale.
Wire into CI validate workflow.

## 2. Routing eval harness (R2)

New tool `tools/eval-routing.py`:
- Input: `evals/routing/queries.jsonl` — lines
  `{"query": "...", "expect": ["skill-name"], "not_expect": ["skill-name"]}`.
- Scorer: score each index entry by keyword overlap of query tokens with the
  entry's `when` clauses weighted 2× and `description` tokens 1× and `name`
  tokens 3×. Take top-K. Reports Hit@1, MRR@10, R@5, and negative violations
  (a `not_expect` name in top-1).
- Hand-label 50 queries across the top domains by inspection of descriptions.

## 3. Overlap lint in CI (R3)

Extend `build-routing-index.py` with `--overlap-fail F`: exit 1 if more than
F same-template pairs exceed 0.55 Jaccard (default F=15, current count ~11).
CI step fails when the corpus gains a true duplicate.

## 4. Skill quality rubric (R4)

New tool `tools/score-skill-quality.py`:
- For each `skills/*/SKILL.md`, four binary checks:
  1. trigger clause present (`use when|triggers|invoke`)
  2. exclusion clause present (`not for|NOT|do not|don't|never`)
  3. exact command/code fence present (``` fence or `python|bash|curl`)
  4. failure-mode text present (`fail|error|fallback|recover|edge case|gotcha`)
- Score = 0–4; repo mean and a ranked list of 0–1 skills exported to
  `reports/skill-quality.md`; the CI threshold rejects the *mean* dropping.

## 5. Minimal task harness (R5)

New `evals/tasks/` with 5 small tasks (one per domain: code, research,
docs, data, design), each with `task.md`, `verifier.py` (stdlib assertion on
the artifact), and expected skill name. `tools/run-task-eval.py` executes:
without-skill (prompt only) vs with-skill (inject that skill's SKILL.md), both
graded by the verifier. This is the smallest form of the SkillsBench design.

## 6. Composio cluster policy (R6)

Add `tool_bound: true` detection (already in `index-tree.py` for 611) and a
family entry: in the routing index, Composio stubs get
`"family": "composio-automation"`, `"standalone": false`, and are excluded
from Hit@1/MRR scoring unless the query names the exact product. This stops
them polluting the metric without deleting capability.

## Order of work

T1 index freshness check  → T2 routing eval + 50 labels  → T3 overlap CI  →
T4 quality rubric + threshold  → T5 task harness  → T6 composio policy.

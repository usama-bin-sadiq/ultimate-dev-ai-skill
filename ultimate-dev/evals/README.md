# evals

Measurement harness for the skill collection. Two independent questions are
asked here, and neither was answerable before this tree existed.

## `routing/` — can the router find the right skill?

`routing/queries.jsonl` holds 60 seed queries, one JSON object per line, each
naming a query and the skill that should win. Run it with:

```bash
python3 tools/eval-routing.py
```

Reports Hit@1, MRR@10 and Recall@5, and counts "negative violations" — cases
where a query's `not_expect` skill was ranked first. Composio template-family
stubs are excluded from scoring unless the query names their product, because
~600 of them share one description shape and would otherwise dominate the
metric.

**Caveat worth knowing before you trust the number:** these queries are
auto-derived from skill names, so they test whether the scorer finds a name it
was handed, not whether a real user's phrasing routes correctly. The scorer is
also token-overlap (`3x name + 2x when + 1x description + 2x body`), not BM25 or
embeddings. Treat Hit@1 as a regression guard, not as a measurement of routing
quality. Hand-written queries and a real retriever are the open work.

## `tasks/` — does a skill actually help an agent do the job?

Thirteen tasks spanning twelve categories at three difficulties, plus a
three-step series task where each step depends on the previous one. Each task
directory holds:

| File | Role |
|---|---|
| `task.md` | the brief handed to the agent |
| `fixtures/` | input files copied into a throwaway workdir |
| `verifier.py` | grades the artifacts; prints PASS/FAIL, exits 0/1 |
| `meta.json` | category, difficulty, target skill, expected artifacts |

| Task | Category | Difficulty | Target skill |
|---|---|---|---|
| `grep-artifact` | text-search | easy | — (control) |
| `json-key` | data-extraction | easy | `strict-api` |
| `rename-files` | filesystem | easy | — (control) |
| `csv-stats` | data-quality | medium | `data-quality-auditor` |
| `git-status` | version-control | medium | `git-workflow-and-versioning` |
| `todo-triage` | code-analysis | medium | `code-reviewer` |
| `yaml-config` | config | medium | `principle-boundary-discipline` |
| `doc-refresh` | documentation | medium | `docs-writer` |
| `bug-diagnosis` | debugging | hard | `systematic-debugging` |
| `test-generation` | testing | hard | `test-driven-development` |
| `api-contract` | api-design | hard | `api-and-interface-design` |
| `slop-removal` | writing | hard | `unslop` |
| `pipeline-series` | multi-step | hard | — (control) |

Three tasks declare no skill and run both conditions identically. They are a
control: they measure run-to-run variance instead of skill value, which is the
only way to tell a real skill effect from noise.

### Prove the graders work

A verifier that accepts a wrong answer is worse than no verifier. The
self-test runs every task twice — once with a reference solution, once with a
deliberately wrong one — and fails if a grader accepts the wrong answer:

```bash
python3 evals/selftest_tasks.py
```

Expected: `all graders discriminate`.

### Run it against a real agent

```bash
python3 tools/run-task-eval.py --list
python3 tools/run-task-eval.py --agent opencode --condition both
```

Every CLI is preflighted first, so an unauthenticated agent is reported in one
line instead of costing 13 timeouts. Results are cached under `evals/.results/`
(`--fresh` to override) and summarised to `evals/.results/summary.md`.


Five deterministic tasks, each a directory holding a `task.md` (the brief given
to the agent) and a `verifier.py` (grades an artifact and prints PASS or FAIL):

| Task | What it exercises |
|------|-------------------|
| `grep-artifact` | regex search, write matches to a file |
| `csv-stats` | parse a CSV and compute an aggregate |
| `rename-files` | bulk filesystem rename |
| `git-status` | read git state and report it |
| `json-key` | extract a nested key from JSON |

The agent-driven entry point is documented above. `tools/run-task-eval.py` is
the supported way in; it builds the workdir, invokes the CLI, and grades.

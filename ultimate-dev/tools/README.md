# Tools

Repository mechanics. Nothing here runs at skill runtime except what a skill's
own instructions name.

## Validate

| Tool | Does |
|---|---|
| `validate-skills.py` | Structural validation of the whole tree. The one that must pass. |
| `check-sibling-imports.py` | Verifies a skill's scripts actually import each other. |
| `check-workflow-auth.py` | Every `gh` call needing a credential must declare it in its own step. |
| `text_rules.py` | Shared emphasis and output-declaration rules, imported by the validator. |

## Self-tests

| Tool | Tests |
|---|---|
| `test-text-rules.py` | `text_rules.py` |
| `test-marker-drift.py` | the unfilled-marker rule in `validate-skills.py` |
| `test-workflow-auth.py` | `check-workflow-auth.py` |

## Search and index

| Tool | Does |
|---|---|
| `index-tree.py` | Builds `TREE.json`; `--search <term>` finds capabilities by name/description. |
| `build-routing-index.py` | Builds `skills/_routing-index.json` — per-skill `what`/`when`/`not`/keywords, and prints keyword-overlap duplicates for disambiguation. |
| `score-roles.py` | Mechanical proxy for whether an agent role has substance. |

## Repair and generation

| Tool | Does |
|---|---|
| `repair-fences.py` | Repairs unbalanced code fences. |
| `repair-frontmatter.py` | Repairs malformed frontmatter. |
| `split-oversized-skills.py` | Splits skills that exceed the size budget. |
| `shorten-descriptions.py` | Trims descriptions that exceed the length budget. |
| `merge-automation-pairs.py` | One-off merge of underscore-named duplicate skills. |
| `check-links.py` | Reports broken internal references. Strips code fences before looking, so a parenthesised token in a sample is not mistaken for a link; separates broken targets from env/placeholder ones. Exit 1 if any broken. |
| `normalize-collection-refs.py` | Rewrites `<upstream-collection>/skills/<name>` to this repo's flat `skills/<name>`, only when the target exists. Skips URLs and `~/.claude/skills/...` install paths. `--dry-run` to preview. |
| `repair-links.py` | Repoints broken relative links that resolve uniquely elsewhere in the same skill. Refuses self-links, generic basenames (`SKILL.md`) and generator templates. `--dry-run` to preview. |
| `run-task-eval.py` | Runs the task suite against real agent CLIs with and without the target skill, then grades with each task's verifier. Preflights every CLI so an unauthenticated one is reported instead of timing out 13 times. `--agent opencode,claude`, `--condition`, `--task`, `--list`. |
| `merge-dupes.py` | Consolidates the "X" / "Use this one, X" duplicate pairs: copies files the winner lacks, ports the `Communication` / `Proactive Triggers` / `Output Artifacts` sections and any bundled-file list, then removes the loser. `--dry-run` reports without touching the tree. |
| `neutralise.py` | Tool-specificity pass over capability descriptions. |
| `adapt-tree.py` | Adapts an imported capability tree to repository conventions. |
| `write-asset-readmes.py` | Writes README indexes for reference directories. |
| `generate-skill-image.py` | Renders a skill diagram through an image model. |
| `baseline-check.sh` | Re-runs the validator pinned to an older commit. |
| `agent_invocation.py` | Resolves which agent runtime to invoke, from argument then environment. |

## Directories

- `agent-runtime/` — helpers used by skills at runtime.
- `session-hooks/` — hook scripts for agent runtimes.
- `js-tooling/` — Node-side validators and tests for those scripts.

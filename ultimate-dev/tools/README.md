# Tools

Forty utilities. All of them ship in the bundle except the five
`bundle-skill.py` names explicitly — a tool that cannot work from an install
should not be present in one, because its presence implies it can. Those five are
marked **[dev]** below: they build, measure or audit the repository, and an
installed copy of the skill has none of those jobs. The kernel names three of the
forty; the other thirty-seven exist to be run deliberately.

This file exists because a tool nothing references is a tool nobody runs. Nine of
these were referenced by no other file in the repository — not the gate, not CI,
not a document — which is a quieter failure than a broken tool, because a broken
tool announces itself. The ones below are grouped by when you would reach for
them, so that "is there something for this?" has an answer that is not a grep.

## The gate

`pre-commit-check.sh` is the authority: it is what `.githooks/pre-commit` execs,
and CI invokes it directly. Start here — it calls 17 of the 40, being every
validator and every self-test. The rest are repair and generation tools that
should run only when you mean them to.

CI used to re-list the underlying tools one by one instead of calling this, which
meant a check added here would not run in CI, and eight of the seventeen below —
the self-tests — ran nowhere but on a maintainer's machine. If you add a check,
add it here and let CI call this; do not add a parallel step.

| Tool | Does |
|---|---|
| `pre-commit-check.sh` | The gate. `--fast` by default, `--full` adds bundle and parity, `--baseline` prints the known backlog, `--base <ref>` compares against something other than HEAD. |
| `validate-skills.py` | Structural validation of the whole tree. The one that must pass. |
| `check-sibling-imports.py` | Verifies a skill's `scripts/` files actually import each other, rather than each being written as if it stood alone. |
| `check-workflow-auth.py` | Every `gh` call needing a credential must have one in its own step, not inherited from an earlier one. |
| `text_rules.py` | The shared emphasis and output-declaration rules. Imported by `validate-skills.py` and `bundle-skill.py`, never run directly — two copies of a rule is how they drift. |
| `agent_invocation.py` | Resolves which agent runtime to invoke, from argument then environment. Imported by `run-pilot.py`. |

## Measurement

Run these when you want a number rather than a feeling.

| Tool | Does |
|---|---|
| `index-tree.py` | The capability index and the reachability band. `--search <term>` to find something. `--write-catalogue` regenerates `references/capability-catalogue.md`. |
| `score-roles.py` | Mechanical proxy for whether a role has substance. A proxy: it counts markers, and a role can score well by listing numbers it never uses. |
| `report-oracle-coverage.py` | How much of the evaluation corpus is gradeable against a declared oracle. |
| `measure-mode-cost.py` | What each coordination mode costs to invoke. |
| `audit-docs.py` **[dev]** | Six ways prose stops agreeing with the tree: dead links, backticked paths that resolve from no root, files their directory index omits, stated counts that disagree with the filesystem, install-payload sizes the bundler would not produce, and skipped heading levels. |
| `baseline-check.sh` | Re-runs the validator pinned to an older commit, so the delta between "the tree improved" and "the instrument changed" can be stated. |

## Repair

These write to the tree. Read the diff.

| Tool | Does |
|---|---|
| `build-dispatch-table.py` | Adds a dispatch row for any role that lacks one. `--refresh` rebuilds the rows that only restate a role's description, from the role's own mission bullets and prohibitions, and leaves the ones that decide alone. |
| `link-orphan-references.py` | Adds a reference section to each `SKILL.md` shipping files nothing points at. |
| `repair-fences.py` | Repairs unbalanced code fences by diagnosis rather than by rule. |

## Running things

These do not repair the tree; they observe or execute it.

| Tool | Does |
|---|---|
| `run-state.py` | The one tool a *run* invokes, to record the rung and the coordination mode. Writes a state file, not source. |
| `run-pilot.py` **[dev]** | Runs a stratified *pilot* of the evaluation suite against a real runtime — a sample across all seven case classes, not all 128. Needs an agent runtime; see `references/runtime-portability.md`. `tools/agent-runtime/` holds the adapters it can drive. |

## One-shot import repair

These ran when a large external capability tree was imported and normalised. They
are kept because the next import will need them, and they are **not** part of
any recurring step — running one on a settled tree either does nothing or makes
a change nobody asked for.

| Tool | Does |
|---|---|
| `adapt-tree.py` | Brings an imported capability tree to this repository's conventions. |
| `repair-frontmatter.py` | Fixes mechanically-fixable frontmatter defects in an imported corpus. |
| `merge-automation-pairs.py` | Merges underscore-named `*-automation` skills into their kebab siblings. |
| `shorten-descriptions.py` | Shortens over-long skill descriptions to the validator's limit. |
| `split-oversized-skills.py` | Splits a skill too large to stay always-loaded. |

## Content generation

| Tool | Does |
|---|---|
| `build-evals.py` **[dev]** | Projects the Markdown corpus into the generated eval case file, in the format standard tooling reads. The output is excluded from the bundle too, which is why the path is not written here as a link. |
| `build-fixtures.py` **[dev]** | Regenerates the testbed fixtures. |
| `apply-progressive-disclosure.py` | Moves detail out of always-loaded `SKILL.md` files and into `references/`. |
| `bundle-skill.py` **[dev]** | Builds and verifies the pruned distributable. `--check` verifies without writing. |
| `generate-skill-image.py` | Renders the skill's diagram. |
| `write-asset-readmes.py` | Writes a README beside an asset directory that lacks one. |

## Housekeeping

| Tool | Does |
|---|---|
| `statusline.sh` | Editor status line. Development only. |
| `neutralise.py` | Neutralises capabilities that claim to be general but are bound to one tool, so the claim stops being false. |

## Self-tests

The gate runs each of these, which is why a broken tool fails the commit rather
than the next person. Listed individually so the set is auditable rather than a
glob that could quietly gain a member.

| Tool | Self-tests |
|---|---|
| `test-changelog-generator.py` | `changelog` generation |
| `test-fence-parity.py` | that the fence reader agrees between validators |
| `test-marker-drift.py` | that emphasis markers are classified identically everywhere |
| `test-mode-cost.py` | `measure-mode-cost.py` |
| `test-oracle-coverage.py` | `report-oracle-coverage.py` |
| `test-progressive-disclosure.py` | `apply-progressive-disclosure.py` |
| `test-provider-neutral.py` | that no harness names a provider |
| `test-routing-assertions.py` | the routing assertions |
| `test-run-state.py` | `run-state.py` |
| `test-workflow-auth.py` | `check-workflow-auth.py` |

## What a run may invoke

The kernel names three of these, and only two of them are commands a run types:

```sh
python3 tools/run-state.py init --rung R1 --objective "<one line>"
python3 tools/index-tree.py --search <term>
```

The third, `tools/agent_invocation.py`, is pointed at rather than called: which
runtime a harness drives is configuration, and the kernel deliberately declines
to name a default.

Both commands resolve from the skill root, and `SKILL.md` now says so. They were
written without that prefix once, and every run that followed the instruction
literally wrote no state file — which the harness then read as "no decision was
recorded" and scored accordingly. If you add a command to the kernel, state
where it resolves from.

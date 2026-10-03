# Installation

The skill is a directory of Markdown. There is no build, no dependency, and no
runtime component.

```text
ultimate-dev/
├── SKILL.md              required — the kernel
├── references/           the corpus, loaded on demand
├── skills/               installed sub-skills, discovered by description
├── agents/               delegated roles, dispatched via a row in
│                         references/delegation.md
└── tools/                the validator, the bundler, the doc auditor,
                          and the evaluation harnesses
```

The counts in this tree are not written down on purpose. Every one of them was
right when written and wrong within a few commits, and a reader who trusts a
stale count is worse off than one who is told to look.

Only `SKILL.md`, `references/`, `skills/`, `agents/`, and `tools/` are read at
runtime. `ARCHITECTURE.md`, `docs/`, `evals/`, `examples/`, `evaluation/`,
`research/`, and `knowledge/` are supporting material and are pruned by default.

## Automatic

```bash
git clone https://github.com/usama-bin-sadiq/ultimate-dev-ai-skill.git
cd ultimate-dev-ai-skill
./install.sh
```

The installer detects an existing skills directory, copies the skill into it,
prunes the documentation trees, and verifies the result. It refuses to overwrite
an existing skill directory without confirmation.

```bash
./install.sh --project          # into ./.agents/skills (or ./.claude/skills)
./install.sh --all              # keep docs, examples, evaluation
./install.sh --target DIR       # an exact directory
./install.sh --dry-run          # print the plan, change nothing
```

## Two ways to install, for two different reasons

The repository is more than the skill. Alongside the runtime tree it carries the
evaluation corpus, worked examples, architecture documentation, and research
notes. The bundler reports the split, and its printed counts are the current
ones — which is why they are not written down here.

| | Use when | Result |
|---|---|---|
| `./install.sh` | You are installing to run the skill | Pruned in place to the runtime tree |
| `./install.sh --bundle` | You are **distributing** it — a marketplace, a PR, another runtime | A standalone `dist/ultimate-dev/` plus a verified size report |

```bash
./install.sh --bundle                # dist/ultimate-dev/
./install.sh --bundle /tmp/out --bundle-zip   # also writes a .zip
./install.sh --check-bundle          # verify without writing
```

The bundle contains only what a runtime loads: `SKILL.md`, `references/`,
`skills/`, `agents/`, `tools/` — the same set a pruned install leaves behind.

Its size, and the fraction it prunes, are computed and printed by the bundler
rather than fixed here, along with the files it kept and the ones it dropped.
Run `./install.sh --check-bundle` to reproduce the current figures without
writing anything, so you can confirm what shipped rather than trust this
paragraph.

Three things the bundler refuses to do:

- **Ship a dangling reference.** If a bundled document points into `docs/`,
  `research/`, or `evaluation/`, the build fails. A trimmed bundle pointing at
  files it no longer contains is worse than the full repository, because it looks
  finished.
- **Guess about a new directory.** An unrecognised top-level tree fails the build
  rather than being silently bundled or silently dropped.
- **Ship something unvalidated.** The bundle must pass the skill validator, and
  its directory must be named after the skill.

```bash
python3 ultimate-dev/tools/bundle-skill.py --check
```

## Manual

Copy the directory to wherever your runtime looks for skills:

| Scope | Common locations |
|---|---|
| User (Kiro / Agents) | `~/.agents/skills/` |
| User (Claude Code) | `~/.claude/skills/` |
| User (OpenCode) | `~/.config/opencode/skills/`, `~/.local/share/opencode/skills/` |
| User (Gemini CLI) | `~/.config/gemini/skills/`, `~/.gemini/skills/` |
| User (Cursor) | `~/.cursor/skills/`, `~/.cursor/extensions/skills/` |
| User (Windsurf / Codeium) | `~/.codeium/skills/`, `~/.windsurf/skills/` |
| User (Amazon Q) | `~/.aws/amazonq/skills/`, `~/.q/skills/` |
| User (Continue.dev) | `~/.continue/skills/` |
| User (GitHub Copilot) | `~/.github-copilot/skills/` |
| User (Aider) | `~/.aider/skills/` |
| User (Goose) | `~/.config/goose/skills/` |
| User (Amp) | `~/.config/amp/skills/` |
| User (Zed) | `~/.config/zed/skills/` |
| Project | `./.agents/skills/`, `./.claude/skills/`, `./.cursor/skills/`, `./.windsurf/skills/`, `./.continue/skills/`, `./.amazonq/skills/` |

```bash
mkdir -p ~/.agents/skills
cp -R ultimate-dev ~/.agents/skills/ultimate-dev
```

Then restart the runtime so it rediscovers skills.

### Discovery hints

The installer can write minimal hint files (`AGENTS.md`, `CLAUDE.md`) next to the
installed skill directory so that runtimes that probe for those files discover the
skill automatically:

```bash
./install.sh --write-discovery-hints
```

This only writes a file when none exists — it never overwrites content you have
already placed there. The files contain a single heading and one line pointing to
the `skills/` directory.

Pass `--dry-run` together with `--write-discovery-hints` to see what would be
written without changing anything:

```bash
./install.sh --dry-run --global --write-discovery-hints
```

## Verify

```bash
python3 ultimate-dev/tools/validate-skills.py --strict
```

Runs on a bare Python 3 install, with or without PyYAML. It checks frontmatter,
naming, description limits, every referenced path, orphan reference files, agent
role contracts, tree indexes, build artefacts, and placeholders.

To confirm the runtime actually loaded it, give it a request that needs the
kernel — something open-ended, multi-step, or high-consequence. Then give it a
trivial request like *"rename this variable"*.

**The trivial request should not trigger it.** That is the design working: the
kernel's own effort gate treats over-orchestration as a defect. A runtime that
loads the skill on every message has loaded it as instructions rather than as a
capability.

## Requirements

None. Python 3 is needed only for the validator, and the validator is optional.

## Uninstall

Delete the installed directory:

```bash
rm -rf ~/.agents/skills/ultimate-dev
```

The installer keeps no state, writes no registry, and creates no symlinks, so
removal is complete when the directory is gone. If you installed with
`--project`, also check your `.gitignore` for an entry a previous install added.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Runtime does not list the skill | The directory is not in a searched path | Install into a known location, or check your runtime's config |
| Skill loads on every request | The runtime is treating it as always-on instructions | Check the runtime's skill configuration; the kernel is meant to be selected, not applied universally |
| Trivial requests get a plan | The kernel's effort gate is being ignored | This is a kernel behaviour problem, not an install problem — report it with the request that triggered it |
| `references/... does not exist` after install | A partial copy | Reinstall; the installer rolls back and refuses to leave a broken tree |
| `--bundle` fails on a reference | A runtime document points into a tree the bundle omits | Rewrite the reference so it does not depend on `docs/`, `research/`, or `evaluation/` being present |
| `--bundle` fails on an unclassified tree | A new top-level directory was added | Add it to `RUNTIME_DIRS`, `EXCLUDED_DIRS`, `RUNTIME_FILES`, or `EXCLUDED_FILES` in `tools/bundle-skill.py` |
| Validator reports an orphan reference | A reference file is not reachable from `SKILL.md` | Add it to the References section of `SKILL.md`, or delete the file |

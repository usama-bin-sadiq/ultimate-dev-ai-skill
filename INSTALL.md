# Installation

The skill is a directory of Markdown plus scripts. There is no build step.

```text
ultimate-dev/
├── SKILL.md              required — the router and execution discipline
├── skills/               installed sub-skills, discovered by description
├── agents/               specialist roles
├── tools/                the validator and corpus-maintenance scripts
└── TREE.json             the capability index
```

## Automatic

```bash
git clone https://github.com/usama-bin-sadiq/ultimate-dev-ai-skill.git
cd ultimate-dev-ai-skill
./install.sh
```

The installer detects an existing skills directory, copies `ultimate-dev/` into
it, and verifies the result. It refuses to overwrite an existing installation
without confirmation.

```bash
./install.sh --target DIR    # copy into an exact directory
./install.sh --all           # every runtime's global + project discovery dir
./install.sh --yes           # non-interactive; safe with --target/--all
./install.sh --dry-run       # print the plan, change nothing
./install.sh --link          # symlink instead of copy (one source, many links)
```

Windows: the same five modes exist in `install.ps1` (`-Target`, `-All`, `-Yes`,
`-DryRun`, `-Link`).

## Verify

```bash
python3 <target>/ultimate-dev/tools/validate-skills.py
```

It prints PASS when every skill and role frontmatter, every cross-reference,
and every repository invariant holds.

## Where each tool looks

| Runtime | Project | Global |
|---|---|---|
| OpenCode | `.opencode/skills`, `.claude/skills`, `.agents/skills` | `~/.config/opencode/skills`, `~/.claude/skills`, `~/.agents/skills` |
| Claude Code | `.claude/skills` | `~/.claude/skills` |
| Codex | `.agents/skills` | `~/.codex/skills` |
| Cursor | `.cursor/skills`, `.agents/skills`, `.claude/skills` | `~/.cursor/skills` |
| Gemini CLI | `.gemini/skills` | `~/.gemini/skills` |
| Copilot | `.github/skills`, `.agents/skills` | `~/.agents/skills` |
| Windsurf / Cline / Trae / Kiro | their own dir, plus `.agents/skills` fallback | matching home dir |

The two directories that cover essentially everything are `~/.agents/skills`
and `~/.claude/skills`. The default (`auto`) installs into whichever of its
candidates already exists, falling back to those two. Use `--all` when you
want every listed runtime discovered without thinking.

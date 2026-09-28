<!-- Moved verbatim from design-review/SKILL.md, the
     'setup' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Setup

**Parse the user's request for these parameters:**

| Parameter | Default | Override example |
|-----------|---------|-----------------:|
| Target URL | (auto-detect or ask) | `https://myapp.com`, `http://localhost:3000` |
| Scope | Full site | `Focus on the settings page`, `Just the homepage` |
| Depth | Standard (5-8 pages) | `--quick` (homepage + 2), `--deep` (10-15 pages) |
| Auth | The user's Aside session (already signed in) | `I'm signed in as user@example.com in Aside` |

**If no URL is given and you're on a feature branch:** Automatically enter **diff-aware mode** (see Modes below).

**If no URL is given and you're on main/master:** Ask the user for a URL.

**Check for DESIGN.md:**

Look for `DESIGN.md`, `design-system.md`, or similar in the repo root. If found, read it — all design decisions must be calibrated against it. Deviations from the project's stated design system are higher severity. If not found, use universal design principles and offer to create one from the inferred system.

**DESIGN.md format:**

```bash
bun --no-env-file run $HOME/.claude/skills/gstack/bin/gstack-design-md.ts check DESIGN.md
```

`DESIGN_MD_FORMAT: spec`: the front matter is normative. Run `bun --no-env-file run $HOME/.claude/skills/gstack/bin/gstack-design-md.ts tokens DESIGN.md` and calibrate against the flat token map: a value present there is never a finding, and a finding that departs from a token names the token. `legacy` or `unknown`: read the file as prose. The `DESIGN_MD_MARKER` line is the user's persisted format choice; respect it and never offer a conversion here (that is /design-consultation's question). `missing`: universal principles.

**Check for clean working tree:**

```bash
git status --porcelain
```

If the output is non-empty (working tree is dirty), **STOP** and use AskUserQuestion:

"Your working tree has uncommitted changes. /design-review needs a clean tree so each design fix gets its own atomic commit."

- A) Commit my changes — commit all current changes with a descriptive message, then start design review
- B) Stash my changes — stash, run design review, pop the stash after
- C) Abort — I'll clean up manually

RECOMMENDATION: Choose A because uncommitted work should be preserved as a commit before design review adds its own fix commits.

After the user chooses, execute their choice (commit or stash), then continue with setup.

**Check the Aside browser:**

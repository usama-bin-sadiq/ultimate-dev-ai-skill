---
name: "agent-md-improver"
description: "Audit and improve the markdown instruction file an agent reads at session start — CLAUDE.md, AGENTS.md, GEMINI.md, .cursorrules and equivalents. Use when asked to check, audit, update, improve or fix a project instruction file, or to optimise project memory. Scans for every instruction file, evaluates quality against templates, outputs a report, then makes targeted updates."
tools: Read, Glob, Grep, Bash, Edit
---

# Agent Instructions Improver

Audit, evaluate, and improve <agent-instructions> files across a codebase so the agent has optimal project context.

**This skill can write to <agent-instructions> files.** After presenting a quality report and getting user approval, it updates <agent-instructions> files with targeted improvements.

## Workflow

### Phase 1: Discovery

Find all <agent-instructions> files in the repository:

```bash
find . \( -name "CLAUDE.md" -o -name "AGENTS.md" -o -name "GEMINI.md" \
       -o -name ".cursorrules" -o -name ".windsurfrules" \) 2>/dev/null | head -50
```

**File Types & Locations:**

| Type | Location | Purpose |
|------|----------|---------|
| Project root | `./<agent-instructions>` | Primary project context (checked into git, shared with team) |
| Global defaults | `<agent-config-dir>/<agent-instructions>` | User-wide defaults across all projects |
| Package-specific | `./packages/*/<agent-instructions>` | Module-level context in monorepos |
| Subdirectory | Any nested location | Feature/domain-specific context |

**Note:** the runtime auto-discovers instruction files in parent directories, making monorepo setups work automatically.

### Phase 2: Quality Assessment

For each <agent-instructions> file, evaluate against quality criteria. See [references/quality-criteria.md](references/quality-criteria.md) for detailed rubrics.

**Quick Assessment Checklist:**

| Criterion | Weight | Check |
|-----------|--------|-------|
| Commands/workflows documented | High | Are build/test/deploy commands present? |
| Architecture clarity | High | Can the agent understand the codebase structure? |
| Non-obvious patterns | Medium | Are gotchas and quirks documented? |
| Conciseness | Medium | No verbose explanations or obvious info? |
| Currency | High | Does it reflect current codebase state? |
| Actionability | High | Are instructions executable, not vague? |

**Quality Scores:**
- **A (90-100)**: Comprehensive, current, actionable
- **B (70-89)**: Good coverage, minor gaps
- **C (50-69)**: Basic info, missing key sections
- **D (30-49)**: Sparse or outdated
- **F (0-29)**: Missing or severely outdated

### Phase 3: Quality Report Output

**ALWAYS output the quality report BEFORE making any updates.**

Format:

```
## Instruction File Quality Report

### Summary
- Files found: X
- Average score: X/100
- Files needing update: X

### File-by-File Assessment

#### 1. ./<agent-instructions> (Project Root)
**Score: XX/100 (Grade: X)**

| Criterion | Score | Notes |
|-----------|-------|-------|
| Commands/workflows | X/20 | ... |
| Architecture clarity | X/20 | ... |
| Non-obvious patterns | X/15 | ... |
| Conciseness | X/15 | ... |
| Currency | X/15 | ... |
| Actionability | X/15 | ... |

**Issues:**
- [List specific problems]

**Recommended additions:**
- [List what should be added]

#### 2. ./packages/api/<agent-instructions> (Package-specific)
...
```

### Phase 4: Targeted Updates

After outputting the quality report, ask user for confirmation before updating.

**Update Guidelines (Critical):**

1. **Propose targeted additions only** - Focus on genuinely useful info:
   - Commands or workflows discovered during analysis
   - Gotchas or non-obvious patterns found in code
   - Package relationships that weren't clear
   - Testing approaches that work
   - Configuration quirks

2. **Keep it minimal** - Avoid:
   - Restating what's obvious from the code
   - Generic best practices already covered
   - One-off fixes unlikely to recur
   - Verbose explanations when a one-liner suffices

3. **Show diffs** - For each change, show:
   - Which <agent-instructions> file to update
   - The specific addition (as a diff or quoted block)
   - Brief explanation of why this helps future sessions

**Diff Format:**

```markdown
### Update: ./<agent-instructions>

**Why:** Build command was missing, causing confusion about how to run the project.

```diff
+ ## Quick Start
+
+ ```bash
+ npm install
+ npm run dev  # Start development server on port 3000
+ ```
```

### Phase 5: Apply Updates

After user approval, apply changes using the Edit tool. Preserve existing content structure.

## Templates

See [references/templates.md](references/templates.md) for <agent-instructions> templates by project type.

## Common Issues to Flag

1. **Stale commands**: Build commands that no longer work
2. **Missing dependencies**: Required tools not mentioned
3. **Outdated architecture**: File structure that's changed
4. **Missing environment setup**: Required env vars or config
5. **Broken test commands**: Test scripts that have changed
6. **Undocumented gotchas**: Non-obvious patterns not captured

## User Tips to Share

When presenting recommendations, remind users:

- **`#` key shortcut**: During a session, press `#` to have the agent auto-incorporate learnings into <agent-instructions>
- **Keep it concise**: The instruction file should be human-readable; dense is better than verbose
- **Actionable commands**: All documented commands should be copy-paste ready
- **Use `.claude.local.md`**: For personal preferences not shared with team (add to `.gitignore`)
- **Global defaults**: Put user-wide preferences in `<agent-config-dir>/<agent-instructions>`

## What Makes a Great Instruction File

**Key principles:**
- Concise and human-readable
- Actionable commands that can be copy-pasted
- Project-specific patterns, not generic advice
- Non-obvious gotchas and warnings

**Recommended sections** (use only what's relevant):
- Commands (build, test, dev, lint)
- Architecture (directory structure)
- Key Files (entry points, config)
- Code Style (project conventions)
- Environment (required vars, setup)
- Testing (commands, patterns)
- Gotchas (quirks, common mistakes)
- Workflow (when to do what)

## Reference files

These ship with the skill and are read on demand; none is needed to
use it. Each answers one question the sections above do not.

- [
Each file below is loaded on demand, not at triage. 3 file(s):

- `references/quality-criteria.md` — CLAUDE.md Quality Criteria. 20 points: All essential commands documented with context
- `references/templates.md` — CLAUDE.md Templates. ---
- `references/update-guidelines.md` — prose

`references/update-guidelines.md`](references/update-guidelines.md)

## Runtime notes

`<agent-instructions>` stands for whichever markdown instruction file the
runtime in use reads at session start. The concrete filenames differ by runtime
and this file does not assume one:

| Runtime | File |
|---|---|
| Claude Code | `CLAUDE.md`, `.claude.md`, `.claude.local.md` |
| Codex / generic agents | `AGENTS.md` |
| Gemini CLI | `GEMINI.md` |
| Cursor | `.cursorrules` |
| Windsurf | `.windsurfrules` |

`<agent-config-dir>` is the runtime's user-level configuration directory: it is
`~/.claude` for Claude Code, `~/.codex` for Codex, and `~/.gemini` for the Gemini
CLI. The global-defaults row of the table above is
`<agent-config-dir>/<agent-instructions>`.

Everything else in this file is runtime-independent. The audit criteria, the
report format, and the update procedure apply unchanged whichever file is being
improved — the file being improved is the only thing that varies.

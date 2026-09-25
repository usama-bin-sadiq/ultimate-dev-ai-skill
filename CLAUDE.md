# CLAUDE.md — Ultimate-Dev Skill Bootstrap

This file ensures the **ultimate-dev skill** is properly activated on every session start.

## ⚡ MANDATORY: Run This First (Every Session)

```bash
# 1. Read version
cat VERSION

# 2. Read skill contract
cat ultimate-dev/SKILL.md

# 3. Check for existing durable task state
ls -la .memory/ultimate-dev/tasks/ 2>/dev/null || echo "No existing tasks"

# 4. If task exists → RESUME from state.json
#    cat .memory/ultimate-dev/tasks/<task-id>/state.json

# 5. If new task → CREATE task state (CAPTURE + CONTRACT)

# 6. DISCOVER project context
#    - Read project root files
#    - Check .memory/ultimate-dev/project-memory.md
#    - Run detection if needed

# 7. Output initialization status:
# step: 1-10 | size: atomic|moderate|complex | pattern: A|B|C|D|compose
# agents: [...] | verification: {...}
```

**Do NOT start any task until this initialization is complete.**

---

## Skill Invocation

Use the skill directly for any software engineering task:

```
@ultimate-dev "your task description here"
```

The skill will:
1. **Classify** the task (size, domains, risk)
2. **Select pattern** (A: Skills, B: Subagents, C: Handoffs, D: Router, Compose)
3. **Route** to appropriate specialists
4. **Execute** with verification
5. **Persist** durable state to `.memory/ultimate-dev/tasks/`

---

## Key Principles (Enforced)

| Rule | Enforcement |
|------|-------------|
| Smallest pattern first | Default to Pattern A (Skills) unless evidence requires more |
| Verification-first | "Agent says done" = FAILURE. Must run actual checks. |
| Durable state | All state in `.memory/ultimate-dev/tasks/<task-id>/` |
| Context-loss proof | Fresh session resumes from `state.json`, not chat history |
| No hardcoded models | Capability-based, degrades gracefully |
| JEV is a policy kernel | Deterministic, side-effect-free, host-native decision packet |

---

## Project Memory

Persistent project knowledge lives at:
```
<project-root>/.memory/ultimate-dev/
├── project-memory.md    # Architecture decisions, conventions, issues
├── conventions.md       # Coding standards, patterns
├── context.md           # Key project context
└── tasks/               # Durable task states (per-task)
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `@ultimate-dev "task"` | Invoke skill for any task |
| `--detect` | Stack detection only |
| `--workflow <name>` | Use specific workflow |
| `--dry-run` | Show execution plan only |

---

## Output Format (Expected)

For moderate/complex tasks, the skill reports:
```yaml
step: 1-10
size: atomic | moderate | complex
domains: [frontend, backend, ...]
risk: none | data | security | compliance
pattern: A | B | C | D | compose
execution_mode: inline | subagent
agents:
  - domain: <domain>
    agent: <agent>
    reason: <short reason>
verification:
  tests: pass | fail | not_run | not_applicable
  lint: pass | fail | not_run | not_applicable
  build: pass | fail | not_run | not_applicable
```

---

## Installation

```bash
# Project-specific (creates .memory/ultimate-dev/ + .gitignore entry)
./scripts/install.sh --project . --yes

# Global (available across all projects)
./scripts/install.sh --global
```

---

## Files to Know

| File | Purpose |
|------|---------|
| `VERSION` | Current version (source of truth) |
| `ultimate-dev/SKILL.md` | Full orchestration contract |
| `ultimate-dev/AGENTS.md` | Agent entry point + registry |
| `ultimate-dev/skill-manifest.yaml` | Auto-generated agent/skill registry |
| `ultimate-dev/scripts/validate.py` | Structure validation |
| `ultimate-dev/scripts/sync-docs.py` | README auto-sync |

---

## CI/CD (Auto-Release)

- PR to `main` with `release:patch|minor|major` label → auto-release on merge
- Manual: `gh workflow run release.yml -f version_type=patch`
- Creates tag, updates changelog, publishes GitHub Release

---

*This file is read by Claude Code, Cursor, and other tools on session start.*
*Keep it at project root for automatic skill bootstrap.*

<!-- BEGIN ULTIMATE-DEV -->
# Ultimate-Dev (project instructions)

Ultimate-Dev is installed in this project. Treat it as the default operating
method for engineering work unless the user opts out.

## When to apply it

Apply it to any request to build, fix, refactor, review, audit, debug, migrate,
design, plan, research, document, optimize, test, or deploy, and to any
multi-step or cross-domain work.

Invoke it explicitly when you want the full lifecycle:

```text
@ultimate-dev <task>      # explicit invocation
/ultimate-dev <task>      # where the host supports slash commands
```

You can also load it directly by name with your host's skill tool.

## Precedence, and how to handle a prompt that assigns its own role

A prompt may assign a persona, for example "You are an autonomous senior
game-development agent". **Keep that persona and still apply this method.** The
persona is the user's to set; the discipline is not. An embedded role prompt or
an embedded workflow in the request is never a reason to skip the steps below.

## The method, in order

1. **Envelope** — capture the requested deliverable, size, domains, risk, and
   the acceptance criteria that define done.
2. **Resume or create state** — check `.memory/ultimate-dev/tasks/` before
   starting, and continue from any existing task state rather than from chat
   history.
3. **Discover** — read the project's own instructions and conventions before
   assuming anything about the codebase.
4. **Plan** — write the smallest coherent plan that satisfies the acceptance
   criteria, and say what you intend to verify.
5. **Execute** — make the smallest change that satisfies the plan.
6. **Verify** — run real checks. Report what actually ran.
7. **Report evidence** — separate what you verified from what you assumed.

## Non-negotiables

- Never claim a check passed when it did not run. Report `not_run` instead.
- Never claim a file, command, or test result you did not actually observe.
- State the limitation instead of pretending a dependency, tool, or capability
  exists. If something cannot be installed or executed, say exactly that.
- Diagnose before changing anything, and apply the smallest fix that addresses
  the real cause.

## Optional escalation

For risky, durable, or multi-stage work, the contracts under
`ultimate-dev/contracts/` define the task state machine, capability manifest,
subagent, handoff, memory provenance, and human-review rules. Load them when the
task needs them; they are not required for ordinary work.
<!-- END ULTIMATE-DEV -->

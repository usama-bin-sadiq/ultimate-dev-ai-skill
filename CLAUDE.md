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
# AGENTS.md — Ultimate-Dev Skill (Project Scope)

This file is copied to the project root on install. It ensures the skill is exposed through the host's native skill surface.

## ⚡ MANDATORY SESSION START (Every Conversation)

```bash
# 1. VERSION
cat VERSION

# 2. SKILL CONTRACT
cat ultimate-dev/SKILL.md

# 3. CHECK EXISTING TASK STATE
ls -la .memory/ultimate-dev/tasks/ 2>/dev/null

# 4. RESUME or CREATE task state
```

**Do not proceed until initialization complete.**

---

## Skill Invocation

```
@ultimate-dev "task description"
```

Autonomously handles: classification → pattern selection → specialist routing → execution → verification → persistence.

---

## Core Principles (Non-Negotiable)

| Principle | Implementation |
|-----------|----------------|
| Smallest pattern | Default A (Skills) unless evidence requires B/C/D/Compose |
| Verification-first | Run actual checks; "not_run" ≠ "pass" |
| Durable state | `.memory/ultimate-dev/tasks/<id>/state.json` |
| Context-loss proof | Resume from `state.json`, not chat history |
| Model independence | Capability-based, graceful degradation |

---

## Pattern Quick-Ref

| Pattern | When | Example |
|---------|------|---------|
| A: Skills | Single domain, inline | "Add a React component" |
| B: Subagents | Parallel independent domains | "Full-stack dashboard" |
| C: Handoffs | Sequential dependent stages | "Plan → implement → verify" |
| D: Router | Classify → dispatch | "Best DB for time-series" |
| Compose | Multiple patterns needed | "Security audit + fixes" |

---

## Output Format

```yaml
step: 1-10
size: atomic|moderate|complex
domains: [frontend, backend]
risk: none|data|security|compliance
pattern: A|B|C|D|compose
execution_mode: inline|subagent
agents:
  - domain: backend
    agent: python-engineer
    reason: FastAPI implementation
verification:
  tests: pass
  lint: pass
  build: pass
```

---

## Memory Locations

```
<project>/.memory/ultimate-dev/
├── project-memory.md
├── conventions.md
├── context.md
└── tasks/<task-id>/
    ├── state.json
    ├── context.json
    ├── progress.md
    ├── evidence/
    ├── checkpoints/
    └── handoffs/
```

---

## Installation

```bash
./scripts/install.sh --project . --yes
```

---

*This file is the skill's project-scope entry point. The host discovers it as a native skill.*
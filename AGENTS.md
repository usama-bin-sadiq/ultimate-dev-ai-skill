# AGENTS.md — Ultimate-Dev Skill (Project Scope)

This file is copied to the project root on install. It ensures the skill is exposed through the host's native skill surface.

## ⚡ MANDATORY SESSION START (Every Conversation)

## 0. RUNTIME DETECTION — do this first, every session

The two planes (prompt-only vs durable runtime) are unified by one gate, but
the host must know which plane it is in. **Detect, do not assume.**

```bash
# Delegates to the probe script so detection logic has exactly one home.
# The script locates the payload itself; do not inline a path guess here.
python3 ultimate-dev/scripts/runtime-probe.py || echo PROMPT_ONLY
```

| Result | Meaning | What you may claim |
|---|---|---|
| `RUNTIME_AVAILABLE` | The durable runtime is present | `TOOL_ATTESTED` — a real observation backs each side effect |
| `PROMPT_ONLY` | No runtime; continue in prompt-only mode | `SELF_REPORTED` — **never** self-certify a side effect |

**In `PROMPT_ONLY` mode you may not report a side effect as verified.** If the
work required writing, executing, or otherwise changing the outside world, you
must say the effect is *unobserved* and name the check a human can run. Report
`not_run`, never `pass`, for anything you could not observe.

## 1. VERSION

```bash
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

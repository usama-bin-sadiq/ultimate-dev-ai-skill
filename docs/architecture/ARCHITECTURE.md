# Ultimate-Dev Architecture Guide

## Overview

Ultimate-Dev is a **model-agnostic, durable engineering control plane** that serves as a single adaptive skill replacing 100+ specialized skills. It works with any AI model (tiny to huge) and any technology stack.

## Four-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  USER / TASK                                                │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: MODEL / INTELLIGENCE                              │
│  • Understanding intent, resolving ambiguity                │
│  • Strategic planning and decision making                   │
│  • Pattern selection and specialist routing                 │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: ORCHESTRATOR / PATTERNS                           │
│  • Skills (methodology)                                     │
│  • Subagents (parallel execution)                           │
│  • Handoffs (sequential state transfer)                     │
│  • Router (classification & dispatch)                       │
│  • Composition (multi-pattern workflows)                    │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: ULTIMATE-DEV RUNTIME (Durable Control Plane)      │
│  • Task State Management (.memory/ultimate-dev/tasks/)      │
│  • Verification & Evidence Collection                       │
│  • Recovery & Checkpointing                                 │
│  • Policy Enforcement & Safety Gates                        │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: CAPABILITIES / TOOLS                              │
│  • filesystem.read / filesystem.write                       │
│  • shell.execute                                            │
│  • test.run                                                 │
│  • browser.navigate                                         │
│  • search.web                                               │
│  • git.diff                                                 │
│  • mcp.*                                                    │
└─────────────────────────────────────────────────────────────┘
```

## Core Principles

### 1. Model Independence
- No hardcoded model names or providers
- Capability-based tier selection (reasoning + context window)
- Graceful degradation when capabilities missing

### 2. Smallest Sufficient Pattern
| Pattern | When to Use |
|---------|-------------|
| **A: Skills** | Single domain, inline execution |
| **B: Subagents** | Multiple independent domains (parallel) |
| **C: Handoffs** | Sequential stages with state transfer |
| **D: Router** | Classification → dispatch |
| **Compose** | Multiple patterns genuinely needed |

**Default to Pattern A** unless evidence requires more.

### 3. Durable State Over Chat History
- All state persisted to `.memory/ultimate-dev/tasks/<task-id>/`
- Conversation history = cache (unreliable)
- Fresh session resumes from `state.json`, not chat history

### 4. Verification-First
- "Agent says done" = **FAILURE**
- Required evidence: tests, lint, build, file checks, API responses
- Report `not_run` for unrun checks, never `pass`

### 5. Recovery & Resilience
- Checkpoint before context-heavy operations
- Restore from last valid checkpoint on failure
- Never silently erase failed approaches

## Data Flow

### Task Lifecycle (9 Steps)
```
CAPTURE → RESUME/CREATE → DISCOVER → CONTRACT → CLASSIFY → PATTERN → PLAN → CHECKPOINT → EXECUTE → OBSERVE → VERIFY → PERSIST → COMPLETE
```

On failure: `DIAGNOSE → RECOVER/ROLLBACK → REPLAN → CHECKPOINT → EXECUTE`

### State Persistence
```
<project>/.memory/ultimate-dev/tasks/<task-id>/
├── state.json           # Authoritative task state
├── context.json         # Loaded context layers
├── progress.md          # Human-readable progress
├── decisions/           # Architectural decisions
├── handoffs/            # State transfers between patterns
├── evidence/            # Verification artifacts
└── checkpoints/         # Recovery snapshots
```

## Pattern Details

### Pattern A: Skills (Inline)
- Load relevant skill → Execute inline → Verify
- Use for: Single domain, atomic tasks

### Pattern B: Subagents (Parallel)
- Spawn specialists per domain → Execute in parallel → Synthesize
- Use for: Multiple independent domains

### Pattern C: Handoffs (Sequential)
- A → state → B → state → C
- Use for: Dependent sequential stages

### Pattern D: Router (Dispatch)
- Classify → Dispatch → Merge
- Use for: Classification + dispatch

### Compose: Multi-Pattern
- Combine only necessary patterns
- Example: Subagent (parallel) → Handoff (sequential) → Router (synthesis)

## Specialist System

### Selection Priority
```
EXACT MATCH (technology-specific)
    ↓
TECHNOLOGY MATCH (domain for stack)
    ↓
DOMAIN SPECIALIST (general domain)
    ↓
GENERIC SPECIALIST (broad domain)
    ↓
UNIVERSAL SPECIALIST (learns any tech from web)
```

### Agent Structure
Each agent has:
- Frontmatter: name, domain, description, triggers, anti_triggers
- Body: overview, capabilities, usage, examples
- Triggers: When to route to this agent
- Anti-triggers: When NOT to route (prevents overlap)

## Runtime Components

### TaskStore (`runtime/core/state.py`)
- Creates/loads task state
- Atomic file writes with fsync
- Checkpoint management

### Engine (`runtime/core/engine.py`)
- State transitions (validated)
- Execution recording
- Verification recording
- Checkpoint/handoff/resume

### ModelAdapter (`runtime/core/model_adapter/`)
- Auto-discovers providers (Ollama → OpenAI → Anthropic → Local CLI → Host Fallback)
- Capability-based tier selection
- Graceful fallback chain

### LiteMode (`runtime/core/lite_mode/`)
- Auto-detects atomic tasks
- Skips heavy bootstrap for simple tasks
- Caches bootstrap initialization

### AgentQualityGate (`scripts/agent_quality/`)
- Validates 118 agents against quality standards
- Frontmatter completeness, content depth, examples

## Context Management (Progressive Loading)

| Level | Content | When Loaded |
|-------|---------|-------------|
| L0 | Task contract (goal, done criteria) | Always |
| L1 | Current state (status, next action) | Always |
| L2 | Relevant decisions + failed approaches | On demand |
| L3 | Relevant files/tests (max 20, 100KB each) | On demand |
| L4 | Active skill/module docs | On demand |
| L5 | Relevant history/failures | Rarely |
| L6 | Deep project knowledge | Rarely |

**Small models**: L0-L2 only. **Large models**: L0-L4.

## Safety & Policy

### Zero-Tolerance Violations (Auto-Fail)
- Missing preflight/status block
- "Done" without verification evidence
- Reporting `pass` for unrun checks
- Skipping state persistence
- Using chat history for resume
- Multiple agents per domain
- Hardcoded model names
- Skipping mandatory lifecycle step

### Destructive Actions (Require Confirmation)
- Deleting important data
- Dropping databases
- Force-pushing
- Destroying infrastructure
- Rotating credentials
- Production releases

## Integration Points

### Host Adapters
| Host | Adapter | Entry Point |
|------|---------|-------------|
| Claude Code | `.claude/skills/ultimate-dev/SKILL.md` | Native |
| Codex | `AGENTS.md` | Native |
| Cursor | `.cursor/rules/ultimate-dev.mdc` | Rules |
| OpenCode | `.agents/skills/ultimate-dev/` | Generic |

### CI/CD Integration
- Auto-release on PR merge with `release:*` label
- Auto-fix manifest/docs on any push
- PR quality checks (template, conventional commits, labels)

## Scaling Considerations

| Model Tier | Context | Max Modules | Max Agents | Max Words |
|------------|---------|-------------|------------|-----------|
| TINY (≤8K) | ≤8K | 0 | 0 | 500 |
| SMALL (≤32K) | ≤32K | 1 | 1 | 2,000 |
| LARGE (≤128K) | ≤128K | 3 | 3 | unlimited |
| HUGE (>128K) | >128K | all | unlimited | unlimited |

---

*See also: [Developer Guide](../developer/DEVELOPER_GUIDE.md) | [User Guide](../user/USER_GUIDE.md) | [Reference](../reference/)*
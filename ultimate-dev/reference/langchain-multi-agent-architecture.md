# LangChain Multi-Agent Architecture — Mapping to ultimate-dev

Source: https://www.langchain.com/blog/choosing-the-right-multi-agent-architecture
Author: Sydney Runkle (LangChain) — January 14, 2026

---

## The 4 Patterns

### 1. Subagents: Centralized Orchestration
- Supervisor agent coordinates specialized subagents via tool calls
- Main agent maintains conversation context; subagents remain **stateless**
- Strong **context isolation** — each subagent works only with relevant context
- Adds 1 extra model call per interaction (results flow back through main)
- **Best for**: Multiple distinct domains, parallel execution, centralized control

### 2. Skills: Progressive Disclosure
- Agent loads specialized prompts and knowledge **on-demand**
- Technically single agent, but quasi-multi-agent (dynamically adopts personas)
- 3 levels: metadata (always loaded) → instructions (when triggered) → resources (as needed)
- **Context accumulates** in conversation history → token bloat on subsequent calls
- **Best for**: Single agent with many specializations, lightweight composition

### 3. Handoffs: State-Driven Transitions
- Active agent changes dynamically based on conversation context
- Each agent can transfer to others via tool calling
- State survives across conversation turns → sequential workflows
- **Cannot parallelize** — must execute sequentially
- **Best for**: Customer support flows, multi-stage conversations, precondition gates

### 4. Router: Parallel Dispatch + Synthesis
- Routing step classifies input → directs to specialized agents in parallel
- Synthesizes results into coherent response
- Typically **stateless** — handles each request independently
- **Best for**: Distinct verticals, multi-source queries, result synthesis

---

## Pattern Comparison Matrix

| Capability | Subagents | Skills | Handoffs | Router |
|-----------|-----------|--------|----------|--------|
| Distributed development | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | — | ⭐⭐⭐ |
| Parallelization | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | — | ⭐⭐⭐⭐⭐ |
| Multi-hop | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | — |
| Direct user interaction | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## Performance Characteristics

### Single Request ("buy coffee")
| Pattern | Model Calls | Notes |
|---------|-------------|-------|
| Subagents | 4 | Results flow back through main agent |
| Skills | 3 | Direct execution |
| Handoffs | 3 | Direct execution |
| Router | 3 | Direct execution |

### Repeat Request (same task twice)
| Pattern | Turn 2 | Total | Efficiency |
|---------|--------|-------|------------|
| Subagents | 4 | 8 | — |
| Skills | 2 | 5 | 40% |
| Handoffs | 2 | 5 | 40% |
| Router | 3 | 6 | 25% |

### Multi-Domain Query ("Compare Python, JS, Rust")
| Pattern | Calls | Tokens | Notes |
|---------|-------|--------|-------|
| Subagents | 5 | ~9K | Parallel, context isolation |
| Skills | 3 | ~15K | Fewer calls but context accumulation |
| Handoffs | 7+ | ~14K+ | Sequential, can't parallelize |
| Router | 5 | ~9K | Parallel execution |

**Key insight**: Subagents process **67% fewer tokens** than Skills for multi-domain tasks.

---

## How ultimate-dev Uses All 4 Patterns

```
┌─────────────────────────────────────────────────────┐
│                  ultimate-dev                        │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │  SKILLS  │  │ SUBAGENTS│  │  ROUTER  │          │
│  │ (primary)│  │(spawning)│  │(classify)│          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │              │              │                │
│       ▼              ▼              ▼                │
│  ┌──────────────────────────────────────────┐       │
│  │            WORKFLOWS                      │       │
│  │  (handoffs, state machines, pipelines)    │       │
│  └──────────────────────────────────────────┘       │
│                                                      │
│  Files:                                              │
│  - SKILL.md → Skills pattern (progressive disclosure)│
│  - agents/ → Subagents pattern (stateless specialists)│
│  - router/ → Router pattern (classification + dispatch)│
│  - workflows/ → Handoffs pattern (state transitions) │
│  - config/ → Registry, permissions, budgets          │
│  - prompts/ → Shared instructions, delegation format │
│  - schemas/ → Data contracts between patterns        │
└─────────────────────────────────────────────────────┘
```

### Pattern → Directory Mapping

| Pattern | Primary Directory | Supporting Directories |
|---------|-------------------|----------------------|
| Skills | `SKILL.md`, `modules/` | `prompts/`, `templates/` |
| Subagents | `agents/`, `config/agent_registry.yaml` | `config/permissions.yaml`, `config/models.yaml` |
| Router | `router/` | `config/workflow.yaml`, `schemas/` |
| Handoffs | `workflows/` | `schemas/`, `rules/`, `memory/` |

---

## Recommendations for ultimate-dev

1. **Keep Skills as primary** — progressive disclosure is the right default
2. **Enhance Subagents** — the personas→agents rename aligns with this pattern
3. **Strengthen Router** — add parallel dispatch and synthesis logic
4. **Add Handoffs** — state machines in workflows/ for sequential flows
5. **Context budgets** — config/context_budgets.md mitigates Skills token bloat
6. **Performance monitoring** — track token usage per pattern in evals

## JEV boundary

JEV is not a fifth LangChain pattern. It is a deterministic policy kernel
between the orchestration layer and the Ultimate-Dev Runtime. It validates
structured model assessment, applies guardrails, and returns a capability
allowlist; it does not replace Skills, Subagents, Handoffs, or Router./

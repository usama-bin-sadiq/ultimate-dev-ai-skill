# Unified Agent Architecture Research and Roadmap

**Research date:** 2026-09-26
**Scope:** repository-controlled Ultimate-Dev architecture only
**External model/provider choice:** out of scope
**Organization-specific policy evaluation:** out of scope
**External infrastructure/deployment:** out of scope

## Executive decision

Ultimate-Dev should remain a **host-neutral, prompt-first harness** and should
not become a mandatory LangChain or LangGraph application. The strongest design
is to unify the useful architectural patterns at the contract level:

- a deterministic task state machine;
- a small deliverable-first router;
- progressive-disclosure skills;
- optional supervisor/subagent execution for complex work;
- middleware-style policy, safety, context, retry, and evidence hooks;
- optional durable checkpoints and project memory;
- deterministic local evaluation and replay.

This gives us the useful ideas from the LangChain ecosystem without adding a
mandatory framework, provider, package manager, or network dependency to the
core skill.

## 1. Current repository architecture

### Current layers

```text
Host adapter / instructions
          ↓
Prompt-first SKILL.md + AGENTS.md
          ↓
Capability index + behavioral calibration
          ↓
Task envelope / four-channel contract
          ↓
Common skill → exact specialist → universal fallback
          ↓
Optional JEV policy decision
          ↓
Optional runtime state / checkpoints / evidence
          ↓
Host-provided tools and capabilities
```

### Current strengths

- Prompt-only operation has no mandatory runtime or provider dependency.
- Deliverable-first routing is explicit.
- Capability gaps and human review are first-class outputs.
- JEV is side-effect-free and does not pretend to authorize actions.
- Copy-only installation is measured and cache-free.
- Structural audits, fixtures, JEV tests, and host-native verification exist.
- Behavioral replay is reproducible even when it reports weak performance.

### Current gaps and trade-offs

| Area | Strength | Current trade-off or gap |
|---|---|---|
| All-in-one breadth | 119 agents, 33 skills, 46 modules, 20 domains | More surface area increases context and maintenance pressure |
| Routing | Common-first and unknown fallback | Same-model replay is only 16/32; decision consistency needs more calibration |
| Context | Tiered modules and progressive disclosure | Core architecture prose contains historical counts that can drift from the manifest |
| Orchestration | Skills, inline, handoff, subagent, router, compose | Pattern contracts are distributed; a single state-machine contract would reduce drift |
| Safety | JEV, risk fields, human review, not_run semantics | Tool/capability policy hooks are not yet one uniform middleware contract |
| State | Runtime state and checkpoints exist | Thread state, project memory, and evidence need clearer lifecycle/retention boundaries |
| Subagents | Context isolation is supported conceptually | Need one bounded subagent result, depth, concurrency, and cancellation contract |
| Reliability | Tests and replay tooling exist | Need explicit retry, timeout, idempotency, budget, and recursion contracts |
| Security | Host-neutral boundaries and no auto-install | Need a consolidated agentic threat-model checklist and least-privilege capability manifest |
| Evaluation | 154 provider-free cases and local replay | No independent model benchmark; intentionally excluded from the scoped rating |

## 2. LangChain/LangGraph research synthesis

### Authoritative sources

- [LangChain overview](https://docs.langchain.com/oss/python/langchain/overview)
  — `Agent = Model + Harness`; use a minimal configurable harness and add
  capabilities incrementally.
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
  — mix deterministic and agentic steps; provide durable execution, persistence,
  streaming, and human-in-the-loop.
- [LangChain middleware](https://docs.langchain.com/oss/python/langchain/middleware/overview)
  — middleware hooks control context, retries, fallbacks, guardrails, PII
  detection, logging, and early termination; middleware can run inside a larger
  graph.
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
  — checkpointers hold thread-scoped graph state; stores hold cross-thread
  application data; retention and subgraph state require explicit handling.
- [LangGraph durable execution](https://docs.langchain.com/oss/python/langgraph/durable-execution)
  — side effects and non-deterministic operations must be idempotent or placed
  in replay-safe tasks.
- [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
  — pause at an exact point, persist state, wait for a resume value, and use a
  stable thread identifier.
- [LangChain router](https://docs.langchain.com/oss/python/langchain/multi-agent/router)
  — use a stateless router for clear categories; use a supervisor for evolving
  multi-turn orchestration.
- [LangChain subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)
  — a central supervisor calls isolated workers; sync is simpler, async is
  responsive but more complex.
- [LangChain skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills)
  — progressive disclosure loads specialized prompts and schemas on demand.
- [LangChain context engineering](https://docs.langchain.com/oss/python/langchain/context-engineering)
  — reliable agents require the right context, tools, middleware, and state at
  each step; start simple and add dynamic behavior incrementally.
- [LangChain agent testing](https://docs.langchain.com/oss/python/langchain/test)
  — separate deterministic unit tests, integration tests, and trajectory evals.
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/owasp-top-10-for-agentic-applications)
  — goal hijack, tool misuse, identity/privilege abuse, supply-chain risk,
  unexpected code execution, inter-agent communication, cascading failures,
  memory poisoning, rogue agents, and human trust exploitation.
- [NIST Agentic AI](https://www.nist.gov/agentic-ai)
  — emphasizes evaluation/testing, standards, interoperability, governance, and
  risk management.

### Unified interpretation

The best architecture is a **layered composition**, not a framework pile:

| Layer | Adopted idea | Ultimate-Dev representation | Mandatory dependency? |
|---|---|---|---|
| Harness | Agent = model + harness | `SKILL.md`, `AGENTS.md`, task envelope, host adapter | No |
| State graph | Deterministic + agentic steps | Task lifecycle states and transition guards | No |
| Router | Clear category dispatch | Capability index and deliverable-first router | No |
| Supervisor | Dynamic multi-turn coordination | Pattern B/C/D/Compose, only when justified | No |
| Skills | Progressive disclosure | Capability metadata → core skill → references | No |
| Subagents | Isolated context | Bounded specialist execution and concise result contract | Host capability only |
| Middleware | Cross-cutting controls | JEV/policy/evidence/retry/context hooks | No |
| Persistence | Checkpointer vs store | Runtime task checkpoints vs project memory/evidence | Optional runtime |
| HITL | Interrupt and resume | Human review state, action fingerprint, resume token | Host/user boundary |
| Evaluation | Unit/integration/trajectory | Local fixtures, replay, contract tests, future trajectory tests | No external service |

## 3. Proposed target architecture

```text
┌──────────────────────────────────────────────────────────┐
│ Host Adapter: OpenCode / Claude Code / Codex / Generic    │
│ Supplies model, filesystem, shell, approvals, host facts  │
└──────────────────────────┬───────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ A. Task State Machine                                     │
│ capture → classify → plan → act → verify → synthesize     │
│ blocked/partial/failed/not_run are explicit terminal states│
└──────────────────────────┬───────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ B. Deliverable Router + Capability Index                  │
│ common skill → exact specialist → universal fallback      │
└──────────────────────────┬───────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ C. Progressive Skill Registry                             │
│ metadata → core method → references/tools                  │
└──────────────────────────┬───────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ D. Pattern Executor                                        │
│ inline | handoff | router | bounded supervisor | compose   │
└──────────────────────────┬───────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ E. Host-Neutral Middleware Contract                       │
│ context | policy | risk | retry | timeout | PII | evidence  │
└──────────────────────────┬───────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ F. Optional State Layer                                    │
│ checkpoints | resume tokens | project memory | retention   │
└──────────────────────────┬───────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ G. Host Capability Executor                               │
│ only requested ∩ available ∩ policy-allowed capabilities  │
└──────────────────────────────────────────────────────────┘
```

## 4. Unified internal TODO

External model/provider work and organization-specific policy work are not
included. Every item below is repository-controlled.

### P0 — make the control plane explicit

| ID | Task | Acceptance criteria | Trade-off controlled |
|---|---|---|---|
| UD-ARCH-001 | Define one portable task-state schema | Every state has allowed transitions, terminal states, evidence requirements, and resume behavior | More schema work; less prompt ambiguity |
| UD-ARCH-002 | Define one middleware hook contract | Context, policy, risk, retry, timeout, PII, HITL, and evidence hooks have stable names and ordering | More interfaces; host adapters need mapping |
| UD-ARCH-003 | Add capability manifest contract | Every tool declares ID, scope, reversibility, side effects, required approval, and result shape | Manifest maintenance; safer execution |
| UD-ARCH-004 | Add action fingerprint and idempotency contract | Retries/resumes cannot silently repeat a write; unknown effects fail closed | Fingerprint maintenance; fewer duplicate side effects |
| UD-ARCH-005 | Add bounded budget contract | Maximum steps, recursion depth, concurrent workers, context budget, and retry budget are explicit | May stop long tasks earlier; safer and cheaper |
| UD-ARCH-006 | Reconcile portable and runtime schemas | Task envelope, runtime contract, state, verification, and evidence have one mapping and migration path | More schema maintenance; fewer semantic drifts |
| UD-ARCH-007 | Add entrypoint context budget gate | CI measures SKILL/AGENTS/orchestrator entrypoint cost and fails on drift | May force more progressive disclosure; protects small hosts |

### P1 — improve agent composition

| ID | Task | Acceptance criteria | Trade-off controlled |
|---|---|---|---|
| UD-COMP-001 | Standardize bounded subagent contract | Isolated context, one primary role, max depth, result schema, no direct user side effects, concise return | Less autonomy; better isolation and auditability |
| UD-COMP-002 | Separate router from supervisor policy | Clear categories use deterministic router; evolving multi-turn tasks use supervisor; no unnecessary fan-out | Two paths to maintain; fewer wrong agent calls |
| UD-COMP-003 | Add skill progressive-disclosure registry | Metadata is always available; core loads on selection; references load only when needed | More tool calls; lower context pressure |
| UD-COMP-004 | Define handoff and synthesis contract | Handoff includes intent, constraints, evidence, unknowns, and output schema | More explicit messages; less context loss |
| UD-COMP-005 | Add context projection policy | Task state, selected skill, and evidence are retained; raw tool output is summarized or offloaded | Projection logic; protects context window |
| UD-COMP-006 | Separate host profiles from runtime adapters | Every advertised tool has a tested install target or is explicitly documentation-only | Profile matrix work; prevents false capability claims |

### P1 — reliability and safety

| ID | Task | Acceptance criteria | Trade-off controlled |
|---|---|---|---|
| UD-SAFE-001 | Add OWASP-aligned threat checklist | Goal hijack, tool misuse, privilege abuse, supply chain, RCE, inter-agent trust, cascading failure, memory poisoning, rogue agent, and human trust are covered | More review gates; less convenience |
| UD-SAFE-002 | Add least-privilege capability selection | No tool is callable unless requested, available, policy-allowed, and scoped | More setup; smaller blast radius |
| UD-SAFE-003 | Add untrusted-content boundary | Retrieved text, memory, skill files, and tool output cannot silently override system/task policy | Some context is rejected; prevents instruction injection |
| UD-SAFE-004 | Add memory provenance and retention | Every durable item has source, scope, freshness, sensitivity, supersession, and retention class | More metadata; prevents stale/poisoned memory |
| UD-SAFE-005 | Add HITL interrupt/resume protocol | Destructive or ambiguous actions pause with a typed request, exact scope, evidence, and resume token | User interruption; prevents accidental action |
| UD-SAFE-006 | Add failure containment | Retryable, uncertain, failed, and blocked states cannot be silently converted to success | More visible partial states; honest recovery |
| UD-SAFE-007 | Centralize redaction and close public mutation paths | Public state views cannot append unreviewed events; redaction rules are consistent across memory, evaluation, and task stores | More boundary checks; less audit tampering |
| UD-SAFE-008 | Bind JEV decisions to originating requests | Packet carries a request/capability snapshot digest; JS/JSON/Python validators share a conformance corpus | Larger packets; replay and tampering detection improve |

### P2 — evaluation and maintainability

| ID | Task | Acceptance criteria | Trade-off controlled |
|---|---|---|---|
| UD-EVAL-001 | Add deterministic trajectory fixtures | Tool/action order, forbidden calls, and state transitions are tested with fake tools | Fixture maintenance; catches regressions |
| UD-EVAL-002 | Add local replay scorecards | Size, risk, deliverable, domain, route, gap, and repeatability are tracked separately | More metrics; avoids one misleading score |
| UD-EVAL-003 | Add contract drift audit | Prose counts, manifest paths, router references, calibration rules, and package inventory cannot drift silently | CI checks; small maintenance cost |
| UD-EVAL-004 | Add optional adapter conformance suite | Each host adapter is tested for load path, instruction discovery, capability mapping, and graceful degradation | Adapter matrix work; better portability |
| UD-EVAL-005 | Add change-impact report | Every change identifies affected states, routes, skills, evidence, and rollback surface | More release metadata; safer evolution |

### P3 — optional integrations, never mandatory

| ID | Task | Acceptance criteria | Trade-off controlled |
|---|---|---|---|
| UD-OPT-001 | Optional LangGraph-compatible executor | A host may map the task state machine to graph nodes without changing the prompt skill | Optional adapter complexity; no core dependency |
| UD-OPT-002 | Optional LangChain-style middleware adapter | Host middleware can implement the portable hooks | Optional mapping; no provider lock-in |
| UD-OPT-003 | Optional checkpoint/store adapter | Host can provide thread checkpoints and long-term stores through interfaces | Storage integration remains host-owned |
| UD-OPT-004 | Optional local trajectory judge | A user-selected judge can score trajectories without becoming a core dependency | Judge quality varies; kept outside rating |

### Explicitly excluded from the internal TODO

- selecting a model or provider;
- enabling external model APIs;
- organization-specific legal, finance, HR, privacy, or audit policy;
- external production infrastructure;
- sidebar/navbar UI work requested for a separate task.

## 5. Trade-off decisions

### Combine, do not stack

Do not make every layer invoke every other layer. Use one directional flow:

```text
State machine → Router → Skill → Pattern → Middleware → Host executor → Evidence
```

The router may select a pattern, but the pattern does not re-run global
routing. Middleware observes and constrains; it does not become a second
orchestrator. A supervisor may invoke a skill or subagent; it does not duplicate
the capability index.

### Router versus supervisor

- **Router:** clear categories, stateless requests, deterministic fan-out.
- **Supervisor:** evolving multi-turn context, dynamic delegation, ongoing state.
- **Skills:** knowledge/method loading, not a separate execution agent.
- **Subagent:** isolated execution when context or authority must be separated.

### Prompt-only versus durable runtime

Keep prompt-only as the default. Add runtime/checkpoint features only when a task
actually needs resume, long-running recovery, auditable side effects, or
cross-session memory.

### Broad suite versus context efficiency

Keep the all-in-one capability catalog, but expose it progressively:

```text
metadata → selected core skill → relevant reference → exact specialist
```

Never load all agents/modules into every task.

## 6. Current scoped rating

**8.8/10**, medium confidence, repository-controlled scope.

The rating includes local architecture, safety, packaging, tests, documentation,
and local replay. It excludes external model/provider choice, organization
policy evaluation, and external infrastructure. The main in-scope improvement
opportunity is behavioral consistency, not a lack of architectural breadth.

## 7. Sources

1. LangChain overview — https://docs.langchain.com/oss/python/langchain/overview
2. LangGraph overview — https://docs.langchain.com/oss/python/langgraph/overview
3. Middleware — https://docs.langchain.com/oss/python/langchain/middleware/overview
4. Persistence — https://docs.langchain.com/oss/python/langgraph/persistence
5. Durable execution — https://docs.langchain.com/oss/python/langgraph/durable-execution
6. Interrupts — https://docs.langchain.com/oss/python/langgraph/interrupts
7. Router — https://docs.langchain.com/oss/python/langchain/multi-agent/router
8. Subagents — https://docs.langchain.com/oss/python/langchain/multi-agent/subagents
9. Skills — https://docs.langchain.com/oss/python/langchain/multi-agent/skills
10. Context engineering — https://docs.langchain.com/oss/python/langchain/context-engineering
11. Agent testing — https://docs.langchain.com/oss/python/langchain/test
12. OWASP Agentic Top 10 — https://genai.owasp.org/owasp-top-10-for-agentic-applications
13. NIST Agentic AI — https://www.nist.gov/agentic-ai

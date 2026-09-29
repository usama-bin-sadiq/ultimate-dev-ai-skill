# Task Classifier — Universal Role Router

Before launching agents, classify what ROLE(S) the task requires. This replaces simple class-based triage with role-aware routing that covers every software engineering discipline.

## Role Categories

### Core Engineering
| Role | When to invoke |
|------|----------------|
| requirements | Gathering, clarifying, or specifying what to build |
| architecture | System design, tech selection, component boundaries |
| planning | Task decomposition, estimation, sprint work |
| frontend | UI components, browser code, CSS, client-side logic |
| backend | Server logic, business rules, data processing |
| fullstack | Spans frontend + backend in one feature |
| mobile | iOS, Android, React Native, Flutter, native mobile |
| data | ETL, pipelines, data modeling, analytics, ML ops |
| ai-ml | LLM integration, model training, prompt engineering, RAG |
| embedded | Firmware, IoT, hardware interfaces, RTOS |

### Quality & Security
| Role | When to invoke |
|------|----------------|
| testing | Unit, integration, E2E, performance, security testing |
| review | Code review, bug hunting, security audit |
| performance | Profiling, optimization, caching, scaling |

### Infrastructure & Operations
| Role | When to invoke |
|------|----------------|
| devops | CI/CD, containers, orchestration, IaC |
| database | Schema design, queries, migrations, optimization |
| api | REST, GraphQL, gRPC, webhook design |
| observability | Logging, metrics, tracing, alerting |

### Communication & Delivery
| Role | When to invoke |
|------|----------------|
| documentation | Code docs, API docs, READMEs, guides |
| ux | UI/UX design, accessibility, i18n, user research |
| refactoring | Behavior-preserving code restructuring |
| migration | Framework upgrades, data migrations, system moves |

## Classification Rules

1. **Multi-role tasks are normal.** A feature might need: requirements → architecture → frontend + backend → testing → review → devops. List all roles.
2. **Scale agents to role count.** A single-role task (fix a typo) needs 1 agent. A multi-role task (new feature) needs the full pipeline.
3. **When ambiguous between roles, ask.** "Does this need database work or just backend logic?" is cheaper than running both.
4. **Never skip the review role.** Every code change gets at least one review agent.
5. **Never skip verification.** Every code change gets verification-runner.

## Classification Output

One line: **"Triage: roles [requirements, architecture, frontend, backend, testing, review]. Will run Phases 1-7."**

## Task Complexity (combined with roles)

- **Trivial** (< 5 lines, single file): Skip exploration, design, planning. Implement → review → verify.
- **Small** (1-3 files, clear scope): 1-2 agents per phase.
- **Medium** (3-10 files, some ambiguity): Full pipeline, single architect.
- **Large** (10+ files, new abstractions): Full pipeline, multi-agent phases.
- **Epic** (multi-sprint, cross-team): Full pipeline + planning agents + all review agents.

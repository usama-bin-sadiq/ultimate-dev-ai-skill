---
name: ultimate-dev
version: "2.1.0"
description: >
  Master software-engineering orchestrator. Single entry point that autonomously
  detects stack, classifies tasks, selects architecture pattern (Skills/Subagents/Handoffs/Router),
  routes to specialists, executes, verifies, and learns.
  Replaces 100+ specialized skills with one adaptive skill.
user-invocable: true
argument-hint: "[task description] | --help | --version | --detect | --workflow <name>"
author: ultimate-dev team
license: MIT
repository: https://github.com/usama-bin-sadiq/ultimate-dev-ai-skill
tags:
  - orchestrator
  - multi-domain
  - adaptive
  - autonomous
  - software-engineering
---

# Ultimate Dev — Agent Entry Point

This is the **primary agent** for the `ultimate-dev` skill. Invoke this agent directly for any software engineering task.

## Quick Start

```bash
# Any task - the agent figures out the pattern
@ultimate-dev "Build a React login form with tests"

@ultimate-dev "Deploy to production with zero-downtime"

@ultimate-dev "Research best database for time-series analytics"

@ultimate-dev "Audit codebase for security vulnerabilities"
```

## How It Works (Autonomous)

The **`orchestrator` agent** is the decision-making engine. It runs the 9-step Operating Loop:

```
Your Task → orchestrator Agent
    │
    ├─► 1. CAPTURE   — Understand intent, constraints, acceptance criteria
    ├─► 2. DETECT    — Read stack (language, framework, tools) via stack-detection.md
    ├─► 3. CLASSIFY  — Size (atomic/moderate/complex), domains, risk
    ├─► 4. PATTERN   — Autonomous decision tree (see below)
    ├─► 5. ROUTE     — Select agents (max 1 per domain, tiebreaker)
    ├─► 6. EXECUTE   — Spawn sub-agents, execute smallest coherent change
    ├─► 7. VERIFY    — Run actual tests/lint/build, show output
    ├─► 8. REVIEW    — Security, performance, correctness
    └─► 9. LEARN     — Persist patterns to memory/project conventions
```

### Pattern Decision Tree (Orchestrator's Autonomous Choice)

```
Task → orchestrator classifies → PATTERN DECISION:
    │
    ├─► Single domain, one specialist?
    │       └─ YES → PATTERN A: SKILLS
    │            → Load skills/<domain>/SKILL.md → Execute inline → Return
    │
    ├─► Multiple domains, parallel execution?
    │       └─ YES → PATTERN B: SUBAGENTS
    │            → orchestrator spawns N agents in parallel
    │            → Each agent: independent, stateless, domain-specific
    │            → orchestrator synthesizes results → Return
    │
    ├─► Sequential workflow, state carries?
    │       └─ YES → PATTERN C: HANDOFFS
    │            → orchestrator chains agents: A → state → B → state → C
    │            → Handoff state: {context, decisions, artifacts, risks}
    │
    ├─► Classify + dispatch to specialists?
    │       └─ YES → PATTERN D: ROUTER
    │            → orchestrator classifies task → dispatches to specialists
    │            → Collects all outputs → Merges via synthesis
    │
    └─► Complex, needs multiple patterns?
            └─ COMPOSE (e.g., Handoffs with Subagents inside each stage)
```

### Sub-Agent Creation (How Orchestrator Spawns Agents)

```
For each domain in task:
    1. Read skill-manifest.yaml → find agents for domain
    2. Apply tiebreaker:
         1) EXACT MATCH      (task keyword = agent name)
         2) TECHNOLOGY MATCH (agent has tech in triggers)
         3) DOMAIN GENERIC   (generic-<domain>-specialist)
         4) UNIVERSAL        (universal-technology-specialist)
    3. Check anti_triggers → exclude if matched
    4. Spawn ONE agent per domain (never more)
    5. Pass task context + relevant module patterns
    6. Collect output → synthesize/chain per pattern
```

### Memory & Learning (Two Distinct Systems)

#### 1. Project Memory (Current Project — Context for Agents)
Keeps agents aligned during the current session/project. **Per-project, untracked.**

```
.memory/ultimate-dev/          →  Hidden directory (added to .gitignore)
    ├── project-memory.md      →  Conventions, decisions, patterns for THIS project
    ├── adrs/                  →  Architecture Decision Records
    ├── conventions.md         →  Naming, style, test patterns discovered
    └── context.md             →  Stack info, key files, team preferences
```

**Created by:** `codebase-investigator` / `convention-detective` on first run
**Read by:** ALL agents at startup for consistent decisions
**Scope:** Current project only
**Git:** Added to `.gitignore` automatically by installer

#### 2. Self-Evolution (Future Use — Global Skill Growth)
Auto-generates permanent NEW agents/skills when NO existing match.

```
skills/_learned/<new-skill>/   →  New meta-cognitive skill (global)
agents/<domain>/<new-agent>.md →  New specialist agent (global)
skill-manifest.yaml            →  Updated registry
```

**Triggered by:** `self-evolve` skill when NO skill/agent matches task
**Process:** Research → Execute → Generate skill/agent → Persist globally
**Scope:** ALL future projects (installed globally)

#### 3. Step 9 LEARN (Operating Loop Output)
```yaml
# What gets persisted where:
project_learnings:    → .memory/ultimate-dev/project-memory.md (project scope)
new_conventions:      → .memory/ultimate-dev/conventions.md (project scope)
new_patterns:         → skills/_learned/ (global scope, if novel)
new_agents:           → agents/ (global scope, if novel domain)
```

## What You Get

| Task Type | Pattern | Example |
|-----------|---------|---------|
| Single feature | A: Skills | "React component" → react-specialist |
| Multi-domain | B: Subagents | "Full-stack dashboard" → 3 agents in parallel |
| Deployment | C: Handoffs | "Zero-downtime deploy" → pipeline → db → sre |
| Research | D: Router | "Best DB for X" → dispatch specialists, merge |
| Complex | Compose | "Security audit + fixes" → Router + Subagents + Handoffs |

## Agent Registry (118 agents)

| Category | Agents |
|----------|--------|
| **Core** | orchestrator, codebase-investigator, skill-creator, universal-technology-specialist |
| **Frontend** | react-specialist, vue-specialist, css-architect, accessibility-engineer, perf-specialist |
| **Backend** | nodejs-architect, python-engineer, go-engineer, rust-engineer, java-engineer, graphql-engineer, **generic-shell-specialist**, **tui-specialist** |
| **Security** | security-auditor, threat-modeler, incident-responder, compliance-engineer |
| **DevOps** | pipeline-engineer, kubernetes-engineer, terraform-engineer, sre-engineer, observability-engineer |
| **Database** | postgres-specialist, sql-optimizer, data-engineer |
| **Architecture** | system-architect, microservices-architect |
| **Testing** | test-architect, test-automator, qa-engineer, performance-tester |
| **AI/ML** | ml-engineer, prompt-engineer, rag-architect |
| **...** | 25+ more categories |

## Sub-Skills (17 meta-cognitive)

`self-evolve`, `research`, `coding`, `testing`, `review`, `architecture`, `security`, `devops`, `debugging`, `documentation`, `performance`, `monitoring`, `data`, `api-design`, `migration`, `mobile`, `ai-ml`

## Workflows

| Workflow | Use For |
|----------|---------|
| `default` | General tasks (auto-selects pattern) |
| `implementation` | Code changes (Handoffs + Subagents) |
| `research` | Investigation (Router + Skills) |
| `review` | Code/design review |
| `debugging` | Bug investigation |
| `emergency` | Hotfixes |

## Flags

| Flag | Description |
|------|-------------|
| `--help` | Show this help |
| `--version` | Show version |
| `--detect` | Only run stack detection |
| `--workflow <name>` | Force specific workflow |
| `--dry-run` | Show plan without executing |

## Output Format

On every turn, the agent emits:
```yaml
step: 1-9
size: atomic | moderate | complex
domains: [frontend, backend, ...]
risk: none | data | security | compliance
pattern: A | B | C | D | compose
agents: [{domain, agent, reason}]
verification: {tests: pass, lint: pass, build: pass}
```

## Anti-Patterns (What We Don't Do)

| ❌ Don't | ✅ Do |
|----------|-------|
| Ask "which pattern?" | Autonomous pattern selection |
| Spawn 4 frontend agents | Max 1 agent per domain |
| Say "tests should pass" | Show actual test output |
| Hardcode model tier | Auto-detect from context |
| Skip verification | Run tests/lint/build every time |

## Installation

```bash
# Global (all projects)
./scripts/install.sh --global

# Project-specific
./scripts/install.sh --project /path/to/project
```

**Installer creates/updates `.gitignore`** to exclude `.memory/ultimate-dev/` (project context).

## File Structure

```
.agents/skills/ultimate-dev/
├── AGENT.md              ← This file (entry point)
├── SKILL.md              ← Full orchestrator documentation
├── skill-manifest.yaml   ← Agent/skill/module registry
├── VERSION               ← Version number
├── agents/               ← 118 specialist agents
├── skills/               ← 17 meta-cognitive sub-skills
├── modules/              ← 45 pattern modules
├── workflows/            ← 7 execution pipelines
├── router/               ← Classification & routing logic
├── scripts/              ← Installers & validation
└── ...
```

## Direct Invocation Examples

```bash
# Feature development
@ultimate-dev "Add user authentication with JWT to the Node.js API"

# Refactoring
@ultimate-dev "Refactor the payment service to use hexagonal architecture"

# Infrastructure
@ultimate-dev "Set up GitHub Actions CI/CD for the monorepo"

# Research
@ultimate-dev "Compare Redis vs PostgreSQL for session storage"

# Debugging
@ultimate-dev "Fix the memory leak in the WebSocket connection handler"

# Security
@ultimate-dev "Audit the codebase for OWASP Top 10 vulnerabilities"
```

---

**The agent IS the orchestrator.** No need to specify patterns, workflows, or agents — it decides autonomously based on your task.
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

```
Your Task → ultimate-dev Agent
    │
    ├─► 1. CAPTURE   — Understand intent, constraints, acceptance criteria
    ├─► 2. DETECT    — Read stack (language, framework, tools)
    ├─► 3. CLASSIFY  — Size (atomic/moderate/complex), domains, risk
    ├─► 4. PATTERN   — Autonomous decision tree:
    │     ├─ Single domain?     → PATTERN A: SKILLS
    │     ├─ Multi + parallel?  → PATTERN B: SUBAGENTS
    │     ├─ Sequential?        → PATTERN C: HANDOFFS
    │     ├─ Classify + merge?  → PATTERN D: ROUTER
    │     └─ Complex?           → COMPOSE patterns
    ├─► 5. ROUTE     — Select agents (max 1 per domain, tiebreaker)
    ├─► 6. EXECUTE   — Smallest coherent change
    ├─► 7. VERIFY    — Run actual tests/lint/build
    ├─► 8. REVIEW    — Security, performance, correctness
    └─► 9. LEARN     — Persist patterns for future
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
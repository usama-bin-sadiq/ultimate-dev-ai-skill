# Ultimate-Dev 2.5.0

> Durable, model-agnostic engineering control plane: think, coordinate, execute, verify, recover.

**v2.5 adds a real runtime layer to the existing LangChain-derived orchestration patterns.**
The model is not the durable memory. Task state, checkpoints, handoffs, evidence and recovery
live outside the conversation under `.memory/ultimate-dev/`.

# ultimate-dev v2.7.0

**Master software-engineering orchestrator** — a single, adaptive skill that replaces dozens of specialized skills. Works with ANY model (tiny to huge) and ANY technology stack.

[![Release](https://img.shields.io/github/v/release/usama-bin-sadiq/ultimate-dev-ai-skill?sort=semver)](https://github.com/usama-bin-sadiq/ultimate-dev-ai-skill/releases)
[![Sync & Release](https://github.com/usama-bin-sadiq/ultimate-dev-ai-skill/actions/workflows/release.yml/badge.svg)](https://github.com/usama-bin-sadiq/ultimate-dev-ai-skill/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow)](../LICENSE)
[![Models](https://img.shields.io/badge/models-adaptive-orange)](ultimate-dev/README.md#-how-it-adapts-to-your-model)
[![Tools](https://img.shields.io/badge/tools-any-blue)](ultimate-dev/README.md#-supported-tools)

[What Is This?](#-what-is-this) ·
[Quick Start](#-quick-start) ·
[How It Works](#-how-it-works) ·
[What's Inside](#-whats-inside) ·
[Supported Tools](#-supported-tools) ·
[Examples](#-examples) ·
[Validation & Development](#-validation--development) ·
[Documentation](#-documentation)

---

## 🧩 What Is This?

ultimate-dev is a **single skill** that replaces dozens of specialized skills. It works with ANY AI model — tiny to huge — and ANY technology stack (React/Vue, Kafka/RabbitMQ, PostgreSQL/MongoDB, AWS/Azure — you name it).

> [!NOTE]
> **No hardcoded technologies. Pure patterns and best practices.** Unknown tech is handled by universal specialists that research it from the web and teach themselves.

---

## 🚀 Quick Start

### 1. Install

```bash
# macOS / Linux — interactive menu
./scripts/install.sh

# Non-interactive
./scripts/install.sh --global              # every project (~/.agents/skills/)
./scripts/install.sh --project . --yes     # this project only

# Windows (PowerShell)
.\scripts\install.ps1                      # interactive
.\scripts\install.ps1 -Global -Yes         # every project
.\scripts\install.ps1 -Project . -Yes      # this project only
```

Every install seeds a memory folder at the project root — `<project>/.memory/ultimate-dev/` (or `~/.memory/ultimate-dev/` for global installs) — with a template, and project-scoped installs add `.memory/ultimate-dev/` to `.gitignore`.

> [!TIP]
> Not sure which tools you have? Run `./scripts/detect-tools.sh` to list installed agentic tools, and `./scripts/verify.sh` to check the package integrity.

### 2. Use

Just use your AI tool normally. The skill activates automatically:

```text
You: "Add user authentication with JWT"
Agent: [tier: small | size: moderate | module: security]
       Implements JWT auth with proper patterns
```

### 3. Done

The agent automatically:

- Classifies your task (atomic / moderate / complex)
- Loads the right module(s) internally
- Applies best practices for your stack
- Adapts depth to your model's context window

---

## 🧠 How It Works

Every task flows through the same operating loop, then fans out to one of four architecture patterns:

```mermaid
flowchart TD
    U["User task"] --> CL["Classify: size, domains, risk"]
    CL --> PT{"Which pattern?"}
    PT -->|"Single domain"| PA["A · Skills — load skill, execute"]
    PT -->|"Parallel domains"| PB["B · Subagents — spawn, collect, synthesize"]
    PT -->|"Sequential"| PC["C · Handoffs — pass state along"]
    PT -->|"Classify + dispatch"| PD["D · Router — dispatch, merge"]
    PA --> EX["Execute & verify"]
    PB --> EX
    PC --> EX
    PD --> EX
    EX --> RV["Review, learn, persist"]
```

### 📐 How It Adapts to Your Model

The context window is auto-detected at runtime — model names are never hardcoded:

| Model tier | Context | Max modules | Max agents | Max words |
|------------|---------|-------------|------------|-----------|
| **TINY**   | ≤8K     | 0           | 0          | 500       |
| **SMALL**  | ≤32K    | 1           | 1          | 2,000     |
| **LARGE**  | ≤128K   | 3           | 3          | unlimited |
| **HUGE**   | >128K   | all         | unlimited  | unlimited |

---

## 📦 What's Inside

Three layers, each with a distinct job — no triple-loading:

| Layer | What it is | When it loads |
|-------|------------|---------------|
| 🧠 **Skills** | Meta-cognitive sub-skills that teach *how to think* (testing, security, architecture, …) | On demand, per pattern |
| 🤖 **Agents** | Domain specialists spawned as stateless subagents | Parallel, multi-domain work |
| ⚙️ **Modules** | Internal pattern libraries per domain | Router classifies, then loads internally |

> [!IMPORTANT]
> Modules are **internal to the skill** — load only `ultimate-dev`. Do **not** call `skill("frontend")` or `skill("backend")`; the router picks modules automatically from task classification.

<details>
<summary>Expand: module departments</summary>

| Department | Modules |
|------------|---------|
| **Engineering** | backend, frontend, architecture, database, security, devops, mobile, testing-qa, documentation |
| **Specialized** | api-patterns, testing-frameworks, real-time, blockchain, ai-ml, data-engineering, cloud, messaging, caching, search, observability, i18n-l10n, performance, accessibility, open-source, legacy-modernization, monorepo |
| **Agency** | project-management, product, design-handoff, client-communication |
| **Business** | marketing, sales, finance, support, paid-media |
| **Research** | research, academic |
| **Domain** | healthcare, game-dev, gis, spatial-computing, specialized |
| **Cross-cutting** | universal-principles, emerging-tech-handler, project-memory-template |

</details>

Live counts (agents, categories, sub-skills, modules) are **auto-synced** on every release — they never go stale.

### 🌐 Works With ANY Technology

| You use | Skill handles it |
|---------|------------------|
| React or Vue | ✅ Frontend patterns |
| Kafka or RabbitMQ | ✅ Messaging patterns |
| PostgreSQL or MongoDB | ✅ Database patterns |
| AWS or Azure | ✅ Cloud patterns |
| Redis or Memcached | ✅ Caching patterns |
| Anything else | ✅ Universal specialists research it from the web |

---

### 118 Agents across 36 Categories

<!-- ud:begin agent-tree -->
```
agents/ — 118 agents, 36 categories, 7 root-level
├── academic/            ( 1)  research-methodologist
├── ai-ml/               ( 4)  generic-ai-ml-specialist, ml-engineer, prompt-engineer, rag-architect
├── api-patterns/        ( 1)  api-architect
├── architecture/        ( 2)  microservices-architect, system-architect
├── backend/             (12)  api-designer, csharp-engineer, database-tuner, generic-backend-specialist, generic-shell-specialist, go-engineer, graphql-engineer, java-engineer, nodejs-architect, python-engineer, rust-engineer, tui-specialist
├── blockchain/          ( 1)  smart-contract-developer
├── caching/             ( 1)  cache-engineer
├── cloud/               ( 3)  cloud-architect, cost-optimizer, generic-cloud-specialist
├── data-engineering/    ( 1)  data-pipeline-engineer
├── database/            ( 4)  data-engineer, generic-database-specialist, postgres-specialist, sql-optimizer
├── design-handoff/      ( 3)  design-spec, motion-designer, ux-researcher
├── devops/              ( 7)  generic-devops-specialist, kubernetes-engineer, observability-engineer, pipeline-engineer, reliability-engineer, sre-engineer, terraform-engineer
├── documentation/       ( 2)  devrel-engineer, tech-writer
├── finance/             ( 5)  compliance-officer, financial-analyst, fintech-analyst, pricing-strategist, revenue-operations
├── frontend/            ( 6)  accessibility-engineer, css-architect, generic-frontend-specialist, perf-specialist, react-specialist, vue-specialist
├── game-dev/            ( 3)  game-designer, game-programmer, level-designer
├── gis/                 ( 2)  cartographer, spatial-analyst
├── git/                 ( 1)  git-specialist
├── healthcare/          ( 3)  biotech-researcher, clinical-data-analyst, health-informaticist
├── legacy/              ( 1)  modernizer
├── marketing/           ( 7)  affiliate-marketer, brand-strategist, content-strategist, email-marketing, growth-hacker, seo-specialist, social-media-manager
├── messaging/           ( 1)  event-architect
├── meta/                ( 4)  agent-generator, auto-persona-generator, gap-tracker, skill-maintainer
├── mobile/              ( 3)  mobile-android, mobile-flutter, mobile-ios
├── monorepo/            ( 1)  monorepo-architect
├── paid-media/          ( 2)  ads-optimizer, programmatic-buyer
├── performance/         ( 1)  performance-engineer
├── project-management/  ( 3)  product-owner, release-manager, scrum-master
├── real-time/           ( 1)  realtime-engineer
├── sales/               ( 3)  account-manager, outbound-strategist, sales-engineer
├── search/              ( 1)  search-engineer
├── security/            ( 4)  compliance-engineer, incident-responder, security-auditor, threat-modeler
├── spatial-computing/   ( 2)  spatial-ui-designer, xr-developer
├── specialized/         ( 6)  blockchain-engineer, edtech-designer, iot-engineer, legal-tech, quantum-computing, supply-chain
├── support/             ( 3)  customer-success, support-ops, technical-support-engineer
├── testing/             ( 6)  generic-testing-specialist, performance-tester, qa-engineer, quality-engineer, test-architect, test-automator
└── root-level           ( 7)  browser-agent, cli-help, codebase-investigator, generalist, orchestrator, skill-creator, universal-technology-specialist
```
<!-- ud:end agent-tree -->

### 17 Meta-Cognitive Sub-Skills

Each teaches HOW to think about a domain — technology-agnostic:

<!-- ud:begin skills-table -->
| Skill | Purpose |
|-------|---------|
| `self-evolve` | Auto-generates new skills from experience |
| `research` | Learn anything |
| `coding` | Build anything |
| `testing` | Verify anything |
| `review` | Evaluate anything |
| `architecture` | Design anything |
| `security` | Protect anything |
| `devops` | Deliver anything |
| `debugging` | Fix anything |
| `documentation` | Communicate anything |
| `performance` | Optimize anything |
| `monitoring` | Observe anything |
| `data` | Work with any data |
| `api-design` | Connect anything |
| `migration` | Transition anything |
| `mobile` | Build for any device |
| `ai-ml` | Build intelligent systems |
<!-- ud:end skills-table -->

### Self-Evolution

When the system encounters a task with no matching sub-skill:

1. Researches how to do it
2. Executes the task
3. Extracts patterns
4. Auto-generates a new sub-skill
5. Persists in `skills/_learned/` for future use

---

## 💡 Examples

### Simple Task (Tier: SMALL)

```
User: "Fix the login bug"
→ Pattern A: Skills (debugging)
→ Load skills/debugging/SKILL.md
→ Spawn codebase-investigator
→ Fix the bug
→ Verify
```

### Multi-Domain Task (Tier: LARGE)

```
User: "Build a React feature with API and tests"
→ Pattern B: Subagents (multi-domain)
→ Spawn react-specialist (frontend)
→ Spawn api-designer (backend)
→ Spawn test-architect (testing)
→ Parallel execution
→ Synthesize results
```

### Sequential Pipeline (Tier: LARGE)

```
User: "Deploy to production"
→ Pattern C: Handoffs (sequential)
→ Plan (system-architect) → handoff state
→ Implement (auto) → handoff state
→ Test (test-architect) → handoff state
→ Review (code-reviewer) → handoff state
→ Deploy (pipeline-engineer)
```

### Unknown Technology (Tier: SMALL)

```
User: "Use Bun for the backend"
→ No dedicated Bun specialist exists
→ Spawn generic-backend-specialist
→ Web research: Bun documentation
→ Apply universal backend patterns
→ Complete the task
→ Auto-generate bun-specialist for future use
```

---

## 🔧 Supported Tools

Install **once** (global or project scope) — tools auto-discover the skill from `.agents/skills/`. Tool-specific conventions are mapped by adapters:

| Tool | Adapter |
|------|---------|
| Claude Code | [`adapters/claude-code.md`](adapters/claude-code.md) |
| Codex CLI | [`adapters/codex.md`](adapters/codex.md) |
| Cursor | [`adapters/cursor.md`](adapters/cursor.md) |
| OpenCode | [`adapters/generic-cli.md`](adapters/generic-cli.md) |
| Windsurf, Cline, GitHub Copilot, Aider | [`adapters/generic-cli.md`](adapters/generic-cli.md) |
| Any other agentic CLI | [`adapters/generic-cli.md`](adapters/generic-cli.md) |

The full compatibility list lives in [`skill-manifest.yaml`](skill-manifest.yaml) (`compatible_tools`).

---

## 🛠 Validation & Development

```bash
# Run all validation checks
python3 scripts/validate.py

# Auto-generate manifest from disk
python3 scripts/generate-manifest.py

# Re-sync README numbers (version, counts, agent tree) with the repo
python3 scripts/sync-docs.py

# Verify README is in sync without rewriting (pre-commit/CI)
python3 scripts/sync-docs.py --check

# Install pre-commit hook (from repo root)
cp ultimate-dev/scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

> [!NOTE]
> `validate.py` and `generate-manifest.py` need PyYAML. One-time setup:
> ```bash
> python3 -m pip install pyyaml
> ```

---

## 📂 Structure

```
ultimate-dev/
├── SKILL.md                    ← Orchestrator (331 lines)
├── skill-manifest.yaml         ← Auto-generated registry
├── README.md                   ← User documentation (this file)
├── VERSION                     ← Version number (source of truth)
├── AGENT.md / CLAUDE.md        ← Agent entry-point docs for other harnesses
├── adapters/                   ← Harness adapters (claude-code, codex, cursor, generic-cli)
├── agents/                     ← 118 specialized agents
├── skills/                     ← 17 meta-cognitive sub-skills
├── modules/                    ← 46 internal pattern modules
├── config/                     ← Configuration files
├── prompts/                    ← Shared prompt components
├── workflows/                  ← Execution pipelines (with agent refs)
├── schemas/                    ← Data contracts
├── rules/                      ← Operational constraints
├── router/                     ← Classification & routing logic
├── templates/                  ← Reusable templates
├── scripts/                    ← validate.py, generate-manifest.py, sync-docs.py, pre-commit
├── tools/                      ← Tool integrations
├── tests/                      ← Validation tests
├── examples/                   ← Usage examples
├── evals/                      ← Evaluation cases
├── reference/                  ← Reference documentation
├── memory/                     ← Memory templates (runtime .memory/ lives at project root)
└── changelog/                  ← Version history
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [README.md](../README.md) | GitHub landing — overview & quick start |
| [ultimate-dev/README.md](README.md) | Full skill reference — counts auto-synced on release |
| [ultimate-dev/SKILL.md](SKILL.md) | Skill entry point (orchestrator) |
| [ARCHITECTURE.md](../ARCHITECTURE.md) | System design for maintainers |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | How to contribute |
| [Changelog](changelog/CHANGELOG.md) | Release notes (source for GitHub Releases) |
| [LICENSE](../LICENSE) | MIT license |

---

## 📄 License

MIT — see [LICENSE](../LICENSE).

---

**One skill. Every domain. Any model.** 🚀

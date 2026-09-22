<div align="center">

# ultimate-dev

**The master software-engineering skill for AI coding assistants.**
**One skill that adapts to any model size and covers every domain.**

[![Release](https://img.shields.io/github/v/release/usama-bin-sadiq/ultimate-dev-ai-skill?sort=semver)](https://github.com/usama-bin-sadiq/ultimate-dev-ai-skill/releases)
[![Sync & Release](https://github.com/usama-bin-sadiq/ultimate-dev-ai-skill/actions/workflows/release.yml/badge.svg)](https://github.com/usama-bin-sadiq/ultimate-dev-ai-skill/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)
![Models](https://img.shields.io/badge/models-adaptive-orange)
![Tools](https://img.shields.io/badge/tools-any-blue)

[What Is This?](#-what-is-this) ·
[Quick Start](#-quick-start) ·
[How It Works](#-how-it-works) ·
[What's Inside](#-whats-inside) ·
[Supported Tools](#-supported-tools) ·
[Examples](#-examples) ·
[Documentation](#-documentation)

</div>

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

Every install creates a memory folder at the project root — `<project>/.memory/ultimate-dev/` (or `~/.memory/ultimate-dev/` for global installs) — seeded with a template, and project-scoped installs add `.memory/ultimate-dev/` to `.gitignore`.

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
| **TINY** | ≤8K | 0 | 0 | 500 |
| **SMALL** | ≤32K | 1 | 1 | 2,000 |
| **LARGE** | ≤128K | 3 | 3 | unlimited |
| **HUGE** | >128K | all | unlimited | unlimited |

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

Live counts (agents, categories, sub-skills, modules) are **auto-synced** into the [skill README](ultimate-dev/README.md) on every release — they never go stale.

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

## 🔧 Supported Tools

Install **once** (global or project scope) — tools auto-discover the skill from `.agents/skills/`. Tool-specific conventions are mapped by adapters:

| Tool | Adapter |
|------|---------|
| Claude Code | [`adapters/claude-code.md`](ultimate-dev/adapters/claude-code.md) |
| Codex CLI | [`adapters/codex.md`](ultimate-dev/adapters/codex.md) |
| Cursor | [`adapters/cursor.md`](ultimate-dev/adapters/cursor.md) |
| OpenCode | [`adapters/generic-cli.md`](ultimate-dev/adapters/generic-cli.md) |
| Windsurf, Cline, GitHub Copilot, Aider | [`adapters/generic-cli.md`](ultimate-dev/adapters/generic-cli.md) |
| Any other agentic CLI | [`adapters/generic-cli.md`](ultimate-dev/adapters/generic-cli.md) |

The full compatibility list lives in [`ultimate-dev/skill-manifest.yaml`](ultimate-dev/skill-manifest.yaml) (`compatible_tools`).

---

## 💡 Examples

### Simple task (atomic)

```text
You: "Write a function to calculate Fibonacci numbers"
Agent: [tier: tiny | work: inline]
       function fibonacci(n) { ... }
```

### Feature task (moderate)

```text
You: "Add user authentication with JWT"
Agent: [tier: small | module: security]
       Loads security module, implements JWT auth
```

### Complex task (decomposed)

```text
You: "Build a full-stack e-commerce platform"
Agent: [tier: large | modules: backend, frontend, database | agents: 3]
       Decomposes into subtasks, spawns agents
```

---

## 📂 Project Structure

```text
ultimate-dev-ai-skill/
├── ultimate-dev/            # The skill package
│   ├── SKILL.md             # Entry point (always loaded)
│   ├── skill-manifest.yaml  # Agent/skill registry (auto-generated)
│   ├── README.md            # Full reference (auto-synced with repo facts)
│   ├── VERSION              # Release version (source of truth)
│   ├── adapters/            # claude-code, codex, cursor, generic-cli
│   ├── agents/              # Domain specialists
│   ├── skills/              # Meta-cognitive sub-skills
│   ├── modules/             # Internal pattern modules
│   └── ...                  # config, prompts, router, workflows, tests, evals…
├── scripts/                 # install.sh, install.ps1, detect-tools.sh, verify.sh
├── .github/workflows/       # Sync & Release CI (README sync + auto-release)
├── ARCHITECTURE.md          # System design
├── CONTRIBUTING.md          # How to contribute
└── README.md                # This file
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | You are here — overview & quick start |
| [ultimate-dev/README.md](ultimate-dev/README.md) | Full skill reference — counts auto-synced on release |
| [ultimate-dev/SKILL.md](ultimate-dev/SKILL.md) | Skill entry point (orchestrator) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design for maintainers |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [Changelog](ultimate-dev/changelog/CHANGELOG.md) | Release notes (source for GitHub Releases) |
| [LICENSE](LICENSE) | MIT license |

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

**One skill. Every domain. Any model.** 🚀

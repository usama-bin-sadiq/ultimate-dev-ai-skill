# ultimate-dev

**The master software-engineering skill for AI coding assistants. One skill that adapts to any model size and covers every domain.**

![Version](https://img.shields.io/badge/version-1.6.0-blue)
![Modules](https://img.shields.io/badge/modules-44-green)
![Personas](https://img.shields.io/badge/personas-33-purple)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Models](https://img.shields.io/badge/models-adaptive-orange)
![Tools](https://img.shields.io/badge/tools-10+-red)

---

## What Is This?

ultimate-dev is a **single skill** that replaces dozens of specialized skills. It works with ANY AI model (tiny to huge) and ANY technology stack (React/Vue, Kafka/RabbitMQ, PostgreSQL/MongoDB — you name it).

**No hardcoded technologies. Pure patterns and best practices.**

---

## Quick Start

### 1. Install

```bash
# macOS/Linux (interactive TUI)
./scripts/install.sh --tui

# Windows (interactive TUI)
.\scripts\install.ps1 -TUI

# Auto-detect your tools
./scripts/install.sh
```

### 2. Use

Just use your AI tool normally. The skill activates automatically:

```
You: "Add user authentication with JWT"
Agent: [tier: small | module: security]
       Implements JWT auth with proper patterns
```

### 3. Done

The agent automatically:
- Classifies your task (atomic/moderate/complex)
- Loads the right module(s)
- Applies best practices
- Follows your model's capabilities

---

## How It Adapts to Your Model

| Model Size | Context | What Happens |
|------------|---------|--------------|
| **Tiny** | ≤8K | Inline answers, no modules, single-file |
| **Small** | ≤32K | 1 module max, lite-mode router |
| **Large** | ≤128K | Full system, up to 3 parallel agents |
| **Huge** | >128K | All features, unlimited agents |

---

## What's Inside

### 44 Pattern-Based Modules

| Department | Modules |
|------------|---------|
| **Engineering** (9) | backend, frontend, architecture, database, security, devops, mobile, testing-qa, documentation |
| **Specialized** (17) | api-patterns, testing-frameworks, real-time, blockchain, ai-ml, data-engineering, cloud, messaging, caching, search, observability, i18n-l10n, performance, accessibility, open-source, legacy-modernization, monorepo |
| **Agency** (4) | project-management, product, design-handoff, client-comms |
| **Business** (5) | marketing, sales, finance, support, paid-media |
| **Research** (2) | research, academic |
| **Domain** (5) | healthcare, game-dev, gis, spatial-computing, specialized |
| **Cross-cutting** (2) | universal-principles, emerging-tech-handler |

### 33 Execution Personas

Every module has a dedicated specialist persona that can be spawned as a sub-agent.

### Works With ANY Technology

| You Use | Skill Handles It |
|---------|------------------|
| React or Vue | ✅ Frontend patterns |
| Kafka or RabbitMQ | ✅ Messaging patterns |
| PostgreSQL or MongoDB | ✅ Database patterns |
| AWS or Azure | ✅ Cloud patterns |
| Redis or Memcached | ✅ Caching patterns |
| Any other tech | ✅ Pattern-based approach |

---

## Supported Tools

| Tool | Command |
|------|---------|
| Claude Code | `./scripts/install.sh --tool claude-code` |
| Codex CLI | `./scripts/install.sh --tool codex` |
| Cursor | `./scripts/install.sh --tool cursor` |
| Windsurf | `./scripts/install.sh --tool windsurf` |
| Cline | `./scripts/install.sh --tool cline` |
| GitHub Copilot | `./scripts/install.sh --tool copilot` |
| Aider | `./scripts/install.sh --tool aider` |
| OpenCode | `./scripts/install.sh --tool opencode` |
| Any CLI tool | `./scripts/install.sh --tool generic` |

---

## Examples

### Simple Task (Atomic)
```
You: "Write a function to calculate Fibonacci numbers"
Agent: [tier: tiny | work: inline]
       function fibonacci(n) { ... }
```

### Feature Task (Moderate)
```
You: "Add user authentication with JWT"
Agent: [tier: small | module: security]
       Loads security module, implements JWT auth
```

### Complex Task (Decomposed)
```
You: "Build a full-stack e-commerce platform"
Agent: [tier: large | modules: backend, frontend, database | agents: 3]
       Decomposes into subtasks, spawns agents
```

---

## Project Structure

```
ultimate-dev/
├── SKILL.md              # Entry point (always loaded)
├── skill-manifest.yaml   # Module/persona registry
├── router/               # Classification & routing
├── modules/              # 44 domain modules
├── personas/             # 33 specialist personas
├── scripts/              # Installers & verification
├── adapters/             # Tool-specific configs
├── evals/                # Test cases
├── templates/            # Reusable templates
└── README.md
```

---

## Documentation

| File | Purpose |
|------|---------|
| [README.md](README.md) | This file — usage guide |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [SKILL.md](SKILL.md) | Core skill entry point |

---

## Credits & Attribution

This skill was **built directly from** the PRD defined in **[ultimate-developer](https://github.com/usama-bin-sadiq/ultimate-developer)** — the agent-based implementation (65 agents) that shares the same architecture.

| Source | What It Contributed |
|--------|---------------------|
| **[ultimate-developer PRD](https://github.com/usama-bin-sadiq/ultimate-developer)** | Core architecture: 3-tier system, token budgets, routing rules, adapter pattern, gap promotion |
| **[ultimate-developer agents](https://github.com/usama-bin-sadiq/ultimate-developer/tree/main/agents)** | Agent patterns, agency/orchestrator design, domain coverage reference |
| **[msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents)** | Content source for Tier 2 personas (engineering, design, marketing, sales personas) — referenced in PRD as useful content reference |
| **[OpenAI Codex](https://github.com/openai/codex)** | Agent instruction format (`AGENTS.md`) and skill loading pattern |
| **[Claude Code](https://github.com/anthropics/claude-code)** | Project instruction patterns (`.claude/CLAUDE.md`) |
| **[Cursor](https://github.com/getcursor/cursor)** | Project rules format (`.cursorrules`) |
| **[Aider](https://github.com/Aider-AI/aider)** | Instruction file conventions |
| **[Conventional Commits](https://www.conventionalcommits.org/)** | Commit message specification |
| **[Semantic Versioning](https://semver.org/)** | Versioning scheme |
| **[OWASP](https://owasp.org/)** | Security best practices |
| **[WCAG](https://www.w3.org/WAI/standards-guidelines/wcag/)** | Accessibility guidelines |
| **[12 Factor App](https://12factor.net/)** | Cloud-native architecture patterns |
| **[Martin Fowler's Patterns](https://martinfowler.com/)** | Enterprise architecture patterns |

---

## License

MIT

---

**One skill. Every domain. Any model.** 🚀

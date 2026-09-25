# User Guide

## What is Ultimate-Dev?

Ultimate-Dev is a **single adaptive skill** that replaces 100+ specialized skills. It works with ANY AI model (tiny to huge) and ANY technology stack.

## Quick Start

### Installation
```bash
# Project-specific (recommended)
./scripts/install.sh --project . --yes

# Global (all projects)
./scripts/install.sh --global
```

Prompt-only installation has no Python, Node.js, or provider dependency. For
measured size, development dependencies, and verification commands, see the
[installation guide](../../ultimate-dev/INSTALLATION.md).

### Usage
Just describe your task naturally:
```
@ultimate-dev "Build a React login form with tests"
@ultimate-dev "Add JWT authentication to Node.js API"
@ultimate-dev "Deploy to Kubernetes with zero-downtime"
@ultimate-dev "Audit codebase for OWASP Top 10 vulnerabilities"
@ultimate-dev "Research best database for time-series analytics"
```

The skill automatically:
1. **Classifies** your task (size, domains, risk)
2. **Selects the right pattern** (Skills/Subagents/Handoffs/Router)
3. **Routes to the right specialists**
4. **Executes with verification**
5. **Persists state** for context-loss recovery when durable runtime is available

## Common Tasks

### Feature Development
```
@ultimate-dev "Add user authentication with JWT to the Node.js API"
@ultimate-dev "Build a React dashboard with charts and filters"
@ultimate-dev "Create GraphQL schema for e-commerce products"
```

### Refactoring
```
@ultimate-dev "Refactor payment service to use hexagonal architecture"
@ultimate-dev "Migrate from REST to GraphQL"
@ultimate-dev "Split monolith into microservices"
```

### Infrastructure & DevOps
```
@ultimate-dev "Set up GitHub Actions CI/CD for monorepo"
@ultimate-dev "Deploy to Kubernetes with zero-downtime"
@ultimate-dev "Set up monitoring with Prometheus/Grafana"
```

### Security & Quality
```
@ultimate-dev "Audit codebase for OWASP Top 10 vulnerabilities"
@ultimate-dev "Add security headers and CSP"
@ultimate-dev "Set up dependency scanning"
```

### Research & Decisions
```
@ultimate-dev "Compare Redis vs PostgreSQL for session storage"
@ultimate-dev "Best database for time-series analytics"
@ultimate-dev "Evaluate message queues: Kafka vs RabbitMQ"
```

### Debugging
```
@ultimate-dev "Fix memory leak in WebSocket handler"
@ultimate-dev "Debug slow GraphQL resolver"
@ultimate-dev "Fix flaky integration tests"
```

## How It Works

### Task Classification
The skill automatically determines:
- **Size**: atomic / moderate / complex
- **Domains**: frontend, backend, database, devops, security, etc.
- **Risk**: none / data / security / compliance
- **Pattern**: A (Skills) / B (Subagents) / C (Handoffs) / D (Router) / Compose

### Pattern Selection
| Pattern | Use Case |
|---------|----------|
| **A: Skills** | Single domain, inline (e.g., "Explain this function") |
| **B: Subagents** | Parallel independent domains (e.g., "Full-stack dashboard") |
| **C: Handoffs** | Sequential stages (e.g., "Plan → implement → verify") |
| **D: Router** | Classify + dispatch (e.g., "Best DB for analytics") |
| **Compose** | Multiple patterns (e.g., "Security audit + fixes") |

### Specialist Routing
The skill routes to the most specific matching specialist:
```
EXACT MATCH (technology-specific)
    ↓
TECHNOLOGY MATCH (domain for stack)
    ↓
DOMAIN SPECIALIST (general domain)
    ↓
UNIVERSAL SPECIALIST (learns any tech from web)
```

### Verification
Every task requires evidence:
- Tests executed and passing
- Lint/build clean
- Files created/verified
- Security scan clean
- Explicit confirmation where needed

## Context & Memory

### Durable State
All work persists to `.memory/ultimate-dev/tasks/<task-id>/`:
- Survives context resets
- Resumes from exactly where you left off
- No work lost between sessions

### Project Memory
Project-level knowledge at `<project>/.memory/ultimate-dev/`:
- Architecture decisions
- Coding conventions
- Known issues
- User preferences

## Tips & Best Practices

### Be Specific
```
❌ "Fix the bug"
✅ "Fix the memory leak in the WebSocket connection handler in services/ws.py"
```

### Use Release Labels
For merges to main, add release labels:
- `release:patch` - Bug fixes, docs, internal improvements
- `release:minor` - New features, backward-compatible
- `release:major` - Breaking changes, architecture changes

### Trust the Skill
- Don't micromanage pattern selection
- Don't ask "which agent?" - the router handles it
- Focus on **what** you want, not **how** to do it

## Troubleshooting

### Skill Not Activating
```bash
# Check installation
ls -la ~/.agents/skills/ultimate-dev/  # Global
ls -la .agents/skills/ultimate-dev/    # Project

# Reinstall
./scripts/install.sh --project . --yes
```

### Tests Failing
```bash
cd ultimate-dev
python scripts/validate.py
python -m pytest tests/ -v
```

### State Issues
```bash
# View task state
cat .memory/ultimate-dev/tasks/<task-id>/state.json

# Resume task
# Just describe the task again - skill resumes from state.json
```

### Reset Everything
```bash
rm -rf .memory/ultimate-dev
./scripts/install.sh --project . --yes
```

## Configuration

### Environment Variables
```bash
export OPENAI_API_KEY=sk-...      # OpenAI models
export ANTHROPIC_API_KEY=sk-...   # Anthropic models
# Ollama runs locally on http://localhost:11434
```

### Model Selection (Automatic)
The skill auto-selects based on capabilities:
- **TINY** (≤8K context) → Pattern A only
- **SMALL** (≤32K) → Pattern A + 1 module
- **LARGE** (≤128K) → Up to 3 parallel
- **HUGE** (>128K) → Full system

## Supported Tools

| Tool | Adapter |
|------|---------|
| Claude Code | `.claude/skills/ultimate-dev/SKILL.md` |
| Codex CLI | `.codex/skills/ultimate-dev/SKILL.md` or `AGENTS.md` reference |
| Cursor | `.cursor/rules/ultimate-dev.mdc` |
| OpenCode | `.agents/skills/ultimate-dev/` |
| Windsurf | `.agents/skills/ultimate-dev/` generic fallback |
| Cline | `.agents/skills/ultimate-dev/` generic fallback |
| GitHub Copilot | `.agents/skills/ultimate-dev/` generic fallback |
| Aider | `.agents/skills/ultimate-dev/` generic fallback |

## Getting Help

- Check [Architecture Guide](../architecture/ARCHITECTURE.md) for deep dive
- Check [Developer Guide](../developer/DEVELOPER_GUIDE.md) for extending
- Run `@ultimate-dev --help` for flags
- Run `@ultimate-dev --detect` for stack detection only
- Run `@ultimate-dev --dry-run` to see execution plan

---

*See also: [Architecture Guide](../architecture/ARCHITECTURE.md) | [Developer Guide](../developer/DEVELOPER_GUIDE.md)*
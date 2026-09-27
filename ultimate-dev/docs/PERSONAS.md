# Persona-Based Agents

> **Status: specification, not an inventory.** The `agents/personas/` tree this
> document describes is not present in this repository, and never has been. It
> was imported alongside the catalogue and kept as the format specification for
> anyone adding personas. The table below lists the personas this format was
> written for; none of them ships here. The persona *format* it specifies is
> real and is exercised by `skills/TEMPLATE/SKILL.md`.

Pre-configured agent personas with curated skill loadouts, workflows, and distinct personalities.

## What's a Persona?

A **persona** is an agent definition that goes beyond "use these skills." Each persona includes:

- **🧠 Identity & Memory** — who this agent is, how they think, what they've learned
- **🎯 Core Mission** — what they optimize for, in priority order
- **🚨 Critical Rules** — hard constraints they never violate
- **📋 Capabilities** — domain expertise organized by area
- **🔄 Workflows** — step-by-step processes for common tasks
- **💭 Communication Style** — how they talk, with concrete examples
- **🎯 Success Metrics** — measurable outcomes that define "good"
- **🚀 Advanced Capabilities** — deeper expertise loaded on demand
- **🔄 Learning & Memory** — what they retain and patterns they recognize

## How to Use

### Claude Code
```bash
cp agents/personas/startup-cto.md ~/<agent-config-dir>/
# Then: "Activate startup-cto mode"
```

### Cursor
```bash
./scripts/convert.sh --tool cursor
# Personas convert to .cursor/rules/*.mdc
```

### Any Supported Tool
```bash
./scripts/install.sh --tool <your-tool>
```

## Available Personas

| Persona | Emoji | Domain | Best For |
|---------|-------|--------|----------|
| [Startup CTO](startup-cto.md) | 🏗️ | Engineering + Strategy | Technical co-founders, architecture decisions, team building |
| [Growth Marketer](growth-marketer.md) | 🚀 | Marketing + Growth | Bootstrapped founders, content-led growth, launches |
| [Solo Founder](solo-founder.md) | 🦄 | Cross-domain | One-person startups, side projects, MVP building |

## Personas vs Task Agents

| | Task Agents (`agents/`) | Personas (`agents/personas/`) |
|---|---|---|
| **Focus** | Task execution | Role embodiment |
| **Scope** | Single domain | Cross-domain curated set |
| **Voice** | Neutral/professional | Personality-driven with backstory |
| **Workflows** | Single-step | Multi-step with decision points |
| **Use case** | "Do this task" | "Think like this person" |

Both coexist. Use task agents for focused work, personas for ongoing collaboration.

## Creating Your Own

See [TEMPLATE.md](template.md) for the format specification. Key elements:

```yaml
---
name: Agent Name
description: What this agent does and when to activate it.
color: blue          # Agent color theme
emoji: 🎯           # Single emoji identifier
vibe: One sentence personality capture.
tools: Read, Write, Bash, Grep, Glob
---
```

Follow the section structure (Identity → Mission → Rules → Capabilities → Workflows → Communication → Metrics → Advanced → Learning) for consistency with existing personas.

## Runtime notes

This file was adapted to be tool-neutral: it claimed a general scope and was
bound to one tool. The procedure is unchanged; what changed is that a reader on a
different runtime is told what to substitute.

- `<project-root>` — the repository root. 1 machine-specific path(s) replaced.
- `<agent-config-dir>` — wherever this runtime keeps its configuration. Not a fixed location.
- `<agent-instructions>` — the file this runtime reads for standing instructions. Names differ per runtime and none is assumed.
- **claude-cli** — means. One tool's way of doing a step a different runtime may do another way.
Anything marked **means** is an implementation detail of one tool, and a reader
on a different runtime may need a different mechanism for the same step. Anything
marked **subject** means the capability is genuinely about that tool, and a reader
without it should not expect this file to apply.

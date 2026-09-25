---
tool: codex
support: native-profile
doc_source: https://github.com/openai/codex
last_verified: 2026-09-21
---

# Codex CLI Adapter

Maps the canonical ultimate-dev package onto Codex CLI's conventions.

## Package Placement

| Scope | Path |
|-------|------|
| User (global) | `~/.codex/skills/ultimate-dev/` |
| Project | `<project>/.codex/skills/ultimate-dev/` (copy-only profile) or `AGENTS.md` reference |

## Sub-Agent Spawning

Codex CLI does not natively spawn sub-agents. Map to Owner Decision table:
- **Mode-switch**: Read the domain module and apply it in the current session.
- **Simulated sequentially**: If isolation is needed, trim context to subtask scope before switching modes.

## Instruction Hierarchy

- **AGENTS.md**: Project-level instructions that can reference the skill.
- **System prompt**: SKILL.md content loaded via AGENTS.md reference.
- **Tier 0 is always resident**: SKILL.md is small enough to survive context pressure.

## File Placement

```
~/.codex/skills/ultimate-dev/
├── SKILL.md
├── router/
├── modules/
├── personas/
├── README.md
├── VERSION
└── CHANGELOG.md
```

## Activation

Reference the skill in AGENTS.md:
```markdown
# Project Instructions

Follow the ultimate-dev skill at ~/.codex/skills/ultimate-dev/SKILL.md
for all engineering tasks.
```

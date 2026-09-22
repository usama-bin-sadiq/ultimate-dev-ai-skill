---
tool: generic-cli
doc_source: https://opencode.ai
last_verified: 2026-09-21
---

# Generic CLI Adapter

Maps the canonical ultimate-dev package onto any agentic CLI tool that doesn't have a specific adapter.

## Package Placement

| Scope | Path |
|-------|------|
| User (global) | `~/.agents/skills/ultimate-dev/` |
| Project | `<repo>/.agent/skills/ultimate-dev/` |

## Sub-Agent Spawning

Generic CLIs typically don't support native sub-agent spawning. Map to Owner Decision table:
- **Mode-switch**: Read the domain module and apply it in the current session.
- **Simulated sequentially**: If isolation is needed, trim context to subtask scope before switching modes.

## Instruction Hierarchy

- **Instruction file**: A single instruction file (e.g., `.agent/instructions.md`) references the skill.
- **Project instructions**: `.agent/instructions.md` can include project-specific rules.
- **Tier 0 is always resident**: SKILL.md is the entry point.

## File Placement

```
~/.agents/skills/ultimate-dev/
├── SKILL.md
├── router/
├── modules/
├── personas/
├── README.md
├── VERSION
└── CHANGELOG.md
```

## Activation

Create `.agent/instructions.md` in your project:
```markdown
# Instructions

Follow the ultimate-dev skill at ~/.agents/skills/ultimate-dev/SKILL.md
for all engineering tasks.
```

## Graceful Degradation

If the host tool lacks features:
- No sub-agent spawning -> mode-switch in same context
- No web search -> use only repository code and docs, note limitation
- No file write -> present code changes as diffs for user to apply
- No bash execution -> describe commands for user to run manually

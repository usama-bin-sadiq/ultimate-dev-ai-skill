---
tool: claude-code
doc_source: https://docs.anthropic.com/en/docs/claude-code
last_verified: 2026-09-21
---

# Claude Code Adapter

Maps the canonical ultimate-dev package onto Claude Code's conventions.

## Package Placement

| Scope | Path |
|-------|------|
| User (global) | `~/.claude/skills/ultimate-dev/` |
| Project | `<repo>/.claude/skills/ultimate-dev/` |

## Sub-Agent Spawning

Claude Code supports the Task tool for spawning sub-agents. Map to Owner Decision table:
- **Mode-switch**: Read the domain module and apply it in the current session.
- **Real sub-agent**: Use the Task tool with the invocation template (router/invocation-template.md).

## Instruction Hierarchy

- **System instructions**: SKILL.md rules are enforced via the skill's description field and always-loaded content.
- **Project instructions**: `<repo>/.claude/CLAUDE.md` can reference project-specific conventions.
- **Tier 0 is always resident**: SKILL.md is small enough (~500 tokens) to survive context pressure.

## File Placement

```
~/.claude/skills/ultimate-dev/
├── SKILL.md                     # Entry point
├── router/                      # Classification and routing rules
├── modules/                     # Domain modules
├── personas/                    # Tier 2 specialists
├── README.md
├── VERSION
└── CHANGELOG.md
```

## Activation

Claude Code auto-discovers skills in `~/.claude/skills/`. The skill activates when the task matches its description trigger.

---
tool: aider
support: generic-fallback
last_verified: 2026-09-25
---

# Aider Adapter

Aider is supported through the generic skill layout and project convention
files. The copy-only installer does not create or modify Aider configuration.

## Package Placement

| Scope | Path |
|-------|------|
| User/global | `~/.agents/skills/ultimate-dev/` (generic fallback) |
| Project | `<project>/.agents/skills/ultimate-dev/` (generic fallback) |

## Host Integration

Reference the copied `SKILL.md` from the project's Aider instructions or
conventions file. The installer does not create symlinks or memory files.

## Capability Boundary

Aider supplies the model and tools. Ultimate-Dev supplies the control plane,
policy decisions, verification, and durable task state.

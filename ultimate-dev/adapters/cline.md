---
tool: cline
support: generic-fallback
last_verified: 2026-09-25
---

# Cline Adapter

Cline is supported through the generic agentic-skill layout and host rules.
Until a native skill directory is verified, the copy-only installer does not
invent one.

## Package Placement

| Scope | Path |
|-------|------|
| User/global | `~/.agents/skills/ultimate-dev/` (generic fallback) |
| Project | `<project>/.agents/skills/ultimate-dev/` (generic fallback) |

## Host Integration

Reference the copied `SKILL.md` from the project's Cline instruction surface.
The installer does not create `.clinerules`, symlinks, or memory files.

## Capability Boundary

Cline supplies tools and model access. Ultimate-Dev supplies routing, policy,
verification, and durable task control.

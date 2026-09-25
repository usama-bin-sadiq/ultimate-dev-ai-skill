---
tool: copilot
support: generic-fallback
last_verified: 2026-09-25
---

# GitHub Copilot Adapter

GitHub Copilot is supported through the generic skill layout and repository
instruction surfaces. The installer does not assume that a Copilot-specific
skill directory exists.

## Package Placement

| Scope | Path |
|-------|------|
| User/global | `~/.agents/skills/ultimate-dev/` (generic fallback) |
| Project | `<project>/.agents/skills/ultimate-dev/` (generic fallback) |

## Host Integration

Reference the copied `SKILL.md` from the repository's Copilot instructions when
needed. The installer does not modify `.github/copilot-instructions.md` or
create symlinks.

## Capability Boundary

Copilot supplies the model and host tools. Ultimate-Dev supplies deterministic
routing, JEV decisions, verification, and recovery.

---
tool: windsurf
support: generic-fallback
last_verified: 2026-09-25
---

# Windsurf Adapter

Windsurf projects commonly use project instruction files rather than a
standard skill directory. The copy-only installer therefore uses the generic
profile unless a future native Windsurf skill contract is verified.

## Package Placement

| Scope | Path |
|-------|------|
| User/global | `~/.agents/skills/ultimate-dev/` (generic fallback) |
| Project | `<project>/.agents/skills/ultimate-dev/` (generic fallback) |

## Host Integration

Use the project's Windsurf instructions or rules file to reference the copied
`SKILL.md`. The installer deliberately does not create or overwrite host
instruction files.

## Capability Boundary

Windsurf supplies the model and tools. Ultimate-Dev supplies the control-plane
contract and never installs a provider or silently assumes a tool exists.

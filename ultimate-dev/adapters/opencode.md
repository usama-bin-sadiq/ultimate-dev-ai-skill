---
tool: opencode
support: native-profile
last_verified: 2026-09-25
---

# OpenCode Adapter

OpenCode uses the generic agentic-skill layout used by Ultimate-Dev.

## Package Placement

| Scope | Path |
|-------|------|
| User/global | `~/.agents/skills/ultimate-dev/` |
| Project | `<project>/.agents/skills/ultimate-dev/` |

## Installer Profile

```bash
./scripts/install.sh --tool opencode --global --yes
./scripts/install.sh --tool opencode --project . --yes
```

The installer copies the inner skill folder only. It does not create a symlink
or modify project memory, `.gitignore`, or host instruction files.

## Capability Boundary

OpenCode supplies the model, filesystem, shell, browser, and MCP capabilities.
Ultimate-Dev supplies routing, JEV decisions, durable task state, verification,
and recovery. Missing host capabilities remain unavailable rather than being
silently installed.

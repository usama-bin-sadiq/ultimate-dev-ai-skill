---
tool: cursor
doc_source: https://docs.cursor.com
last_verified: 2026-09-21
---

# Cursor Adapter

Maps the canonical ultimate-dev package onto Cursor's conventions.

## Package Placement

| Scope | Path |
|-------|------|
| User (global) | n/a (Cursor is project-scoped) |
| Project | `<repo>/.cursor/rules/ultimate-dev.mdc` |

## Sub-Agent Spawning

Cursor does not natively spawn sub-agents. Map to Owner Decision table:
- **Mode-switch**: Read the domain module and apply it in the current session.
- **Simulated sequentially**: If isolation is needed, trim context to subtask scope before switching modes.

## Instruction Hierarchy

- **Cursor Rules**: `.cursor/rules/ultimate-dev.mdc` generated from SKILL.md.
- **Project instructions**: `.cursorrules` can reference project-specific conventions.
- **Tier 0 is always resident**: SKILL.md content is embedded in the rules file.

## File Placement

```
<repo>/.cursor/rules/
└── ultimate-dev.mdc    # Generated from SKILL.md + all modules
```

## Generation

To generate the Cursor rules file:
```bash
cat SKILL.md router/*.md modules/**/*.md > .cursor/rules/ultimate-dev.mdc
```

Note: Cursor has a context limit. If the file is too large, split into:
- `ultimate-dev-core.mdc` — Tier 0 (SKILL.md + router files)
- `ultimate-dev-modules.mdc` — Tier 1 modules (loaded on demand)

## Activation

Cursor auto-discovers `.cursor/rules/` files. The rules activate when the task matches the description.

# Memory Directory

Skill-internal memory shipped with the skill: templates and caches.

> **Runtime project memory lives at the project root**, not here:
> `<project-root>/.memory/ultimate-dev/` is created and managed by the
> runtime when needed. The installer copies this skill payload only and does
> not create or delete project memory. This directory ships the
> `project-memory.md` template used by the runtime.

## Contents

### `project-memory.md`
Project-specific knowledge that persists across sessions:
- Architecture decisions and their rationale
- Coding conventions and patterns
- Known issues and workarounds
- User preferences and feedback

### Learning Files
- `learned-patterns.md` — Patterns that worked well in this project
- `known-issues.md` — Recurring issues and their solutions
- `user-preferences.md` — User's coding style and preferences

## How Memory Works

1. **During execution** — Agents can write to memory files
2. **Between sessions** — Memory persists and is loaded in new sessions
3. **Periodic cleanup** — Outdated or incorrect memory is removed
4. **User control** — Users can edit or delete memory files

## Memory Rules

- **Be accurate** — Only store verified information
- **Be specific** — Include context, not just facts
- **Be current** — Remove outdated information
- **Be useful** — Store information that helps future tasks
- **Be concise** — Keep entries brief and scannable

## Privacy

Memory files may contain:
- Project-specific patterns and conventions
- User preferences (coding style, tool preferences)
- Architecture decisions for the current project

Memory files should NOT contain:
- Secrets or credentials
- Personal information
- Sensitive business data

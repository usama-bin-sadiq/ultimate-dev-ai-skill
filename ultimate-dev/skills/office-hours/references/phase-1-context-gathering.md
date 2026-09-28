<!-- Moved verbatim from office-hours/SKILL.md, the
     'phase-1-context-gathering' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 1: Context Gathering

Understand the project and the area the user wants to change.

```bash
eval "$(~/.claude/skills/gstack/bin/gstack-slug 2>/dev/null)"
```

1. Read `CLAUDE.md`, `TODOS.md` (if they exist).
2. Run `git log --oneline -30` and `git diff origin/main --stat 2>/dev/null` to understand recent context.
3. Use Grep/Glob to map the codebase areas most relevant to the user's request.
4. **List existing design docs for this project:**
   ```bash
   setopt +o nomatch 2>/dev/null || true  # zsh compat
   ls -t ~/.gstack/projects/$SLUG/*-design-*.md 2>/dev/null
   ```
   If design docs exist, list them: "Prior designs for this project: [titles + dates]"

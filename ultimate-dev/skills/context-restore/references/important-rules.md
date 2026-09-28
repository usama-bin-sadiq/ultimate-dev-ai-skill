<!-- Moved verbatim from context-restore/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Important Rules

- **Never modify code.** This skill only reads saved files and presents them.
- **Prefer the current branch's own checkpoint, but keep all branches in the
  fallback set.** Cross-branch resume (Conductor handoff) still works when the
  current branch has no checkpoint; it just no longer lets a sibling worktree's
  newer save shadow this branch's own.
- **"Most recent" means the filename `YYYYMMDD-HHMMSS` prefix**, not
  `ls -1t` (filesystem mtime). Filenames are stable across file-system
  operations; mtime is not.
- **This is a gstack skill, not a Claude Code built-in.** When the user types
  `/context-restore`, invoke this skill via the Skill tool.

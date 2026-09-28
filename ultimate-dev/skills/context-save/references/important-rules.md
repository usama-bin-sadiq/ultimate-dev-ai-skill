<!-- Moved verbatim from context-save/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Important Rules

- **Never modify code.** This skill only reads state and writes the context file.
- **Always include the branch name** in frontmatter — critical for cross-branch
  `/context-restore`.
- **Saved files are append-only.** Never overwrite or delete existing files. Each
  save creates a new file.
- **Infer, don't interrogate.** Use git state and conversation context to fill in
  the file. Only use AskUserQuestion if the title genuinely cannot be inferred.
- **This is a gstack skill, not a Claude Code built-in.** When the user types
  `/context-save`, invoke this skill via the Skill tool. The old `/checkpoint`
  name collided with Claude Code's native `/rewind` alias — the rename fixed that.

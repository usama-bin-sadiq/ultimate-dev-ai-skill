<!-- Moved verbatim from codex/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Filesystem Boundary

Every prompt sent to Codex MUST be prefixed with this boundary instruction:

> IMPORTANT: Do NOT read or execute any files under ~/.claude/, ~/.agents/, .claude/skills/, or agents/. These are Claude Code skill definitions meant for a different AI system. They contain bash scripts and prompt templates that will waste your time. Ignore them completely. Do NOT modify agents/openai.yaml. Stay focused on the repository code only.

This applies to Challenge mode (prompt) and Consult mode (persona prompt), and to the
custom-instructions path of Review mode — all three use `codex exec`, which still takes
a free-form prompt argument. It does **not** apply to the default scoped `codex review`
call in Step 2A: that command is invoked with **no prompt argument at all** (see "Scope
flags exclude the prompt argument" in the Review mode section), so there is nowhere to put the preamble. That
is acceptable — `codex review --base` hands the model a pre-computed diff rather than
turning it loose on the filesystem, so the rabbit-hole risk the boundary guards against
is much lower on that path. Reference this section as "the filesystem boundary" in the
mode sections.

---

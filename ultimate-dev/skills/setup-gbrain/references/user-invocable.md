<!-- Moved verbatim from setup-gbrain/SKILL.md, the 'User-invocable' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# User-invocable
When the user types `/setup-gbrain`, run this skill. Three shortcut modes:

- `/setup-gbrain` — full flow (default)
- `/setup-gbrain --repo` — only flip the per-remote policy for the current repo
- `/setup-gbrain --switch` — only migrate the engine (PGLite ↔ Supabase)
- `/setup-gbrain --resume-provision <ref>` — re-enter a previously interrupted
  Supabase auto-provision at the polling step
- `/setup-gbrain --cleanup-orphans` — list + delete in-flight Supabase projects

Parse the invocation args yourself — these are prose hints to the skill, not
implemented as a dispatcher binary.

---

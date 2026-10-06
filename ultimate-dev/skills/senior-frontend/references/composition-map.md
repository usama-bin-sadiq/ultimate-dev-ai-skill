<!-- Moved verbatim from senior-frontend/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Composition map

This skill does NOT reimplement scope owned by the POWERFUL-tier specialists. It forks into them. See `./composition_map.md` for the full routing table. Key forks:

| Concern | Fork into |
|---|---|
| WCAG audit, contrast, screen-reader | `skills/a11y-audit/` |
| Bundle profiling + runtime perf | `skills/performance-profiler/` |
| Cinematic / scroll-storytelling landing | `skills/epic-design/` |
| Apple HIG (iOS / macOS / visionOS) | `skills/apple-hig-expert/` |
| Pre-commit Karpathy review | `engineering/karpathy-coder/` |
| Pre-flight architecture grill | `engineering/grill-me/` |

The `cs-frontend-engineer` agent orchestrates these forks via `context: fork`. Invoke it from another agent with `Agent({subagent_type: "cs-frontend-engineer", prompt: "..."})` or via `/cs:frontend-review <your problem>`.

---

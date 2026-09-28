<!-- Moved verbatim from senior-frontend/SKILL.md, the
     'composition-map' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Composition map

This skill does NOT reimplement scope owned by the POWERFUL-tier specialists. It forks into them. See `references/composition_map.md` for the full routing table. Key forks:

| Concern | Fork into |
|---|---|
| WCAG audit, contrast, screen-reader | `engineering-team/skills/a11y-audit/` |
| Bundle profiling + runtime perf | `engineering/skills/performance-profiler/` |
| Cinematic / scroll-storytelling landing | `engineering-team/skills/epic-design/` |
| Apple HIG (iOS / macOS / visionOS) | `product-team/skills/apple-hig-expert/` |
| Pre-commit Karpathy review | `engineering/karpathy-coder/` |
| Pre-flight architecture grill | `engineering/grill-me/` |

The `cs-frontend-engineer` agent orchestrates these forks via `context: fork`. Invoke it from another agent with `Agent({subagent_type: "cs-frontend-engineer", prompt: "..."})` or via `/cs:frontend-review <your problem>`.

---

<!-- Moved verbatim from senior-frontend/SKILL.md, the
     'invocation-from-other-agents-and-skills' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Invocation from other agents and skills

Three surfaces:

1. **Slash command:** `/cs:frontend-review <prompt>` — full grill + decision engine + composition routing.
2. **Agent subagent:** `Agent({subagent_type: "cs-frontend-engineer", prompt: "..."})` — forks context, returns ≤ 200-word digest.
3. **Direct tool call:** `python scripts/frontend_decision_engine.py ...` — deterministic profile match when inputs are known.

Each file below is loaded on demand, not at triage. 14 file(s):

- `references/accessibility-and-testing.md` — Accessibility and Testing. <!-- Moved verbatim from senior-frontend/SKILL.md, the
- `references/assumptions-and-verifiable-success-criteria-karpathy-discipline.md` — Assumptions and Verifiable Success Criteria (Karpathy discipline). <!-- Moved verbatim from senior-frontend/SKILL.md, the
- `references/bundle-analysis.md` — Bundle Analysis. <!-- Moved verbatim from senior-frontend/SKILL.md, the
- `references/component-generation.md` — Component Generation. <!-- Moved verbatim from senior-frontend/SKILL.md, the
- `references/composition-map.md` — Composition map. <!-- Moved verbatim from senior-frontend/SKILL.md, the
- `references/customization-profiles.md` — Customization profiles. <!-- Moved verbatim from senior-frontend/SKILL.md, the
- `references/forcing-question-library-matt-pocock-grill.md` — Forcing-question library (Matt Pocock grill). <!-- Moved verbatim from senior-frontend/SKILL.md, the
- `references/invocation-from-other-agents-and-skills.md` — Invocation from other agents and skills. <!-- Moved verbatim from senior-frontend/SKILL.md, the
- `references/next-js-optimization.md` — Next.js Optimization. <!-- Moved verbatim from senior-frontend/SKILL.md, the
- `references/project-scaffolding.md` — Project Scaffolding. <!-- Moved verbatim from senior-frontend/SKILL.md, the
- `references/quick-reference.md` — Quick Reference. <!-- Moved verbatim from senior-frontend/SKILL.md, the
- `references/react-patterns.md` — React Patterns. <!-- Moved verbatim from senior-frontend/SKILL.md, the
- `references/resources.md` — Resources. <!-- Moved verbatim from senior-frontend/SKILL.md, the
- `references/table-of-contents.md` — Table of Contents. <!-- Moved verbatim from senior-frontend/SKILL.md, the

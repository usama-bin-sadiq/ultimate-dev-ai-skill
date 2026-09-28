<!-- Moved verbatim from senior-frontend/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Forcing-question library (Matt Pocock grill)

Before locking any framework or rendering decision, walk the seven forcing questions in `./forcing_questions.md`. Discipline:

1. One question per turn. No bundling.
2. Always recommend the answer with cited canon.
3. Track answers in `/tmp/frontend-grill-<date>.md`.
4. If a kill criterion trips, stop. Don't scaffold around an unresolved gap.
5. After Q7, run `frontend_decision_engine.py` with the seven answers.

Summary:

1. Primary device + network?
2. LCP target in ms (and INP, CLS)?
3. RSC / SPA / SSR / SSG — pick and defend?
4. JS bundle budget per route?
5. SEO-dependent or auth-walled?
6. Design-system source of truth?
7. WCAG target + named a11y owner?

---

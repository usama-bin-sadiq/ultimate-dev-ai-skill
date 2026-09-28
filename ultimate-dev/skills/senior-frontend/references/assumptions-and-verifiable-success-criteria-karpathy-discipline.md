<!-- Moved verbatim from senior-frontend/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Assumptions and Verifiable Success Criteria (Karpathy discipline)

Before this skill scaffolds a component, recommends a framework, or audits a bundle, the following four assumptions MUST be surfaced.

1. **Primary user device + network** — mobile-4G, desktop-fiber, low-end-Android, or corporate-network. Drives every perf decision.
2. **LCP target in milliseconds** — a single number, not "fast." Drives bundle budget and rendering choice.
3. **SEO-dependent vs. auth-walled** — drives rendering (SSR/SSG/RSC vs. SPA).
4. **WCAG target + named a11y owner** — AA, AAA, or best-effort. Drives a11y investment and CI gates.

**Verifiable success criteria** (Karpathy #4) — every recommendation must include:

- Core Web Vitals targets (LCP, INP, CLS) at p75 on the primary device
- A per-route JS bundle budget in KB-gzip
- A Lighthouse a11y floor + perf floor

If any of those three is not stated, the recommendation is incomplete — return to Q2 of the forcing-question library.

The `scripts/frontend_decision_engine.py` tool encodes these checks: it refuses to recommend a profile without the four assumption inputs and prints the verifiable thresholds for the matched profile.

---

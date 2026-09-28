<!-- Moved verbatim from senior-frontend/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Customization profiles

Four built-in profiles in `profiles/` calibrate every recommendation:

| Profile | When to pick | LCP target (mobile-4G p75) | Bundle budget |
|---|---|---|---|
| `next-app-router` | SaaS customer-facing, SEO + dynamic, RSC-first | 2000ms | 150 KB-gzip / route |
| `remix-or-sveltekit` | Mobile-4G primary, low-JS-first, progressive enhancement | 1500ms | 80 KB-gzip / route |
| `vite-spa` | Auth-walled app, desktop/corporate primary | 2500ms | 200 KB init + 80 KB / route |
| `astro-or-static` | Marketing / docs / blog, near-zero write, SEO-critical | 1200ms | 30 KB JS / page |

Pick a profile via:

```bash
python scripts/frontend_decision_engine.py \
  --primary-device mobile-4g --lcp-target-ms 2000 \
  --seo-dependent true --auth-walled false --team-size 5
```

The tool returns the best-fit profile, the runner-up tradeoff (if within 15%), the stack picks, the anti-patterns to avoid on that profile, and the required CI gates.

To add a custom profile (e.g., your org's internal-tool defaults): copy `profiles/vite-spa.json` to `profiles/<your-org>.json` and adjust `constraints` + `success_thresholds`.

---

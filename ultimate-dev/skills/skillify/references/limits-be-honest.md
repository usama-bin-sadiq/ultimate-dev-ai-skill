<!-- Moved verbatim from skillify/SKILL.md, the 'Limits (be honest)' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Limits (be honest)

- **Bun runtime required.** The codified skill runs as a Bun process
  (`bun run script.ts`). Phase 1 design carry-over (Codex finding #7).
  Real fix lands in Phase 4 (self-contained binary or Node fallback).
  For now: the skill works on any machine that has gstack installed,
  which means it has Bun.
- **Fixture-replay tests are point-in-time.** When the target site
  rotates HTML, the fixture goes stale and the test passes against an
  outdated snapshot. Phase 4 will add fixture-staleness detection.
- **Synthesis is best-effort.** You're writing a script from your own
  conversation memory. If the prototype was complex (multi-page, JS
  hydration, lazy load) the codified script may need a hand-edit before
  it's reliable. The post-commit verify step catches obvious drift.
- **Single-target only.** One `$B goto` URL per skill. Multi-page
  crawls are out of scope — write a separate skill per target, or
  parameterize via `args:` if the URL pattern is regular.

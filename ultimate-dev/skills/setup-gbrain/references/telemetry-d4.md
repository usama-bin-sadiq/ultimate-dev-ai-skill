<!-- Moved verbatim from setup-gbrain/SKILL.md, the 'Telemetry (D4)' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Telemetry (D4)

The preamble's Telemetry block logs skill success/failure at exit. When
emitting the event, add these enumerated categorical values to the
telemetry payload (SAFE — no free-form secrets, never the URL or PAT):

- `scenario`: `supabase-existing` | `supabase-auto-provision` |
  `supabase-manual` | `pglite-local` | `switch-to-supabase` |
  `switch-to-pglite` | `repo-flip-only` | `cleanup-orphans` |
  `resume-provision`
- `install_performed`: `yes` | `no` (D5 reuse) | `skipped` (pre-existing)
- `mcp_registered`: `yes` | `no` | `claude-missing`
- `trust_tier_set`: `read-write` | `read-only` | `deny` |
  `skip-for-now` | `n/a` (outside git repo)

Never pass `SUPABASE_ACCESS_TOKEN`, `DB_PASS`, `GBRAIN_POOLER_URL`,
`GBRAIN_DATABASE_URL`, or any `postgresql://` substring to the telemetry
invocation. The CI grep test in `test/skill-validation.test.ts` enforces
this at build time.

---

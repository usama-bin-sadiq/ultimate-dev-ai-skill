<!-- Moved verbatim from sync-gbrain/SKILL.md, the 'Step 5: Verdict block (idempotent doctor output)' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 5: Verdict block (idempotent doctor output)

Print a status block matching `/setup-gbrain` Step 10 conventions. Each row
is `[OK]/[FIX]/[WARN]/[ERR]`. Reuse `gbrain doctor --json --fast` for
informational rows but DO NOT gate the guidance block on doctor (per
/plan-eng-review §6 — doctor is too strict for unrelated reasons).

```
gbrain status: GREEN

  CLI ............. OK   <gbrain version>
  Engine .......... OK   <pglite|supabase>
  Capability ...... OK   source-scoped page read verified (no page/source mutation)
  CWD source ...... OK   <gstack-code-{repo_slug}> (page_count=<N>)
  Call graph ...... OK   <N> edges resolved (code-callers/callees live)
  ~/.gstack source. OK   <gstack-brain-{user}> (page_count=<N>) — managed by /setup-gbrain
  Memory sync ..... OK   <artifacts_sync_mode>
  CLAUDE.md ....... OK   ## GBrain Search Guidance present
  Last sync ....... OK   <last_sync from state file>

Run `/sync-gbrain` again any time gbrain feels off; safe and idempotent.
```

The **Call graph** row reports the most authoritative signal available:

1. **If a dream stage ran this invocation** (`--dream`, or `--full` auto-build),
   mirror its row verbatim — it's the ground truth for this run:
   - `OK   <N> edges resolved (code-callers/callees live)`
   - `WARN dream ran but this source's schema pack does not extract code symbols
     — switch to a code-aware pack (\`gbrain schema use <pack>\`)`
   - `WARN dream ran but the embed phase failed (missing embedding key)`
   - `WARN dream ran but resolved 0 edges (no code symbols matched yet)`
2. **Otherwise** fall back to the `CYCLE` value from Step 3.5, with honest wording
   (a completed cycle proves a cycle ran, NOT that edges exist):
   - `completed` → `OK   cycle complete — code-callers/callees live IF this source's pack extracts code symbols`
   - `never` → `WARN call graph not built — run /sync-gbrain --dream`
   - `unknown` → `WARN could not probe call graph (doctor unavailable) — run /sync-gbrain --dream if code-callers returns 0`

Any `WARN` Call graph row flips the verdict to YELLOW.

If any row is YELLOW or RED, the verdict line says so and the failing rows
surface a one-line next action. An unknown read gives `Capability ...... WARN
source-scoped read unverified; guidance preserved — retry /sync-gbrain` and
flips the verdict to YELLOW, not RED.
For a skipped probe, show `Capability ...... WARN  code read not probed in
this mode; guidance unchanged` and do not print a GREEN capability verdict.
A `never`/`unknown` Call graph row flips the verdict to YELLOW.

---

<!-- Moved verbatim from setup-gbrain/SKILL.md, the 'Step 10: GREEN/YELLOW/RED verdict block (idempotent doctor output)' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 10: GREEN/YELLOW/RED verdict block (idempotent doctor output)

After Steps 1-9 complete, summarize. Re-running `/setup-gbrain` on a
configured Mac is a first-class doctor path: every step detects existing
state, repairs only what's missing, and reports here.

```bash
~/.claude/skills/gstack/bin/gstack-gbrain-detect 2>/dev/null || true
~/.claude/skills/gstack/bin/gstack-config get transcript_ingest_mode 2>/dev/null || echo "off"
~/.claude/skills/gstack/bin/gstack-config get artifacts_sync_mode 2>/dev/null || echo "off"
[ -f ~/.gstack/.gbrain-sync-state.json ] && cat ~/.gstack/.gbrain-sync-state.json || echo "{}"
```

Read `gbrain_mcp_mode` from the detect output and pick the right verdict
template. Each row is `[OK]/[FIX]/[WARN]/[ERR]`.

### Path 4 (Remote MCP)

```
gbrain status: GREEN  (mode: remote-http)

  MCP ............. OK   {SERVER_NAME} v{SERVER_VERSION} at {MCP_URL}
  Auth ............ OK   bearer accepted (verified via /tools/list)
  Engine .......... N/A  remote mode
  Doctor .......... N/A  remote mode (brain admin runs `gbrain doctor`)
  Repo policy ..... OK   {read-write|read-only|deny}
  Artifacts repo .. OK   {gstack_artifacts_remote URL}
  Artifacts sync .. OK   {artifacts_sync_mode}
  Transcripts ..... OK   route to artifacts repo → remote brain (plan D11)
  Code search ..... {OK local-pglite (~/.gbrain/pglite) | N/A declined at Step 4d}
  CLAUDE.md ....... OK
  Smoke test ...... INFO printed for post-restart manual verification

Restart Claude Code to pick up the `mcp__gbrain__*` tools.
Re-run `/setup-gbrain` any time the bearer rotates or the URL moves.
```

The **Code search** row reflects the choice at Step 4d:
- If user picked A (Yes): `OK local-pglite` and `gbrain_local_status == "ok"` going forward.
- If user picked B (No): `N/A declined at Step 4d` — `gstack-config set local_code_index_offered true` to silence future migration notices.

The **Transcripts** row changed in v1.34.0.0: in remote-http mode,
gstack-memory-ingest now persists staged transcripts to
`~/.gstack/transcripts/run-<pid>-<ts>/` and gstack-brain-sync pushes them
to the artifacts repo. Brain admin's pull job indexes into the remote brain.
Local PGLite (when present) stays code-only — no transcript pollution.

### Paths 1, 2a, 2b, 3 (Local stdio)

```
gbrain status: GREEN  (mode: local-stdio)

  CLI ............. OK   <gbrain version>
  Engine .......... OK   <pglite|supabase> at <path>
  doctor .......... OK
  MCP ............. OK   registered (user scope)
  Repo policy ..... OK   <read-write|read-only|deny>
  Code import ..... OK   <last_imported_head>
  Artifacts sync .. OK   <artifacts_sync_mode> to <remote>
  Transcripts ..... OK   <N> sessions, last ingest <when>
  CLAUDE.md ....... OK
  Smoke test ...... OK   put → search → delete round-trip

Run `/setup-gbrain` again any time gbrain feels off; it's safe and idempotent.
```

If any row is YELLOW or RED, the verdict line says so and the failing rows
surface a one-line "next action" (e.g.,
`Engine .......... ERR  PGLite corrupt — run \`gbrain restore-from-sync\` (V1.5)`).
For V1, restore-from-sync is deferred to V1.5 as a P0 cross-repo work item; until it ships,
the user's brain remote (with brain-sync enabled) holds curated artifacts
as markdown + git, recoverable manually via `gbrain import` from a clone.

---

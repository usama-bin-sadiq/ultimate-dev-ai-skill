<!-- Moved verbatim from sync-gbrain/SKILL.md, the
     'user-invocable' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## User-invocable

When the user types `/sync-gbrain`, run this skill. Argument modes (parsed by
the skill itself, not a dispatcher binary):

- `/sync-gbrain` — incremental sync (default; mtime fast-path; ~50ms steady-state)
- `/sync-gbrain --full` — full code reindex via `gbrain reindex-code` (~25-35 min on a big repo). Auto-builds the call graph (`gbrain dream`) **only when it was never built**.
- `/sync-gbrain --dream` — build this source's call graph (`gbrain code-callers`/`code-callees`) via a source-scoped `gbrain dream --source <id>` cycle; ~minutes; runs lock-free after the sync stages. Always forces, even if already built. Only produces a graph on a code-aware schema pack; otherwise the run reports a WARN explaining why the graph is still empty.
- `/sync-gbrain --no-dream` — skip the dream cycle that `--full` would otherwise auto-run.
- `/sync-gbrain --code-only` — only run the code stage; skip memory + brain-sync
- `/sync-gbrain --dry-run` — preview what would sync; no writes anywhere
- `/sync-gbrain --no-memory` / `--no-brain-sync` — selectively skip stages
- `/sync-gbrain --quiet` — suppress per-stage output
- `/sync-gbrain --refresh-cache` — force-rebuild brain-aware planning cache (v1.48; replaces /brain-refresh-context per D1 fold). Skips code + memory stages; routes to `gstack-brain-cache refresh --project <slug>`.
- `/sync-gbrain --audit` — emit summary of gstack-owned pages per project + sensitive-content audit (v1.48 / D10 lifecycle). Read-only.

Pass-through args go straight to the orchestrator at
`~/.claude/skills/gstack/bin/gstack-gbrain-sync.ts`.

**`--refresh-cache` short-circuit:** when this flag is present, the skill
runs ONLY the cache refresh (`gstack-brain-cache refresh --project <slug>`
for the current worktree's slug, plus a cross-project refresh of
user-profile if `gstack/user-profile/<user-slug>` exists). Code +
memory + brain-sync stages are skipped. Useful when the user knows the
brain has new info gstack should pick up before the next planning skill.

**`--audit` short-circuit:** when this flag is present, the skill runs
`gstack-brain-cache list --project <slug> --json`, summarizes by page
type, then scans for any cached salience entries that ended up outside
the SALIENCE_DEFAULT_ALLOWLIST (T17 / D9 leak check). Read-only; no
modifications to brain or cache.

---

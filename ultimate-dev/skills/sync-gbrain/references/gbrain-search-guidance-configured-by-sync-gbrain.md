<!-- Moved verbatim from sync-gbrain/SKILL.md, the
     'gbrain-search-guidance-configured-by-sync-gbrain' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## GBrain Search Guidance (configured by /sync-gbrain)
<!-- gstack-gbrain-search-guidance:start -->

This worktree's pinned code source answered a source-scoped page read. This
does not verify semantic search or write availability. Prefer gbrain over Grep
when the question is semantic or when you don't know the exact identifier yet;
if a query fails, report that failure rather than assuming the index is healthy.

**This worktree is pinned to a worktree-scoped code source** via the
`.gbrain-source` file in the repo root (kubectl-style context).
`gbrain code-def`, `code-refs`, `code-callers`, `code-callees`, `search`, and
`query` from anywhere under this worktree route to that source by default —
no `--source` flag needed (gbrain >= 0.41.38.0; on older gbrain the call-graph
commands need `--source "$(cat .gbrain-source)"`). Conductor sibling worktrees
of the same repo each have their own pin and their own indexed pages, so
semantic results match the code on disk here.

Call-graph queries (`code-callers`/`code-callees`) also need the graph to be
built first — run `/sync-gbrain --dream` (or `--full`) if they return
`count: 0`. This only works if this source's gbrain schema pack extracts code
symbols; on a non-code-aware pack `--dream` completes but the graph stays empty
and reports a WARN. `code-def`/`code-refs` need the same extraction.

Two indexed corpora available via the `gbrain` CLI:
- This worktree's code (auto-pinned via `.gbrain-source`).
- `~/.gstack/` curated memory (registered as `gstack-brain-<user>` source via
  the existing federation pipeline).

Prefer gbrain when:
- "Where is X handled?" / semantic intent, no exact string yet:
    `gbrain search "<terms>"` or `gbrain query "<question>"`
- "Where is symbol Y defined?" / symbol-based code questions:
    `gbrain code-def <symbol>` or `gbrain code-refs <symbol>`
- "What calls Y?" / "What does Y depend on?":
    `gbrain code-callers <symbol>` / `gbrain code-callees <symbol>`
- "What did we decide last time?" / past plans, retros, learnings:
    `gbrain search "<terms>" --source gstack-brain-<user>`

Grep is still right for known exact strings, regex, multiline patterns, and
file globs. Run `/sync-gbrain` after meaningful code changes; for ongoing
auto-sync across all worktrees, run `gbrain autopilot --install` once per
machine — gbrain's daemon handles incremental refresh on a schedule.

Safety: don't run `/sync-gbrain` while `gbrain autopilot` is active — the
orchestrator refuses destructive source ops when it detects a running autopilot
to avoid racing it (#1734). Prefer registering user repos with `gbrain sources
add --path <dir>` (no `--url`): URL-managed sources can auto-reclone, and the
sync code walk for them requires an explicit `--allow-reclone` opt-in.

<!-- gstack-gbrain-search-guidance:end -->
```

Use the Read + Edit tools. The find-and-replace target is the entire region
from `<!-- gstack-gbrain-search-guidance:start -->` through
`<!-- gstack-gbrain-search-guidance:end -->`. If those markers are missing,
search for `## GBrain Search Guidance (configured by /sync-gbrain)` heading
and replace from there to the next `## ` or EOF. If no heading exists, append
the entire block at the end of CLAUDE.md.

**Atomic write:** write the new CLAUDE.md content to a tmp file alongside it
(e.g., `CLAUDE.md.sync-gbrain.tmp`) then `mv` to atomic-rename, so a crash
mid-write never leaves the file half-modified.

**If `status=unknown`** — preserve the existing guidance block, if any, and
report the helper's reason as WARN with advice to retry `/sync-gbrain` or the
read check when the transient failure clears. Do not install new guidance on
an unknown result or remove the existing guidance merely because this read
could not verify it. The `## GBrain Configuration` block stays in place.

**If `status=skipped`** — leave guidance unchanged. Report that code readiness
was not probed in this mode, not that it passed or failed.

Do NOT crash if CLAUDE.md is missing or unwritable — log a warning and
continue.

---

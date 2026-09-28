<!-- Moved verbatim from sync-gbrain/SKILL.md, the
     'step-2-run-the-orchestrator' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 2: Run the orchestrator

Pass user args to the orchestrator. Do not paraphrase them — pass through
as-is.

```bash
bun run ~/.claude/skills/gstack/bin/gstack-gbrain-sync.ts <user-args>
```

The orchestrator runs three stages: code → memory → brain-sync (per the
plan's storage tiering). Each stage failure is non-fatal; subsequent stages
still run. State is persisted to `~/.gstack/.gbrain-sync-state.json` via
tmp-file + atomic rename. Concurrent runs are blocked by a lock file at
`~/.gstack/.sync-gbrain.lock` (5-min stale-takeover).

---

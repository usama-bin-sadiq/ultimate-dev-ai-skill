<!-- Moved verbatim from health/SKILL.md, the
     'step-5-persist-to-health-history' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 5: Persist to Health History

```bash
eval "$(~/<agent-config-dir>/gstack/bin/gstack-slug 2>/dev/null)" && mkdir -p ~/.gstack/projects/$SLUG
```

Only when a numeric composite exists, append one JSONL line to
`~/.gstack/projects/$SLUG/health-history.jsonl`. Zero-check and capture-error runs
must leave any existing history unchanged:

```json
{"ts":"2026-03-31T14:30:00Z","branch":"main","score":9.1,"typecheck":10,"lint":8,"test":10,"deadcode":7,"shell":10,"gbrain":10,"duration_s":23}
```

Fields:
- `ts` -- ISO 8601 timestamp
- `branch` -- current git branch
- `score` -- composite score (one decimal)
- `typecheck`, `lint`, `test`, `deadcode`, `shell`, `gbrain` -- individual category scores (integer 0-10)
- `duration_s` -- total time for all tools in seconds

If a category was skipped, set its value to `null`. Pre-D6 history entries
won't have a `gbrain` field — treat them as `null` for trend comparison
and start new tracking from the first post-D6 run.

---

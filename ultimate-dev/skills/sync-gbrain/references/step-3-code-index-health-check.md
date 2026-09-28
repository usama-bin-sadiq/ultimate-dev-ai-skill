<!-- Moved verbatim from sync-gbrain/SKILL.md, the
     'step-3-code-index-health-check' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 3: Code-index health check

After the sync run, verify the cwd source registration and its page count:

```bash
SOURCE_JSON=$(bun run ~/.claude/skills/gstack/bin/gstack-gbrain-read-capability.ts --source-only 2>/dev/null)
SOURCE_ID=$(printf '%s' "$SOURCE_JSON" | jq -er 'if .status=="source" then .source_id else empty end' 2>/dev/null)
PAGES=$(printf '%s' "$SOURCE_JSON" | jq -er 'if .status=="source" and (.page_count | type)=="number" then .page_count else empty end' 2>/dev/null)
echo "cwd source: $SOURCE_ID, page_count: $PAGES"
```

`--source-only` validates the pretty state schema, writer, successful code stage,
real worktree path, `.gbrain-source` pin, and gbrain's registration path before
returning its safe integer page count. It does not read any page. An empty source
or page count is **unknown**, not zero: report WARN and do not offer a full
reindex on that evidence. If `PAGES` is proven `0` AND the user did NOT
pass `--no-code` AND mode was not `--full`, AskUserQuestion via the format in
the preamble:

> D1 — This repo has 0 indexed pages in gbrain. Run a full code reindex now?
>
> ELI10: gbrain hasn't indexed this repo's code yet. The semantic search
> tools (`gbrain search`, `code-def`, `code-refs`) will return nothing
> until we run a full pass. Takes ~25-35 minutes on a big Mac.
>
> Recommendation: A — the brain is unusable for code search until indexed,
> and Step 2 of this skill already verified gbrain is configured correctly.
>
> Note: options differ in kind, not coverage — no completeness score.
>
> A) Run /sync-gbrain --full now (recommended)
> B) Skip — I'll run it later

If A: re-invoke the orchestrator with `--full --code-only`.
If B: continue to Step 4 with the empty-corpus state recorded.

---

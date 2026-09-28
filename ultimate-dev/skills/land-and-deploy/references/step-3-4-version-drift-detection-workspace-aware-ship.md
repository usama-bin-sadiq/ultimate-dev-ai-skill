<!-- Moved verbatim from land-and-deploy/SKILL.md, the
     'step-3-4-version-drift-detection-workspace-aware-ship' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 3.4: VERSION drift detection (workspace-aware ship)

Check that another workspace has not claimed this PR's VERSION since `/ship`.

```bash
BRANCH_VERSION=$(git show "$PR_HEAD:VERSION" 2>/dev/null | tr -d '\r\n[:space:]')
BASE_VERSION=$(git show "$BASE_SHA:VERSION" 2>/dev/null | tr -d '\r\n[:space:]')
QUEUE_JSON=$(bun run ~/<agent-config-dir>/gstack/bin/gstack-next-version \
  --base "$BASE_BRANCH" \
  --exclude-pr "$PR_NUMBER" \
  --bump patch \
  --current-version "$BASE_VERSION" 2>/dev/null || echo '{"offline":true}')
NEXT_SLOT=$(echo "$QUEUE_JSON" | jq -r '.version // empty')
OFFLINE=$(echo "$QUEUE_JSON" | jq -r '.offline // false')
```

Use the existing conservative patch-level allocation; compare numeric version
components, not lexical strings. If this project has no VERSION, report this check
not applicable. A missing/unparseable version on only one side is unavailable, not green.

1. `OFFLINE=true`, helper failure or invalid result: report VERSION check unavailable
   with the reason; continue to Step 3.5. CI's version gate is the backstop.
2. `BRANCH_VERSION >= NEXT_SLOT`: no drift; continue.
3. `BRANCH_VERSION < NEXT_SLOT`: **STOP** with "VERSION drift detected", both versions
   and instructions to rerun `/ship` from the feature branch. Its ALREADY_BUMPED path
   reconciles VERSION, package.json, CHANGELOG header and PR title together. Do NOT
   auto-bump or merge here: duplicate versions can overwrite another branch's release notes.

---

> **STOP.** Before the pre-merge readiness gate (Step 3.5) — the last check before the irreversible merge, Read `~/<agent-config-dir>/gstack/land-and-deploy/sections/readiness-gate.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

---

> **STOP.** Before merging the PR and detecting the deploy strategy (Steps 4-5), Read `~/<agent-config-dir>/gstack/land-and-deploy/sections/merge-and-deploy.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

---

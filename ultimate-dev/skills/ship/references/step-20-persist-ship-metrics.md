<!-- Moved verbatim from ship/SKILL.md, the
     'step-20-persist-ship-metrics' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 20: Persist ship metrics

Log coverage and plan completion for `/retro` through `gstack-review-log`.
It resolves the project/branch, validates JSON, creates storage and queues sync.
It takes **no path argument**: hand-built `<branch>-reviews.jsonl` paths break
branches containing `/`.

```bash
~/.claude/skills/gstack/bin/gstack-review-log '{"skill":"ship","timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","coverage_pct":COVERAGE_PCT,"plan_items_total":PLAN_TOTAL,"plan_items_done":PLAN_DONE,"verification_result":"VERIFY_RESULT","version":"VERSION","branch":"'"$(git rev-parse --abbrev-ref HEAD)"'"}'
```

Substitute from earlier steps:
- **COVERAGE_PCT**: coverage percentage from Step 7 diagram (integer, or -1 if undetermined)
- **PLAN_TOTAL**: total plan items extracted in Step 8 (0 if no plan file)
- **PLAN_DONE**: count of DONE + CHANGED items from Step 8 (0 if no plan file)
- **VERIFY_RESULT**: "pass", "fail", or "skipped" from Step 8.1
- **VERSION**: from the VERSION file

The branch name is filled in by the shell — there is no `BRANCH` placeholder to
substitute.

This step is automatic — never skip it, never ask for confirmation.

---

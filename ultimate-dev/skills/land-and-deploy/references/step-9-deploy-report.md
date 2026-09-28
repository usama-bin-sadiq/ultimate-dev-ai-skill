<!-- Moved verbatim from land-and-deploy/SKILL.md, the 'Step 9: Deploy report' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 9: Deploy report

Choose the first matching verdict; never infer deployment success from merge or HTTP 200:

| Evidence | Verdict |
|----------|---------|
| Rollback requested, not yet confirmed on base and live/healthy (when deploy applies) | ROLLBACK PENDING |
| Rollback confirmed as described in Step 8 | REVERTED |
| Any accepted target-health failure | DEGRADED |
| User chose staging-only and staging passed | STAGING VERIFIED — PRODUCTION UNVERIFIED |
| Explicit no-deploy confirmation or Step 5's docs-only skip | MERGED — NO DEPLOY NEEDED |
| Matching production deployment PASSED and production HEALTHY | DEPLOYED AND VERIFIED |
| Matching production deployment PASSED but canary skipped/unavailable | DEPLOYED (UNVERIFIED) |
| Everything else, including failed/pending/unknown deploy even with a healthy old site | MERGED (UNVERIFIED) |

Display **LAND & DEPLOY REPORT** and save `.gstack/deploy-reports/{date}-pr{number}-deploy.md`
(`date` = UTC YYYY-MM-DD). Include PR/title/repository, head → base, approved head,
merge timestamp/SHA/method/path, first-run status, CI/review status and warnings,
scope, separate deploy/staging/canary outcomes with evidence links/errors, console
count, load time, screenshot paths (N/A when not checked), verdict and next action.
Record dry-run, CI wait, queue, deploy, staging, canary and total durations in seconds;
skipped stages have duration 0 with a reason, never a fabricated pass. Inline review
is passed/skipped/not-needed; inline fixes stopped before merge and cannot appear here.
For rollback include revert SHA or PR URL and unresolved work.

```bash
mkdir -p .gstack/deploy-reports
eval "$(~/<agent-config-dir>/gstack/bin/gstack-slug 2>/dev/null)"
mkdir -p ~/.gstack/projects/$SLUG
```

Pass one JSON entry to `~/<agent-config-dir>/gstack/bin/gstack-review-log '<JSON>'` for
the dashboard's branch-scoped JSONL log. `status` is SUCCESS
only for DEPLOYED AND VERIFIED or MERGED — NO DEPLOY NEEDED, REVERTED for confirmed
rollback, otherwise INCOMPLETE. Keep the full `verdict` and independent evidence states:
```json
{"skill":"land-and-deploy","timestamp":"<ISO>","status":"<SUCCESS/REVERTED/INCOMPLETE>","verdict":"<verdict>","pr":<number>,"merge_sha":"<sha>","merge_path":"<auto/direct/queue/external>","first_run":<true/false>,"deploy_status":"<PASSED/FAILED/PENDING/UNKNOWN/NOT_NEEDED>","verification":"<HEALTHY/DEGRADED/SKIPPED>","staging_status":"<VERIFIED/DEGRADED/SKIPPED/N/A>","review_status":"<observed status>","dry_run_s":<N>,"ci_wait_s":<N>,"queue_s":<N>,"deploy_s":<N>,"staging_s":<N>,"canary_s":<N>,"total_s":<N>}
```

---

<!-- Moved verbatim from land-and-deploy/SKILL.md, the 'Step 6: Wait for deploy (if applicable)' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 6: Wait for deploy (if applicable)

Unless returning for rollback, set `TARGET=production` and `DEPLOY_SHA=MERGE_SHA`. Use the deployment facts from
Steps 3.5/5; preserve status separately from canary health. A reachable URL alone
does not prove this revision deployed. No configured trigger: do not invent one.

### Strategy A: GitHub Actions workflow

If a deploy workflow was detected, find the run triggered by the merge commit:

```bash
gh run list --repo "$REPO" --branch "$BASE_BRANCH" --limit 10 --json databaseId,headSha,status,conclusion,name,workflowName
```

Match `DEPLOY_SHA`, workflow and target environment. If no run appears yet, repeat
the lookup within the same 20-minute deadline. A name match on another SHA is not evidence.

Poll every 30 seconds:
```bash
gh run view <run-id> --repo "$REPO" --json status,conclusion
```

### Strategy B: Platform CLI (Fly.io, Render, Heroku)

If a deploy status command was configured in <agent-instructions> (e.g., `fly status --app myapp`), use it instead of or in addition to GitHub Actions polling.

**Fly.io:** Check the configured app (do not issue `fly deploy`):
```bash
fly status --app {app} 2>/dev/null
```
Look for started Machines and a release tied to `DEPLOY_SHA`; time alone is not proof.

**Render:** Check its release record for the connected branch/revision, then reachability:
```bash
curl -sf {production-url} -o /dev/null -w "%{http_code}" 2>/dev/null
```
Poll every 30 seconds. HTTP 200 proves reachability, not which release is live.

**Heroku:** Check latest release:
```bash
heroku releases --app {app} -n 1 2>/dev/null
```

### Strategy C: Auto-deploy platforms (Vercel, Netlify)

When configured to auto-deploy on this merge, wait 60 seconds, inspect the deployment
record for `DEPLOY_SHA`, then Step 7. No record means deployment UNVERIFIED, not success.

### Strategy D: Custom deploy hooks

Run only the configured read-only status command. Check its exit code and revision
output; a generic health check cannot certify a new deployment.

### Common: Timing and failure handling

Record deploy start time. Show progress every 2 minutes: "Deploy is still running... ({X}m so far). This is normal for most platforms."

Matching revision successfully deployed: record `DEPLOY_STATUS=PASSED`, duration,
and evidence. Continue to Step 7, or Step 5's URL question if none is available.

If deploy fails/cancels: record `DEPLOY_STATUS=FAILED`, then use AskUserQuestion:
- **Re-ground:** "The deploy workflow failed after the merge. The code is merged but may not be live yet. Here's what I can do:"
- **RECOMMENDATION:** Choose A to investigate before reverting.
- A) Let me look at the deploy logs to figure out what went wrong
- B) Revert the merge immediately — roll back to the previous version
- C) Continue to health checks anyway — the deploy failure might be a flaky step, and the site might actually be fine

**A:** Read `gh run view <run-id> --repo "$REPO" --log-failed` (or configured platform
logs), summarize the cause and evidence limits, then ask: revert (Step 8), inspect
health (Step 7), or finish unverified (Step 9). No automatic code edits or redeploy.
**B:** Step 8. **C:** Step 7 if a URL exists, otherwise Step 5's URL question. A passing
canary never erases FAILED deployment evidence.

At 20 minutes (including waiting for a run to appear), ask: **A)** wait another bounded
20 minutes, **B)** finish without verification. A resets only the wait deadline and
resumes the same lookup/poll; B records pending/unknown deployment and goes to Step 9.
Status-query failure is unknown: show the error and offer the same bounded wait or
finish choices, not a fabricated success. During rollback monitoring, failure offers
logs or a pending report, never a second automatic revert.

---

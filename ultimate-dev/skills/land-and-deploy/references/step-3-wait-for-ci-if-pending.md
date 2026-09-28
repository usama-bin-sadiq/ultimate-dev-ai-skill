<!-- Moved verbatim from land-and-deploy/SKILL.md, the
     'step-3-wait-for-ci-if-pending' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 3: Wait for CI (if pending)

If required checks are still pending, wait for them to complete. Use a timeout of 15 minutes:

```bash
gh pr checks "$PR_NUMBER" --repo "$REPO" --required --watch --fail-fast --interval 30
```

Record the CI wait time for the deploy report.

Pass: report duration and continue to Step 3.4, then Step 3.5 before merging.
Failure: **STOP**, show failing checks. Timeout (15 minutes): **STOP**, point to
GitHub Actions. Enforce the deadline; do not leave an unbounded watch running.

---

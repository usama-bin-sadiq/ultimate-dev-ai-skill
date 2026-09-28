<!-- Moved verbatim from land-and-deploy/SKILL.md, the
     'step-2-pre-merge-checks' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 2: Pre-merge checks

Tell the user: "Checking CI status and merge readiness..."

```bash
gh pr checks "$PR_NUMBER" --repo "$REPO" --required --json name,state,bucket,link
```

Parse valid JSON using `bucket` (pass/fail/pending/skipping/cancel). Exit 8 means
pending; a nonzero exit with valid failing checks is a CI failure. Auth/network/schema
errors are **STOP**, never "no required checks". An empty successful result or the
CLI's explicit "no required checks reported" response means none are configured.
1. Required checks **FAILING/cancelled**: **STOP**, list failures to fix.
2. Required checks **PENDING**: announce the wait and proceed to Step 3.
3. All pass (or none required): report that exact result. Skip only Step 3's wait;
   continue to Step 3.4, then Step 3.5 before merging.

Also check for merge conflicts:
```bash
gh pr view "$PR_NUMBER" --repo "$REPO" --json mergeable -q .mergeable
```
If `CONFLICTING`: **STOP**, resolve conflicts first. Failed/UNKNOWN readback: **STOP**,
readiness is not established. Cancelled required checks are failures, not passes.

---

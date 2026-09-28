<!-- Moved verbatim from land-and-deploy/SKILL.md, the
     'step-8-revert-if-needed' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 8: Revert (if needed)

Enter only after the user's explicit rollback choice. Explain that this adds inverse
commits; production is not restored until rollback deploys and health is checked.
Require a clean worktree, fetch `BASE_BRANCH` from `REPO`, switch to the local base
and fast-forward only to that fetched tip. Dirty, diverged, or occupied base: **STOP**
with ROLLBACK PENDING, never reset/force or discard work.

Inspect the actual landed commit, not just the requested merge method:
```bash
git show --no-patch --format='%H %P' "$MERGE_SHA"
```
- Two parents: verify parent 1 is the base-side history, then
  `git revert -m 1 "$MERGE_SHA" --no-edit`.
- One-parent **confirmed squash**: `git revert "$MERGE_SHA" --no-edit`.
- **Rebase merge:** establish the exact landed commit range for this PR and revert
  it newest-first. `mergeCommit.oid` alone is only the last commit, not the range.
  Unknown range/method (including an external merge) or other parent shapes: **STOP**
  with ROLLBACK PENDING and request manual rollback; do not guess.

Conflicts: stop, show `git status` and the attempted command, leave resolution to the
user. After a clean revert, record `REVERT_SHA` and push to the selected base:
`git push "https://github.com/$REPO.git" "HEAD:refs/heads/$BASE_BRANCH"`. If branch
protection rejects it, keep the commit, create `revert/pr-<number>-<timestamp>` there,
push that branch and open a revert PR against `BASE_BRANCH`. Report its URL and
ROLLBACK PENDING; never merge it without separate approval. Other push errors stop
with the error and pending status, not a protection bypass.

After a successful base push, set `ROLLBACK=true`, `TARGET=production`,
`DEPLOY_SHA=REVERT_SHA`, and reset production deployment/health to UNKNOWN/SKIPPED
for that revision. Keep original/staging evidence separately. Monitor via Steps 6-7
without resetting those values. Only a confirmed rollback deployment
and healthy production canary yields REVERTED (or a confirmed base revert where no
deploy is required). All incomplete, failed, skipped or PR-based rollback paths go
to Step 9 as ROLLBACK PENDING. Preserve the original merge SHA in the report.

---

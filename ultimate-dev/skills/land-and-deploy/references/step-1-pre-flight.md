<!-- Moved verbatim from land-and-deploy/SKILL.md, the
     'step-1-pre-flight' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 1: Pre-flight

Tell the user: "Checking access and finding your PR."

1. Check GitHub CLI authentication:
```bash
gh auth status
```
If unauthenticated, **STOP**; ask the user to run `gh auth login`, then retry.

2. Save any URL as `VERIFY_URL` (an explicit verification request). Set `PR_NUMBER`
to the numeric `#NNN` argument, or detect it once from the current branch:
```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner) || exit 1
if [ -z "$PR_NUMBER" ]; then
  PR_NUMBER=$(gh pr view --repo "$REPO" --json number -q .number) || exit 1
fi
PR_JSON=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json number,state,title,url,mergeable,baseRefName,headRefName,headRefOid,baseRefOid) || exit 1
PR_HEAD=$(printf '%s' "$PR_JSON" | jq -er .headRefOid) || exit 1
HEAD_BRANCH=$(printf '%s' "$PR_JSON" | jq -er .headRefName) || exit 1
BASE_BRANCH=$(printf '%s' "$PR_JSON" | jq -er .baseRefName) || exit 1
```
Carry these values across fresh shells. Every later command targets this repository
and PR, never implicit current-branch detection. A failed query is unknown, not an
empty PR. Tell the user the selected number, title, head → base and head SHA.

3. No PR: **STOP**, suggest `/ship`. CLOSED: **STOP**, ask to reopen it. MERGED:
**STOP**, suggest `/canary <url>`; do not merge again or claim a deploy happened.
Only OPEN continues. Before any HEAD-based evidence, require the matching clean checkout:
```bash
LOCAL_HEAD=$(git rev-parse HEAD) || exit 1
LOCAL_BRANCH=$(git branch --show-current) || exit 1
LOCAL_STATUS=$(git status --porcelain) || exit 1
if [ "$LOCAL_HEAD" != "$PR_HEAD" ] || [ "$LOCAL_BRANCH" != "$HEAD_BRANCH" ] || [ -n "$LOCAL_STATUS" ]; then
  echo "LOCAL_TARGET_MISMATCH"
  exit 1
fi
git fetch "https://github.com/$REPO.git" "$BASE_BRANCH" || exit 1
BASE_SHA=$(git rev-parse FETCH_HEAD) || exit 1
SCOPE_RESULT=$(~/<agent-config-dir>/gstack/bin/gstack-diff-scope "$BASE_SHA") || exit 1
eval "$SCOPE_RESULT"
```
On mismatch, **STOP** and ask the user to save their work, check out/update the PR
branch, and rerun. Do not switch, reset, or stash for them. Preserve `BASE_SHA`, the
PR's commit list and all scope flags before merging; cleanup may change HEAD afterward.
Unknown scope is not docs-only. `DOCS_ONLY=true` requires SCOPE_DOCS and no other scope.

---

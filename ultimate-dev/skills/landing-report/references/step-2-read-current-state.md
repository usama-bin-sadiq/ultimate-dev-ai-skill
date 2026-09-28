<!-- Moved verbatim from landing-report/SKILL.md, the
     'step-2-read-current-state' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 2: Read current state

```bash
CURRENT_VERSION=$(cat VERSION 2>/dev/null | tr -d '[:space:]' || echo "0.0.0.0")
git fetch origin "$BASE_BRANCH" --quiet 2>/dev/null || true
BASE_VERSION=$(git show "origin/$BASE_BRANCH:VERSION" 2>/dev/null | tr -d '[:space:]' || echo "$CURRENT_VERSION")
echo "origin/$BASE_BRANCH VERSION: $BASE_VERSION"
echo "branch HEAD VERSION: $CURRENT_VERSION"
```

---

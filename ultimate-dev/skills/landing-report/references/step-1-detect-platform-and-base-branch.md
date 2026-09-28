<!-- Moved verbatim from landing-report/SKILL.md, the
     'step-1-detect-platform-and-base-branch' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 1: Detect platform and base branch

Same detection as other gstack skills.

```bash
BASE_BRANCH=$(gh pr view --json baseRefName -q .baseRefName 2>/dev/null || \
              gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || \
              echo main)
echo "Base branch: $BASE_BRANCH"
```

---

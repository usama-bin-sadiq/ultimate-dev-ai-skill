<!-- Moved verbatim from review/SKILL.md, the
     'step-3-get-the-diff' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 3: Get the diff

Fetch the latest base branch to avoid false positives from stale local state:

```bash
git fetch origin <base> --quiet
```

Compute the merge base, then diff the working tree against that point:

```bash
DIFF_BASE=$(git merge-base origin/<base> HEAD)
~/<agent-config-dir>/gstack/bin/gstack-review-log --start review
git diff "$DIFF_BASE"
```

This includes both committed and uncommitted changes while excluding commits that landed on the base branch after this branch was created.
Remember the printed start token as REVIEW_START for this pass. Capture it before reading the diff, never at log time. On each full re-review, capture a new token. Read any non-ignored untracked source files too (`git ls-files --others --exclude-standard`); the fingerprint includes them.

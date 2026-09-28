<!-- Moved verbatim from document-release/SKILL.md, the
     'step-1-pre-flight-diff-analysis' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 1: Pre-flight & Diff Analysis

`<base>` and the hosting platform come from the shared Step 0 above this workflow.
Resolve the release merge-base, stopping if neither ref exists.
Use the printed SHA for `<diff-base>` in later commands, not a shell variable:

```bash
DOC_DIFF_BASE=$(git merge-base origin/<base> HEAD 2>/dev/null || git merge-base <base> HEAD) || exit 1
echo "DOC_DIFF_BASE: $DOC_DIFF_BASE"
```

1. Check the current branch. If on the base branch, **abort**: "You're on the base branch. Run from a feature branch."

2. Gather context about what changed:

```bash
git diff <diff-base> HEAD --stat
```

```bash
git log <diff-base>..HEAD --oneline
```

```bash
git diff <diff-base> HEAD --name-only
```

3. Discover all documentation files in the repo:

```bash
find . -maxdepth 2 -name "*.md" -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./.gstack/*" -not -path "./.context/*" | sort
```

4. Classify the changes into categories relevant to documentation:
   - **New features** — new files, new commands, new skills, new capabilities
   - **Changed behavior** — modified services, updated APIs, config changes
   - **Removed functionality** — deleted files, removed commands
   - **Infrastructure** — build system, test infrastructure, CI

5. Output a brief summary: "Analyzing N files changed across M commits. Found K documentation files to review."

---

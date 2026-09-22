---
name: never-commits
description: Hard rule - skill never commits or pushes
---

# Never Commits / Pushes (HARD RULE)

**The skill/agent NEVER:**
- Runs `git commit`, `git commit --amend`, or equivalent
- Runs `git push`, `git push --force`, or equivalent
- Runs `gh pr create`, `gh pr merge`, or equivalent
- Uses `--no-verify`, `--no-gpg-sign`, `--force` on shared branches

**The skill/agent ALWAYS:**
- Presents the diff, draft commit message, and draft PR body
- Says: "Ready for you to commit and push when you're satisfied."
- Stops there — waits for explicit developer confirmation

**Rationale:** The developer is the only authority that adds to history.
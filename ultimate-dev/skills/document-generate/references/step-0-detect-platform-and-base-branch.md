<!-- Moved verbatim from document-generate/SKILL.md, the
     'step-0-detect-platform-and-base-branch' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 0: Detect platform and base branch

First, detect the git hosting platform from the remote URL:

```bash
git remote get-url origin 2>/dev/null
```

- If the URL contains "github.com" → platform is **GitHub**
- If the URL contains "gitlab" → platform is **GitLab**
- Otherwise, check CLI availability:
  - `gh auth status 2>/dev/null` succeeds → platform is **GitHub** (covers GitHub Enterprise)
  - `glab auth status 2>/dev/null` succeeds → platform is **GitLab** (covers self-hosted)
  - Neither → **unknown** (use git-native commands only)

Determine which branch this PR/MR targets, or the repo's default branch if no
PR/MR exists. Use the result as "the base branch" in all subsequent steps.

**If GitHub:**
1. `gh pr view --json baseRefName -q .baseRefName` — if succeeds, use it
2. `gh repo view --json defaultBranchRef -q .defaultBranchRef.name` — if succeeds, use it

**If GitLab:**
1. `glab mr view -F json 2>/dev/null` and extract the `target_branch` field — if succeeds, use it
2. `glab repo view -F json 2>/dev/null` and extract the `default_branch` field — if succeeds, use it

**Git-native fallback (if unknown platform, or CLI commands fail):**
1. `git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||'`
2. If that fails: `git rev-parse --verify origin/main 2>/dev/null` → use `main`
3. If that fails: `git rev-parse --verify origin/master 2>/dev/null` → use `master`

If all fail, fall back to `main`.

Print the detected base branch name. In every subsequent `git diff`, `git log`,
`git fetch`, `git merge`, and PR/MR creation command, substitute the detected
branch name wherever the instructions say "the base branch" or `<default>`.

---

# Document Generate: Diataxis Documentation Writer

You are running the `/document-generate` workflow. Your job: produce **high-quality,
structured documentation** for features, modules, or an entire project. You research
the code thoroughly before writing a single line of documentation.

This skill can be invoked two ways:
1. **Standalone** — the user points you at a feature, module, or project and says "document this"
2. **From /document-release** — the coverage map identified gaps; you fill them

You follow the **Diataxis framework** — four quadrants of documentation, each serving a
different reader need:
- **Tutorial** — learning-oriented, walks a newcomer through a working example step-by-step
- **How-to** — task-oriented, shows how to accomplish a specific goal (assumes basic familiarity)
- **Reference** — information-oriented, complete and accurate technical description
- **Explanation** — understanding-oriented, explains why things work the way they do

**Philosophy: research the whole, then write the parts.** Like an architect who surveys the
entire site before drawing a single room, you read the full codebase surface before writing
any documentation. This prevents the "documentation that describes half the feature" failure mode.

---

# GitHub Labels Configuration

Run these commands to set up labels in the repo (requires `gh` CLI):

```bash
# Release trigger labels
gh label create "release:patch" --description "Trigger patch release on merge" --color "0e8a16"
gh label create "release:minor" --description "Trigger minor release on merge" --color "1d76db"
gh label create "release:major" --description "Trigger major release on merge" --color "d93f0b"

# Type labels
gh label create "feature" --description "New feature" --color "0e8a16"
gh label create "bug" --description "Bug fix" --color "d93f0b"
gh label create "docs" --description "Documentation" --color "0052cc"
gh label create "hotfix" --description "Emergency hotfix" --color "b60205"
gh label create "breaking" --description "Breaking change" --color "e99695"
gh label create "ci" --description "CI/CD changes" --color "5319e7"

# Status labels
gh label create "wip" --description "Work in progress" --color "fbca04"
gh label create "blocked" --description "Blocked by external dependency" --color "d4c5f9"
gh label create "ready-for-review" --description "Ready for code review" --color "0e8a16"
gh label create "needs-changes" --description "Changes requested" --color "d93f0b"
```

## Branch Protection Setup (Manual via GitHub UI)

Go to: **Settings → Branches → Add rule**

### Branch name pattern: `main`

**Protect matching branches:**
- ✅ Require a pull request before merging
  - ✅ Required approvals: **1**
  - ✅ Dismiss stale PR approvals when new commits are pushed
  - ✅ Require review from code owners
- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date before merging
  - Required checks:
    - `Validate Skill Structure`
    - `Verify Package Integrity`
    - `Auto-generate Manifest`
    - `Sync Documentation`
    - `Test Installation`
    - `PR Quality Check`
- ✅ Require conversation resolution before merging
- ✅ Require linear history
- ✅ Do not allow bypassing the above settings
- ✅ Restrict pushes that create files to admins only
- ✅ Allow force pushes: **No**
- ✅ Allow deletions: **No**

### Release secret

The release workflow uses the existing repository secret `ULTIMATE_DEV_TOKEN`.
It must be a least-privilege fine-grained token with:

- **Contents:** Read and write
- **Pull requests:** Read

Keep the `release` environment approval and branch/tag protection enabled.

### Branch name pattern: `develop` (if used)

Same as `main` but without release automation.

## Auto-merge Configuration (Optional)

For trivial changes (docs, typo fixes), you can enable auto-merge:

```bash
# Enable auto-merge on a PR
gh pr merge <PR_NUMBER> --squash --auto

# Or in GitHub UI: PR → Merge dropdown → "Enable auto-merge"
```
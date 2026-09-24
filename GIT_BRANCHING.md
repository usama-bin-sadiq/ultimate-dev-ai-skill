# Git Branching & Release Strategy

This document defines the professional Git workflow for the ultimate-dev project.

## Branch Structure

```
main (protected)
  ↑
  │  release/* branches (short-lived, merged via PR)
  │    ↑
  │    │  feature/* branches (from main, merged via PR)
  │    │    ↑
  │    │    │  hotfix/* branches (from main, merged to main + develop)
  │    │    │
develop (optional, for ongoing development)
```

### Branch Types

| Branch | Purpose | Source | Target | Lifetime |
|--------|---------|--------|--------|----------|
| `main` | Production-ready code | — | — | Permanent |
| `develop` | Integration branch | `main` | `main` | Permanent (optional) |
| `feature/*` | New features/fixes | `main`/`develop` | `main`/`develop` | Days-weeks |
| `release/*` | Release preparation | `main` | `main` | Hours-days |
| `hotfix/*` | Emergency fixes | `main` | `main` (+ `develop`) | Hours |

---

## Branch Protection Rules (main)

**Required (configure in GitHub Settings → Branches → Add rule):**

- [x] Require a pull request before merging
- [x] Require approvals: **1** minimum
- [x] Dismiss stale PR approvals when new commits are pushed
- [x] Require review from code owners
- [x] Require status checks to pass before merging:
  - `Validate Skill Structure`
  - `Verify Package Integrity`
  - `Auto-generate Manifest`
  - `Sync Documentation`
  - `Test Installation`
- [x] Require branches to be up to date before merging
- [x] Require linear history
- [x] Do not allow bypassing the above settings
- [x] Restrict pushes that create files to admins only

---

## Pull Request Workflow

### Creating a PR

1. **Branch from `main`** (or `develop` if active):
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Commit with conventional messages:**
   ```
   feat: add new agent for X
   fix: resolve validation bug in Y
   docs: update README with Z
   chore: bump version to 2.5.3
   ```

3. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   # Create PR via GitHub UI or: gh pr create
   ```

### PR Requirements

- **Title:** Clear, descriptive (follows conventional commits if possible)
- **Description:** Use `.github/PULL_REQUEST_TEMPLATE.md`
- **Labels:** Add appropriate labels (`feature`, `bug`, `docs`, `release:patch/minor/major`)
- **Checks:** All CI must pass before merge
- **Review:** At least 1 approval required

### Merging

- **Squash and merge** (default) — keeps history clean
- **Delete branch after merge** — enforced
- **Auto-merge** can be enabled for trivial changes

---

## Release Process

### Standard Release (Recommended)

1. **Create release PR:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b release/v2.5.3
   # Make any final adjustments if needed
   git push origin release/v2.5.3
   # Create PR with label "release:patch" (or minor/major)
   ```

2. **CI validates** on the PR (same as any PR)

3. **Merge PR** → triggers `release.yml` workflow → creates tag + GitHub Release

### Emergency Hotfix

1. **Create hotfix branch from main:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/critical-fix
   # Apply fix
   git push origin hotfix/critical-fix
   # Create PR with label "release:patch" + "hotfix"
   ```

2. **Expedited review** (can merge with 1 approval)

3. **Merge** → auto-releases patch version

### Manual Release (if needed)

```bash
# Via GitHub Actions UI → "Sync & Release" → Run workflow
# Select: patch / minor / major
# Optional: add custom release notes
```

---

## Versioning (Semantic Versioning)

| Bump | When |
|------|------|
| **patch** (2.5.2 → 2.5.3) | Bug fixes, docs, internal improvements |
| **minor** (2.5.2 → 2.6.0) | New features, new agents/skills, backward-compatible |
| **major** (2.5.2 → 3.0.0) | Breaking changes, architecture overhaul, removal of public APIs |

---

## Commit Message Convention

Follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | minor |
| `fix` | Bug fix | patch |
| `docs` | Documentation only | patch |
| `style` | Formatting, no logic change | patch |
| `refactor` | Code restructuring | patch |
| `perf` | Performance improvement | patch |
| `test` | Adding/updating tests | patch |
| `chore` | Maintenance, version bumps | patch (auto) |
| `ci` | CI/CD changes | patch |
| `build` | Build system changes | patch |

### Examples

```
feat(agent): add new python-engineer specialist
fix(runtime): handle edge case in state transitions
docs: update installation guide for Windows
chore: release v2.5.2
```

---

## Labels

| Label | Purpose |
|-------|---------|
| `feature` | New functionality |
| `bug` | Bug fix |
| `docs` | Documentation |
| `hotfix` | Emergency fix |
| `release:patch` | Release trigger: patch |
| `release:minor` | Release trigger: minor |
| `release:major` | Release trigger: major |
| `ci` | CI/CD changes |
| `breaking` | Breaking change (requires major) |

---

## CI/CD Pipeline

### On Every PR (validate.yml)
1. `Validate Skill Structure` — structure validation
2. `Verify Package Integrity` — verify.sh
3. `Auto-generate Manifest` — manifest sync check
4. `Sync Documentation` — README sync check
5. `Test Installation` — global + project install test

### On Release (release.yml)
Triggered by:
- Any ordinary commit pushed or merged to `main` (including merge queues)
- A PR merged to `main` with a `release:*` label (the push event detects this and avoids a duplicate)
- Manual `workflow_dispatch` (patch/minor/major + optional notes)

Version selection:
- Explicit `release:*` PR labels select the bump for labeled PRs.
- Push events infer `major` from `BREAKING CHANGE`/`!:` or `[release:major]`,
  `minor` from `feat:`/`feature:` or `[release:minor]`, and otherwise use `patch`.
- Generated `chore: release v*` and `chore: auto-sync manifest and docs` commits
  are ignored so automation cannot recursively release itself.

Actions:
- Bump version (from label, commit convention, or input)
- Regenerate manifest + sync docs
- Update changelog
- Commit + tag + push
- Create GitHub Release

The repository secret `ULTIMATE_DEV_TOKEN` supplies the token used by the
release job. It should be a least-privilege fine-grained token with Contents
read/write and Pull requests read access. The `release` environment remains
the required approval boundary.

---

## Local Development Setup

```bash
# 1. Clone
git clone https://github.com/usama-bin-sadiq/ultimate-dev-ai-skill.git
cd ultimate-dev-ai-skill

# 2. Install pre-commit hooks (optional but recommended)
./scripts/pre-commit  # or: pre-commit install

# 3. Run validation locally
cd ultimate-dev
python scripts/validate.py
python -m pytest tests/ -v

# 4. Before pushing
python scripts/sync-docs.py --check
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start new feature | `git checkout main && git pull && git checkout -b feature/name` |
| Update from main | `git fetch origin && git rebase origin/main` |
| Run all checks | `cd ultimate-dev && python scripts/validate.py && python -m pytest tests/ -v` |
| Sync docs | `cd ultimate-dev && python scripts/sync-docs.py` |
| Create release PR | `git checkout -b release/vX.Y.Z && git push && gh pr create --label "release:patch"` |
| Emergency hotfix | `git checkout -b hotfix/name && git push && gh pr create --label "release:patch" --label "hotfix"` |
| View tags | `git tag -l "v*"` |

---

## Configuration

Branch protection and labels must be configured in **GitHub Settings** (not in this repo). See "Branch Protection Rules" above for required settings.
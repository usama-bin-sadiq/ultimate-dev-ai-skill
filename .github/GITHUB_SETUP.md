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
    - `PR Template Compliance (Read-only)`
  - These are the `name:` values of the jobs, not their YAML keys. GitHub
    matches on the display name, and a name that does not exist never
    reports — so a typo here does not fail loudly, it silently makes the
    branch unprotectable. A required check is only valid if the job that
    produces it actually runs on the event being gated, so the list is
    the jobs that report on a pull request, across *all* workflow files:
    ```sh
    python3 - <<'PY'
    import pathlib, yaml

    # A required check must report on the event being gated. A pull_request
    # trigger narrowed to `closed` never fires on an open PR, so its jobs
    # would block every merge forever.
    ON_OPEN_PR = {"opened", "synchronize", "reopened", "edited", "ready_for_review"}

    def fires_on_open_pr(trigger):
        pr = (trigger.get(True) or trigger).get("pull_request")
        if pr is None:
            return False
        types = pr.get("types") if isinstance(pr, dict) else None
        return not types or bool(set(types) & ON_OPEN_PR)

    for p in sorted(pathlib.Path(".github/workflows").glob("*.yml")):
        doc = yaml.safe_load(p.read_text())
        # bare `on:` parses as the boolean True, so check both spellings
        trigger = doc.get(True) or doc.get("on") or {}
        if not fires_on_open_pr(trigger):
            continue
        for job in doc["jobs"].values():
            # a job gated on failure() reports only when something broke
            if "failure()" in str(job.get("if", "")):
                continue
            print(f"    - `{job['name']}`")
    PY
    ```
  - Do **not** require the release jobs (`Validate Before Release`,
    `Determine Release Need`, `Release Approval Gate`, `Create Release`).
    They trigger on `push: main`, `pull_request: closed`, and
    `workflow_dispatch` — never on an open pull request — so requiring
    them would block every merge forever. Do not require
    `Cancel sibling workflows on failure` either; it is gated on
    `failure()` and reports only when something already broke.
  - Release ordering lives in `release.yml`, not here. Its `validate`
    job runs `validate-skills.py --strict` and everything downstream
    `needs:` it, so a red tree cannot reach a tag. That gate is
    deliberately duplicated from `validate.yml` rather than shared:
    `needs:` cannot express "wait for another workflow", and
    `validate.yml` ignores pushes touching only `VERSION` and
    `CHANGELOG.md` — which is the exact shape of a release commit, so
    those commits were never validated at all.
- ✅ Require conversation resolution before merging
- ✅ Require linear history
- ✅ Do not allow bypassing the above settings
- ✅ Restrict pushes that create files to admins only
- ✅ Allow force pushes: **No**
- ✅ Allow deletions: **No**

### Release secret

The release workflow uses the existing environment secret
`ULTIMATE_DEV_TOKEN` from the `CICD` environment. It must be a
least-privilege fine-grained token with:

- **Contents:** Read and write
- **Pull requests:** Read

The separate `release` environment remains the approval gate; the write job
runs in `CICD` so the configured secret is available. Keep branch/tag
protection enabled.

The decision job that determines *whether* to release uses the default read-only
`GITHUB_TOKEN` and never holds `ULTIMATE_DEV_TOKEN`. Only the gated
`create-release` job is write-capable, and it re-validates both skills and the
bundle test suite before committing, so a release cannot ship a skill that does
not validate.

### Branch name pattern: `develop` (if used)

Same as `main` but without release automation.

## Auto-merge Configuration (Optional)

For trivial changes (docs, typo fixes), you can enable auto-merge:

```bash
# Enable auto-merge on a PR
gh pr merge <PR_NUMBER> --squash --auto

# Or in GitHub UI: PR → Merge dropdown → "Enable auto-merge"
```
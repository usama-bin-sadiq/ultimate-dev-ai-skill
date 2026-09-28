<!-- Moved verbatim from ship/SKILL.md, the
     'step-2-distribution-pipeline-check' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 2: Distribution Pipeline Check

If the diff introduces a new standalone artifact (CLI binary, library package, tool) — not a web
service with existing deployment — verify that a distribution pipeline exists.

1. Check for newly added distribution entry points and package manifests:
   ```bash
   git diff origin/<base> --diff-filter=A --name-only | grep -E '(^|/)(cmd/[^/]+/main\.go|bin/[^/]+|Cargo\.toml|setup\.py|package\.json)$' | head -5
   ```
   Also inspect matching untracked files from Step 1's status. Read each match:
   a new `package.json` or `Cargo.toml` alone does not establish a publishable
   artifact. Also inspect existing manifests for newly declared binaries or
   package exports. Apply the pipeline gate only when a new distributable is present.

2. If new artifact detected, check for a release workflow:
   ```bash
   ls .github/workflows/ 2>/dev/null | grep -iE 'release|publish|dist'
   grep -qE 'release|publish|deploy' .gitlab-ci.yml 2>/dev/null && echo "GITLAB_CI_RELEASE"
   ```

3. **If no release pipeline exists and a new artifact was added:** Use AskUserQuestion:
   - "This PR adds a new binary/tool but there's no CI/CD pipeline to build and publish it.
     Users won't be able to download the artifact after merge."
   - A) Add a release workflow now (CI/CD release pipeline — GitHub Actions or GitLab CI depending on platform)
   - B) Defer — add a P1 distribution follow-up to the TODOS list in Step 14
   - C) Not needed — this is internal/web-only, existing deployment covers it

4. **If the user chooses A:** Add packaging and publish configuration using this repository's CI conventions. Ask for the intended distribution target if it is unknown; do not invent a registry or credentials. Include the new workflow in the tests and review below. Do not publish a release during `/ship`.
5. **If release pipeline exists:** Continue silently.
6. **If no new artifact detected:** Skip silently.

---

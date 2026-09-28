---
name: land-and-deploy
preamble-tier: 4
version: 1.0.0
description: Land and deploy workflow.
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - AskUserQuestion
triggers:
  - merge and deploy
  - land the pr
  - ship to production
neutralised: tool-specific paths and single-runtime invocations replaced
---
<!-- AUTO-GENERATED from SKILL.md.tmpl — do not edit directly -->
<!-- Regenerate: bun run gen:skill-docs -->


## When to invoke this skill

Merges the PR, waits for CI and deploy,
verifies production health via canary checks. Takes over after /ship
creates the PR. Use when: "merge", "land", "deploy", "merge and verify",
"land it", "ship it to production".

## Preamble (run first)

Detail moved to `references/preamble-run-first.md`.

## Plan Mode Safe Operations

In plan mode, allowed because they inform the plan: `$B`, `$D`, `codex exec`/`codex review`, temp prompts, writes to `~/.gstack/`, writes to the plan file, and `open` for generated artifacts.

## Skill Invocation During Plan Mode

If the user invokes a skill in plan mode, the skill takes precedence over generic plan mode behavior. **Treat the skill file as executable instructions, not reference.** Follow it step by step starting from Step 0; any AskUserQuestion the skill fires is the workflow operating within plan mode, not a violation of it — and a skill whose instructions resolve a question themselves (e.g. a plan-mode auto-select) may legitimately not ask it. AskUserQuestion (any variant — `mcp__*__AskUserQuestion` or native; see "AskUserQuestion Format → Tool resolution") satisfies plan mode's end-of-turn requirement. If AskUserQuestion is unavailable or a call fails, follow the AskUserQuestion Format failure fallback: `headless` → BLOCKED; `interactive` → the prose fallback (also satisfies end-of-turn). At a STOP point, stop immediately. Do not continue the workflow or call ExitPlanMode there. Commands marked "PLAN MODE EXCEPTION — ALWAYS RUN" execute. Call ExitPlanMode only after the skill workflow completes, or if the user tells you to cancel the skill or leave plan mode.

If `PROACTIVE` is `"false"`, do not auto-invoke or proactively suggest skills. If a skill seems useful, ask: "I think /skillname might help here — want me to run it?"

If `SKILL_PREFIX` is `"true"`, suggest/invoke `/gstack-*` names. Disk paths stay `~/<agent-config-dir>/gstack/[skill-name]/SKILL.md`.

## AskUserQuestion Format

Detail moved to `references/askuserquestion-format.md`.

## Artifacts Sync (skill start)

The skill-start output above already ran artifacts sync. Act on its lines:
GBrain hint text (if present) tells you when to prefer `gbrain` over Grep;
`ARTIFACTS_SYNC:` reports sync health (`off`, `mode=... | queue=N`,
`remote-mode`, or a restore hint naming `gstack-brain-restore`).

The one-time privacy stop-gate (artifacts-sync consent) arrives as a
`GSTACK_INSTRUCTION` block from skill-start when consent is actually pending
— fire it via AskUserQuestion exactly as the block instructs.

## Model-Specific Behavioral Patch (claude)

Detail moved to `references/model-specific-behavioral-patch-claude.md`.

## Voice

Detail moved to `references/voice.md`.

## Context Recovery

Detail moved to `references/context-recovery.md`.

## Writing Style (skip entirely if `EXPLAIN_LEVEL: terse` appears in the preamble echo OR the user's current message explicitly requests terse / no-explanations output)

Detail moved to `references/writing-style-skip-entirely-if-explain-level-terse-appears-in-the-preamble-echo-or-the-user-s-current-message-explicitly-requests-terse-no-explanations-output.md`.

## Completeness Principle — Boil the Ocean

AI makes completeness cheap, so the complete thing is the goal. Recommend full coverage (tests, edge cases, error paths) — boil the ocean one lake at a time. The only thing out of scope is genuinely unrelated work (rewrites, multi-quarter migrations); flag that as separate scope, never as an excuse for a shortcut.

When options differ in coverage, include `Completeness: X/10` (10 = all edge cases, 7 = happy path, 3 = shortcut). When options differ in kind, write: `Note: options differ in kind, not coverage — no completeness score.` Do not fabricate scores.

## Confusion Protocol

For high-stakes ambiguity (architecture, data model, destructive scope, missing context), STOP. Name it in one sentence, present 2-3 options with tradeoffs, and ask. Do not use for routine coding or obvious changes.

## Claimed Limitations Need Evidence

A claimed limitation or requirement ("the API can't do this", "X requires a credential", "that's impossible on this platform") is a material claim. State one only with the verbatim error, the documented statement, or a live probe in hand — pattern-matching a failure to a familiar story is not evidence. When a cheap probe settles the question, run it BEFORE asking the user anything or declaring a step blocked.

## Context Health (soft directive)

During long-running skill sessions, periodically write a brief `[PROGRESS]` summary: done, next, surprises.

If you are looping on the same diagnostic, same file, or failed fix variants, STOP and reassess. Consider escalation or /context-save. Progress summaries must NEVER mutate git state.

## Question Tuning (skip entirely if `QUESTION_TUNING: false`)

Detail moved to `references/question-tuning-skip-entirely-if-question-tuning-false.md`.

## Repo Ownership — See Something, Say Something

`REPO_MODE` controls how to handle issues outside your branch:
- **`solo`** — You own everything. Investigate and offer to fix proactively.
- **`collaborative`** / **`unknown`** — Flag via AskUserQuestion, don't fix (may be someone else's).

Always flag anything that looks wrong — one sentence, what you noticed and its impact.

## Search Before Building

Detail moved to `references/search-before-building.md`.

## Completion Status Protocol

When completing a skill workflow, report status using one of:
- **DONE** — completed with evidence.
- **DONE_WITH_CONCERNS** — completed, but list concerns.
- **BLOCKED** — cannot proceed; state blocker and what was tried.
- **NEEDS_CONTEXT** — missing info; state exactly what is needed.

Escalate after 3 failed attempts, uncertain security-sensitive changes, or scope you cannot verify. Format: `STATUS`, `REASON`, `ATTEMPTED`, `RECOMMENDATION`.

## Operational Self-Improvement

Detail moved to `references/operational-self-improvement.md`.

## Telemetry (run last)

Detail moved to `references/telemetry-run-last.md`.

## Plan Status Footer

Skills that run plan reviews (`/plan-*-review`, `/codex review`) include the EXIT PLAN MODE GATE blocking checklist at the end of the skill, which verifies the plan file ends with `## GSTACK REVIEW REPORT` before ExitPlanMode is called. Skills that don't run plan reviews (operational skills like `/ship`, `/qa`, `/review`) typically don't operate in plan mode and have no review report to verify; this footer is a no-op for them. Writing the plan file is the one edit allowed in plan mode.

## Third-Party Web Actions

Detail moved to `references/third-party-web-actions.md`.

## BROWSER SETUP (Aside — run this check BEFORE any browser step)

Detail moved to `references/browser-setup-aside-run-this-check-before-any-browser-step.md`.

## Browser fallback: gstack's own headless browser

Detail moved to `references/browser-fallback-gstack-s-own-headless-browser.md`.

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

**If the platform detected above is GitLab or unknown:** STOP with: "GitLab support for /land-and-deploy is not yet implemented. Run `/ship` to create the MR, then merge manually via the GitLab web UI." Do not proceed.

# /land-and-deploy — Merge, Deploy, Verify

As **Release Engineer**, pick up the PR created by `/ship`: check readiness, merge
with approval, monitor deployment, verify production, and report evidence.

## User-invocable
When the user types `/land-and-deploy`, run this skill.

## Arguments
- `/land-and-deploy` — auto-detect PR from current branch, no post-deploy URL
- `/land-and-deploy <url>` — auto-detect PR, verify deploy at this URL
- `/land-and-deploy #123` — specific PR number
- `/land-and-deploy #123 <url>` — specific PR + verification URL

## Automation and approval

Automate read-only detection and polling. First-run setup confirmation (Step 1.5)
and pre-merge approval (Step 3.5) are mandatory when applicable. Stop on missing
access, unknown target/state, failing required CI, conflicts, or failing tests.
After any merge error, read server state before deciding whether to stop.
Failures, timeouts, staging choices, rollback, and optional cleanup use the explicit
decisions below; no approval overrides a blocker or authorizes a different revision.

## Voice & Tone

Narrate progress, name the actual app/PR and explain the stakes before asking.
First run: teach what each check does. Confirmed runs: brief status updates.

---

## Section index — Read each section when its situation applies

Detail moved to `references/section-index-read-each-section-when-its-situation-applies.md`.

## Step 1: Pre-flight

Tell the user: "Checking access and finding your PR."

1. Check GitHub CLI authentication:
```bash
gh auth status
```
If unauthenticated, **STOP**; ask the user to run `gh auth login`, then retry.

2. Save any URL as `VERIFY_URL` (an explicit verification request). Set `PR_NUMBER`
to the numeric `#NNN` argument, or detect it once from the current branch:
```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner) || exit 1
if [ -z "$PR_NUMBER" ]; then
  PR_NUMBER=$(gh pr view --repo "$REPO" --json number -q .number) || exit 1
fi
PR_JSON=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json number,state,title,url,mergeable,baseRefName,headRefName,headRefOid,baseRefOid) || exit 1
PR_HEAD=$(printf '%s' "$PR_JSON" | jq -er .headRefOid) || exit 1
HEAD_BRANCH=$(printf '%s' "$PR_JSON" | jq -er .headRefName) || exit 1
BASE_BRANCH=$(printf '%s' "$PR_JSON" | jq -er .baseRefName) || exit 1
```
Carry these values across fresh shells. Every later command targets this repository
and PR, never implicit current-branch detection. A failed query is unknown, not an
empty PR. Tell the user the selected number, title, head → base and head SHA.

3. No PR: **STOP**, suggest `/ship`. CLOSED: **STOP**, ask to reopen it. MERGED:
**STOP**, suggest `/canary <url>`; do not merge again or claim a deploy happened.
Only OPEN continues. Before any HEAD-based evidence, require the matching clean checkout:
```bash
LOCAL_HEAD=$(git rev-parse HEAD) || exit 1
LOCAL_BRANCH=$(git branch --show-current) || exit 1
LOCAL_STATUS=$(git status --porcelain) || exit 1
if [ "$LOCAL_HEAD" != "$PR_HEAD" ] || [ "$LOCAL_BRANCH" != "$HEAD_BRANCH" ] || [ -n "$LOCAL_STATUS" ]; then
  echo "LOCAL_TARGET_MISMATCH"
  exit 1
fi
git fetch "https://github.com/$REPO.git" "$BASE_BRANCH" || exit 1
BASE_SHA=$(git rev-parse FETCH_HEAD) || exit 1
SCOPE_RESULT=$(~/<agent-config-dir>/gstack/bin/gstack-diff-scope "$BASE_SHA") || exit 1
eval "$SCOPE_RESULT"
```
On mismatch, **STOP** and ask the user to save their work, check out/update the PR
branch, and rerun. Do not switch, reset, or stash for them. Preserve `BASE_SHA`, the
PR's commit list and all scope flags before merging; cleanup may change HEAD afterward.
Unknown scope is not docs-only. `DOCS_ONLY=true` requires SCOPE_DOCS and no other scope.

---

## Step 1.5: First-run dry-run validation

Check for prior setup confirmation and changed configuration (not proof of a successful deploy):

```bash
eval "$(~/<agent-config-dir>/gstack/bin/gstack-slug 2>/dev/null)"
if [ ! -f ~/.gstack/projects/$SLUG/land-deploy-confirmed ]; then
  echo "FIRST_RUN"
else
  # Check if deploy config has changed since confirmation
  SAVED_HASH=$(cat ~/.gstack/projects/$SLUG/land-deploy-confirmed 2>/dev/null)
  CURRENT_HASH=$(sed -n '/## Deploy Configuration/,/^## /p' <agent-instructions> 2>/dev/null | shasum -a 256 | cut -d' ' -f1)
  # Also hash workflow files that affect deploy behavior
  WORKFLOW_HASH=$(find .github/workflows -maxdepth 1 \( -name '*deploy*' -o -name '*cd*' \) 2>/dev/null | xargs cat 2>/dev/null | shasum -a 256 | cut -d' ' -f1)
  COMBINED_HASH="${CURRENT_HASH}-${WORKFLOW_HASH}"
  if [ "$SAVED_HASH" != "$COMBINED_HASH" ] && [ -n "$SAVED_HASH" ]; then
    echo "CONFIG_CHANGED"
  else
    echo "CONFIRMED"
  fi
fi
```

**If CONFIRMED:** Say "Setup was previously confirmed." Go to Step 2; do NOT read the dry-run section.

**If FIRST_RUN or CONFIG_CHANGED:** Read and execute the dry-run section:

> **STOP.** Before running the first-run dry-run validation — Step 1.5's check returned FIRST_RUN or CONFIG_CHANGED (skip on CONFIRMED), Read `~/<agent-config-dir>/gstack/land-and-deploy/sections/first-run-validation.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

Choice A saves the fingerprint and continues to Step 2; B/C stop.

---

## Step 2: Pre-merge checks

Tell the user: "Checking CI status and merge readiness..."

```bash
gh pr checks "$PR_NUMBER" --repo "$REPO" --required --json name,state,bucket,link
```

Parse valid JSON using `bucket` (pass/fail/pending/skipping/cancel). Exit 8 means
pending; a nonzero exit with valid failing checks is a CI failure. Auth/network/schema
errors are **STOP**, never "no required checks". An empty successful result or the
CLI's explicit "no required checks reported" response means none are configured.
1. Required checks **FAILING/cancelled**: **STOP**, list failures to fix.
2. Required checks **PENDING**: announce the wait and proceed to Step 3.
3. All pass (or none required): report that exact result. Skip only Step 3's wait;
   continue to Step 3.4, then Step 3.5 before merging.

Also check for merge conflicts:
```bash
gh pr view "$PR_NUMBER" --repo "$REPO" --json mergeable -q .mergeable
```
If `CONFLICTING`: **STOP**, resolve conflicts first. Failed/UNKNOWN readback: **STOP**,
readiness is not established. Cancelled required checks are failures, not passes.

---

## Step 3: Wait for CI (if pending)

If required checks are still pending, wait for them to complete. Use a timeout of 15 minutes:

```bash
gh pr checks "$PR_NUMBER" --repo "$REPO" --required --watch --fail-fast --interval 30
```

Record the CI wait time for the deploy report.

Pass: report duration and continue to Step 3.4, then Step 3.5 before merging.
Failure: **STOP**, show failing checks. Timeout (15 minutes): **STOP**, point to
GitHub Actions. Enforce the deadline; do not leave an unbounded watch running.

---

## Step 3.4: VERSION drift detection (workspace-aware ship)

Check that another workspace has not claimed this PR's VERSION since `/ship`.

```bash
BRANCH_VERSION=$(git show "$PR_HEAD:VERSION" 2>/dev/null | tr -d '\r\n[:space:]')
BASE_VERSION=$(git show "$BASE_SHA:VERSION" 2>/dev/null | tr -d '\r\n[:space:]')
QUEUE_JSON=$(bun run ~/<agent-config-dir>/gstack/bin/gstack-next-version \
  --base "$BASE_BRANCH" \
  --exclude-pr "$PR_NUMBER" \
  --bump patch \
  --current-version "$BASE_VERSION" 2>/dev/null || echo '{"offline":true}')
NEXT_SLOT=$(echo "$QUEUE_JSON" | jq -r '.version // empty')
OFFLINE=$(echo "$QUEUE_JSON" | jq -r '.offline // false')
```

Use the existing conservative patch-level allocation; compare numeric version
components, not lexical strings. If this project has no VERSION, report this check
not applicable. A missing/unparseable version on only one side is unavailable, not green.

1. `OFFLINE=true`, helper failure or invalid result: report VERSION check unavailable
   with the reason; continue to Step 3.5. CI's version gate is the backstop.
2. `BRANCH_VERSION >= NEXT_SLOT`: no drift; continue.
3. `BRANCH_VERSION < NEXT_SLOT`: **STOP** with "VERSION drift detected", both versions
   and instructions to rerun `/ship` from the feature branch. Its ALREADY_BUMPED path
   reconciles VERSION, package.json, CHANGELOG header and PR title together. Do NOT
   auto-bump or merge here: duplicate versions can overwrite another branch's release notes.

---

> **STOP.** Before the pre-merge readiness gate (Step 3.5) — the last check before the irreversible merge, Read `~/<agent-config-dir>/gstack/land-and-deploy/sections/readiness-gate.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

---

> **STOP.** Before merging the PR and detecting the deploy strategy (Steps 4-5), Read `~/<agent-config-dir>/gstack/land-and-deploy/sections/merge-and-deploy.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

---

## Step 6: Wait for deploy (if applicable)

Detail moved to `references/step-6-wait-for-deploy-if-applicable.md`.

## Step 7: Canary verification (conditional depth)

Detail moved to `references/step-7-canary-verification-conditional-depth.md`.

## Step 8: Revert (if needed)

Detail moved to `references/step-8-revert-if-needed.md`.

## Step 9: Deploy report

Detail moved to `references/step-9-deploy-report.md`.

## Step 10: Suggest follow-ups

Detail moved to `references/step-10-suggest-follow-ups.md`.

## Section self-check (before you finish)

You ran a carved skill. For your situation, list every section the Section index
named as applying, and confirm you issued a Read for each one (a CONFIRMED Step 1.5
correctly skips the dry-run section). Missing Read: STOP and read the source now.
Recheck read-only evidence; never redo a merge/deploy because a section was missed.

---

## Important Rules

- Never force-push, bypass CI, replay a confirmed merge, or hide missing evidence.
- Auto-detect facts; ask when unknown or when an explicit approval gate applies.
- Poll at 30-second intervals with the stated deadlines and progress messages.
- After merge failures, offer approved rollback when appropriate; never revert a rollback automatically.
- Verify once; `/canary` provides extended monitoring. Rechecks require the user's choice.
- Use `--delete-branch`; reconcile failed cleanup non-destructively with confirmation.

## Runtime notes

Detail moved to `references/runtime-notes.md`.


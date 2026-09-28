---
name: ship
preamble-tier: 4
version: 1.0.0
description: "Ship workflow: detect + merge base branch, run tests, review diff, bump VERSION, update CHANGELOG, commit, push, create PR. Requires the bundled agent runtime."
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Agent
  - AskUserQuestion
  - WebSearch
triggers:
  - ship it
  - create a pr
  - push to main
  - deploy this
---
<!-- AUTO-GENERATED from SKILL.md.tmpl — do not edit directly -->
<!-- Regenerate: bun run gen:skill-docs -->


## When to invoke this skill

Use when asked to "ship", "deploy",
"push to main", "create a PR", "merge and push", or "get it deployed".
Proactively invoke this skill (do NOT push/PR directly) when the user says code
is ready, asks about deploying, wants to push code up, or asks to create a PR.

## Preamble (run first)

Detail moved to `references/preamble-run-first.md`.

## Plan Mode Safe Operations

In plan mode, allowed because they inform the plan: `$B`, `$D`, `codex exec`/`codex review`, temp prompts, writes to `~/.gstack/`, writes to the plan file, and `open` for generated artifacts.

## Skill Invocation During Plan Mode

If the user invokes a skill in plan mode, the skill takes precedence over generic plan mode behavior. **Treat the skill file as executable instructions, not reference.** Follow it step by step starting from Step 0; any AskUserQuestion the skill fires is the workflow operating within plan mode, not a violation of it — and a skill whose instructions resolve a question themselves (e.g. a plan-mode auto-select) may legitimately not ask it. AskUserQuestion (any variant — `mcp__*__AskUserQuestion` or native; see "AskUserQuestion Format → Tool resolution") satisfies plan mode's end-of-turn requirement. If AskUserQuestion is unavailable or a call fails, follow the AskUserQuestion Format failure fallback: `headless` → BLOCKED; `interactive` → the prose fallback (also satisfies end-of-turn). At a STOP point, stop immediately. Do not continue the workflow or call ExitPlanMode there. Commands marked "PLAN MODE EXCEPTION — ALWAYS RUN" execute. Call ExitPlanMode only after the skill workflow completes, or if the user tells you to cancel the skill or leave plan mode.

If `PROACTIVE` is `"false"`, do not auto-invoke or proactively suggest skills. If a skill seems useful, ask: "I think /skillname might help here — want me to run it?"

If `SKILL_PREFIX` is `"true"`, suggest/invoke `/gstack-*` names. Disk paths stay `~/.claude/skills/gstack/[skill-name]/SKILL.md`.

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

## Section index — Read each section when its situation applies

Detail moved to `references/section-index-read-each-section-when-its-situation-applies.md`.

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

`<base>` means the detected branch name for fetch/helper arguments;
`origin/<base>` is its remote-tracking ref for comparisons. Step 1 fetches it.



## Step 0.9: Apple target detection

If the repo has an `.xcodeproj`, `.xcworkspace`, or Swift app package AND the ask
is App Store/TestFlight distribution, **STOP and Read
`~/.claude/skills/gstack/ship/sections/apple-release.md` FIRST**. Store distribution proceeds
through that adapter from the current branch, including a clean base branch.
The branch gate and repository-landing pipeline below apply ONLY to
repository-landing asks, including on Apple repos.

## Step 1: Pre-flight

1. Check the current branch. If on the base branch or the repo's default branch, **abort**: "You're on the base branch. Ship from a feature branch."

2. Run `git status` (never use `-uall`). Uncommitted changes are always included — no need to ask.

3. Run `git fetch origin <base>` before inspecting the diff. If fetch fails, STOP:
   report the error and restore access before continuing. Then inspect
   `git diff origin/<base> --stat`, untracked files from status, and
   `git log origin/<base>..HEAD --oneline`.

4. Display historical review readiness. This preflight snapshot does not replace
   Step 9's mandatory review or its blocker, ASK, and convergence gates — even
   when prior reviews are CLEAR or the dashboard's global skip is enabled.

## Review Readiness Dashboard

Detail moved to `references/review-readiness-dashboard.md`.

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

## Step 3: Merge the base branch (BEFORE tests)

Merge the base ref fetched in Step 1 so tests and reviews cover the integrated code:

```bash
git merge origin/<base> --no-edit
```

**If there are merge conflicts:** Try to auto-resolve if they are simple (VERSION, schema.rb, CHANGELOG ordering). If conflicts are complex or ambiguous, **STOP** and show them.

**If already up to date:** Continue silently.

---

> **STOP.** Before running the test suites and (if prompt files changed) the eval suites (Steps 4-6), Read `~/.claude/skills/gstack/ship/sections/tests.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

> **STOP.** Before auditing test coverage of the diff (Step 7), Read `~/.claude/skills/gstack/ship/sections/test-coverage.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

> **STOP.** Before auditing plan completion, verification, and scope drift (Step 8), Read `~/.claude/skills/gstack/ship/sections/plan-completion.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

> **STOP.** Before the pre-landing review and specialist dispatch (Step 9), Read `~/.claude/skills/gstack/ship/sections/review-army.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

> **STOP.** Before addressing Greptile review comments when a PR exists (Step 10), Read `~/.claude/skills/gstack/ship/sections/greptile.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

> **STOP.** Before the adversarial review and learnings capture (Step 11), Read `~/.claude/skills/gstack/ship/sections/adversarial.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

## Step 12: Version bump (auto-decide)

Use **`gstack-version-bump`** for classify/write/repair and `gstack-next-version`
for slot selection. Bump level and queue collisions remain agent decisions.

1. **Classify state** — pure reader, never writes:
   ```bash
   bun run ~/.claude/skills/gstack/bin/gstack-version-bump classify --base <base>
   ```
   Save the JSON `baseVersion` as `BASE_VERSION`, then read `state` and dispatch:
   - **FRESH** → do the bump (steps 2-4).
   - **ALREADY_BUMPED** → keep `NEW_VERSION` at `currentVersion`. Reuse this branch's earlier ship decision for `BUMP_LEVEL` if recorded; otherwise compare `baseVersion` and `currentVersion` left to right: the first changed major/minor/patch/micro component supplies `BUMP_LEVEL` (a missing fourth component is zero). Then run step 3's queue check. This recovers the level, not permission to bump again.
   - **DRIFT_STALE_PKG** → run `gstack-version-bump repair`, then reclassify. On success, follow **ALREADY_BUMPED**, including its queue check; on failure, STOP. Repair alone never re-bumps.
   - **DRIFT_UNEXPECTED** → **STOP**. package.json disagrees with VERSION while VERSION matches base — a manual edit bypassed /ship. Reconcile manually, then re-run.

2. **Decide the bump level** from the diff (agent judgment):
   - **MICRO**: <50 lines, trivial tweaks/config. **PATCH**: 50+ lines, no feature signals.
   - **MINOR**: AskUserQuestion for any feature signal (new route/page, migration, new module), OR 500+ lines. **MAJOR**: AskUserQuestion for milestones or breaking changes. Offer the recommended level with rationale, a smaller level, or cancel; wait for the answer. Cancel ends this ship attempt before release writes or push; preserve existing work.
   Save `BUMP_LEVEL` as lowercase `micro`, `patch`, `minor`, or `major`. Queue placement may advance the slot without changing the intended level.

3. **Queue-aware pick** (workspace-aware ship):
   ```bash
   QUEUE_JSON=$(bun run ~/.claude/skills/gstack/bin/gstack-next-version --base <base> --bump "$BUMP_LEVEL" --current-version "$BASE_VERSION" 2>/dev/null || echo '{"offline":true}')
   CANDIDATE_VERSION=$(echo "$QUEUE_JSON" | jq -r '.version // empty')
   ```
   - **Usable candidate** (including `offline:true` with `fallback:"git"`): print warnings and any claimed queue. FRESH sets `NEW_VERSION` to `CANDIDATE_VERSION`. ALREADY_BUMPED compares it with `currentVersion`; if different, ask to rebump (refresh CHANGELOG/PR title) or keep current (CI rejects a collision). Only approval changes the existing version. An active sibling is a workspace listed in JSON `active_siblings`; use its `branch` and `version`. If one holds `>= NEW_VERSION`, ask to advance past it or stop this attempt and sync.
   - **No usable candidate** (utility failure or empty result): print queue-unverified; FRESH sets `NEW_VERSION` using local `BUMP_LEVEL` arithmetic, while ALREADY_BUMPED keeps `currentVersion`. Do not follow the usable-candidate instructions above.

4. **Write the bump** (FRESH, or an approved rebump):
   ```bash
   bun run ~/.claude/skills/gstack/bin/gstack-version-bump write --version "$NEW_VERSION" --regen-digest
   ```
   The CLI validates 4-digit `MAJOR.MINOR.PATCH.MICRO` (or 3-digit pinned semver), then writes VERSION, the manifest, and existing `package-lock.json` / `npm-shrinkwrap.json` files; it never creates lockfiles. Manifest resolution: `--package-json-path` → `.gstack/package-json-path` (supports subdirectory packages). npm manifests/locks use the 3-digit translation (`1.67.0.0` → `1.67.0`); VERSION remains authoritative. Exit 3 means a half-write: reclassify and use `repair` for DRIFT_STALE_PKG.

   `--regen-digest` executes repo code with the same privileges as Step 5: `scripts/gen-agents-digest.ts`, only when it and committed `agents-digest/gstack-AGENTS.md` both exist. Check `agentsDigest`: if false, run `bun scripts/gen-agents-digest.ts` and stage the digest with the bump before continuing. Its VERSION stamp is freshness-gated.

5. **Record the release decision** (skip if ALREADY_BUMPED):
   ```bash
   ~/.claude/skills/gstack/bin/gstack-decision-log '{"decision":"Ship NEW_VERSION (BUMP_LEVEL)","rationale":"WHY","scope":"repo","source":"skill","confidence":9}' 2>/dev/null || true
   ```
   Substitute `NEW_VERSION`, `BUMP_LEVEL`, and one-line `WHY` (scope or breaking-change signal). Best-effort, non-interactive, non-blocking.

> **STOP.** Before writing the CHANGELOG entry (Step 13), Read `~/.claude/skills/gstack/ship/sections/changelog.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

## Step 14: TODOS.md (auto-update)

Persist approved follow-ups, then conservatively mark completed work.

Read `~/.claude/skills/gstack/review/TODOS-format.md` for the canonical format reference (or `review/TODOS-format.md` in a gstack checkout).

**1. Open or create:** Read root `TODOS.md`. An earlier explicit "add a follow-up" choice authorizes its creation with `# TODOS` and `## Completed`. Otherwise, if missing, ask: "Create a component/priority-organized TODOS.md?" Options: A) Create now, B) Skip. If B, continue to Step 15 with the outcome in the summary below.

**2. Organization:** Expect component headings, `**Priority:**` P0–P4 fields, and `## Completed` at the bottom. If disorganized, ask: A) Reorganize (recommended), B) Leave as-is. A preserves all content; B continues without restructuring.

**3. Add approved deferrals:**
- Step 2: add the approved distribution follow-up as P1 with the missing pipeline and affected artifact.
- Step 8: add each approved P1 plan deferral with `Deferred from plan: {plan file path}` and the missing work.
- Step 5: retain P0 test-failure entries already written; deduplicate by failure and source, adding missing approved entries with error output and branch.
Never turn dropped scope into TODOs or invent unapproved follow-ups. Reuse matching existing entries rather than duplicating them.

**4. Detect completed TODOs:** Match titles, files, and behavior against `git diff origin/<base>`, untracked files from status, and `git log origin/<base>..HEAD --oneline`. Only clear evidence earns completion; leave uncertain items open. Move completed items to `## Completed` and append `**Completed:** vX.Y.Z (YYYY-MM-DD)`.

**5. Save the summary:** Report added/deferred items, items marked complete, remaining count, and any creation/reorganization. If creation was declined or a write fails, warn and retain the unpersisted follow-ups in the Step 19 PR summary; never claim they were saved. A TODO write failure remains non-blocking.

---

## Step 15: Commit (bisectable chunks)

Create small, logical commits for `git bisect`. If all changes are already committed, continue to Step 16; never create an empty commit.

1. Group by coherent change. Keep each model/service/controller with its tests;
   keep controller views together. Migrations may stand alone or accompany their
   model; config/routes may accompany the feature they enable. A diff under
   50 lines across fewer than 4 files may use one commit.
2. Order dependencies first: infrastructure → models/services → controllers/views.
   Each commit must work independently, without broken imports or missing code.
   VERSION + CHANGELOG + TODOS.md belong in the final commit.
3. Use `<type>: <summary>` (feat/fix/chore/refactor/docs) and a brief body.
   Only the final VERSION/CHANGELOG commit gets the version tag and co-author trailer:

```bash
git commit -m "$(cat <<'EOF'
chore: bump version and changelog (vX.Y.Z.W)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Step 16: Verification Gate

**IRON LAW: NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.**

Find generation/build commands in CLAUDE.md/AGENTS.md, package scripts, and build
configuration; run them first, skipping only when none are defined. A failed build blocks push. If it changes tracked files, inspect the
changes, run affected checks from Steps 6–11, refresh release facts, and commit
under Step 15 before returning here. Reuse unchanged results and actual approvals.

Then check test evidence against the final content:

```bash
~/.claude/skills/gstack/bin/gstack-evidence check --label tests --expect-cmd '<exact tests-lane command from Step 5>' --label vitest --expect-cmd '<exact vitest-lane command from Step 5>' --max-age 24 --allow-paths CHANGELOG.md,VERSION,package.json,agents-digest/gstack-AGENTS.md
```

Use only Step 5's actual lane labels and exact commands; `vitest` is an example.
If Step 4 explicitly declined testing and no lanes exist, report that gap instead
of inventing FRESH evidence. Build verification still applies.

The allow-list covers release bookkeeping, including Step 12's package/digest
version stamps. Behavioral package.json edits still require live tests despite
the path exemption. Do not add `TODOS.md` or generated tests to the allow-list:
Step 7 tests, review fixes, and Step 14 TODOS edits intentionally make evidence STALE.

- **Every line FRESH (exit 0):** recorded runs passed on identical content except
  the listed release files. Cite label, exit, timestamp, and log path; continue.
- **Any STALE/MISSING (exit non-zero):** inspect the reason before choosing recovery:
  - **Content, command or age mismatch, or no passing live evidence:** rerun the
    affected lanes on final content, wrapped as `~/.claude/skills/gstack/bin/gstack-evidence run --label <lane> -- '<command>'`.
    Read results and recheck once. TODOS edits and generated tests are content
    changes, not ledger-only bookkeeping.
  - **Ledger read/write failure only:** if a successful live run already covers
    the unchanged final content, exact command and permitted age, cite its exit,
    timestamp and log directly. Report ledger unavailable and continue, never
    ledger FRESH. Do not rerun green suites solely because the ledger cannot save
    or read its record. If unchanged content cannot be confirmed, STOP.

A failed CHECK identifies evidence to repair; it is not a test failure. The
required live RUN must pass, except for the explicit triage waiver below.

Paste build and rerun results. Later code, test, or build-input changes return
through this gate before pushing. Step 18 owns validation of its post-push
docs-only edits; follow repository-required checks there too. Do not claim an
earlier test run covered changed inputs.

**If tests fail here:** apply Step 5's triage. A prior explicit waiver remains valid
only for the same verified pre-existing failures and approved scope; cite that
approval and actual failing counts, never FRESH or all-green evidence. New,
changed, or unwaived failures STOP publication and return to Step 5.

Claiming work is complete without verification is dishonesty, not efficiency.

---

## Step 17: Push

Detail moved to `references/step-17-push.md`.

## Step 20: Persist ship metrics

Detail moved to `references/step-20-persist-ship-metrics.md`.

## Step 21: Plan-tune discoverability nudge (first-successful-ship only)

Detail moved to `references/step-21-plan-tune-discoverability-nudge-first-successful-ship-only.md`.

## Section self-check (before you finish)

You ran a carved skill. For your situation, list every section the Section index
named as applying, and confirm you issued a Read for each one. If you executed any
of those steps from memory without reading its section, you skipped the source of
truth — STOP, Read it now, and redo that step. Deterministic version work goes
through `gstack-version-bump`; never hand-roll the VERSION/package.json write.

---

## Important Rules

Detail moved to `references/important-rules.md`.


---
name: plan-ceo-review
preamble-tier: 3
version: 1.0.0
description: CEO/founder-mode plan review.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - AskUserQuestion
  - WebSearch
triggers:
  - think bigger
  - expand scope
  - strategy review
  - rethink this plan
gbrain:
  schema: 1
  context_queries:
    - id: prior-ceo-plans
      kind: filesystem
      glob: "{gstack_state_root}/projects/{repo_slug}/ceo-plans/*.md"
      sort: mtime_desc
      limit: 5
      render_as: "## Prior CEO plans for this project"
    - id: recent-design-docs
      kind: filesystem
      glob: "~/.gstack/projects/{repo_slug}/*-design-*.md"
      sort: mtime_desc
      limit: 3
      render_as: "## Recent design docs for this project"
    - id: recent-reviews
      kind: list
      filter:
        type: timeline
        tags_contains: "repo:{repo_slug}"
        content_contains: "plan-ceo-review"
      sort: updated_at_desc
      limit: 5
      render_as: "## Recent CEO review activity"
neutralised: tool-specific paths and single-runtime invocations replaced
---
<!-- AUTO-GENERATED from SKILL.md.tmpl — do not edit directly -->
<!-- Regenerate: bun run gen:skill-docs -->


## When to invoke this skill

Rethink the problem, find the 10-star product,
challenge premises, expand scope when it creates a better product. Four modes:
SCOPE EXPANSION (dream big), SELECTIVE EXPANSION (hold scope + cherry-pick
expansions), HOLD SCOPE (maximum rigor), SCOPE REDUCTION (strip to essentials).
Use when asked to "think bigger", "expand scope", "strategy review", "rethink this",
or "is this ambitious enough".
Proactively suggest when the user is questioning scope or ambition of a plan,
or when the plan feels like it could be thinking bigger.

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

# Mega Plan Review Mode

## Philosophy
Make this plan extraordinary. Match posture:
* SCOPE EXPANSION: Build the platonic ideal, 10x better for 2x effort. Recommend expansions enthusiastically.
* SELECTIVE EXPANSION: Harden current scope; neutrally offer each expansion's opportunity, effort and risk. Accepted items govern later sections; rejected ones go to "NOT in scope."
* HOLD SCOPE: Preserve scope; trace failures, edge cases, error paths, tests and observability.
* SCOPE REDUCTION: Propose the minimum viable core; cut only with approval.
* COMPLETENESS IS CHEAP: AI makes 70 LOC seconds. Prefer complete ~150 LOC over 90% ~80 LOC. Boil the ocean.
Approval is required for each scope change. Raise concerns in Step 0, then commit: no arguing for less in EXPANSION, silent SELECTIVE additions/cuts, or scope restored to REDUCTION.
Review only. Do not change code or implement.

## Prime Directives
1. Zero silent failures: surface every failure to system, team and user.
2. Name each error's class, trigger, handler, user result and test; flag catch-alls.
3. Trace happy, nil, empty/zero and upstream-error paths.
4. Map double-clicks, navigation, slow links, stale state and back button.
5. Dashboards, alerts and runbooks are launch scope.
6. Require ASCII diagrams for new flows, state, pipelines, deps and decisions.
7. Record every deferral in TODOS.md or chat per storage policy.
8. Optimize for the 6-month future; flag future harm.
9. Propose better approaches now, including "scrap it and do this instead."

## Engineering Preferences (use these to guide every recommendation)
* DRY: flag repetition aggressively.
* Tests are required; prefer too many to too few.
* Avoid fragile hacks, premature abstractions and unnecessary complexity.
* Favor more edge cases and thoughtfulness over speed; explicit over clever.
* Prefer the smallest clear diff; broken foundations may need a rewrite under directive #9.
* New codepaths need logs, metrics or traces and threat modeling.
* Plan partial deploys, rollbacks and feature flags.
* Add and maintain ASCII comments for complex state, pipelines, requests, mixins and test setup.

## Priority Hierarchy Under Context Pressure
Step 0 > System audit > Error/rescue map > Test diagram > Failure modes > Opinionated recommendations > Everything else.
Never skip Step 0, system audit, error/rescue map or failure modes.

## Web research runs in Aside

Detail moved to `references/web-research-runs-in-aside.md`.

## PRE-REVIEW SYSTEM AUDIT (before Step 0)

Detail moved to `references/pre-review-system-audit-before-step-0.md`.

## Prerequisite Skill Offer

Detail moved to `references/prerequisite-skill-offer.md`.

## Prior Learnings

Detail moved to `references/prior-learnings.md`.

## Brain Context (preflight)

Detail moved to `references/brain-context-preflight.md`.

## Section index — Read each section when its situation applies

This skill is a decision-tree skeleton. The steps below point to on-demand
sections. Read a section in full before doing its step; do not work from memory.

| When | Read this section |
|------|-------------------|
| running the 11-section deep review, required outputs, and review report (only after Step 0 scope and mode are agreed) | `sections/review-sections.md` |

## Step 0: Nuclear Scope Challenge + Mode Selection

Detail moved to `references/step-0-nuclear-scope-challenge-mode-selection.md`.

## Continue after Step 0 (all modes)

> **STOP.** Before running the 11-section deep review, required outputs, and review report (only after Step 0 scope and mode are agreed), Read `~/<agent-config-dir>/gstack/plan-ceo-review/sections/review-sections.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

## Section self-check (before you finish)

Confirm you Read `sections/review-sections.md` and executed Sections 1–10,
Section 11's findings or no-UI skip, required outputs and report from that file.
If the Summary or report preceded that Read, stop, Read and redo the review.

## EXIT PLAN MODE GATE (BLOCKING)

Detail moved to `references/exit-plan-mode-gate-blocking.md`.

## Brain Cache Background Refresh

Detail moved to `references/brain-cache-background-refresh.md`.

## Runtime notes

Detail moved to `references/runtime-notes.md`.


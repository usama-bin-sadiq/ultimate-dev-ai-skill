<!-- Moved verbatim from context-restore/SKILL.md, the
     'plan-status-footer' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Plan Status Footer

Skills that run plan reviews (`/plan-*-review`, `/codex review`) include the EXIT PLAN MODE GATE blocking checklist at the end of the skill, which verifies the plan file ends with `## GSTACK REVIEW REPORT` before ExitPlanMode is called. Skills that don't run plan reviews (operational skills like `/ship`, `/qa`, `/review`) typically don't operate in plan mode and have no review report to verify; this footer is a no-op for them. Writing the plan file is the one edit allowed in plan mode.

# /context-restore — Restore Saved Working Context

You are a **Staff Engineer reading a colleague's meticulous session notes** to
pick up exactly where they left off. Your job is to load the most recent saved
context and present it clearly so the user can resume work without losing a beat.

**HARD GATE:** Do NOT implement code changes. This skill only reads saved
context files and presents the summary.

**Default: prefer the most recent checkpoint saved on the CURRENT branch; if
this branch has none, fall back to the most recent across ALL branches.** The
fallback is for Conductor workspace handoff — a context saved on one branch can
be resumed from another. The current-branch preference exists because every
worktree of a repo shares one checkpoints directory (same origin-derived slug),
so without it `/context-restore` in one worktree could silently load a sibling
worktree's newer checkpoint.

**Do NOT hard-filter the candidate set to the current branch** — other-branch
checkpoints stay in the set as a fallback. They are just ordered *after* the
current branch's own, so a current-branch save is never shadowed by a newer
sibling-worktree save. (`/context-save list` is the flow that hard-scopes to one
branch.)

---

<!-- Moved verbatim from ship/SKILL.md, the 'Review Readiness Dashboard' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Review Readiness Dashboard

During pre-flight, read the existing review log and config to display readiness; the new pre-landing review runs in Step 9.

```bash
~/.claude/skills/gstack/bin/gstack-review-read
```

Render each record using its recorded host, source, outside_provider, outside_status, and phase. Historical source "claude" means a native Claude subagent; source "claude-code" means the external CLI. Never infer a historical provider from the current harness. Unknown model identity remains unknown. Missing/disabled/skipped outside coverage is distinct from native completion.

Parse the output. Find the most recent entry for each skill (plan-ceo-review, plan-eng-review, review, plan-design-review, design-review-lite, adversarial-review, codex-review, codex-plan-review). Ignore entries with timestamps older than 7 days. For the Eng Review row, show whichever is more recent between `review` (diff-scoped pre-landing review) and `plan-eng-review` (plan-stage architecture review). Append "(DIFF)" or "(PLAN)" to the status to distinguish. For the Adversarial row, show whichever is more recent between `adversarial-review` (new auto-scaled) and `codex-review` (legacy). For Design Review, show whichever is more recent between `plan-design-review` (full visual audit) and `design-review-lite` (code-level check). Append "(FULL)" or "(LITE)" to the status to distinguish. For the Outside Voice row, show the most recent `codex-plan-review` entry — this captures outside voices from both /plan-ceo-review and /plan-eng-review.

**Source attribution:** If the most recent entry for a skill has a \`"via"\` field, append it to the status label in parentheses. Examples: `plan-eng-review` with `via:"autoplan"` shows as "CLEAR (PLAN via /autoplan)". `review` with `via:"ship"` shows as "CLEAR (DIFF via /ship)". Entries without a `via` field show as "CLEAR (PLAN)" or "CLEAR (DIFF)" as before.

From gstack-review-read output, use entries whose skill is `autoplan-voices` or `design-outside-voices` for the coverage detail below the dashboard. Group by workflow run and phase, not merely skill. Show each phase’s recorded provider and outside_status; partial coverage must remain partial. These records do not change the engineering gate.

Display:

```
+====================================================================+
|                    REVIEW READINESS DASHBOARD                       |
+====================================================================+
| Review          | Runs | Last Run            | Status    | Required |
|-----------------|------|---------------------|-----------|----------|
| Eng Review      |  1   | 2026-03-16 15:00    | CLEAR     | YES      |
| CEO Review      |  0   | —                   | —         | no       |
| Design Review   |  0   | —                   | —         | no       |
| Adversarial     |  0   | —                   | —         | no       |
| Outside Voice   |  0   | —                   | —         | no       |
+--------------------------------------------------------------------+
| VERDICT: CLEARED — Eng Review passed                                |
+====================================================================+
```

**Review tiers:**
- **Eng Review (historical readiness):** Required for a CLEARED dashboard, not for continuing Step 1. Step 9 remains mandatory, with its finding, approval and convergence gates. The skip_eng_review setting changes this dashboard only.
- **CEO Review (optional):** Use your judgment. Recommend it for big product/business changes, new user-facing features, or scope decisions. Skip for bug fixes, refactors, infra, and cleanup.
- **Design Review (optional):** Use your judgment. Recommend it for UI/UX changes. Skip for backend-only, infra, or prompt-only changes.
- **Adversarial Review (automatic):** Always-on for every review. Every diff gets a native adversarial pass and, when enabled and available, a host-selected outside challenge. Large diffs (200+ lines) additionally get a structured outside review with P1 gate.
- **Outside Voice (default-on):** Independent plan review through the host-selected provider after /plan-ceo-review and /plan-eng-review. The codex_reviews switch disables the entire extra step. Provider failure uses the existing native fallback and reports missing outside coverage. Never gates shipping.

**Verdict logic:**
- **CLEARED**: Eng Review has >= 1 entry within 7 days from either \`review\` or \`plan-eng-review\` with status "clean"; diff review must also grade CURRENT below (or \`skip_eng_review\` is \`true\`)
- **NOT CLEARED**: Eng Review missing, stale (>7 days), or has open issues
- CEO, Design, and outside reviews are shown for context but never block shipping
- If \`skip_eng_review\` config is \`true\`, Eng Review shows "SKIPPED (global)" and verdict is CLEARED

**Staleness detection:** Grade before deciding CLEARED:
- Ship telemetry reports metrics, not review coverage; it never satisfies a review row.
- **Content-first rule (diff-scoped rows only: `review`, `adversarial-review`, `codex-review`, ship-stage entries, `design-review-lite`).** Use the helper's computed `review_freshness.status` and show its `reason`. CURRENT requires a completed clean pass with captured start/end wtree equal to the current `---WTREE---`. STALE or UNVERIFIED never clears Eng Review. Missing `review_freshness` is UNVERIFIED, including legacy log-only rows. Never fall back to HEAD equality or commit distance for diff evidence, even at 0 commits. Show recorded cycles, completed/converged state, and missing per-source/phase coverage; unknown is not a pass.
- Plan-tier rows (plan-ceo-review, plan-eng-review, plan-design-review, codex-plan-review) grade a plan file, not the repo tree — never apply the wtree rule to them; they keep the 7-day freshness logic. If an entry carries `plan_sha256`, you MAY compare it with the plan file and note "plan changed since review" on mismatch.
- Plan-tier fallback only: parse `---HEAD---`. For entries with a different `commit`, count elapsed commits: `git rev-list --count STORED_COMMIT..HEAD`. If that command FAILS, grade UNKNOWN and treat as stale. Display: "Note: {skill} review from {date} may be stale — {N} commits since review". Missing commit tracking retains the legacy note to consider re-running.
- If all reviews grade CURRENT, do not display staleness notes

If Eng Review is not CLEAR, print its actual status and reason: "Eng Review: {status} — {reason}. Ship will run its pre-landing review in Step 9." For diffs >200 lines (`git diff origin/<base> --stat | tail -1`), recommend `/plan-eng-review` or `/autoplan` for architecture review.

If CEO Review is missing, mention as informational ("CEO Review not run — recommended for product changes") but do NOT block.

For Design Review: run `source <(~/.claude/skills/gstack/bin/gstack-diff-scope <base> 2>/dev/null)`. If `SCOPE_FRONTEND=true` and no design review exists, mention: "Design Review not run — Step 9 includes the lite check; consider /design-review for a full visual audit."

Continue to Step 2 without a preflight approval question. Apply the review gates when Step 9 runs.

---

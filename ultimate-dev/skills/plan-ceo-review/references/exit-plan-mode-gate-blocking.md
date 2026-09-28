<!-- Moved verbatim from plan-ceo-review/SKILL.md, the
     'exit-plan-mode-gate-blocking' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## EXIT PLAN MODE GATE (BLOCKING)

Read-only verification: apply **Artifact outcomes**. Missing plan/report saves
and failed permitted 0H metrics block completion. Best-effort history does not;
show unsaved fields and errors.

Verify `Approval readiness: PASS` against current row IDs and answer references.
If stale because a choice changed, stop and return to 0D for that choice only;
then repeat readiness, affected outputs, report Read-back, Review Log and
dashboard before returning here.

Verify all five checks:
1. Read the plan file after your most recent write.
2. Its LAST `## ` heading is exactly `## GSTACK REVIEW REPORT`.
3. The report contains the Runs / Status / Findings table and VERDICT, with
   OUTSIDE COVERAGE / CROSS-MODEL when applicable.
4. Its final non-whitespace line is the exact unbolded `NO UNRESOLVED DECISIONS`,
   or the last bullet under `**UNRESOLVED DECISIONS:**`. A bolded sentinel,
   missing status or any trailing prose fails this check.
5. For permitted history, confirm `gstack-review-log` was attempted and
   `gstack-review-read` ran. For forbidden history, confirm no write was attempted.
   Show unsaved fields and any errors as not persisted. Never invent dashboard
   results when its read fails.

Failed checks use **Gate outcome: Blocked**. Chat or body prose cannot replace
the verified terminal report. Do not call ExitPlanMode until all checks pass.

**Gate outcome:**
- **Pass with log-only gaps:** A verified report plus forbidden metadata or
  failed best-effort history can pass. Mark unsaved fields **not persisted**.
  Failed required writes still block.
- **Blocked:** Return the failed check and complete plan, report and summary.
  Label only unwritten artifacts **not persisted**; missing logs do not unsave
  a verified report. State **completion blocked**; end without success telemetry,
  ExitPlanMode or the queued handoff. Resume when the blocker is resolved.
- **Passed with a verified persisted report:** finish the cache refresh below,
  then run telemetry as the last review operation.

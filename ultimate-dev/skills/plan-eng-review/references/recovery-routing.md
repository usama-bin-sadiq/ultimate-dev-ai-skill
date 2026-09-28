<!-- Moved verbatim from plan-eng-review/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Recovery routing

At every STOP or failed check, use this route; do not restart.

**Paused question:** Wait for its actual answer without completion telemetry or ExitPlanMode.
Resume its local procedure with the reply. A missing-result call
that may have surfaced is still pending; do not duplicate it.

**Repairable write/read failure:** Stop before the dependent question or output.
Use that step's stated recovery, then repeat its full Read-back verification.
If no recovery is specified or it fails, follow **Blocked outcome**. Never turn
a failed permitted save into a chat-only success.

**Late change or missing work:** Return to the affected review stage; new or
reopened choices use Decision procedure. Repeat Approval readiness, then Required
outputs steps 1–4 for changed outputs before choosing navigation again. Refresh
affected tests, tasks, dependencies and parallelization. Unchanged saved outputs
may reuse their successful Review Log. If a final gate discovers stale evidence,
follow **Blocked outcome** first; then resume here.

**Blocked outcome:** Stop the review and report `BLOCKED`, the missing path/work, actual attempts and what is needed to resume. Label complete chat-only output **not persisted**; it supplies no saved-review or completion credit. If startup values and a permitted telemetry command are available, run **Telemetry (run last)** once with `OUTCOME=error` and the actual `ERROR_MESSAGE`/`FAILED_STEP`. Do not call ExitPlanMode. Resume at the failed step using Recovery routing.

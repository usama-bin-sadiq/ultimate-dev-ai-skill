<!-- Moved verbatim from plan-eng-review/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# EXIT PLAN MODE GATE (BLOCKING)

Run this final verification for every review target, in every host mode. It
checks the completed work; only the later ExitPlanMode call is plan-mode-only.

Confirm Approval readiness passed for the current decisions. This is a
read-only verification, not a new approval or output-writing step. If it is
stale, report the stale verification and stop before success telemetry;
follow **Blocked outcome**. A resumed repair starts at Decision procedure for
changed choices, then Approval readiness, then repeats affected outputs,
Read-back, Review Log and dashboard.

Verify all five checks against the selected report file:
1. Read the report file after your most recent write.
2. Its LAST `## ` heading is exactly `## GSTACK REVIEW REPORT`.
3. The report table has all six columns: Review / Trigger / Why / Runs / Status /
   Findings. It includes VERDICT and, when applicable, OUTSIDE COVERAGE / CROSS-MODEL.
4. Its final non-whitespace line is the exact unbolded `NO UNRESOLVED DECISIONS`,
   or the last bullet under `**UNRESOLVED DECISIONS:**`. A bolded sentinel,
   missing status or trailing prose fails this check.
5. Confirm `gstack-review-log` was called and `gstack-review-read` ran at
   least once for the completed saved review.

Apply **Review record and write policy**: forbidden report/log persistence or
an unrecovered save cannot pass. If any check fails, follow **Blocked outcome**
without success telemetry or ExitPlanMode. Body prose cannot replace the
separate terminal structured report.

After the gate passes: **Telemetry (run last)** once with `OUTCOME=success`, then cache refresh. Make no further working-plan or approval changes between verification and exit.

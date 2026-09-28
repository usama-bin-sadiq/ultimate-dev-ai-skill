<!-- Moved verbatim from plan-design-review/SKILL.md, the
     'exit-plan-mode-gate-blocking' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## EXIT PLAN MODE GATE (BLOCKING)

Before calling ExitPlanMode, run this self-check. If any item fails, do the
missing work — do NOT call ExitPlanMode:

0. Approvals: each issue's remedy needs its own AskUserQuestion call and answer.
   Never group distinct issues. DESIGN.md tokens and navigation are not approval.
   Honor prior exact decisions and preamble-authorized per-issue auto-decisions;
   record why. Deferrals remain unresolved.
   If missing, reset drafts to pending, ask and wait. After answers or resets,
   refresh the plan and report, pass the Read-back gate, then update the review
   log and rerun this gate.

1. Read the plan file with the Read tool (after your most recent write to it).
2. Confirm the LAST `## ` heading in the file is `## GSTACK REVIEW REPORT`.
   In-body prose that mentions "outside voice", "codex findings", or similar
   does NOT count — only the structured `## GSTACK REVIEW REPORT` section
   satisfies this check.
3. Confirm the report has a Runs / Status / Findings table and a VERDICT line
   (OUTSIDE COVERAGE / CROSS-MODEL included when applicable).
4. Confirm the report's FINAL non-whitespace line is the unresolved-decisions
   status: the exact unbolded `NO UNRESOLVED DECISIONS`, or a bullet of a final
   `**UNRESOLVED DECISIONS:**` block. BLOCKING, no "if applicable" escape — a
   bolded sentinel, any trailing report field or prose, or a missing
   status each FAILS the gate.
5. If a plan file is in context for this skill invocation: confirm
   `gstack-review-log` was called and `gstack-review-read` was run at least
   once. If no plan file is in context (e.g. a diff review with no plan),
   this check short-circuits — checks 1-4 already
   short-circuit when no plan file exists.

Failing this gate and calling ExitPlanMode anyway is a contract violation —
the user will see a plan whose review report is missing or stale, and will
(correctly) reject it. Self-deception failure mode to watch for: feeling
"done" after writing review prose into the plan body. The body prose is not
the report. The report is a separate, structured, table-bearing section that
must be the file's terminal heading.

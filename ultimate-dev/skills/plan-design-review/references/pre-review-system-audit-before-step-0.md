<!-- Moved verbatim from plan-design-review/SKILL.md, the
     'pre-review-system-audit-before-step-0' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## PRE-REVIEW SYSTEM AUDIT (before Step 0)

> Before this audit, require resolved scope. For plan-mode auto-selection, verify you publicly identified the selected plan for this invocation before review work. If missing, send "Scope gate: plan mode — auto-selected B (reviewing <target>)." now; do not claim an earlier announcement.

Before reviewing the plan, gather context:

```bash
git log --oneline -15
git diff <base> --stat
```

Then read:
- The plan file (current plan or branch diff)
- CLAUDE.md — project conventions
- DESIGN.md — if it exists, ALL design decisions calibrate against it
- TODOS.md — any design-related TODOs this plan touches

Map:
* What is the UI scope of this plan? (pages, components, interactions)
* Does a DESIGN.md exist? If not, flag as a gap.
* Are there existing design patterns in the codebase to align with?
* What prior design reviews exist? (check reviews.jsonl)

### Retrospective Check
Check git log for prior design review cycles. If areas were previously flagged for design issues, be MORE aggressive reviewing them now.

### UI Scope Detection
Analyze the plan. If it involves NONE of: new UI screens/pages, changes to existing UI, user-facing interactions, frontend framework changes, or design system changes — tell the user "This plan has no UI scope. A design review isn't applicable." and exit early. Don't force design review on a backend change.

Report findings before proceeding to Step 0.

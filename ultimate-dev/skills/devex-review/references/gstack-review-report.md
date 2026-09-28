<!-- Moved verbatim from devex-review/SKILL.md, the
     'gstack-review-report' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | \`/plan-ceo-review\` | Scope & strategy | {runs} | {status} | {findings} |
| Outside Review | {recorded provider and trigger} | Independent 2nd opinion | {runs} | {outside_status} | {findings} |
| Eng Review | \`/plan-eng-review\` | Architecture & tests (required) | {runs} | {status} | {findings} |
| Design Review | \`/plan-design-review\` | UI/UX gaps | {runs} | {status} | {findings} |
| DX Review | \`/plan-devex-review\` | Developer experience gaps | {runs} | {status} | {findings} |
\`\`\`

Below the table, add these lines. **OUTSIDE COVERAGE** and **CROSS-MODEL** are conditional:
include them when the phase ran, was disabled/skipped/unavailable, or has findings;
omit them only when no such phase applies. **VERDICT** is always present:

- **OUTSIDE COVERAGE:** provider, phase, completion state, and findings. Include unavailable, disabled, and skipped phases; never infer completion from another phase.
- **CROSS-MODEL:** only when native and completed external reviews exist — overlap analysis with recorded providers and known model identity. Do not infer distinct model families from harness names.
- **VERDICT:** list reviews that are CLEAR (e.g., "CEO + ENG CLEARED — ready to implement").
  If Eng Review is not CLEAR and not skipped globally, append "eng review required".

**Unresolved-decisions status (MANDATORY — never omitted; the report's final non-whitespace
line).** After VERDICT, end the report (content under the \`## GSTACK REVIEW REPORT\`
heading — a bold label, never a new \`## \` heading; exempt from the "omit when empty"
rule) with exactly one: the exact unbolded line \`NO UNRESOLVED DECISIONS\` (a bolded one
does NOT count), OR a \`**UNRESOLVED DECISIONS:**\` header + one bullet per open item
(last bullet = final line; add \`+ N unresolved from prior reviews\` only when N > 0).
This avoids double-counting: list THIS review's open items from context; for prior reviews
sum \`unresolved\` over the latest fresh row per skill (dashboard 7-day window) after you
DROP the current skill's row; emit the sentinel only when both are zero.

### Write to the plan file

**PLAN MODE EXCEPTION — ALWAYS RUN:** This writes to the plan file, which is the one
file you are allowed to edit in plan mode. The plan file review report is part of the
plan's living status.

The report must always be the LAST section of the plan file — never mid-file.
Use a single delete-then-append flow:

1. Read the plan file (Read tool) to see its full current content. Search the read
   output for a \`## GSTACK REVIEW REPORT\` heading anywhere in the file.
2. If found, use the Edit tool to DELETE the entire existing section. Match from
   \`## GSTACK REVIEW REPORT\` through either the next \`## \` heading or end of
   file, whichever comes first. Replace with the empty string. This applies
   regardless of where the section currently lives — mid-file deletion is
   intentional, not a special case. If the Edit fails (e.g., concurrent edit
   changed the content), re-read the plan file and retry once.
3. If a report was deleted, Read the updated file. Append the new
   \`## GSTACK REVIEW REPORT\` at EOF. Use Edit to match the suffix
   confirmed by the latest Read, or Write the full file with the report last.
   "Unresolved Decisions" is not an EOF anchor when other sections follow it.
4. Verify with the Read tool that \`## GSTACK REVIEW REPORT\` is the last
   \`## \` heading in the file before continuing. If it isn't, repeat steps
   2-3 once.

Do NOT replace the section in place. The "replace mid-file" path is what allowed
prior versions to leave the report mid-file when an older report already lived
there — the user then sees a plan whose review report is not at the bottom and
(correctly) rejects it.

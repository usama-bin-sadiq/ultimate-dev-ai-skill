<!-- Moved verbatim from design-review/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Phase 10: Report

Write the report to `$REPORT_DIR` (already set up in the setup phase):

**Primary:** `$REPORT_DIR/design-audit-{domain}.md`

**Also write a summary to the project index:**
```bash
eval "$(~/.claude/skills/gstack/bin/gstack-slug 2>/dev/null)" && mkdir -p ~/.gstack/projects/$SLUG
```
Write a one-line summary to `~/.gstack/projects/{slug}/{user}-{branch}-design-audit-{datetime}.md` with a pointer to the full report in `$REPORT_DIR`.

**Per-finding additions** (beyond standard design audit report):
- Fix Status: verified / best-effort / reverted / deferred
- Commit SHA (if fixed)
- Files Changed (if fixed)
- Before/After screenshots (if fixed)

**Summary section:**
- Total findings
- Fixes applied (verified: X, best-effort: Y, reverted: Z)
- Deferred findings
- Design score delta: baseline → final
- AI slop score delta: baseline → final
- Detector: N → M (counted findings; "not installed" or "off" when it did not run)

**PR Summary:** Include a one-line summary suitable for PR descriptions:
> "Design review found N issues, fixed M. Design score X → Y, AI slop score X → Y."

---

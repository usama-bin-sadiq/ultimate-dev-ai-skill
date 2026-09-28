<!-- Moved verbatim from investigate/SKILL.md, the
     'phase-5-verification-report' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 5: Verification & Report

**Fresh verification:** Reproduce the original bug scenario and confirm it's fixed. This is not optional.

Run the test suite and paste the output.

Run the Scope Lock terminal cleanup before reporting completion or an ending error; only use this investigation's retained owner token.

Output a structured debug report:
```
DEBUG REPORT
════════════════════════════════════════
Symptom:         [what the user observed]
Root cause:      [what was actually wrong]
Fix:             [what was changed, with file:line references]
Evidence:        [test output, reproduction attempt showing fix works]
Regression test: [file:line of the new test]
Related:         [TODOS.md items, prior bugs in same area, architectural notes]
Status:          DONE | DONE_WITH_CONCERNS | BLOCKED
════════════════════════════════════════
```

Log the investigation as a learning for future sessions. Use `type: "investigation"` and include the affected files so future investigations on the same area can find this:

```bash
~/<agent-config-dir>/gstack/bin/gstack-learnings-log '{"skill":"investigate","type":"investigation","key":"ROOT_CAUSE_KEY","insight":"ROOT_CAUSE_SUMMARY","confidence":9,"source":"observed","files":["affected/file1.ts","affected/file2.ts"]}'
```

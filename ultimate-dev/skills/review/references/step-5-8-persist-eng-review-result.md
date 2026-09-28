<!-- Moved verbatim from review/SKILL.md, the 'Step 5.8: Persist Eng Review result' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 5.8: Persist Eng Review result

After all review passes complete, persist the final `/review` outcome so `/ship` can
recognize that Eng Review was run on this branch.

Follow the completion/retry and detailed record-field rules in the adversarial section before persisting.

Run:

```bash
~/<agent-config-dir>/gstack/bin/gstack-review-log '{"skill":"review","timestamp":"TIMESTAMP","status":"STATUS","issues_found":N,"critical":N,"informational":N,"quality_score":SCORE,"specialists":SPECIALISTS_JSON,"findings":FINDINGS_JSON,"commit":"COMMIT","completed":COMPLETED,"converged":CONVERGED,"cycles":CYCLES}' --finish REVIEW_START
```

Substitute:
- `TIMESTAMP` = ISO 8601 datetime
- `STATUS` = `"clean"` if there are no remaining unresolved non-advisory defects after Fix-First handling and adversarial review, otherwise `"issues_found"`. Unapproved or skipped advisories never block clean status; incomplete or nonconverged coverage remains governed by the completion rules.
- `issues_found` = total remaining unresolved non-advisory defects
- `critical` = remaining unresolved non-advisory critical defects
- `informational` = remaining unresolved non-advisory informational defects
- `quality_score` = the PR Quality Score computed in Step 4.6 (e.g., 7.5). If specialists were skipped (small diff), use `10.0`
- `COMMIT` = output of `git rev-parse --short HEAD`

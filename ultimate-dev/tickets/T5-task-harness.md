# T5: Task Harness

## Status: COMPLETE

### Experiment Results (Oct 2026)
- **rename-files**: PASS both conditions (with-skill 132s, without-skill 96s) — fixture fixed; 5 files renamed in both conditions
- **bug-diagnosis**: PASS with-skill, FAIL without-skill — genuine skill effect (48.3s → 75.3s, skill helps)
- **All 13 self-test tasks**: discriminate (PASS/FAIL verdicts)

### Active
- Re-run `rename-files` with corrected fixture — DONE
- Commit all changes on `kernel-removal` branch — DONE
- Update ticket statuses reflecting experiment results — IN PROGRESS

### Next
- T6: Composio policy review
- T7: Unshipped assets audit

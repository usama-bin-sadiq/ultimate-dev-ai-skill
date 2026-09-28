<!-- Moved verbatim from design-review/SKILL.md, the
     'phase-9-final-design-audit' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 9: Final Design Audit

After all fixes are applied:

1. Re-run the design audit on all affected pages
2. If target mockups were generated during the fix loop AND `DESIGN_READY`: run `$D verify --mockup "$REPORT_DIR/screenshots/finding-NNN-target.png" --screenshot "$REPORT_DIR/screenshots/finding-NNN-after.png"` to compare the fix result against the target. Include pass/fail in the report.
3. Compute final design score and AI slop score
4. Recompute the detector count the same way Phase 0 scanned: DOM mode re-dumps the affected pages after reload into `$REPORT_DIR/dom/$RUN_ID/` and rescans; source mode rescans the files you touched. Then delete `$REPORT_DIR/dom/$RUN_ID/` unless the user passed `--keep-dom`.
5. **If final scores are WORSE than baseline:** WARN prominently — something regressed

---

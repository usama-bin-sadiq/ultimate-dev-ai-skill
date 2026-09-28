<!-- Moved verbatim from qa/SKILL.md, the
     'output-structure' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Output Structure

```
.gstack/qa-reports/
├── qa-report-{domain}-{YYYY-MM-DD}.md    # Structured report
├── screenshots/
│   ├── initial.jpg                        # Landing page screenshot
│   ├── issue-001-step-1.jpg               # Per-issue evidence
│   ├── issue-001-result.jpg
│   ├── issue-002.png                      # Annotated screenshot (static bugs)
│   ├── issue-001-after.jpg                # After fix (if fixed); the Phase 5 evidence is the before
│   └── ...
└── baseline.json                          # For regression mode
```

Report filenames use the domain and date: `qa-report-myapp-com-2026-03-12.md`

---

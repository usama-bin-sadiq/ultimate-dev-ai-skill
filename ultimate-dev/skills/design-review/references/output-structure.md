<!-- Moved verbatim from design-review/SKILL.md, the
     'output-structure' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Output Structure

```
$GSTACK_STATE_ROOT/projects/$SLUG/designs/design-audit-{YYYYMMDD}/
├── design-audit-{domain}.md                  # Structured report
├── screenshots/
│   ├── first-impression.jpg                  # Phase 1
│   ├── {page}-annotated.png                  # Per-page annotated
│   ├── {page}-mobile.jpg                     # Responsive
│   ├── {page}-tablet.jpg
│   ├── {page}-desktop.jpg
│   ├── finding-001-before.png                # Before fix
│   ├── finding-001-target.png                # Target mockup (if generated)
│   ├── finding-001-after.png                 # After fix
│   └── ...
└── design-baseline.json                      # For regression mode
```

---

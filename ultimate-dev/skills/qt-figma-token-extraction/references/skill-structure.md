<!-- Moved verbatim from qt-figma-token-extraction/SKILL.md, the
     'skill-structure' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Skill Structure

Supporting files are loaded alongside this SKILL.md:

```
qt-figma-token-extraction/
├── SKILL.md                        # this file — entry point
├── references/
│   └── token-mapping.md            # Figma variable type → QML type mapping rules
└── examples/
    ├── Primitives.qml      # primitive color palette template
    ├── Theme.qml           # semantic token template (references Primitives)
    ├── FontInterface.qml   # font loaders + icon index template
    ├── Spacing.qml         # spacing and radii template
    └── Typography.qml      # typography scale template
```

When reaching Step 4 (type mapping), read `references/token-mapping.md` before generating any QML.
When generating QML files in Step 6, use the files in `examples/` as structural templates — they reflect the real Qt Design Studio naming and organisation patterns.

---

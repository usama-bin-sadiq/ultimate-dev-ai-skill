<!-- Moved verbatim from qt-figma-token-extraction/SKILL.md, the
     'step-8-summary' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 8 — Summary

Give the user a brief summary and ask them to review the output:

- Total tokens extracted per category (colors, spacing, typography, radii)
- Modes and themes captured
- Any unresolved aliases or unresolved token markers that need attention
- Files produced: `design-tokens.json`, `Primitives.qml`, `Theme.qml`, `Spacing.qml`, `FontInterface.qml`
- Reminder that `set_source_files_properties(... QT_QML_SINGLETON_TYPE TRUE)` must be set in CMakeLists.txt for each singleton file
- Use the **Token Categories Checklist** at the end of this file to verify nothing was missed
- Confirmation that the design system foundation is ready — the component generation skill can now begin

---

<!-- Moved verbatim from qt-figma-token-extraction/SKILL.md, the
     'step-4-map-token-types-and-apply-naming-conventions' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 4 — Map Token Types and Apply Naming Conventions

**Before generating any QML, read `references/token-mapping.md`** to determine the correct QML type for each Figma variable type (COLOR → `color`, FLOAT → `int` or `real`, STRING → `string`, etc.). Apply this mapping consistently across all generated files.

Ask the user if they have an existing naming convention. If not, use the Qt Design Studio convention below and confirm:

| Token type | Convention | Example |
|---|---|---|
| Primitive colors | `{family}_{scale}` | `neutral_900`, `neon_500` |
| Primitive groups | nested `QtObject` per family | `Primitives.neutrals.neutral_900` |
| Semantic colors | `{role}_{variant}` | `background_default`, `text_muted` |
| Semantic groups | flat on Theme singleton | `Theme.background_default` |
| Semantic variants | `_default` / `_muted` / `_subtle` | `stroke_strong`, `stroke_muted`, `stroke_subtle` |
| Notification tokens | `notification_{type}_{variant}` | `notification_alert_default`, `notification_danger_muted` |
| Spacing steps | `x{multiplier}` | `x4` (= 8 px), `x8` (= 16 px) |
| Corner radii | `radius_{size}` | `radius_s`, `radius_m`, `radius_full` |
| Font loaders | descriptive component name | `interFont`, `titilliumSemiBold`, `inconsolata` |
| Icon names | `{icon_name}_{size}` | `close_16`, `settings_fill_16` |

All names use `snake_case`. The original Figma name is always preserved in a `figmaName` field in `design-tokens.json`.

> **JSON vs QML naming:** These conventions apply to the generated QML output. `design-tokens.json` stores token keys in camelCase (e.g. `backgroundPrimary`, `cornerRadiusM`) for JSON compatibility — the conversion to snake_case happens when generating QML in Step 6.

---

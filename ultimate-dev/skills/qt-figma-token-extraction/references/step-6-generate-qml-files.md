<!-- Moved verbatim from qt-figma-token-extraction/SKILL.md, the
     'step-6-generate-qml-files' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 6 — Generate QML Files

Using the completed `design-tokens.json` as the source of truth, generate QML singleton files. Place all files in a `design-system/` folder at the root of the Qt project.

### Read the asset templates first

Before writing any QML, read the asset file that matches each output file. These are the authoritative templates — they define the exact structure, naming, grouping, and section order to follow:

| Output file | Example to read | What it shows |
|---|---|---|
| `Primitives.qml` | `examples/Primitives.qml` | Nested `QtObject` per color family, `{family}_{scale}` naming |
| `Theme.qml` | `examples/Theme.qml` | Flat semantic tokens referencing Primitives, grouped by role |
| `Spacing.qml` | `examples/Spacing.qml` | `x{n}` spacing steps, `radius_{size}` corner radii |
| `FontInterface.qml` | `examples/FontInterface.qml` | Inline `component` font loaders, `Icons` QtObject with unicode mappings |
| `Typography.qml` | `examples/Typography.qml` | Font weight constants and type scale size/weight pairs |

Read each asset file immediately before generating that file — do not rely on memory of a previously read asset.

### Folder structure

```
design-system/
├── Primitives.qml      ← raw color palette (nested by family: neutrals, accents)
├── Theme.qml           ← semantic color tokens (references Primitives)
├── Spacing.qml         ← spacing steps and corner radii
└── FontInterface.qml   ← font loaders + icon unicode index
```

Generate in this order: Primitives first (it has no dependencies), then Spacing and FontInterface (independent), then Theme last (it references Primitives).

> **No hand-written qmldir.** Module registration is handled by `qt_add_qml_module()` in CMakeLists.txt. Singleton registration uses `set_source_files_properties` — updated in Step 7.

### Generation rules

- Every value comes from `design-tokens.json` — never hardcode values not in the token file
- Use `snake_case` throughout — `background_default`, `neutral_900`, `x4`, `radius_m`
- `Primitives.qml` holds raw values only — no semantic meaning. `Theme.qml` holds semantic tokens only — always referencing `Primitives`, never raw hex values
- Apply type mapping from `references/token-mapping.md` — `readonly property color` for colors, `readonly property int` for sizes, `readonly property string` for font names
- Include the source comment and CMake note at the top of every file
- Group related properties with section comments (`// ── Section name ─────`)
- If a token is missing from the JSON, leave a `// TODO: <figmaName>` placeholder rather than guessing a value
- **Imports:** Use `import QtQuick` — `import QtQuick.Window` is redundant in Qt 6 (Window is already included) but not an error if added
- **Effects and gradients:** Use `MultiEffect` from `import QtQuick.Effects` (available from Qt 6.5). Never use `Qt5Compat.GraphicalEffects` — it requires an extra compatibility module and is not available in all Qt 6 configurations
- **QML coding skill:** If the `qt-development-skills:qt-qml` skill is available, use it when generating QML files to ensure correct Qt 6 patterns are applied

---

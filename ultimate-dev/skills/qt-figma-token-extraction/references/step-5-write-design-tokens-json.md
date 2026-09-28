<!-- Moved verbatim from qt-figma-token-extraction/SKILL.md, the
     'step-5-write-design-tokens-json' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 5 — Write design-tokens.json

Write a single merged `design-tokens.json` combining all extracted files. Primitive tokens and semantic tokens from separate Figma files are kept in distinct sections — this preserves the two-tier structure and makes it clear which layer each token belongs to. Single-mode tokens use a flat `value` field; multi-mode tokens nest values under `modes`:

```json
{
  "meta": {
    "extractedAt": "<ISO 8601 timestamp>",
    "namingConvention": "camelCase (JSON) / snake_case (QML)",
    "extractionMethod": "MCP | curl",
    "sources": [
      { "figmaFileName": "Global Tokens", "url": "<Figma URL>", "tier": "primitive" },
      { "figmaFileName": "Design Tokens", "url": "<Figma URL>", "tier": "semantic"  }
    ]
  },

  "_comment_primitives": "Raw values from the Global Tokens file — the building blocks",
  "colors": {
    "neutral000": { "value": "#ffffff", "figmaName": "Neutral/000", "type": "COLOR" },
    "neon600":    { "value": "#1f9b5d", "figmaName": "Neon/600",    "type": "COLOR" }
  },

  "_comment_semantic": "Semantic values from the Design Tokens file — reference primitives via resolvedFrom",
  "semanticColors": {
    "backgroundPrimary": {
      "figmaName": "Background/Primary", "type": "COLOR",
      "resolvedFrom": "neutral000",
      "modes": {
        "Light": { "value": "#ffffff" },
        "Dark":  { "value": "#181818" }
      }
    }
  },
  "typography": {
    "fontFamilyHeading": { "value": "Titillium Web", "figmaName": "Font/Heading", "type": "STRING" },
    "h1Size":            { "value": 36, "unit": "px", "figmaName": "H1/Size",      "type": "FLOAT" },
    "h1Weight":          { "value": 600,               "figmaName": "H1/Weight",    "type": "FLOAT" },
    "h1LineHeight":      { "value": 54, "unit": "px", "figmaName": "H1/LineHeight", "type": "FLOAT" }
  },
  "spacing": {
    "x4": { "value": 8,  "unit": "px", "figmaName": "Spacing/X4", "type": "FLOAT" },
    "x8": { "value": 16, "unit": "px", "figmaName": "Spacing/X8", "type": "FLOAT" }
  },
  "radii": {
    "cornerRadiusS":    { "value": 4,    "unit": "px", "figmaName": "Radius/Small", "type": "FLOAT" },
    "cornerRadiusFull": { "value": 9999, "unit": "px", "figmaName": "Radius/Full",  "type": "FLOAT" }
  },
  "shadows": {
    "shadowLow": {
      "offsetX": 0, "offsetY": 1, "blur": 3, "spread": 0,
      "color": "rgba(0,0,0,0.12)", "figmaName": "Shadow/Low"
    }
  }
}
```

Save to the root of the design system project folder. Confirm the path with the user.

---

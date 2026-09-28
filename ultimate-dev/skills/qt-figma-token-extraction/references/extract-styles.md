<!-- Moved verbatim from qt-figma-token-extraction/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Extract Styles

> **Note:** Figma Styles (text, color, effect) live separately from Variables and need their own extraction step. If the user's design system uses Styles as the primary token source (not Variables), this step becomes the main extraction — not a secondary one. If the design system uses both Variables and Styles, complete Step 1 first then do this step.

> **Page-by-page approach:** Figma files often spread token types across multiple pages (e.g. Colors on one page, Typography on another). Do not try to extract everything at once. Ask the user which page contains which token type, then extract one page at a time. Confirm what was found after each page before moving to the next.

### MCP method — Text Styles

Use `get_design_context` on a text frame or component that uses the design system's text styles. Ask the user to select a frame in Figma that contains representative text elements — headings, body text, labels — and read it:

```
Tool: get_design_context
Input: { "fileKey": "<key>", "nodeId": "<selected text frame node id>" }
```

From the response, extract for each text style: the style name, font family, font size, font weight, line height, and letter spacing. Work through all text roles (H1–H6, body, label, caption, code). If not all are visible in one frame, ask the user to select additional frames.

### curl method — Text Styles

Text styles require two curl calls — one to get the style list with node IDs, then one to fetch the actual property values for those nodes. The PAT from Step 1a is already verified, so proceed directly:

```bash
curl -H "X-Figma-Token: YOUR_TOKEN" "https://api.figma.com/v1/files/FILE_KEY/styles" -o text-styles-list.json
```

Then extract the `node_id` values from `text-styles-list.json`, join them with commas, and run:

```bash
curl -H "X-Figma-Token: YOUR_TOKEN" "https://api.figma.com/v1/files/FILE_KEY/nodes?ids=NODE_IDS" -o text-styles-nodes.json
```

From `text-styles-nodes.json`, extract for each text style: font family, font size, font weight, line height, letter spacing, and any text decoration or text transform applied.

Ask the user to upload or paste both files into the conversation once the commands complete.

### Merging text styles into the token file

Text styles merge into the `typography` section of `design-tokens.json`. Mark them with `"source": "textStyle"` to distinguish from variable-based typography tokens:

```json
"typography": {
  "fontFamilyHeading": { "value": "Titillium Web", "figmaName": "Font/Heading", "type": "STRING", "source": "variable" },
  "h1Size":            { "value": 36,  "unit": "px", "figmaName": "H1/Size",    "type": "FLOAT",  "source": "variable" },
  "h1":  {
    "figmaName": "Heading/H1",
    "source": "textStyle",
    "fontFamily":    "Titillium Web",
    "fontSize":      36,
    "fontWeight":    600,
    "lineHeight":    54,
    "letterSpacing": 0
  },
  "bodyDefault": {
    "figmaName": "Body/Default",
    "source": "textStyle",
    "fontFamily":    "Inter",
    "fontSize":      14,
    "fontWeight":    400,
    "lineHeight":    22,
    "letterSpacing": 0
  }
}
```

If the design system defines typography entirely through text styles (and has no typography variables), the `source: "variable"` entries won't exist — that's fine, text styles alone are sufficient.

---

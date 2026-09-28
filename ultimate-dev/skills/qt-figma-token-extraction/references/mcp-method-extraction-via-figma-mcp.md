<!-- Moved verbatim from qt-figma-token-extraction/SKILL.md, the
     'mcp-method-extraction-via-figma-mcp' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## MCP Method — Extraction via Figma MCP

*(Use when: single-mode system, or user is not comfortable with a terminal)*

**Requires:** Figma MCP connected. No personal access token or local setup needed.

**Note:** This method reads only the currently active variable mode in Figma. If the design system has multiple modes (e.g. Light/Dark) the user will need to switch modes in Figma between reads — workable but more steps. Don't mention this limitation upfront; only explain it if multiple modes are discovered during extraction.

### Step 1a — Verify Figma MCP is connected

Before doing anything else, confirm that Figma MCP tools are available. Look for tools whose names suggest variable extraction, design context reading, or file metadata — different Figma MCP servers may use different exact names (e.g. `get_variable_defs`, `getVariableDefinitions`, `figma_get_variables`). Treat the tool names in this skill as examples, not fixed contracts — match by purpose, not exact string.

If no Figma tools are available at all, tell the user:
> "The Figma MCP connector isn't connected yet. Connect it in your Claude interface (Settings → Connectors or MCP configuration), then come back and we can start."

Do not proceed until the connection is confirmed.

### Step 1b — Check for modes

Call `get_variable_defs` with the file node ID to see what collections and modes exist:

```
Tool: get_variable_defs
Input: { "nodeId": "<root node id or specific variable group node id>" }
```

If the response shows multiple modes and the user wants all of them, explain that you'll need them to switch modes in Figma between reads, and proceed.

### Step 1c — Extract variables

Call `get_variable_defs` on the relevant nodes. Work through token categories one collection at a time — colors, typography, spacing, radii, shadows. For each collection, read the active mode's values.

**If multiple modes need to be captured:**
- Extract and record all values for the current mode
- Ask the user to switch the active mode in Figma (View menu → Variable Modes, or the mode switcher on the canvas)
- Call `get_variable_defs` again and record values for the new mode
- Repeat for each mode
- Merge into a single token file with mode keys (see output format in Step 5)

### Step 1d — Resolve aliases

If any variable value references another variable (an alias), resolve it to its final value. Do not write unresolved alias references into the output file — flag any that cannot be resolved and ask the user.

---

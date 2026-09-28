<!-- Moved verbatim from qt-figma-token-extraction/SKILL.md, the
     'step-1-routing-questions' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 1 — Routing Questions

Call the **AskUserQuestion tool** for each question below — one at a time. If the AskUserQuestion tool is not available in the current interface, ask the same question as plain text and wait for the answer before continuing. Do not ask for any Figma links yet.

**Call 1 — Modes:**
```
tool: AskUserQuestion
question: "Does your Figma design system use multiple variable modes?"
options:
  - "Yes — for example Light and Dark themes"
  - "No — single mode only"
  - "I'm not sure"
```

Wait for the answer, then ask:

**Call 2 — Terminal:**
```
tool: AskUserQuestion
question: "Are you comfortable running a short command in a terminal on your own computer?"
options:
  - "Yes, I can use a terminal"
  - "No, I prefer not to use a terminal"
```

| Answer combination | Which method to use (internal) |
|---|---|
| Single mode / Not sure + any terminal answer | **MCP method** — check for modes during extraction and adapt if needed |
| Multiple modes + comfortable with terminal | **curl method** — fetches all modes in one command |
| Multiple modes + not comfortable with terminal | **MCP method** with manual mode switching |

If the user answered "I'm not sure" on modes, proceed with MCP and check for modes during extraction. Explain what you find then, not upfront.

> **Do not ask whether the file uses Variables or Styles.** Auto-detect this after receiving the Figma file URL in Step 2 — call `get_variable_defs` or inspect the file and report what you find. Use Variables extraction if variables exist, Styles extraction if only styles exist, both if both are present.

---

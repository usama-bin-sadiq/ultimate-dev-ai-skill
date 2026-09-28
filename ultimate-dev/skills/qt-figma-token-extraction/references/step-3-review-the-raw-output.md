<!-- Moved verbatim from qt-figma-token-extraction/SKILL.md, the
     'step-3-review-the-raw-output' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 3 — Review the Raw Output

Whichever method was used, review the raw token data with the user before applying naming conventions:

- **All files extracted:** Confirm every file the user mentioned has been extracted. Do not proceed if any are missing.
- **Collections present:** Do the collection names match what the user expects from each file?
- **Modes captured:** If multi-mode, confirm all modes appear with correct values.
- **Color values:** Spot-check a few hex values against the Figma file.
- **Alias resolution:** Semantic tokens that reference primitives should have resolved values. If an alias could not be resolved, it almost certainly means the referenced primitive lives in a file that hasn't been extracted yet — go back and extract that file before continuing.
- **Missing collections:** If something expected is absent, ask the user which Figma file it lives in and add it to the inventory.

---

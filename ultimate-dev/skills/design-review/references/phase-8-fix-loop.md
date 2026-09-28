<!-- Moved verbatim from design-review/SKILL.md, the
     'phase-8-fix-loop' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 8: Fix Loop

For each fixable finding, in impact order:

### 8a. Locate source

```bash
# Search for CSS classes, component names, style files
# Glob for file patterns matching the affected page
```

- Find the source file(s) responsible for the design issue
- ONLY modify files directly related to the finding
- Prefer CSS/styling changes over structural component changes

### 8a.5. Target Mockup (if DESIGN_READY)

If the gstack designer is available and the finding involves visual layout, hierarchy, or spacing (not just a CSS value fix like wrong color or font-size), generate a target mockup showing what the corrected version should look like:

```bash
$D generate --brief "<description of the page/component with the finding fixed, referencing DESIGN.md constraints>" --output "$REPORT_DIR/screenshots/finding-NNN-target.png"
```

Show the user: "Here's the current state (screenshot) and here's what it should look like (mockup). Now I'll fix the source to match."

This step is optional — skip for trivial CSS fixes (wrong hex color, missing padding value). Use it for findings where the intended design isn't obvious from the description alone.

### 8b. Fix

- Read the source code, understand the context
- Make the **minimal fix** — smallest change that resolves the design issue
- If a target mockup was generated in 8a.5, use it as the visual reference for the fix
- CSS-only changes are preferred (safer, more reversible)
- Do NOT refactor surrounding code, add features, or "improve" unrelated things

### 8c. Commit

```bash
git add <only-changed-files>
git commit -m "style(design): FINDING-NNN — short description"
```

- One commit per fix. Never bundle multiple fixes.
- Message format: `style(design): FINDING-NNN — short description`

### 8d. Re-test

Navigate back to the affected page and verify the fix — one Aside script per finding:

```bash
aside repl '
const HOOK = `(() => { window.__gstackErrs = window.__gstackErrs || []; const oe = console.error; console.error = (...a) => { window.__gstackErrs.push(a.map(String).join(" ")); oe.apply(console, a); }; window.addEventListener("error", e => window.__gstackErrs.push("uncaught: " + e.message)); })()`;
const pg = await openTab("about:blank");
await pg._sendToTarget("Page.addScriptToEvaluateOnNewDocument", { source: HOOK });
await pg.goto("<affected-url>");
const s = await snapshot(pg, { interactive: true });
console.log(s.tree);
console.log("CONSOLE_ERRORS=" + JSON.stringify(await pg.evaluate(() => window.__gstackErrs)));
await pg.screenshot({ path: "finding-NNN-after.png", type: "png", fullPage: true });
console.log("ASIDE_DIR=" + pwd);
await closeTab(pg);
console.log("GSTACK_STEP_OK");
'
```

Then `cp "<ASIDE_DIR>/finding-NNN-after.png" "$REPORT_DIR/screenshots/"` and Read it next to the before shot. `CONSOLE_ERRORS=` must be `[]` (or no worse than the baseline) — a new error is a regression.

Take **before/after screenshot pair** for every fix.

### 8e. Classify

- **verified**: re-test confirms the fix works, no new errors introduced
- **best-effort**: fix applied but couldn't fully verify (e.g., needs specific browser state)
- **reverted**: regression detected → `git revert HEAD` → mark finding as "deferred"

### 8e.5. Regression Test (design-review variant)

Design fixes are typically CSS-only. Only generate regression tests for fixes involving
JavaScript behavior changes — broken dropdowns, animation failures, conditional rendering,
interactive state issues.

For CSS-only fixes: skip entirely. CSS regressions are caught by re-running /design-review.

If the fix involved JS behavior: follow the same procedure as /qa Phase 8e.5 (study existing
test patterns, write a regression test encoding the exact bug condition, run it, commit if
passes or defer if fails). Commit format: `test(design): regression test for FINDING-NNN`.

### 8f. Self-Regulation (STOP AND EVALUATE)

Every 5 fixes (or after any revert), compute the design-fix risk level:

```
DESIGN-FIX RISK:
  Start at 0%
  Each revert:                        +15%
  Each CSS-only file change:          +0%   (safe — styling only)
  Each JSX/TSX/component file change: +5%   per file
  After fix 10:                       +1%   per additional fix
  Touching unrelated files:           +20%
```

**If risk > 20%:** STOP immediately. Show the user what you've done so far. Ask whether to continue.

**Hard cap: 30 fixes.** After 30 fixes, stop regardless of remaining findings.

---

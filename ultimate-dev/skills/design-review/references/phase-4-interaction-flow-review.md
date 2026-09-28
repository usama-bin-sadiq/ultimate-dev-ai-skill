<!-- Moved verbatim from design-review/SKILL.md, the
     'phase-4-interaction-flow-review' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 4: Interaction Flow Review

Walk 2-3 key user flows and evaluate the *feel*, not just the function. One flow per Aside script — open, act, diff, evidence:

```bash
aside repl '
const HOOK = `(() => { window.__gstackErrs = window.__gstackErrs || []; const oe = console.error; console.error = (...a) => { window.__gstackErrs.push(a.map(String).join(" ")); oe.apply(console, a); }; window.addEventListener("error", e => window.__gstackErrs.push("uncaught: " + e.message)); })()`;
const pg = await openTab("about:blank");
await pg._sendToTarget("Page.addScriptToEvaluateOnNewDocument", { source: HOOK });
await pg.goto("<url>");
await snapshot(pg, { interactive: true });                            // baseline for .diff; refs like [ref=e3] name every control
await pg.screenshot({ path: "flow-<name>-step-1.jpg", type: "jpeg", quality: 60 });
await pg.locator("e3").click();                                        // perform the action — or pg.getByRole("button", { name: "Sign Up" })
await sleep(500);                                                      // or: await pg.waitForSelector("<selector>"); await pg.waitForURL(/dashboard/)
const s = await snapshot(pg);
console.log("DIFF_START"); console.log(s.diff); console.log("DIFF_END");   // what changed since the baseline
console.log("URL=" + pg.url());
console.log("CONSOLE_ERRORS=" + JSON.stringify(await pg.evaluate(() => window.__gstackErrs)));
await pg.screenshot({ path: "flow-<name>-result.jpg", type: "jpeg", quality: 60 });
console.log("ASIDE_DIR=" + pwd);
await closeTab(pg);
console.log("GSTACK_STEP_OK");
'
```

Chain more steps inside the same script for a longer flow (re-snapshot before clicking by ref again). Forms may be filled but not submitted on a non-local target without the one-time consent in BROWSER SETUP.

Evaluate:
- **Response feel:** Does clicking feel responsive? Any delays or missing loading states?
- **Transition quality:** Are transitions intentional or generic/absent?
- **Feedback clarity:** Did the action clearly succeed or fail? Is the feedback immediate?
- **Form polish:** Focus states visible? Validation timing correct? Errors near the source?

**Narration mode:** Narrate the flow in first person. "I click 'Sign Up'... spinner appears... 3 seconds pass... still spinning... I'm getting nervous. Finally the dashboard loads, but where am I? The nav doesn't highlight anything." Name the specific element, its position, its visual weight. If you can't name it specifically, you're not actually experiencing the flow, you're generating platitudes.

### Goodwill Reservoir (track across the flow)

As you walk the user flow, maintain a mental goodwill meter (starts at 70/100).
These scores are heuristic, not measured. The value is in identifying specific
drains and fills, not in the final number.

Subtract points for:
- Hidden information the user would want (pricing, contact, shipping): subtract 15
- Format punishment (rejecting valid input like dashes in phone numbers): subtract 10
- Unnecessary information requests: subtract 10
- Interstitials, splash screens, forced tours blocking the task: subtract 15
- Sloppy or unprofessional appearance: subtract 10
- Ambiguous choices that require thinking: subtract 5 each

Add points for:
- Top user tasks are obvious and prominent: add 10
- Upfront about costs and limitations: add 5
- Saves steps (direct links, smart defaults, autofill): add 5 each
- Graceful error recovery with specific fix instructions: add 10
- Apologizes when things go wrong: add 5

Report the final goodwill score with a visual dashboard:

```
Goodwill: 70 ████████████████████░░░░░░░░░░
  Step 1: Login page        70 → 75  (+5 obvious primary action)
  Step 2: Dashboard          75 → 60  (-15 interstitial tour popup)
  Step 3: Settings           60 → 50  (-10 format punishment on phone)
  Step 4: Billing            50 → 35  (-15 hidden pricing info)
  FINAL: 35/100 ⚠️ CRITICAL UX DEBT
```

Below 30 = critical UX debt. 30-60 = needs work. Above 60 = healthy.
Include the biggest drains and fills as specific findings.

---

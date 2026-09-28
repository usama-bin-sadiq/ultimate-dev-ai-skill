<!-- Moved verbatim from design-html/SKILL.md, the
     'step-4-preview-refinement-loop' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 4: Preview + Refinement Loop

### Slop Gate (bounded, never a loop)

If the Setup probe printed `IMPECCABLE_READY`, scan the finalized page once before the screenshots:

```bash
_DJ=$(mktemp); bun --no-env-file run $HOME/.claude/skills/gstack/bin/gstack-design-detect.ts scan --format gstack --host claude <finalized.html> > "$_DJ"; echo "DETECT_EXIT_CODE=$?"; echo "DETECT_JSON=$_DJ"
```

Exit 2 → one surgical fix pass over the non-advisory rules in the `DETECT_TOP` block, then scan once more. Whatever remains, present the page with those findings listed as accepted-with-reason: a pattern the approved mockup contains, a value DESIGN.md's tokens bless or a pattern its Decisions Log or Do's and Don'ts records as intentional, or an inline `<!-- impeccable-disable <rule>: <reason> -->` the user agreed to. One pass, not a loop. Any other first line from the probe: skip, no ceremony.

### Verification Screenshots

Take verification screenshots at 3 viewports. One `gstack-render` call serves
the HTML's directory on 127.0.0.1 (so relative assets resolve), opens the page
in the Aside browser when it is running — otherwise in gstack's own headless
browser (the first output line, `ENGINE=aside` or `ENGINE=browse`, says which)
— and captures each width:

```bash
bun run ~/.claude/skills/gstack/bin/gstack-render.ts <path-to-finalized.html> \
  --screenshot /tmp/gstack-verify-mobile.jpg --width 375 --jpeg \
  --screenshot /tmp/gstack-verify-tablet.jpg --width 768 --jpeg \
  --screenshot /tmp/gstack-verify-desktop.jpg --width 1440 --jpeg
```

Show all three screenshots inline using the Read tool. Check for:
- Text overflow (text cut off or extending beyond containers)
- Layout collapse (elements overlapping or missing)
- Responsive breakage (content not adapting to viewport)

If issues are found, note them and fix before presenting to the user.

Only if `gstack-render` prints `NEEDS_ASIDE` or `ASIDE_NOT_RUNNING` followed by
`ERROR: no browser available` (Aside is not open AND gstack's own browser is not
built), skip verification and note: "No browser available (open the Aside app). Skipping automated
viewport verification." Never install either for the user.

### Refinement Loop

```
LOOP:
  1. If server is running, tell user to open http://localhost:PORT/finalized.html
     Otherwise: open <path>/finalized.html

  2. If an approved mockup PNG exists, show it inline (Read tool) for visual comparison.
     If in plan-driven or freeform mode, skip this step.

  3. AskUserQuestion (adjust wording based on mode):
     With mockup: "The HTML is live in your browser. Here's the approved mockup for comparison.
      Try: resize the window (text should reflow dynamically),
      click any text (it's editable, layout recomputes instantly).
      What needs to change? Say 'done' when satisfied."
     Without mockup: "The HTML is live in your browser. Try: resize the window
      (text should reflow dynamically), click any text (it's editable, layout
      recomputes instantly). What needs to change? Say 'done' when satisfied."

  4. If "done" / "ship it" / "looks good" / "perfect" → exit loop, go to Step 5

  5. Apply feedback using targeted Edit tool changes on the HTML file
     (do NOT regenerate the entire file — surgical edits only)

  6. Brief summary of what changed (2-3 lines max)

  7. If verification screenshots are available, re-take them to confirm the fix

  8. Go to LOOP
```

Maximum 10 iterations. If the user hasn't said "done" after 10, use AskUserQuestion:
"We've done 10 rounds of refinement. Want to continue iterating or call it done?"

---

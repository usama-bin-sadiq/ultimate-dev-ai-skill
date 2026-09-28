<!-- Moved verbatim from plan-design-review/SKILL.md, the
     'step-0-5-visual-mockups-default-when-design-ready' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 0.5: Visual Mockups (DEFAULT when DESIGN_READY)

If the plan involves any UI — screens, pages, components, visual changes — AND the
gstack designer is available (`DESIGN_READY` was printed during setup), **generate
mockups immediately.** Do not ask permission. This is the default behavior.

Tell the user: "Generating visual mockups with the gstack designer. This is how we
review design — real visuals, not text descriptions."

The ONLY time you skip mockups is when:
- `DESIGN_NOT_AVAILABLE` was printed (designer binary not found)
- The plan has zero UI scope (pure backend/API/infrastructure)

If the user explicitly says "skip mockups" or "text only", respect that. Otherwise, generate.

**PLAN MODE EXCEPTION — ALWAYS RUN:** These commands write design artifacts to
`$GSTACK_STATE_ROOT/projects/$SLUG/designs/` (the configured state directory).
Mockups are design artifacts that inform the plan, not code changes. The gstack
designer outputs PNGs and HTML comparison boards for human review during the
planning phase. Generating mockups during planning is the whole point.

Allowed commands under this exception:
- `mkdir -p "$GSTACK_STATE_ROOT/projects/$SLUG/designs/..."`
- `$D generate`, `$D variants`, `$D compare`, `$D iterate`, `$D evolve`, `$D check`
- `open` (viewing comparison boards in the default browser)

First, set up the output directory. Name it after the screen/feature being designed and today's date:

```bash
eval "$(~/.claude/skills/gstack/bin/gstack-slug 2>/dev/null)"
eval "$(~/.claude/skills/gstack/bin/gstack-paths)"
_DESIGN_DIR="$GSTACK_STATE_ROOT/projects/$SLUG/designs/<screen-name>-$(date +%Y%m%d)"
mkdir -p "$_DESIGN_DIR"
echo "DESIGN_DIR: $_DESIGN_DIR"
```

Replace `<screen-name>` with a descriptive kebab-case name (e.g., `homepage-variants`, `settings-page`, `onboarding-flow`).

**Generate mockups ONE AT A TIME in this skill.** The inline review flow generates
fewer variants and benefits from sequential control. Note: /design-shotgun uses
parallel Agent subagents for variant generation, which works at Tier 2+ (15+ RPM).
The sequential constraint here is specific to plan-design-review's inline pattern.

For each UI screen/section in scope, construct a design brief from the plan's description (and DESIGN.md if present) and generate variants:

```bash
$D variants --brief "<description assembled from plan + DESIGN.md constraints>" --count 3 --output-dir "$_DESIGN_DIR/"
```

After generation, run a cross-model quality check on each variant:

```bash
$D check --image "$_DESIGN_DIR/variant-A.png" --brief "<the original brief>"
```

Flag any variants that fail the quality check. Offer to regenerate failures.

**Do NOT show variants inline via Read tool and ask for preferences.** Proceed
directly to the Comparison Board + Feedback Loop section below. The comparison board
IS the chooser — it has rating controls, comments, remix/regenerate, and structured
feedback output. Showing mockups inline is a degraded experience.

### Comparison Board + Feedback Loop

Create the comparison board and serve it over HTTP:

```bash
$D compare --images "$_DESIGN_DIR/variant-A.png,$_DESIGN_DIR/variant-B.png,$_DESIGN_DIR/variant-C.png" --output "$_DESIGN_DIR/design-board.html" --serve
```

Creates HTML and opens the board. **Run it in the background** (host task, or `&` redirecting stdout/stderr to private files in `$_DESIGN_DIR`). Read captured stderr for the startup marker; a PID is not readiness. Missing marker: use the failure fallback below.

Default stderr: `BOARD_URL: http://127.0.0.1:N/boards/<id>/`. Use that full per-board URL for AskUserQuestion and as the reload base. Only explicit legacy `--no-daemon` emits `SERVE_STARTED: port=XXXXX`, serving one board at `/` with reload at `/api/reload`.

**PRIMARY WAIT: AskUserQuestion with board URL**

Once serving, wait with AskUserQuestion including the board URL:

"I've opened a comparison board with the design variants:
<BOARD_URL> — Rate them, leave comments, remix
elements you like, and click Submit when you're done. Let me know when you've
submitted your feedback (or paste your preferences here). If you clicked
Regenerate or Remix on the board, tell me and I'll generate new variants."

Substitute `<BOARD_URL>` from the stderr marker above.

**The user chooses variants in the board; AskUserQuestion only waits.**

**After the user responds to AskUserQuestion:**

Check for feedback files next to the board HTML:
- `$_DESIGN_DIR/feedback.json` — written when user clicks Submit (final choice)
- `$_DESIGN_DIR/feedback-pending.json` — written when user clicks Regenerate/Remix/More Like This

```bash
if [ -f "$_DESIGN_DIR/feedback.json" ]; then
  echo "SUBMIT_RECEIVED"
  cat "$_DESIGN_DIR/feedback.json"
elif [ -f "$_DESIGN_DIR/feedback-pending.json" ]; then
  echo "REGENERATE_RECEIVED"
  cat "$_DESIGN_DIR/feedback-pending.json"
  rm "$_DESIGN_DIR/feedback-pending.json"
else
  echo "NO_FEEDBACK_FILE"
fi
```

The feedback JSON has this shape:
```json
{
  "preferred": "A",
  "ratings": { "A": 4, "B": 3, "C": 2 },
  "comments": { "A": "Love the spacing" },
  "overall": "Go with A, bigger CTA",
  "regenerated": false
}
```

**If `feedback.json` found:** The user clicked Submit on the board.
Read `preferred`, `ratings`, `comments`, `overall` from the JSON. Proceed with
the approved variant.

**If `feedback-pending.json` found:** The user clicked Regenerate/Remix on the board.
1. Read `regenerateAction` from the JSON (`"different"`, `"match"`, `"more_like_B"`,
   `"remix"`, or custom text)
2. If `regenerateAction` is `"remix"`, read `remixSpec` (e.g. `{"layout":"A","colors":"B"}`)
3. Generate new variants with `$D iterate` or `$D variants` using updated brief
4. Create new board: `$D compare --images "..." --output "$_DESIGN_DIR/design-board.html"`
5. Reload the board in the user's browser (same tab) — the URL is per-board
   under daemon mode, so use `<BOARD_URL>` (from the `BOARD_URL:` stderr
   line) as the base:
   `jq -nc --arg html "$_DESIGN_DIR/design-board.html" '{html: $html}' | curl -sS -X POST "${BOARD_URL}api/reload" -H 'Content-Type: application/json' --data-binary @-`
   Under `--no-daemon` the reload endpoint is `/api/reload` at the legacy
   port; this path only matters if the caller explicitly opted out of the
   daemon.
6. The board auto-refreshes. **AskUserQuestion again** with the same board URL to
   wait for the next round of feedback. Repeat until `feedback.json` appears.

**If `NO_FEEDBACK_FILE`:** The user typed their preferences directly in the
AskUserQuestion response instead of using the board. Use their text response
as the feedback.

Exit 0 with `BOARD_URL` means the daemon is serving; use the board feedback flow above.
**SERVER FALLBACK:** Nonzero exit or no readiness marker: show each variant inline using the Read tool (so the user can see them),
then use AskUserQuestion:
"The comparison board server failed to start. I've shown the variants above.
Which do you prefer? Any feedback?"

**After receiving feedback (any path):** Output a clear summary confirming
what was understood:

"Here's what I understood from your feedback:
PREFERRED: Variant [X]
RATINGS: [list]
YOUR NOTES: [comments]
DIRECTION: [overall]

Is this right?"

Use AskUserQuestion to verify before proceeding.

**Save the approved choice:**
```bash
echo '{"approved_variant":"<V>","feedback":"<FB>","date":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","screen":"<SCREEN>","branch":"'$(git branch --show-current 2>/dev/null)'"}' > "$_DESIGN_DIR/approved.json"
```

**Do NOT use AskUserQuestion to ask which variant the user picked.** Read `feedback.json` — it already contains their preferred variant, ratings, comments, and overall feedback. Only use AskUserQuestion to confirm you understood the feedback correctly, never to re-ask what they chose.

Note which direction was approved. This becomes the visual reference for all subsequent review passes.

**Multiple variants/screens:** If the user asked for multiple variants (e.g., "5 versions of the homepage"), generate ALL as separate variant sets with their own comparison boards. Each screen/variant set gets its own subdirectory under `designs/`. Complete all mockup generation and user selection before starting review passes.

**If `DESIGN_NOT_AVAILABLE`:** Tell the user: "The gstack designer isn't set up yet. Run `$D setup` to enable visual mockups. Proceeding with text-only review, but you're missing the best part." Then proceed to review passes with text-based review.

<!-- Moved verbatim from design-review/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Phase 3: Page-by-Page Visual Audit

For each page in scope, two Aside scripts. First the read: console hook, interactive snapshot, annotated screenshot, load-time errors, navigation timing:

```bash
aside repl '
const HOOK = `(() => { window.__gstackErrs = window.__gstackErrs || []; const oe = console.error; console.error = (...a) => { window.__gstackErrs.push(a.map(String).join(" ")); oe.apply(console, a); }; window.addEventListener("error", e => window.__gstackErrs.push("uncaught: " + e.message)); window.addEventListener("unhandledrejection", e => window.__gstackErrs.push("unhandledrejection: " + (e.reason && e.reason.message || e.reason))); })()`;
const pg = await openTab("about:blank");
await pg._sendToTarget("Page.addScriptToEvaluateOnNewDocument", { source: HOOK });
await pg.goto("<url>");
const s = await snapshot(pg, { interactive: true });
console.log(s.tree);
const a = await annotatedScreenshot(pg);
await fs.writeFile(path.join(pwd, "{page}-annotated.png"), Buffer.from(a.base64Image, "base64"));
console.log("URL=" + pg.url());
console.log("CONSOLE_ERRORS=" + JSON.stringify(await pg.evaluate(() => window.__gstackErrs)));
console.log("NAV=" + await pg.evaluate(() => JSON.stringify(performance.getEntriesByType("navigation")[0])));
console.log("ASIDE_DIR=" + pwd);
await closeTab(pg);
console.log("GSTACK_STEP_OK");
'
```

Then the responsive captures (mobile 375, tablet 768, desktop 1440):

```bash
aside repl '
const pg = await openTab("<url>");
for (const [name, width, height] of [["mobile", 375, 812], ["tablet", 768, 1024], ["desktop", 1440, 900]]) {
  await pg._sendToTarget("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 2, mobile: width < 1024 });
  await sleep(300);
  await pg.screenshot({ path: `{page}-${name}.jpg`, type: "jpeg", quality: 60, fullPage: true });
}
await pg._sendToTarget("Emulation.clearDeviceMetricsOverride", {});
console.log("ASIDE_DIR=" + pwd); await closeTab(pg); console.log("GSTACK_STEP_OK");
'
```

After each script, `cp` its files out of the `ASIDE_DIR` it printed into `$REPORT_DIR/screenshots/` (each script gets its own directory) and Read them.

### DOM dump (DOM mode only: Setup printed `IMPECCABLE_READY` and the target is a URL)

Rule 4 forbids reading source, so the detector reads the rendered page. One shared script, `$HOME/.claude/skills/gstack/lib/dom-dump.js` (an arrow function the page runs), serves both engines: it clones the document, inlines linked stylesheets as `<style data-gstack-dom-css>`, strips scripts, templates, noscript blocks, inline event handlers, input values, long attributes, and URL query strings, and notes what it cannot capture (shadow DOM, constructed and runtime-injected styles). Aside, third script per page. The script stays single-quoted like every other Aside script, so the URL and the page slug are never inside a double-quoted bash string; only the function text is spliced in from the file through a closed-quote segment, and `pg.evaluate` receives the function and runs it in the page. `{page}` is the screenshot slug (letters, digits, hyphens); paste `<url>` with any `'` percent-encoded as `%27` (a bare single quote would end the script), and never paste a URL you have not read:

```bash
_DUMP=$(cat "$HOME/.claude/skills/gstack/lib/dom-dump.js")
aside repl '
const pg = await openTab("<url>");
const html = await pg.evaluate('"$_DUMP"');
await fs.writeFile(path.join(pwd, "{page}.dom.html"), html);
console.log("ASIDE_DIR=" + pwd); await closeTab(pg); console.log("GSTACK_STEP_OK");
'
```

Fallback engine (`$B js` calls the function in the page, spliced the same way; `--out` accepts only temp dirs or cwd; never `$B html`, which wraps output in content markers):

```bash
_TMP=$(mktemp -d); _DUMP=$(cat "$HOME/.claude/skills/gstack/lib/dom-dump.js")
$B js '('"$_DUMP"')()' --out "$_TMP/{page}.dom.html" --raw && echo "DUMP=$_TMP/{page}.dom.html"
```

Persist it into this run's directory, size-capped and redaction-checked: a HIGH finding, or a redaction tool that fails to run, skips the page, not the review; MEDIUM findings (emails, PII shapes on an authenticated page) persist owner-only (mode 600) and are deleted with the rest after Phase 9 (`--keep-dom`, a design-review flag, keeps them; an interrupted run's dumps stay owner-only under their run id until you delete them). Each bash block is a fresh shell: restate the report directory and run id from Setup literally.

```bash
_D="<ASIDE_DIR or $_TMP>/{page}.dom.html"; _REPORT="<REPORT_DIR from Setup>"; _RUN="<RUN_ID from Setup>"
if [ ! -s "$_D" ]; then echo "DOM_DUMP_MISSING: {page} (the dump script wrote nothing)"
elif [ "$(wc -c < "$_D")" -gt 10485760 ]; then echo "DOM_DUMP_TOO_LARGE: {page} $(wc -c < "$_D")"; rm -f "$_D"
elif $HOME/.claude/skills/gstack/bin/gstack-redact --from-file "$_D" --max-bytes 10485760 >/dev/null 2>&1; _RC=$?; [ "$_RC" -ne 0 ] && [ "$_RC" -ne 2 ]; then echo "DOM_DUMP_REDACTION_BLOCKED: {page} redact-exit=$_RC"; rm -f "$_D"
else mkdir -p "$_REPORT/dom/$_RUN" && cp "$_D" "$_REPORT/dom/$_RUN/" && chmod 600 "$_REPORT/dom/$_RUN/{page}.dom.html" && rm -f "$_D" && echo "DOM_DUMP_OK: {page}"; fi
```

After the LAST page's dump, scan the run directory once (source mode scanned in Setup instead):

```bash
_DJ=$(mktemp); bun --no-env-file run $HOME/.claude/skills/gstack/bin/gstack-design-detect.ts scan --format gstack --host claude "<REPORT_DIR from Setup>/dom/<RUN_ID>" > "$_DJ"; echo "DETECT_EXIT_CODE=$?"; echo "DETECT_JSON=$_DJ"
```

Say once in the report: "static scan of the rendered DOM; cross-origin CSS not resolved". A DOM-mode `file:line` points into `{page}.dom.html` and is approximate (HTML findings carry line 0); the `snippet` locates the element. Confirm each hit in the rendered page, never by hunting a source line. `design-system-*` rows compare the page against THIS repository's DESIGN.md: keep them only when the page is this repository's own app. An empty `$_DJ` with exit 0 means the probe state changed since Setup: read the sentinel the scan printed on stderr. Dumps are deleted after Phase 9 unless the user passed `--keep-dom`.

### Auth Detection

Check the `URL=` line every script prints. If it contains `/login`, `/signin`, `/auth`, or `/sso`, the page bounced you to a sign-in wall: follow the credential rule in BROWSER SETUP — tell the user to sign in to that origin in Aside themselves, wait for them to say they're done, then re-run the script. The session now carries their cookies. No cookie import, no typed passwords, ever.

### Trunk Test (run on every page)

Imagine being dropped on this page with no context. Can you immediately answer:
1. What site is this? (Site ID visible and identifiable)
2. What page am I on? (Page name prominent, matches what I clicked)
3. What are the major sections? (Primary nav visible and clear)
4. What are my options at this level? (Local nav or content choices obvious)
5. Where am I in the scheme of things? ("You are here" indicator, breadcrumbs)
6. How can I search? (Search box findable without hunting)

Score: PASS (all 6 clear) / PARTIAL (4-5 clear) / FAIL (3 or fewer clear).
A FAIL on the trunk test is a HIGH-impact finding regardless of how polished the visual design is.

### Design Audit Checklist (10 categories, ~80 items)

Apply these at each page. Each finding gets an impact rating (high/medium/polish) and category.

**1. Visual Hierarchy & Composition** (8 items)
- Clear focal point? One primary CTA per view?
- Eye flows naturally top-left to bottom-right?
- Visual noise — competing elements fighting for attention?
- Information density appropriate for content type?
- Z-index clarity — nothing unexpectedly overlapping?
- Above-the-fold content communicates purpose in 3 seconds?
- Squint test: hierarchy still visible when blurred?
- White space is intentional, not leftover?

**2. Typography** (15 items)
- Font count <=3 (flag if more)
- Scale follows ratio (1.25 major third or 1.333 perfect fourth)
- Line-height: 1.5x body, 1.15-1.25x headings
- Measure: 45-75 chars per line (66 ideal)
- Heading hierarchy: no skipped levels (h1→h3 without h2)
- Weight contrast: >=2 weights used for hierarchy
- No banned fonts (Papyrus, Comic Sans, Lobster, Impact, Jokerman, Bleeding Cowboys, Permanent Marker, Bradley Hand, Brush Script, Hobo, Trajan, Raleway, Clash Display, Courier New)
- Display face on the overused list (Inter, Roboto, Arial, Helvetica, Open Sans, Lato, ...) → flag `[overused-font]`; as body/UI on an Operate or Read surface it passes when DESIGN.md says so
- `text-wrap: balance` or `text-pretty` on headings (check via `await pg.evaluate(() => getComputedStyle(document.querySelector("h1")).textWrap)`)
- Curly quotes used, not straight quotes
- Ellipsis character (`…`) not three dots (`...`)
- `font-variant-numeric: tabular-nums` on number columns
- Body text >= 16px
- Caption/label >= 12px
- No letterspacing on lowercase text

**3. Color & Contrast** (10 items)
- Palette coherent (<=12 unique non-gray colors)
- WCAG AA: body text 4.5:1, large text (18px+) 3:1, UI components 3:1
- Semantic colors consistent (success=green, error=red, warning=yellow/amber)
- No color-only encoding (always add labels, icons, or patterns)
- Dark mode: surfaces use elevation, not just lightness inversion
- Dark mode: text off-white (~#E0E0E0), not pure white
- Primary accent desaturated 10-20% in dark mode
- `color-scheme: dark` on html element (if dark mode present)
- No red/green only combinations (8% of men have red-green deficiency)
- Neutral palette is warm or cool consistently — not mixed

**4. Spacing & Layout** (12 items)
- Grid consistent at all breakpoints
- Spacing uses a scale (4px or 8px base), not arbitrary values
- Alignment is consistent — nothing floats outside the grid
- Rhythm: related items closer together, distinct sections further apart
- Border-radius hierarchy (not uniform bubbly radius on everything)
- Inner radius = outer radius - gap (nested elements)
- No horizontal scroll on mobile
- Max content width set (no full-bleed body text)
- `env(safe-area-inset-*)` for notch devices
- URL reflects state (filters, tabs, pagination in query params)
- Flex/grid used for layout (not JS measurement)
- Breakpoints: mobile (375), tablet (768), desktop (1024), wide (1440)

**5. Interaction States** (12 items)
- Hover state on all interactive elements
- `focus-visible` ring present (never `outline: none` without replacement)
- Active/pressed state with depth effect or color shift
- Disabled state: reduced opacity + `cursor: not-allowed`
- Loading: skeleton shapes match real content layout
- Empty states: warm message + primary action + visual (not just "No items.")
- Error messages: specific + include fix/next step
- Success: confirmation animation or color, auto-dismiss
- Touch targets >= 44px on all interactive elements
- `cursor: pointer` on all clickable elements
- Mindless choice audit: every decision point (button, link, dropdown, modal choice) is a mindless click (obvious what happens). If a click requires thought about whether it's the right choice, flag as HIGH.
- Browser surfaces themed from the palette: `::selection`, caret, scrollbars, focus ring, underline offset, tabular numerals. Left at defaults, the page reads as assembled, not designed

**6. Responsive Design** (8 items)
- Mobile layout makes *design* sense (not just stacked desktop columns)
- Touch targets sufficient on mobile (>= 44px)
- No horizontal scroll on any viewport
- Images handle responsive (srcset, sizes, or CSS containment)
- Text readable without zooming on mobile (>= 16px body)
- Navigation collapses appropriately (hamburger, bottom nav, etc.)
- Forms usable on mobile (correct input types, no autoFocus on mobile)
- No `user-scalable=no` or `maximum-scale=1` in viewport meta

**7. Motion & Animation** (7 items)
- Easing: ease-out for entering, ease-in for exiting, ease-in-out for moving
- Duration: 50-700ms range (nothing slower unless page transition)
- Purpose: every animation communicates something (state change, attention, spatial relationship)
- `prefers-reduced-motion` respected (check: `await pg.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches)`)
- No `transition: all` — properties listed explicitly
- Only `transform` and `opacity` animated (not layout properties like width, height, top, left)
- One authored motion moment per page: not the same entrance on every section, not a hover effect on everything. Ease-out from an already-visible default; content never hides behind animation timing

**8. Content & Microcopy** (8 items)
- Empty states designed with warmth (message + action + illustration/icon)
- Error messages specific: what happened + why + what to do next
- Button labels specific ("Save API Key" not "Continue" or "Submit")
- No filler or sample copy visible in production — the stand-in text a word processor inserts
- Truncation handled (`text-overflow: ellipsis`, `line-clamp`, or `break-words`)
- Active voice ("Install the CLI" not "The CLI will be installed")
- Loading states end with `…` ("Saving…" not "Saving...")
- Destructive actions have confirmation modal or undo window
- Happy talk detection: scan for introductory paragraphs that start with "Welcome to..." or tell users how great the site is. If you can hear "blah blah blah", it's happy talk. Flag for removal.
- Instructions detection: any visible instructions longer than one sentence. If users need to read instructions, the design has failed. Flag the instructions AND the interaction they're compensating for.
- Happy talk word count: count total visible words on the page. Classify each text block as "useful content" vs "happy talk" (welcome paragraphs, self-congratulatory text, instructions nobody reads). Report: "This page has X words. Y (Z%) are happy talk."

**9. AI Slop Detection** (11 blacklist patterns, 30 detector rules, 16 judgment tells; polish-level ones on the last line)

The test: would a human designer at a respected studio ever ship this? A `[rule-id]` is the detector's name for the same pattern; a scan hit and a judgment hit on one element are one finding.

- Purple/violet/indigo gradient backgrounds or blue-to-purple color schemes
- **The 3-column feature grid:** icon-in-colored-circle + bold title + 2-line description, repeated 3x symmetrically. THE most recognizable AI layout.
- Icons in colored circles as section decoration (SaaS starter template look)
- Centered everything (`text-align: center` on all headings, descriptions, cards)
- Uniform bubbly border-radius on every element (same large radius on everything)
- Decorative blobs, floating circles, wavy SVG dividers (if a section feels empty, it needs better content, not decoration)
- Emoji as design elements (rockets in headings, emoji as bullet points)
- Colored left-border on cards (`border-left: 3px solid <accent>`)
- Generic hero copy ("Welcome to [X]", "Unlock the power of...", "Your all-in-one solution for...")
- Cookie-cutter section rhythm (hero → 3 features → testimonials → pricing → CTA, every section same height)
- system-ui or `-apple-system` as the PRIMARY display/body font — the "I gave up on typography" signal. Pick a real typeface.

Detector rules (ids only; the scan prints each one's impact and message, and `gstack-design-detect.ts rules` lists the full mapped set): [border-accent-on-rounded] border accent on a rounded card; [overused-font] overused display font; [flat-type-hierarchy] flat type hierarchy; [gradient-text] gradient text; [cream-palette] cream default palette; [nested-cards] nested cards; [shape-assembled-illustration] shape-assembled illustration; [dark-glow] dark-mode glow; [radial-halo] radial halo; [radial-spotlight-glow] radial spotlight glow; [marquee] logo marquee; [icon-tile-stack] icon tile above every heading; [italic-serif-display] italic serif display; [hero-eyebrow-chip] hero eyebrow chip; [kicker-above-heading] kicker above heading; [marketing-buzzword] marketing buzzwords; [aphoristic-cadence] aphoristic cadence; [oversized-h1] oversized h1; [theater-slop-phrase] theater phrases.

Judgment tells (no detector rule; you are the detector):
- Gradient buttons as the primary call to action. One solid color the palette owns.
- A generic stock-photo hero, or a gray placeholder div standing in for one. Show the product or show nothing.
- Rounded cards with drop shadows as the container for everything. App UI made of stacked cards is not layout.
- A testimonial row with avatars, five stars, and quotes nobody said. Real names with real claims, or cut it.
- The cookie-cutter hero: headline left, screenshot right, two buttons. The first template every generator reaches for.
- "Get Started" and "Learn More" as the only calls to action. Name the outcome the click buys.
- Three big numbers with tiny labels under the hero ("10k+ users", "99.9%"). The template counts, not the product.
- A grid of cards with the same shape, the same icon slot, the same two lines. Content of unequal weight given equal boxes.
- Frosted-glass panels with blurred backdrops as the default surface. One translucent layer where it explains depth, not everywhere.
- Generated SVG doodles and mascots in place of art direction. Commission or license an asset, or ship none.
- Every secondary action in a modal. Inline, a side panel, or a new page usually costs the user less.
- Sparklines, progress rings, and fake avatars filling space where content should be. Real data or an honest empty state.
- Dark because it is a dev tool, light because it is health. Light or dark comes from the use scene: who, where, under what light.
- Only the happy path is designed. Empty, loading, error, and long-content states are part of the component.

Polish-level tells, note but do not grade: [monotonous-spacing], [bounce-easing], [pulsing-dot], [blinking-cursor], [numbered-section-labels], [em-dash-overuse], [extreme-negative-tracking], [gpt-thin-border-wide-shadow], [repeating-stripes-gradient], [codex-grid-background], [image-hover-transform], monospace as costume, unthemed browser surfaces.

**10. Performance as Design** (6 items)
- LCP < 2.0s (web apps), < 1.5s (informational sites)
- CLS < 0.1 (no visible layout shifts during load)
- Skeleton quality: shapes match real content layout, shimmer animation
- Images: `loading="lazy"`, width/height dimensions set, WebP/AVIF format
- Fonts: `font-display: swap`, preconnect to CDN origins
- No visible font swap flash (FOUT) — critical fonts preloaded

---

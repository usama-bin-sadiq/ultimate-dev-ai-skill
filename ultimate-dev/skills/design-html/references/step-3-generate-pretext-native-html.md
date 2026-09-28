<!-- Moved verbatim from design-html/SKILL.md, the
     'step-3-generate-pretext-native-html' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 3: Generate Pretext-Native HTML

> **STOP.** Before writing the finalized HTML in Step 3 — the Pretext wiring patterns and API cheatsheet are the required reference for all text-layout code, Read `~/.claude/skills/gstack/design-html/sections/pretext-patterns.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

### Pretext Source Embedding

For **vanilla HTML output**, check for the vendored Pretext bundle:
```bash
_PRETEXT_VENDOR=""
_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
[ -n "$_ROOT" ] && [ -f "$_ROOT/.claude/skills/gstack/design-html/vendor/pretext.js" ] && _PRETEXT_VENDOR="$_ROOT/.claude/skills/gstack/design-html/vendor/pretext.js"
[ -z "$_PRETEXT_VENDOR" ] && [ -f ~/.claude/skills/gstack/design-html/vendor/pretext.js ] && _PRETEXT_VENDOR=~/.claude/skills/gstack/design-html/vendor/pretext.js
[ -n "$_PRETEXT_VENDOR" ] && echo "VENDOR: $_PRETEXT_VENDOR" || echo "VENDOR_MISSING"
```

- If `VENDOR` found: read the file and inline it in a `<script>` tag. The HTML file
  is fully self-contained with zero network dependencies.
- If `VENDOR_MISSING`: use CDN import as fallback:
  `<script type="module">import { prepare, layout, prepareWithSegments, walkLineRanges, layoutNextLine, layoutWithLines } from 'https://esm.sh/@chenglou/pretext'</script>`
  Add a comment: `<!-- FALLBACK: vendor/pretext.js missing, using CDN -->`

For **framework output**, add to the project's dependencies instead:
```bash
# Detect package manager
[ -f bun.lockb ] && echo "bun add @chenglou/pretext" || \
[ -f pnpm-lock.yaml ] && echo "pnpm add @chenglou/pretext" || \
[ -f yarn.lock ] && echo "yarn add @chenglou/pretext" || \
echo "npm install @chenglou/pretext"
```
Run the detected install command. Then use standard imports in the component.

### HTML Generation

Write a single file using the Write tool. Save to:
`$GSTACK_STATE_ROOT/projects/$SLUG/designs/<screen-name>-YYYYMMDD/finalized.html`

For framework output, save to:
`$GSTACK_STATE_ROOT/projects/$SLUG/designs/<screen-name>-YYYYMMDD/finalized.[tsx|svelte|vue]`

**Always include in vanilla HTML:**
- Pretext source (inlined or CDN, see above)
- CSS custom properties for design tokens from DESIGN.md / Step 1 extraction
- Fonts from the source DESIGN.md names (Google Fonts, Fontshare, or self-hosted) via `<link>` tags + `document.fonts.ready` gate before first `prepare()`
- Semantic HTML5 (`<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`)
- Responsive behavior via Pretext relayout (not just media queries)
- Breakpoint-specific adjustments at 375px, 768px, 1024px, 1440px
- ARIA attributes, heading hierarchy, focus-visible states
- `contenteditable` on text elements + MutationObserver to re-prepare + re-layout on edit
- ResizeObserver on containers to re-layout on resize
- `prefers-color-scheme` media query for dark mode
- `prefers-reduced-motion` for animation respect
- Real content extracted from the mockup (never lorem ipsum)

**Never include by default (AI slop blacklist):** an approved mockup that carries one, a DESIGN.md blessing, or an explicit user ask overrides it; say the tradeoff once.
- Purple/blue gradients as default <!-- ai-color-palette -->
- Cream-and-serif default palette <!-- cream-palette -->
- Gradient text <!-- gradient-text -->
- Generic 3-column feature grids <!-- feature-grid-3col -->
- Identical card grids, nested cards <!-- identical-cards --> <!-- nested-cards -->
- Center-everything layouts with no visual hierarchy <!-- centered-everything -->
- Kickers or icon tiles above headings <!-- kicker-above-heading --> <!-- icon-tile-stack -->
- Hero metric rows ("10k+ users") <!-- hero-metrics -->
- Decorative blobs, waves, or geometric patterns not in the mockup <!-- decorative-blobs -->
- Glowing edges or pulsing status dots <!-- dark-glow --> <!-- pulsing-dot -->
- Stock photo placeholder divs <!-- stock-photo-hero -->
- "Get Started" / "Learn More" generic CTAs not from the mockup <!-- generic-cta-copy -->
- Rounded-corner cards with drop shadows as the default component <!-- card-default-component -->
- Emoji as visual elements <!-- emoji-decoration -->
- Generic testimonial sections <!-- generic-testimonials -->
- Cookie-cutter hero sections with left-text right-image <!-- split-hero-template -->

Each `<!-- id -->` is the pattern's id in `lib/design-catalog.ts`; the design detector reports the same ids.

---

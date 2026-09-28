<!-- Moved verbatim from design-review/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Important Rules

1. **Think like a designer, not a QA engineer.** You care whether things feel right, look intentional, and respect the user. You do NOT just care whether things "work."
2. **Screenshots are evidence.** Every finding needs at least one screenshot. Use annotated screenshots (`annotatedScreenshot(pg)`) to highlight elements.
3. **Be specific and actionable.** "Change X to Y because Z" — not "the spacing feels off."
4. **Never read source code.** Evaluate the rendered site, not the implementation. (Exception: offer to write DESIGN.md from extracted observations.)
5. **AI Slop detection is your superpower.** Most developers can't evaluate whether their site looks AI-generated. You can. Be direct about it.
6. **Quick wins matter.** Always include a "Quick Wins" section — the 3-5 highest-impact fixes that take <30 minutes each.
7. **Fall back to `annotatedScreenshot(pg)` for tricky UIs.** When the snapshot tree does not surface a control you can plainly see (clickable divs, canvas buttons), take the annotated screenshot, Read it, and drive by CSS selector or `pg.getByText(...)` instead of by ref.
8. **Responsive is design, not just "not broken."** A stacked desktop layout on mobile is not responsive design — it's lazy. Evaluate whether the mobile layout makes *design* sense.
9. **Document incrementally.** Write each finding to the report as you find it. Don't batch.
10. **Depth over breadth.** 5-10 well-documented findings with screenshots and specific suggestions > 20 vague observations.
11. **Show screenshots to the user.** After every script that saves a screenshot, annotated screenshot, or responsive set, `cp` the files out of the printed `ASIDE_DIR` into `$REPORT_DIR/screenshots/` and use the Read tool on each copied file so the user can see them inline. For the responsive set (3 files), Read all three. This is critical — without it, screenshots are invisible to the user.

### Design Hard Rules

**Classifier: name the mode before you judge a pixel.** The mode is what the visitor's win looks like on THIS surface, not what the product is. A dev tool's landing page is Persuade. A fashion house's docs are Read.
- **PERSUADE** (MARKETING/LANDING PAGE: hero-driven, brand-forward, pricing, campaigns) → they decide and act. Design IS the product. Apply Landing Page Rules.
- **OPERATE** (APP UI: dashboards, admin, settings, editors, tools) → they finish a task. Scanability and native expectations beat expression; the brand lives in the details. Apply App UI Rules.
- **READ** (docs, articles, guides, changelogs) → they understand something. Structure for comprehension, then make staying worth it. Apply Read Rules.
- **EXPERIENCE** (portfolios, galleries, showcases) → they are inside the work. The artifact owns the first viewport; the interface gets out of the way. Apply Experience Rules.
- **HYBRID** (marketing shell with app-like sections) → classify per section, not per page.

**Hard rejection criteria** (instant-fail patterns — flag if ANY apply):
1. Generic SaaS card grid as first impression
2. Beautiful image with weak brand
3. Strong headline with no clear action
4. Busy imagery behind text
5. Sections repeating same mood statement
6. Carousel with no narrative purpose
7. App UI made of stacked cards instead of layout

**Litmus checks** (answer YES/NO for each — used for cross-model consensus scoring):
1. Brand/product unmistakable in first screen?
2. One strong visual anchor present?
3. Page understandable by scanning headlines only?
4. Each section has one job?
5. Are cards actually necessary?
6. Does motion improve hierarchy or atmosphere?
7. Would design feel premium with all decorative shadows removed?

**Landing page rules** (apply when classifier = PERSUADE / MARKETING/LANDING):
- First viewport reads as one composition, not a dashboard
- Brand-first hierarchy: brand > headline > body > CTA
- Typography: expressive, purposeful — no default stacks (Inter, Roboto, Arial, system)
- No flat single-color backgrounds by default: texture from the brand or a real asset, never a halo, spotlight, stripe, or grid-paper gradient (the catalog names each)
- Hero: full-bleed, edge-to-edge, no inset/tiled/rounded variants
- Hero budget: brand, one headline, one supporting sentence, one CTA group, one image
- No cards in hero. Cards only when card IS the interaction
- One job per section: one purpose, one headline, one short supporting sentence
- Motion: one authored moment on the first viewport (an entrance or a scroll-linked reveal), ease-out from a visible default; hover states only where they carry information
- Color: define CSS variables, avoid purple-on-white defaults, one accent color default
- Copy: product language not design commentary. "If deleting 30% improves it, keep deleting"
- Beautiful defaults: composition-first, brand as loudest text, two text faces max (plus a mono for data and code), cardless by default, first viewport as one composition, not a document (poster in stance, not in type size: display stays under 6rem)

**App UI rules** (apply when classifier = OPERATE / APP UI):
- Calm surface hierarchy, strong typography, few colors
- Dense but readable, minimal chrome
- Organize: primary workspace, navigation, secondary context, one accent
- Avoid: dashboard-card mosaics, thick borders, decorative gradients, ornamental icons
- Copy: utility language — orientation, status, action. Not mood/brand/aspiration
- Cards only when card IS the interaction
- Section headings state what area is or what user can do ("Selected KPIs", "Plan status")

**Read rules** (apply when classifier = READ):
- Measure 65-75ch, one reading column, headings closer to what follows than to what precedes
- Wayfinding is a feature: where am I, what is next, where do I search
- A docs index is Read, not Persuade: no hero, no CTA theater

**Experience rules** (apply when classifier = EXPERIENCE):
- The work fills the first viewport; chrome earns every pixel
- One authored transition, not a scroll-jacked tour
- Never crop the artifact to fit a template

**Universal rules** (apply to ALL types):
- Define CSS variables for color system
- No default font stacks as the display voice (Inter, Roboto, Arial, system); body/UI use on an Operate or Read surface follows the role-scoped list (DM Sans, Instrument Sans, IBM Plex Sans pass when the proposal says so)
- One job per section
- "If deleting 30% of the copy improves it, keep deleting"
- Cards earn their existence — no decorative card grids
- NEVER use small, low-contrast type (body text < 16px or contrast ratio < 4.5:1 on body text)
- NEVER put labels inside form fields as the only label (placeholder-as-label pattern — labels must be visible when the field has content)
- ALWAYS preserve visited vs unvisited link distinction (visited links must have a different color)
- NEVER float headings between paragraphs (heading must be visually closer to the section it introduces than to the preceding section)

**Reflexes no detector catches** (check by hand, every time):
- **Depth has an offset.** Shadows are offset plus soft blur. A zero-offset colored halo is decoration, not depth.
- **Secondary text on a colored surface is tinted from that hue.** Never gray.
- **More space above a heading than below it.** Read the computed values.
- **Light or dark comes from the use scene.** Who, where, under what light: one sentence. Never from the category.

**Calibration: the three looks.** AI-built interfaces land in one of three looks no matter what the product is: (1) cream ground, high-contrast serif display, terracotta or signal-red accent; (2) near-black, one neon accent, glowing edges; (3) broadsheet hairlines, italic display serif, tiny tracked mono labels. Each is fine when the brief asks for it. If the brief left the look open and you landed in one anyway, you stopped looking. The test: could someone guess your look from the category alone? From "the category, but avoiding the obvious"? Either way, start over. "It's about books, so cream and a serif" fails this test. Book cloth and jackets come in every saturated color there is.

**AI Slop blacklist:** the 11 legacy patterns, the 30 detector rules, and the 16 judgment tells are Methodology category 9. Grade against that list; do not re-derive it here.

Source: [OpenAI "Designing Delightful Frontends with GPT-5.4"](https://developers.openai.com/blog/designing-delightful-frontends-with-gpt-5-4) (Mar 2026) + gstack design methodology.

Record baseline design score and AI slop score at end of Phase 6.

---

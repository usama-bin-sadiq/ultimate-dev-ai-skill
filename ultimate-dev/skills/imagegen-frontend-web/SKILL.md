---
name: imagegen-frontend-web
description: Elite frontend image-direction skill for generating premium, conversion-aware website design references. CRITICAL OUTPUT RULE — generate ONE separate horizontal image FOR EVERY section. A landing page with 8 sections produces 8 images. Never compress multiple sections into one image. Enforces composition variety (not always left-text / right-image), background-image freedom, varied CTAs, varied hero scales (giant / mid / mini minimalist), narrative concept spine, second-read moments, and a single consistent palette across all images. Optimized for landing pages, marketing sites, and product comps that developers or coding models can accurately recreate.
---

# HARD OUTPUT RULE — READ FIRST

**Generate one separate horizontal image PER section. Always. No exceptions.**

- 1 section requested -> 1 image
- 4 sections requested -> 4 images
- 8 sections requested -> 8 images
- 12 sections requested -> 12 images
- "landing page" with no count -> default to 6 sections -> 6 images
- "full website template" -> default to 8 sections -> 8 images

Each image is one section, generated as its own image call. Never combine multiple sections into one frame. Never return a single tall image that contains the whole page.

If you can only render one image at a time, output them sequentially in the same response, one after the other, until every section has its own image. Announce each one ("Section 1 of 8: Hero", "Section 2 of 8: Trust bar", etc.).

This rule overrides any model default that wants to collapse output into a single image.

---

# HERO COMPOSITION BIAS — READ FIRST

The default **left-text / right-image hero is the most overused AI pattern**. It is allowed, but it should not be your first instinct.

Before reaching for it, consider these alternatives and pick whichever fits the brand best:
- centered over background image
- bottom-left over image
- bottom-right over image
- top-left lead
- stacked center
- image-as-canvas
- off-grid editorial
- mini minimalist
- right-text / left-image (inverted classic)

Use left-text / right-image only when it is genuinely the strongest choice — not by default.

---

# CORE DIRECTIVE: AWWWARDS-LEVEL IMAGE ART DIRECTION
You are an elite frontend image art director.

Your job is not to generate generic AI art.
Your job is to generate highly creative, premium, frontend design reference images that feel like real high-end website concepts.

Standard image generation tends to collapse into repetitive defaults:
- centered dark hero
- purple/blue AI glow
- floating meaningless blobs
- generic dashboard card spam
- weak typography hierarchy
- cloned sections
- "luxury" that is just beige serif text
- "creative" that is actually messy and unreadable
- text-heavy layouts with not enough imagery
- overly dense sections with no breathing room

Your goal is to aggressively break these defaults.

The output must feel:
- art-directed
- premium
- visually memorable
- structured
- readable
- implementation-friendly
- clearly usable as a frontend reference

Do not generate random mood art unless explicitly asked.
Default to website design comps.

---

## 1. ACTIVE BASELINE CONFIGURATION

Detail moved verbatim to `references/1-active-baseline-configuration.md`. Load it when this section matters and the pointer is not enough.

## 2. THE COMBINATORIAL VARIATION ENGINE

Detail moved verbatim to `references/2-the-combinatorial-variation-engine.md`. Load it when this section matters and the pointer is not enough.

## 3. FRONTEND REFERENCE RULE
Every generated image must clearly communicate:
- layout
- section hierarchy
- spacing
- typography scale
- visual rhythm
- CTA priority
- component styling
- image treatment
- overall design system

A developer or coding model should be able to look at the image and understand how to build it.

Do not produce vague abstract artwork when the request is for frontend.

---

## 4. HERO MINIMALISM RULES

Detail moved verbatim to `references/4-hero-minimalism-rules.md`. Load it when this section matters and the pointer is not enough.

## 5. IMAGE COUNT & PAGE SLICING

Detail moved verbatim to `references/5-image-count-page-slicing.md`. Load it when this section matters and the pointer is not enough.

## 6. CREATIVITY ESCALATION RULE
The design must show real creative ambition.

Do not settle for the first obvious layout solution.
Push the work beyond generic SaaS patterns.

Actively increase at least 3 of these:
- stronger composition
- more distinctive typography
- more confident scale contrast
- more memorable hero concept
- more interesting image treatment
- more expressive section rhythm
- more original framing / cropping
- more art-directed visual tension
- more surprising but clear layout structure

Creativity must feel intentional, not chaotic.

Do:
- make bold but controlled design decisions
- use asymmetry when it improves the page
- create visual moments that feel premium and memorable
- make the page feel designed, not auto-generated

Do not:
- default to safe template layouts
- repeat the same block structure too often
- confuse creativity with clutter
- make the page overly dense

---

## 7. IMAGE-FIRST ART DIRECTION
This skill must actively use images.

Images are not optional decoration.
Images are a core part of the frontend design language.

Strongly prefer:
- art-directed photography
- product imagery
- editorial imagery
- image crops
- framed image panels
- layered image compositions
- image-led hero sections
- image-supported storytelling blocks

Use images to:
- create visual hierarchy
- break up text-heavy layouts
- build mood and brand character
- support section transitions
- make the design easier to interpret and implement

Important:
- the design should not become text-only or card-only unless the user explicitly wants that
- if a page has multiple sections, several sections should meaningfully include imagery
- if a hero exists, it should usually contain a strong visual image, product visual, or art-directed media element
- imagery should feel premium and intentional, not like stock filler

Avoid:
- tiny useless thumbnails
- random decorative images with no structural role
- one single image and then a completely text-heavy rest of page
- overusing fake UI panels instead of real visual variety

---

## 8. ANTI-AI-SLOP RULES
Strictly avoid these patterns unless explicitly requested.

### Layout slop
- endless centered sections
- identical card rows repeated section after section
- cloned left-text/right-image blocks
- perfect but lifeless symmetry everywhere
- fake complexity without hierarchy
- empty decorative space with no purpose

### Visual slop
- default purple/blue AI gradients
- too many glowing edges
- floating spheres / blobs everywhere
- glassmorphism stacked without reason
- random futuristic details with no structure
- over-rendered noise that hides the layout

### Typography slop
- giant heading + weak tiny subcopy
- too many font moods in one page
- awkward line breaks
- lazy all-caps everywhere
- gradient headline as shortcut for "premium"

### Content slop
Ban generic copy vibes like:
- unleash
- elevate
- revolutionize
- next-gen
- seamless
- powerful solution
- transformative platform

Avoid fake brand slop:
- Acme
- Nexus
- Flowbit
- Quantumly
- NovaCore
- obvious nonsense wordmarks

Use short, believable, design-friendly copy.

### Density slop
- no over-packed sections
- no card overload in every block
- no tiny spacing between major sections
- no trying to fill every empty area
- no visually exhausting wall-of-content layouts

### Carousel / marquee slop (layout)
- infinity logo strips repeating the same 6 blobs
- “trusted by” ticker that is unreadable mosquito logos
- auto-play-style hero dots with no semantic purpose

### Data / KPI slop
- three identical stat columns (99% satisfaction, $10 saved, ∞ scale) unless user asked for KPIs
- fake dashboards with pointless charts shading the real layout

---

## 9. TYPOGRAPHY-FIRST DISCIPLINE
Typography is not filler.
Typography is a primary design material.

Always ensure:
- clear size contrast
- obvious reading order
- strong display moments
- supporting text that is readable and brief
- labels, captions, and section headings that reinforce structure

For editorial directions:
- let typography shape composition

For tech/product directions:
- let typography communicate trust and precision

---

## 10. SECTION RHYTHM RULE
A high-end site does not feel like repeated boxes.

Vary section rhythm across the page by changing:
- density
- image-to-text ratio
- alignment
- scale
- whitespace
- card grouping
- background intensity
- visual tempo

Do not let every section feel generated from the same template.

Important:
- rhythm variation should not break overall cleanliness
- keep the page visually balanced from top to bottom
- section heights may vary, but the spacing between sections should feel controlled and fairly even
- avoid abrupt jumps between very small and very large sections without enough breathing room
- the full page should feel curated, smooth, and consistent

---

## 11. COMPONENT EXECUTION GUIDELINES

### Diagonal Staggered Square Masonry
Use square image or content blocks with strong staggered vertical rhythm.
Should feel curated and graphic, not messy.

### 3D Cascading Card Deck
Cards layered as a physical stack with depth logic.
Should feel premium and tactile, not gimmicky.

### Hover-Accordion Slice Layout
A row of compressed visual slices that feel expandable.
In static images, imply interaction clearly through proportions and emphasis.

### Pristine Gapless Bento Grid
Mathematically clean grid.
No accidental gaps.
Mix large visual blocks with smaller dense information panels.

### Turning Polaroid Arc
Clustered, rotated imagery with elegant composition.
Should feel styled and intentional, not scrapbook-random.

### Off-Grid Editorial Layout
Use asymmetry and tension with control.
Must remain readable and clearly structured.

### Product UI Panel Stack
Layer UI screens or interface crops to imply a product story.
Avoid generic fake dashboards.

### Vertical Rhythm Lines
Use fine lines and spacing systems to reinforce order and elegance.
Never let them become decorative clutter.

---

## 12. DENSITY & SPACING DISCIPLINE
Do not make everything too dense.

The page should breathe.
Leave slightly more blank space between sections than a default AI-generated design would.

Rules:
- use more even vertical spacing between major sections
- keep section-to-section spacing consistent unless there is a strong design reason not to
- avoid one section feeling very cramped while the next feels too empty
- prefer a clean, balanced cadence across the page
- allow negative space to create rhythm and emphasis
- separate denser sections with calmer sections
- avoid stacking too many cards, labels, and content blocks too tightly
- smaller sections should still receive enough surrounding space so the page feels polished and intentional

A premium page should feel:
- open
- composed
- balanced
- confident
- breathable

Not:
- cramped
- noisy
- uneven
- overfilled
- visually exhausted

Section rhythm should alternate with control:
- some sections can be more content-rich
- some sections can be smaller and calmer
- but the overall spacing cadence should still feel even, clean, and deliberate

Whitespace is a design tool.
Use it deliberately.
Do not let spacing become random.

---

## 13. COLOR & MATERIAL RULES

Detail moved verbatim to `references/13-color-material-rules.md`. Load it when this section matters and the pointer is not enough.

## 14. IMAGE / MEDIA DIRECTION
If imagery is present, it must support the layout.

Allowed:
- art-directed product visuals
- refined editorial photography
- UI crops
- abstract forms with structural purpose
- framed objects
- premium texture use
- campaign-style visuals

Avoid:
- irrelevant scenery
- stock-photo cliches
- decorative junk
- visuals that overpower the page hierarchy

---

## 15. DEFAULT SITE PACKS

### 4-section pack
1. Hero
2. Features
3. Social proof / testimonial
4. CTA

### 8-section pack
1. Hero
2. Trust bar
3. Features
4. Product showcase
5. Benefits / use cases
6. Testimonials
7. Pricing
8. CTA

### 12-section pack
1. Hero
2. Trust bar
3. Feature grid
4. Product preview
5. Problem / solution
6. Benefits
7. Workflow
8. Metrics / proof / integration
9. Testimonials
10. Pricing
11. FAQ
12. CTA + footer

---

## 16. MULTI-IMAGE CONSISTENCY RULE
Because every section is its own image, consistency is critical. Across all per-section frames enforce:
- same brand world
- same type scale logic
- same spacing discipline
- same CTA family (style variations are fine, identity is not)
- same icon or illustration mood
- same image treatment (grade, framing, material vocabulary)
- same tonal language in any copy

Variation IS allowed in:
- composition anchor (per section)
- background mode (per section)
- section size and density
- which "second-read" moment appears

A viewer flipping through every per-section frame must still recognize one brand. Anything that breaks brand recall is over-variation.

---

## 17. CLARITY CHECK
Before finalizing, verify internally:

1. Is the hierarchy obvious?
2. Is the hero clean enough?
3. Is the design visually distinctive?
4. Is it free of obvious AI tells?
5. Is it premium rather than template-like?
6. Can someone code from this?
7. If multiple images exist, do they clearly belong together?
8. Is imagery used strongly enough (with variation, not one repeated crop)?
9. Does the page breathe, or is it too dense?
10. Is there enough spacing between sections?
11. Does the creativity feel intentional and premium (concept spine visible, not cluttered)?
12. Is the spacing between sections even and controlled?
13. Do smaller sections still have enough surrounding space to feel clean?
14. Is there exactly one disciplined "second-read" moment supporting scan order?
15. Is composition varied across sections (anchors and background modes mixed)?
16. Is the hero scale (giant / mid / mini) chosen and executed cleanly?
17. Is there a clear conversion path (hook -> proof -> action) even in artistic sites?
18. Is the palette consistent across all per-section images?
19. Is each image horizontal and one-section-only?
20. Is the **total number of images equal to the number of sections** (never fewer)?
21. Is the hero using a varied composition (not defaulting to left-text / right-image out of habit)?

If not, refine internally before output. If the count is wrong, regenerate the missing sections. If the hero feels like a reflexive left-text / right-image default, prefer a different composition anchor.

---

## 18. EXTRA CREATIVITY & IMPLEMENTATION EDGE

Detail moved verbatim to `references/18-extra-creativity-implementation-edge.md`. Load it when this section matters and the pointer is not enough.

## 19. RESPONSE BEHAVIOR
When the user asks for a frontend design:
1. infer site type and primary conversion goal
2. infer number of sections (if unclear, use the defaults from §5: landing page = 6, full website = 8)
3. **commit out loud** to the section count and announce it ("Generating N horizontal images, one per section")
4. plan ONE horizontal image PER SECTION — always separate generations, never collapse
5. choose Hero Scale for the whole site (giant / mid / mini)
5. choose a strong visual combination (theme, type, hero arch, section system, motion, narrative spine, second-read moment)
7. for each section: pick a Composition Anchor, Background Mode, and CTA Variation — vary across sections
8. choose 4 signature components used appropriately across sections
9. enforce hero minimalism + section size variety (some giant, some mini)
10. enforce strong image usage including full-bleed backgrounds where it fits
11. lock one consistent palette across all images
12. apply §18 EXTRA CREATIVITY & IMPLEMENTATION EDGE
13. keep spacing generous, even, and clean
14. remove AI slop (including marquee / fake KPI clichés unless requested)
15. run §17 CLARITY CHECK
16. **generate every per-section horizontal image, labeled "Section X of N: <name>"**, until the full set is delivered. Do not stop early. Do not summarize. Do not return only one image.

Do not ask unnecessary follow-up questions if a strong interpretation is possible.

---

## 20. EXAMPLE INTERPRETATIONS

### Example 1
User: "make a hero section for an AI startup"

Interpretation:
- 1 horizontal image
- Hero Scale: Mid Editorial or Giant Statement
- Composition Anchor: bottom-left text over full-bleed product/atmosphere image
- Background Mode: full-bleed image with dark tonal overlay
- CTA Variation: outlined inline + small label hint
- Palette: Deep Dark or Bold Studio Solid, one consistent accent
- no cliche dashboard spam, no purple AI glow

### Example 2
User: "design 8 sections for a fintech website"

Interpretation:
- 8 separate horizontal images (one per section)
- Hero Scale: Mid Editorial (trust-driven)
- vary Composition Anchor across sections (centered low, right-third caption, bottom-left over chart visual, stacked center for closing CTA)
- Background Mode mix: solid surface, full-bleed image background once, editorial side-image at use cases
- one consistent palette (e.g. ink + paper + single brand accent)
- conversion path: hook -> proof bar -> features -> use case -> testimonial -> pricing -> FAQ -> final CTA

### Example 3
User: "creative agency landing page, 12 sections"

Interpretation:
- 12 horizontal images (one per section)
- Hero Scale: Giant Statement OR Mini Minimalist (decisive choice, not in-between)
- editorial / poster-like direction; off-grid composition appears 2-3 times
- multiple Background Modes (full-bleed image at hero + showcase, editorial side-image at case studies, solid + accent for process)
- palette consistent throughout, with one bold accent recurring
- closing CTA section: mini minimalist, strong type, single primary action

---

## 21. FINAL GOAL
Generate frontend reference images that feel:
- artistic
- premium
- clear
- structured
- image-led
- breathable
- memorable
- anti-generic
- implementation-friendly

The result should look like a top-tier website concept with strong imagery, confident creativity, and generous spacing - not a dense, repetitive AI layout.

Each file below is loaded on demand, not at triage. 15 file(s):

- `references/10-section-rhythm-rule.md` — 10. SECTION RHYTHM RULE. <!-- Moved verbatim from imagegen-frontend-web/SKILL.md, the
- `references/11-component-execution-guidelines.md` — 11. COMPONENT EXECUTION GUIDELINES. <!-- Moved verbatim from imagegen-frontend-web/SKILL.md, the
- `references/12-density-spacing-discipline.md` — 12. DENSITY & SPACING DISCIPLINE. <!-- Moved verbatim from imagegen-frontend-web/SKILL.md, the
- `references/14-image-media-direction.md` — 14. IMAGE / MEDIA DIRECTION. <!-- Moved verbatim from imagegen-frontend-web/SKILL.md, the
- `references/15-default-site-packs.md` — 15. DEFAULT SITE PACKS. <!-- Moved verbatim from imagegen-frontend-web/SKILL.md, the
- `references/16-multi-image-consistency-rule.md` — 16. MULTI-IMAGE CONSISTENCY RULE. <!-- Moved verbatim from imagegen-frontend-web/SKILL.md, the
- `references/17-clarity-check.md` — 17. CLARITY CHECK. <!-- Moved verbatim from imagegen-frontend-web/SKILL.md, the
- `references/19-response-behavior.md` — 19. RESPONSE BEHAVIOR. <!-- Moved verbatim from imagegen-frontend-web/SKILL.md, the
- `references/20-example-interpretations.md` — 20. EXAMPLE INTERPRETATIONS. <!-- Moved verbatim from imagegen-frontend-web/SKILL.md, the
- `references/21-final-goal.md` — 21. FINAL GOAL. <!-- Moved verbatim from imagegen-frontend-web/SKILL.md, the
- `references/3-frontend-reference-rule.md` — 3. FRONTEND REFERENCE RULE. <!-- Moved verbatim from imagegen-frontend-web/SKILL.md, the
- `references/6-creativity-escalation-rule.md` — 6. CREATIVITY ESCALATION RULE. <!-- Moved verbatim from imagegen-frontend-web/SKILL.md, the
- `references/7-image-first-art-direction.md` — 7. IMAGE-FIRST ART DIRECTION. <!-- Moved verbatim from imagegen-frontend-web/SKILL.md, the
- `references/8-anti-ai-slop-rules.md` — 8. ANTI-AI-SLOP RULES. <!-- Moved verbatim from imagegen-frontend-web/SKILL.md, the
- `references/9-typography-first-discipline.md` — 9. TYPOGRAPHY-FIRST DISCIPLINE. <!-- Moved verbatim from imagegen-frontend-web/SKILL.md, the


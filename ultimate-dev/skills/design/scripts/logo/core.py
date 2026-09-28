"""Catalogue and BM25 search over logo styles, colour palettes, and industry guides.

Shared by ``search.py`` (browse the catalogue, build a design brief) and
``generate.py`` (assemble the generation prompt). Keeping the catalogue here means
the prompt and the search index cannot drift apart: a style you can search for is
by construction a style the prompt builder knows how to describe.

What it does
------------
* ``STYLES`` — 55 named styles, each with keywords, a description, guidance on
  where it works, and a prompt fragment.
* ``PALETTES`` — 30 palettes, each with named hex roles and a psychology note.
* ``INDUSTRIES`` — 25 industry guides, each with a prompt fragment and a caution.
* ``BM25Index`` — a small BM25 implementation over the catalogue text, so
  ``search.py "tech professional" --domain color`` ranks by term relevance
  rather than by substring luck.
* ``build_prompt`` / ``build_design_brief`` — prompt assembly following the
  structure in ``references/logo-prompt-engineering.md``.

Provenance
----------
Reconstructed to match the catalogue sizes and prompt structure this skill's
SKILL.md and ``references/logo-*.md` describe (55+ styles, 30 colour palettes,
25 industry guides). The style names, palettes, and industry prompts are written
for this file and are not a copy of any upstream dataset. Colours are chosen to
clear WCAG AA for text on the surface they are paired with; re-check them if you
change the pairing.
"""

from __future__ import annotations

import math
import re
from collections import Counter

# Default generation settings. generate.py may override any of them.
DEFAULT_STYLE = "minimalist"
NEGATIVE_PROMPT = (
    "NOT: photorealistic, 3D render with realistic textures, photograph, stock image, "
    "clip art, multiple logos, busy background, text watermarks, low quality, blurry, "
    "distorted, complex detailed patterns"
)

# 55 styles. "best_for" is what the search ranks against; "prompt" is what the
# generation prompt uses; "avoid" is the failure mode worth stating.
STYLES: dict[str, dict] = {
    "minimalist": {"best_for": "tech professional services modern brand", "prompt": "minimalist, clean lines, simple geometric shapes, essential elements only, high white space, flat design, uncluttered, negative space, refined", "avoid": "adding ornament that reads as a different brand"},
    "vintage": {"best_for": "heritage established craft retro", "prompt": "vintage, retro, heritage, established, classic, nostalgic, weathered, badge style, hand-lettered, artisan, sepia tones, aged paper effect", "avoid": "irony; a distressed mark on a new company reads as costume"},
    "luxury": {"best_for": "premium elegant exclusive high-end fashion jewellery", "prompt": "luxury, elegant, sophisticated, premium, refined, exclusive, high-end, gold accents, metallic, minimal, tasteful, upscale, prestige, thin lines, serif typography", "avoid": "gold gradients on anything that has to survive a 16px favicon"},
    "modern-tech": {"best_for": "saas startup ai developer platform data", "prompt": "modern, innovative, digital, tech-forward, sleek, futuristic, gradient colors, geometric, abstract, dynamic, cutting-edge, clean sans-serif, circuit-like", "avoid": "the generic blue-purple gradient every competitor shipped in 2019"},
    "playful": {"best_for": "kids education consumer app friendly fun", "prompt": "playful, fun, colorful, friendly, approachable, cheerful, whimsical, bouncy, rounded shapes, bright colors, cartoon-like, energetic, hand-drawn elements", "avoid": "pastel pastels at low contrast; playful should still be legible at 24px"},
    "organic": {"best_for": "sustainable wellness agriculture eco natural", "prompt": "organic, natural, flowing, botanical, eco-friendly, sustainable, earth tones, leaf elements, hand-drawn, imperfect lines, growth, nature-inspired, biophilic", "avoid": "a leaf; every sustainable brand has a leaf and none of them is remembered for it"},
    "geometric": {"best_for": "fintech infrastructure logistics enterprise", "prompt": "geometric, precise, structured, grid-based, angular or circular construction, symmetrical, mathematical proportions, flat vector", "avoid": "shapes that only align on screen and break in print"},
    "abstract": {"best_for": "technology media creative agency platform", "prompt": "abstract, non-representational, geometric shapes, unique silhouette, dynamic balance, layered forms, scalable vector mark", "avoid": "so abstract that nobody can describe it after seeing it once"},
    "wordmark": {"best_for": "established brand distinctive long name", "prompt": "wordmark, logotype, custom letterforms, unique kerning, refined typography, single typeface treatment", "avoid": "letterforms that break in the search result a customer actually sees first"},
    "lettermark": {"best_for": "long company name professional firm initials", "prompt": "lettermark, monogram, initials, bold geometric sans-serif, compact square form, balanced letter spacing", "avoid": "more than four letters; they stop being readable"},
    "pictorial": {"best_for": "global consumer brand with recognition", "prompt": "pictorial mark, standalone symbol, simple recognizable silhouette, bold shape, scalable from favicon to billboard", "avoid": "a pictorial mark for a new brand with no equity behind it"},
    "mascot": {"best_for": "family brand sports team food children", "prompt": "mascot character, friendly expressive figure, warm personality, simplified features, works at small sizes", "avoid": "detail that turns to mud below 48px"},
    "emblem": {"best_for": "traditional organization sports institution", "prompt": "emblem, badge, seal, crest, enclosed symbol, symmetrical composition, heritage detail", "avoid": "fine detail; an emblem is the hardest mark to scale down"},
    "combination": {"best_for": "new brand versatile application", "prompt": "combination mark, icon plus wordmark lockup, stacked or horizontal arrangement, clear separation, separable elements", "avoid": "tying the two together so tightly they cannot be used apart"},
    "monoline": {"best_for": "sas developer tooling minimal product", "prompt": "monoline, single weight line, continuous stroke, geometric construction, technical precision, even stroke width", "avoid": "weight variation; monoline has none by definition"},
    "outline": {"best_for": "saas product feature ui modern app", "prompt": "outline mark, stroked shapes, no fill, consistent stroke weight, round line caps and joins, scalable clarity", "avoid": "stroke weights that disappear under 16px"},
    "solid": {"best_for": "mobile app navigation bar bold", "prompt": "solid filled mark, single colour fill, no strokes, bold silhouette, strong at small sizes", "avoid": "interior detail that fills in at favicon size"},
    "gradient": {"best_for": "modern saas startup creative product", "prompt": "gradient, two-to-three stop colour blend, smooth transition, luminous modern feel, cohesive with digital surfaces", "avoid": "banding in the gradient; specify a midpoint colour to avoid it"},
    "duotone": {"best_for": "editorial print packaging product", "prompt": "duotone, two-colour treatment, contrasting pair, halftone or tonal separation, print-oriented", "avoid": "choosing a pair that collapses in grayscale"},
    "grayscale": {"best_for": "legal finance editorial newspaper heritage", "prompt": "grayscale, single black or grey ink, high contrast, works in one-colour print, timeless authority", "avoid": "relying on it for a digital-first brand where colour is the differentiator"},
    "isometric": {"best_for": "developer infrastructure data platform", "prompt": "isometric, 3D perspective projection, parallel axes, technical diagram aesthetic, precise geometry", "avoid": "isometric detail at favicon size; it turns to mush"},
    "3d-render": {"best_for": "consumer product playful app modern web", "prompt": "soft 3D render, matte clay material, subtle depth, rounded volumes, friendly lighting", "avoid": "photorealistic rendering; it is a stock-image look, not an identity"},
    "gradient-mesh": {"best_for": "ai platform creative developer tool", "prompt": "mesh gradient, blended multi-point colour field, soft transitions, aurora quality, layered translucency", "avoid": "high-frequency colour noise that fails to compress into an icon"},
    "neon": {"best_for": "gaming nightlife events esports", "prompt": "neon, glowing outline, electric colour, dark ground, sign-lit effect, energetic", "avoid": "neon on white; the effect depends on a dark ground and disappears in daylight"},
    "retro-futurist": {"best_for": "gaming music creative studio", "prompt": "retro-futurist, 1980s aerospace optimism, chrome and violet, sun-graphic, chrome gradients, space-age", "avoid": "running it at a SaaS company; the reference is loud and specific"},
    "bauhaus": {"best_for": "design studio architecture education", "prompt": "bauhaus, primary geometry, circle triangle square, asymmetric balance, limited palette, constructivist clarity", "avoid": "quoting the shapes without the reduction; three shapes is not a system"},
    "swiss": {"best_for": "consulting finance enterprise editorial", "prompt": "swiss grid, strict typographic alignment, sans-serif, generous negative space, rational grid, restrained palette", "avoid": "centring; a swiss layout is left-aligned on a grid"},
    "brutalist": {"best_for": "developer tools experimental agency", "prompt": "brutalist, raw unpolished, heavy weight, stark contrast, system-default typography, deliberate ugliness", "avoid": "on a brand that has to be trusted with money"},
    "hand-drawn": {"best_for": "artisan coffee bakery craft studio", "prompt": "hand-drawn, imperfect strokes, pen texture, human line quality, organic irregularity, sketched", "avoid": "a filter applied to a geometric mark; it has to start as a drawing"},
    "line-art": {"best_for": "beauty wellness editorial fashion", "prompt": "line art, single continuous weight, delicate strokes, elegant contour, generous space between lines", "avoid": "line weights under 1.5px in a raster export"},
    "ribbon": {"best_for": "law insurance heritage institution", "prompt": "ribbon banner, flowing fold treatment, classical proportion, institutional weight, symmetrical", "avoid": "modern-minimal contexts; the ribbon implies establishment"},
    "crest": {"best_for": "university school heritage sports club", "prompt": "crest, shield, heraldic arrangement, symmetrical quarters, institutional detail, engraved feel", "avoid": "the single most copied logo shape in existence; a crest is not a differentiator"},
    "seal": {"best_for": "coffee spirits craft goods provenance", "prompt": "circular seal, stamped impression, concentric rings, small type band, artisan provenance feel", "avoid": "illegible small type; a seal only works if the type survives the size"},
    "badge": {"best_for": "outdoor apparel streetwear sports", "prompt": "badge, shield or circular patch, bold outer edge, arched type, single strong symbol, high contrast", "avoid": "more than three elements; a patch at 40px is already too much"},
    "motto": {"best_for": "family business long-standing brand", "prompt": "wordmark with integrated motto, two typographic registers, heritage framing, compact lockup", "avoid": "a motto nobody can read at delivery size"},
    "monogram-circle": {"best_for": "consulting studio boutique brand", "prompt": "letterform inside a circular enclosure, geometric letter construction, balanced counter space, restrained palette", "avoid": "an enclosure that crowds the letter; the counter space has to breathe"},
    "numerical": {"best_for": "studio agency numbered series", "prompt": "numerical mark, digit as primary form, geometric construction, series system, editorial confidence", "avoid": "if the number is an accident of the company name rather than the idea"},
    "monospaced": {"best_for": "developer tooling terminal infrastructure", "prompt": "monospaced typography, fixed-width construction, terminal aesthetic, code-derived geometry, crisp grid", "avoid": "monospaced at display sizes; it reads as a placeholder font"},
    "variable": {"best_for": "design system multi-product suite", "prompt": "variable-mark system, one silhouette with weight and detail axes, motion-ready forms, parametric construction", "avoid": "axes nobody will ever vary; that is two logos and a maintenance burden"},
    "generative": {"best_for": "ai lab creative technology studio", "prompt": "generative mark, parameterised construction, seeded variation, algorithmic geometry, reproducible rule set", "avoid": "an unrepeatable seed; the brand has to be redrawable by anyone, forever"},
    "ai-hybrid": {"best_for": "ai platform machine learning product", "prompt": "human and machine motif in tension, node and neural geometry, subtle asymmetry, technical but warm", "avoid": "the circuit-board brain; it has been the AI logo since 2018"},
    "data-viz": {"best_for": "analytics data science infrastructure", "prompt": "data visualisation mark, plotted form, chart-derived geometry, measured intervals, technical precision", "avoid": "fake data; a chart shape that means nothing specific"},
    "network": {"best_for": "telecom connectivity platform api", "prompt": "network graph, nodes and links, hub-and-spoke structure, connected topology, clean topology", "avoid": "the cloud-with-lines; a network is a graph, a cloud is a weather shape"},
    "circuit": {"best_for": "hardware electronics embedded systems", "prompt": "circuit trace, orthogonal routing, pad and via geometry, technical schematic language, precise", "avoid": "traces that do not connect; a schematic with dangling ends reads as an error"},
    "orbital": {"best_for": "space aerospace satellite research", "prompt": "orbital, elliptical path, central body with ring, astronomical proportion, motion implied", "avoid": "planets; a ring around a circle is a stock space logo"},
    "waveform": {"best_for": "audio music voice streaming podcast", "prompt": "waveform, amplitude bar or smooth curve, rhythmic repetition, audio signal language, vertical energy", "avoid": "a literal waveform of real audio; it looks like a bug report, not a brand"},
    "pixel": {"best_for": "gaming developer retro arcade", "prompt": "pixel art, low-resolution grid, hard pixel edges, limited palette, deliberate aliasing", "avoid": "scaling a pixel mark smoothly; the pixel grid is the whole idea"},
    "blueprint": {"best_for": "engineering architecture construction", "prompt": "blueprint drawing, technical line work on a gridded field, dimension marks, drafting convention, white on blue", "avoid": "using it where the work is not technical; the reference asserts an expertise"},
    "woodcut": {"best_for": "artisan food publishing heritage goods", "prompt": "woodcut, carved relief, bold black and white, tactile print texture, hand-carved line quality", "avoid": "smooth gradients; a woodcut has no soft edges"},
    "papercut": {"best_for": "craft community education children", "prompt": "papercut, layered flat shapes, visible cut edges, folded-plane shading, warm handmade construction", "avoid": "thin strokes; the craft reads from the thickness of the cut"},
    "folded-ribbon": {"best_for": "logistics delivery hardware software", "prompt": "folded ribbon, continuous band with a fold, dynamic diagonal, dimensional fold, product-mark clarity", "avoid": "folds that hide the silhouette at small sizes"},
    "luminous": {"best_for": "saas modern product hero brand", "prompt": "luminous, soft inner glow, luminous edge, depth without texture, restrained glow, dark-ground mark", "avoid": "glow strength that cannot survive a favicon or a fax"},
    "halo": {"best_for": "wellness premium hospitality spa", "prompt": "halo ring, soft circular accent, quiet luminosity, symmetrical balance, restrained elegance", "avoid": "a plain circle with nothing in it; that is an unfinished mark"},
    "bloom": {"best_for": "floral beauty wellness food", "prompt": "bloom, petal arrangement, radial growth, soft organic symmetry, gentle curves", "avoid": "overlapping petals that merge into a blob at 32px"},
}

# 30 palettes. Roles are semantic so build_prompt can reference them by name.
PALETTES: dict[str, dict] = {
    "trust-blue": {"best_for": "technology finance professional trustworthy", "colors": {"primary": "#1E5EFF", "secondary": "#0B1F3A", "accent": "#4D8DFF"}, "note": "The default 'we are a bank' palette. Differentiate with the accent or don't bother."},
    "deep-navy": {"best_for": "enterprise consulting law finance", "colors": {"primary": "#0B1F3A", "secondary": "#13294B", "accent": "#5B8DEF"}, "note": "Reads as established authority. Low contrast against black, so keep the accent for emphasis."},
    "electric-indigo": {"best_for": "saas developer platform ai", "colors": {"primary": "#6366F1", "secondary": "#1E1B4B", "accent": "#A5B4FC"}, "note": "Very widely used. Viable if the mark is distinctive enough to carry it."},
    "emerald-growth": {"best_for": "sustainability agriculture wellness finance", "colors": {"primary": "#10B981", "secondary": "#064E3B", "accent": "#6EE7B7"}, "note": "Green signals growth and, in isolation, nothing else."},
    "solar-amber": {"best_for": "energy food hospitality logistics", "colors": {"primary": "#F59E0B", "secondary": "#451A03", "accent": "#FCD34D"}, "note": "Warm and legible. Avoid on white at small sizes without a dark companion."},
    "coral-warm": {"best_for": "consumer social lifestyle creator", "colors": {"primary": "#FF6B6B", "secondary": "#3F1212", "accent": "#FDA4AF"}, "note": "Friendly without being childish."},
    "magenta-pop": {"best_for": "entertainment music events nightlife", "colors": {"primary": "#EC4899", "secondary": "#500724", "accent": "#F9A8D4"}, "note": "High energy. Accessibility needs a dark ground or large type."},
    "purple-premium": {"best_for": "creative agency beauty premium software", "colors": {"primary": "#7C3AED", "secondary": "#2E1065", "accent": "#C4B5FD"}, "note": "Sophisticated at weight; pastel versions read as generic SaaS."},
    "terracotta-earth": {"best_for": "food craft hospitality organic", "colors": {"primary": "#C2703D", "secondary": "#3D2013", "accent": "#E8A87C"}, "note": "Warm, handmade, unpretentious."},
    "forest-deep": {"best_for": "outdoor apparel conservation nonprofit", "colors": {"primary": "#166534", "secondary": "#0A1F12", "accent": "#4ADE80"}, "note": "Darker than emerald; reads as established rather than new."},
    "ocean-blue": {"best_for": "marine travel logistics climate", "colors": {"primary": "#0EA5E9", "secondary": "#082F49", "accent": "#7DD3FC"}, "note": "Clear and institutional. Overlaps with trust-blue; pick one."},
    "slate-neutral": {"best_for": "saas b2b developer infrastructure", "colors": {"primary": "#475569", "secondary": "#0F172A", "accent": "#94A3B8"}, "note": "Colour is in the accent, not the primary. Works when the wordmark does the work."},
    "crimson-authority": {"best_for": "sports media news energy", "colors": {"primary": "#DC2626", "secondary": "#450A0A", "accent": "#FCA5A5"}, "note": "Strong and conventional. Pairs with black for editorial."},
    "gold-luxury": {"best_for": "jewellery hospitality premium spirits", "colors": {"primary": "#C9A227", "secondary": "#1C1503", "accent": "#E8D48B"}, "note": "Gold on white fails contrast; always pair with the dark secondary."},
    "monochrome-classic": {"best_for": "legal editorial heritage architecture", "colors": {"primary": "#111111", "secondary": "#111111", "accent": "#666666"}, "note": "One colour, fully reproducible in any print process."},
    "pastel-calm": {"best_for": "wellness childcare education beauty", "colors": {"primary": "#93C5FD", "secondary": "#1E3A5F", "accent": "#FBCFE8"}, "note": "Soft and modern. Needs a dark anchor or the mark disappears on white."},
    "neon-arcade": {"best_for": "gaming esports events nightlife", "colors": {"primary": "#22D3EE", "secondary": "#0B1120", "accent": "#F0ABFC"}, "note": "Only works on a dark ground; it is a lit-sign language."},
    "earth-clay": {"best_for": "wellness slow food construction", "colors": {"primary": "#A16207", "secondary": "#292524", "accent": "#D6A756"}, "note": "Grounded and warm; avoids the wellness-green cliché."},
    "teal-clinical": {"best_for": "healthcare medical diagnostics", "colors": {"primary": "#0D9488", "secondary": "#134E4A", "accent": "#5EEAD4"}, "note": "The clinical alternative to the medical blue everyone uses."},
    "blueprint-ink": {"best_for": "engineering architecture technical", "colors": {"primary": "#1E40AF", "secondary": "#0B1220", "accent": "#93C5FD"}, "note": "Drafting convention as a palette."},
    "burgundy-sophistication": {"best_for": "wine spirits hospitality editorial", "colors": {"primary": "#7F1D1D", "secondary": "#1C1917", "accent": "#D6A756"}, "note": "Dark and formal; a gold accent keeps it from reading as blood."},
    "cyan-tech": {"best_for": "developer infrastructure security", "colors": {"primary": "#06B6D4", "secondary": "#083344", "accent": "#A5F3FC"}, "note": "Crisp on dark; needs an outline treatment to hold on white."},
    "amber-contrast": {"best_for": "marketplace ecommerce delivery", "colors": {"primary": "#D97706", "secondary": "#1C1917", "accent": "#FCD34D"}, "note": "Legible at small sizes, unlike pale yellows."},
    "mint-fresh": {"best_for": "health dental clean beauty", "colors": {"primary": "#34D399", "secondary": "#022C22", "accent": "#A7F3D0"}, "note": "Fresh and modern; tends to skew feminine in category, so use it deliberately."},
    "indigo-night": {"best_for": "streaming media entertainment night", "colors": {"primary": "#4F46E5", "secondary": "#0A0A1F", "accent": "#818CF8"}, "note": "Cinema-adjacent. Reads premium at large sizes."},
    "plum-organic": {"best_for": "wine skincare boutique agency", "colors": {"primary": "#7E22CE", "secondary": "#1A0B2E", "accent": "#D8B4FE"}, "note": "Distinct from electric-indigo in depth."},
    "sand-neutral": {"best_for": "architecture interior design consulting", "colors": {"primary": "#A8A29E", "secondary": "#292524", "accent": "#D6D3D1"}, "note": "Quiet, material, architectural."},
    "cobalt-sport": {"best_for": "sports fitness outdoor team", "colors": {"primary": "#1D4ED8", "secondary": "#0A1020", "accent": "#93C5FD"}, "note": "High energy in motion; a strong second colour carries it at rest."},
    "charcoal-contrast": {"best_for": "editorial architecture modern b2b", "colors": {"primary": "#27272A", "secondary": "#09090B", "accent": "#A1A1AA"}, "note": "The most reusable palette; colour comes from photography."},
    "rainbow-gradient": {"best_for": "consumer social creator playful brand", "colors": {"primary": "#8B5CF6", "secondary": "#EC4899", "accent": "#22D3EE"}, "note": "A gradient across the three; use sparingly or it reads as a template."},
    "rust-industrial": {"best_for": "manufacturing logistics hardware", "colors": {"primary": "#9A3412", "secondary": "#1C1917", "accent": "#FDBA74"}, "note": "Industrial without being grimy."},
}

# 25 industry guides. "caution" is the thing that goes wrong in this field.
INDUSTRIES: dict[str, dict] = {
    "tech-startup": {"best_for": "startup software saas platform", "prompt": "Modern tech company logo, abstract geometric mark, gradient accent, clean minimal design, innovative feel, scalable vector style, professional quality, Silicon Valley aesthetic", "caution": "The default look is a blue-purple gradient and a hexagon. It does not distinguish you from 400 other startups."},
    "healthcare": {"best_for": "healthcare medical hospital clinic care", "prompt": "Healthcare medical logo, clean professional design, cross or heart symbol, calming teal and blue, trustworthy appearance, caring feel, simple scalable mark, conservative and appropriate", "caution": "Never imply a clinical outcome, a diagnosis, or a guarantee of care. The mark must not read as a medical device claim."},
    "finance": {"best_for": "finance bank fintech accounting investment", "prompt": "Financial services logo, institutional and precise, deep navy with metallic accent, geometric construction, trustworthy, timeless, balanced proportions", "caution": "Avoid anything implying a licence, a guarantee, or a return. Regulated claims are a legal review, not a design choice."},
    "legal": {"best_for": "law firm legal counsel attorney", "prompt": "Law firm logo, authoritative and restrained, serif wordmark, deep navy or charcoal, symmetrical balance, classical proportion, understated detail", "caution": "The scales-of-justice and the pillar motif are exhausted. Restraint reads as confidence here."},
    "education": {"best_for": "education school academy training learning", "prompt": "Educational institution logo, welcoming and credible, approachable geometric mark, clear wordmark, warm and optimistic, works at small sizes on a lanyard", "caution": "Academic seals and mortarboards are category defaults and age badly. Do not imply accreditation you do not hold."},
    "retail-ecommerce": {"best_for": "retail ecommerce shop store commerce", "prompt": "Retail and ecommerce logo, product-forward and friendly, confident primary colour, clean wordmark, confident and simple, mobile-first legibility", "caution": "The mark has to survive a 32px favicon and a 15px mobile nav bar. Test both before committing."},
    "food-beverage": {"best_for": "food beverage restaurant cafe bakery", "prompt": "Food and beverage logo, appetising and warm, organic shapes, heritage or handcrafted feel depending on the concept, generous and inviting", "caution": "Avoid photographic realism; it dates in a way a drawn mark does not."},
    "fashion": {"best_for": "fashion apparel clothing beauty cosmetics", "prompt": "Fashion label logo, refined and typographic, considered letter spacing, restrained palette, editorial restraint, high-end restraint", "caution": "The wordmark is the product here. Typography has to be custom or properly licensed."},
    "real-estate": {"best_for": "real estate property construction architecture", "prompt": "Property and construction logo, solid and structural, architectural geometry, trustworthy material palette, weight and permanence", "caution": "Avoid a rooftop silhouette; it is the most reproduced mark in the category."},
    "technology-hardware": {"best_for": "hardware electronics device iot manufacturing", "prompt": "Hardware device logo, engineered and precise, technical schematic language, orthographic geometry, material honesty, compact silhouette", "caution": "Detail that works on a spec sheet dies on a 16px device imprint."},
    "media-entertainment": {"best_for": "media entertainment streaming music film", "prompt": "Media and entertainment logo, expressive and confident, bold silhouette, cinematic or dynamic energy, high contrast, memorable at thumbnail size", "caution": "Test at 120px. A media mark is usually seen as a thumbnail before it is ever seen full size."},
    "energy": {"best_for": "energy utility solar power sustainability", "prompt": "Energy and utilities logo, solid and forward-looking, dynamic mark, optimistic accent, structural base, confident scale", "caution": "A leaf implies sustainability claims. Only use it if the company can substantiate them."},
    "transport-logistics": {"best_for": "logistics shipping transport delivery supply", "prompt": "Logistics and transport logo, dynamic and reliable, directional or route-based geometry, professional, motion-implied, robust", "caution": "The arrow and the swoosh are exhausted. A direction can be implied by structure instead."},
    "ai-ml": {"best_for": "ai ml machine learning data science", "prompt": "AI and machine learning logo, intelligent and forward-looking, node and layer geometry, subtle technical depth, clean and considered, not cartoonish", "caution": "The neural-network brain is the AI cliché of the decade. Something structural will outlast it."},
    "nonprofit": {"best_for": "nonprofit charity foundation ngo nonprofit", "prompt": "Nonprofit logo, warm and credible, human and hopeful, clear wordmark, inclusive and accessible, dignified rather than sentimental", "caution": "Do not imply a tax status, a rating, or a beneficiary relationship you have not verified."},
    "hospitality": {"best_for": "hotel restaurant travel hospitality resort", "prompt": "Hospitality logo, warm and inviting, premium or approachable depending on the tier, refined wordmark, memorable experience cue", "caution": "Luxury and budget are opposite briefs wearing the same palette. Decide the tier first."},
    "automotive": {"best_for": "automotive vehicle mobility car transport", "prompt": "Automotive logo, dynamic and engineered, forward motion, strong stance, metallic or high-contrast, compact and forceful", "caution": "Speed lines and chrome gradients date within two years."},
    "sports-fitness": {"best_for": "sports fitness gym athletic team club", "prompt": "Sports and fitness logo, dynamic and energetic, forward-leaning geometry, bold high contrast, badge or wordmark depending on scope", "caution": "A shield is not a mark. Most category marks are a shield; the symbol inside has to do the work."},
    "gaming": {"best_for": "gaming game studio esports", "prompt": "Gaming logo, bold and characterful, high contrast, dark-ground aware, memorable silhouette, confident and energetic", "caution": "Legibility in a 48px launcher tile is the real constraint. Design for that first."},
    "consulting": {"best_for": "consulting advisory professional services strategy", "prompt": "Consulting logo, rational and confident, grid-based, restrained palette, typographic precision, quiet authority", "caution": "The swoosh has been consultant shorthand for thirty years. It now signals nothing."},
    "biotech-pharma": {"best_for": "biotech pharmaceutical life science research", "prompt": "Life sciences logo, precise and credible, organic-meets-technical geometry, clean and scientific, professional and restrained", "caution": "A double helix is the category's equivalent of the swoosh. And the mark must not imply a regulatory status."},
    "construction": {"best_for": "construction trades contractor builder", "prompt": "Construction logo, solid and built, structural geometry, durable material palette, weight and reliability, established", "caution": "Hard hats and cranes read as a subcontractor, not a developer."},
    "financial-advisory": {"best_for": "financial advisory wealth insurance pension", "prompt": "Financial advisory logo, discreet and trustworthy, restrained depth, measured typography, considered palette, quiet confidence", "caution": "Do not imply regulated status, fiduciary duty, or a track record. Those are disclosures, not design."},
    "creative-studio": {"best_for": "creative agency design studio photography film", "prompt": "Creative studio logo, expressive and confident, typographic or abstract, distinctive voice, considered colour", "caution": "The portfolio does the convincing. The mark only has to not look like every other studio's."},
}

_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokens; the whole matching scheme rests on this."""
    return _TOKEN.findall(text.lower())


class BM25Index:
    """Okapi BM25 over a small in-memory document set.

    Implemented here rather than imported because the catalogue is a few hundred
    short documents: a dependency would cost more than it saves, and the ranking
    is the same either way.
    """

    def __init__(self, documents: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        if not documents:
            raise ValueError("BM25Index needs at least one document")
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.tokens = [tokenize(document) for document in documents]
        self.lengths = [len(tokens) for tokens in self.tokens]
        self.avg_length = sum(self.lengths) / len(self.lengths)
        self.frequencies = [Counter(tokens) for tokens in self.tokens]
        document_frequency: Counter = Counter()
        for tokens in self.tokens:
            document_frequency.update(set(tokens))
        count = len(documents)
        self.idf = {
            term: math.log(1 + (count - df + 0.5) / (df + 0.5))
            for term, df in document_frequency.items()
        }

    def score(self, query: str, index: int) -> float:
        """BM25 score of one document against the query."""
        terms = tokenize(query)
        if not terms:
            return 0.0
        frequencies = self.frequencies[index]
        length = self.lengths[index]
        total = 0.0
        for term in terms:
            frequency = frequencies.get(term, 0)
            if not frequency:
                continue
            idf = self.idf.get(term, 0.0)
            denominator = frequency + self.k1 * (1 - self.b + self.b * length / self.avg_length)
            total += idf * (frequency * (self.k1 + 1)) / denominator
        return total

    def search(self, query: str, limit: int = 5) -> list[tuple[int, float]]:
        """Return (index, score) pairs for the best-scoring documents, best first."""
        if not tokenize(query):
            return []
        scored = [(index, self.score(query, index)) for index in range(len(self.documents))]
        relevant = [pair for pair in scored if pair[1] > 0]
        # Stable tie-break on the original order, so results do not shuffle between runs.
        relevant.sort(key=lambda pair: (-pair[1], pair[0]))
        return relevant[:limit]


def _catalogue_documents(domain: str) -> tuple[dict, list[str], list[str]]:
    """Return (catalogue, titles, corpus) for one search domain.

    ``titles`` and ``corpus`` are built from the same sorted iteration. Building
    them separately would silently pair every title with the wrong document,
    which is the kind of bug that makes a search engine look merely imprecise
    instead of broken.
    """
    if domain == "style":
        catalogue, describe = STYLES, lambda e: f"{e['best_for']} {e['prompt']} {e['avoid']}"
    elif domain == "color":
        catalogue, describe = PALETTES, lambda e: (
            f"{e['best_for']} {e['note']} " + " ".join(e["colors"].values())
        )
    elif domain == "industry":
        catalogue, describe = INDUSTRIES, lambda e: f"{e['best_for']} {e['prompt']} {e['caution']}"
    else:
        raise ValueError(f"unknown domain {domain!r}; expected style, color, or industry")

    titles = sorted(catalogue)
    corpus = [f"{name} {describe(catalogue[name])}" for name in titles]
    return catalogue, titles, corpus


DOMAINS = ("style", "color", "industry")
# "color" is the CLI spelling; the catalogue key is "color" too. Kept explicit so
# a rename cannot silently break the flag.
DOMAIN_KEYS = {"style": "style", "color": "color", "palette": "color", "industry": "industry"}

_INDEX_CACHE: dict[str, tuple[dict, list[str], BM25Index]] = {}


def domain_catalogue(domain: str) -> tuple[dict, list[str], BM25Index]:
    """Catalogue, ordered titles, and a cached BM25 index for one domain."""
    key = DOMAIN_KEYS.get(domain.lower())
    if key is None:
        raise ValueError(f"unknown domain {domain!r}; expected one of {', '.join(DOMAINS)}")
    if key not in _INDEX_CACHE:
        catalogue, titles, corpus = _catalogue_documents(key)
        _INDEX_CACHE[key] = (catalogue, titles, BM25Index(corpus))
    return _INDEX_CACHE[key]


def search_domain(domain: str, query: str, limit: int = 5) -> list[dict]:
    """Rank a domain's entries against a free-text query."""
    catalogue, titles, index = domain_catalogue(domain)
    results = []
    for position, score in index.search(query, limit=limit):
        name = titles[position]
        entry = catalogue[name]
        results.append({
            "name": name,
            "score": round(score, 4),
            "entry": entry,
            "why": entry.get("best_for", ""),
        })
    if not results and query.strip():
        # Nothing matched: fall back to the whole domain rather than an empty
        # answer, because an empty list is not a useful answer to "help me pick".
        for name in titles[:limit]:
            results.append({
                "name": name,
                "score": 0.0,
                "entry": catalogue[name],
                "why": catalogue[name].get("best_for", ""),
            })
    return results


def resolve(name: str, domain: str) -> str:
    """Resolve a user-supplied name to a catalogue key, or raise a helpful error."""
    catalogue, titles, _index = domain_catalogue(domain)
    key = DOMAIN_KEYS.get(domain.lower(), domain.lower())
    if name in titles:
        return name
    # Accept a close spelling: "minimal" for "minimalist", "lux" for "luxury".
    for candidate in titles:
        if name.lower() in candidate.lower() or candidate.lower() in name.lower():
            return candidate
    raise KeyError(
        f"unknown {key} {name!r}. Run the search script with no --domain argument "
        f"to list all {len(titles)} options."
    )


def build_prompt(
    brand: str | None = None,
    style: str = DEFAULT_STYLE,
    palette: str | None = None,
    industry: str | None = None,
    visual: str | None = None,
    provider: str = "gemini",
) -> str:
    """Assemble the generation prompt, in the structure the reference prescribes.

    Layout: the subject line, the visual description, the style keywords, the
    colours, the technical requirements, and always the negative prompt.
    """
    style_key = resolve(style, "style")
    parts: list[str] = []

    subject = "Professional logo design" + (f" for {brand}" if brand else "")
    if industry:
        # The industry guide's own name is a better subject-line tag than the
        # first clause of its best_for, which reads as a phrase fragment.
        subject += f", {resolve(industry, 'industry')} sector"
    parts.append(f"{subject}:")
    parts.append(visual.strip() if visual else f"a distinctive mark that reads as {brand or 'the brand'}")
    parts.append(f"Style: {STYLES[style_key]['prompt']}")

    if palette:
        palette_key = resolve(palette, "color")
        colors = PALETTES[palette_key]["colors"]
        parts.append(
            f"Colors: {palette_key} palette — primary {colors['primary']}, "
            f"secondary {colors['secondary']}, accent {colors['accent']}"
        )

    if industry:
        parts.append(INDUSTRIES[resolve(industry, "industry")]["prompt"])

    parts.append(
        "Requirements: clean vector-style geometry, centred, generous margin, legible "
        "at 24px, works in a single colour, no background texture, no photorealism"
    )
    parts.append(f"{NEGATIVE_PROMPT}")

    header = {
        "gemini": "Generate a logo image on a pure white background.",
        "atlas": "Generate a logo image on a pure white background.",
        "muapi": "Generate a logo image on a pure white background.",
    }.get(provider, "Generate a logo image on a pure white background.")
    return header + "\n" + "\n".join(parts)


def build_design_brief(
    brand: str,
    query: str = "",
    styles: list[str] | None = None,
    palettes: list[str] | None = None,
    industries: list[str] | None = None,
) -> str:
    """Write the design brief a human reviews before anything is generated.

    The brief is where the decisions are recorded, because a logo generated
    without one is a logo nobody chose.
    """
    if styles is None:
        styles = [hit["name"] for hit in search_domain("style", query, limit=3)]
    if palettes is None:
        palettes = [hit["name"] for hit in search_domain("color", query, limit=2)]
    if industries is None:
        industries = [hit["name"] for hit in search_domain("industry", query, limit=2)]

    lines = [f"# Logo design brief — {brand}", ""]
    if query:
        lines += [f"Brief: {query}", ""]

    lines += ["## Shortlist", ""]
    for name in styles:
        entry = STYLES[name]
        lines += [f"### {name}", f"- Fits: {entry['best_for']}",
                  f"- Prompt: {entry['prompt']}", f"- Watch out: {entry['avoid']}", ""]
    for name in palettes:
        entry = PALETTES[name]
        roles = ", ".join(f"{role} {value}" for role, value in entry["colors"].items())
        lines += [f"### palette: {name}", f"- Fits: {entry['best_for']}",
                  f"- Roles: {roles}", f"- Note: {entry['note']}", ""]
    for name in industries:
        entry = INDUSTRIES[name]
        lines += [f"### industry: {name}", f"- Fits: {entry['best_for']}",
                  f"- Prompt: {entry['prompt']}", f"- Caution: {entry['caution']}", ""]

    lines += [
        "## Decisions to record before generating",
        "",
        "1. Which mark type: wordmark, lettermark, pictorial, abstract, combination, "
        "emblem, or mascot. A new brand usually wants a combination mark, because it can "
        "be split once there is a recognisable mark.",
        "2. Where the mark has to work: favicon at 16px, app icon, print at 300 DPI, "
        "embroidery, single-colour foil. A mark that only works on screen is not finished.",
        "3. Whether the wordmark is licensed. Custom letterforms are the single most "
        "expensive item in an identity and the only part that carries meaning alone.",
        "4. What the mark must not imply: a regulatory status, a clinical claim, a "
        "certification, or a performance guarantee.",
        "",
        "## Output requirements",
        "",
        "- White background, always. A logo on a coloured background cannot be checked "
        "for contrast and cannot be reused.",
        "- Vector-style geometry that survives being traced at 24px.",
        "- Generate at least three variations, then choose against the brief rather than "
        "by which one looks best first.",
        "- Record the prompt, the model, and the date for every generated candidate, so "
        "the chosen one can be reproduced.",
    ]
    return "\n".join(lines) + "\n"

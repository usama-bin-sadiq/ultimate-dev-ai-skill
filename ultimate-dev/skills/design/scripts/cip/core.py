"""Catalogue and BM25 search over CIP deliverables, styles, industries, and mockup settings.

Shared by ``search.py`` (browse, build a CIP brief), ``generate.py`` (assemble the
mockup prompt), and ``render-html.py`` (group the outputs for a presentation).

What it does
------------
* ``DELIVERABLES`` — 52 corporate identity deliverables, each with its production
  constraints, so a generated mockup is a usable mockup and not a pretty picture
  of an impossible object.
* ``STYLES`` — 20 corporate identity styles with colours, type, materials, finishes.
* ``INDUSTRIES`` — 20 sectors, each with the deliverables that matter most to it.
* ``MOCKUPS`` — photographic mockup settings, with the camera and lighting notes
  that decide whether a mockup reads as a photograph.
* ``BM25Index`` — the same small BM25 as the logo catalogue, for the same reason.
* ``build_mockup_prompt`` / ``build_cip_brief`` — prompt and brief assembly.

Provenance
----------
Reconstructed to match the catalogue sizes this skill's SKILL.md states (50+
deliverables, 20 styles, 20 industries) and the deliverable names in
``references/cip-deliverable-guide.md`` and ``references/cip-style-guide.md``. The
per-deliverable production constraints, the mockup settings, and the prompt
assembly are this file's own work.
"""

from __future__ import annotations

import math
import re
from collections import Counter

DEFAULT_STYLE = "corporate-minimal"
DEFAULT_MODEL = "flash"
MODELS = {"flash": "gemini-2.5-flash-image", "pro": "gemini-3-pro-image-preview"}

# 52 deliverables, grouped the way a real CIP request list is grouped. "spec" is
# what the generated mockup has to look like for the artefact to be real.
DELIVERABLES: dict[str, dict] = {
    # Core identity
    "primary-logo": {"group": "Core identity", "best_for": "the master mark every other piece derives from", "spec": "flat vector mark, centred, pure white background, no mockup"},
    "logo-horizontal": {"group": "Core identity", "best_for": "letterhead, email signature, website header", "spec": "mark left, wordmark right, one line of height between"},
    "logo-vertical": {"group": "Core identity", "best_for": "square formats, signage, social avatars", "spec": "mark above wordmark, optically centred, not mathematically centred"},
    "logo-stacked-compact": {"group": "Core identity", "best_for": "tight vertical space, embroidery", "spec": "mark above wordmark, reduced clear space"},
    "logo-monochrome": {"group": "Core identity", "best_for": "single-colour print, laser engraving, embroidery, fax", "spec": "single colour, no gradients, no transparency-dependent detail"},
    "logo-reversed": {"group": "Core identity", "best_for": "dark grounds, photographic backgrounds, signage", "spec": "knockout in a single light colour, tested over a photograph"},
    "logo-one-colour-black": {"group": "Core identity", "best_for": "newsprint, stamps, legal documents, photocopies", "spec": "solid black, no detail that disappears at one colour"},
    "favicon": {"group": "Core identity", "best_for": "browser tab at 16px", "spec": "one shape, no wordmark, no detail below 2px, square canvas"},
    "app-icon": {"group": "Core identity", "best_for": "iOS and Android launchers, which round and mask the artwork", "spec": "square canvas, safe area inset 10%, no transparent edges"},
    "social-avatar": {"group": "Core identity", "best_for": "platform profile images, which are displayed as a small circle", "spec": "square canvas, mark within the central 60% so the circle crop keeps it"},
    "clear-space-rule": {"group": "Core identity", "best_for": "the rule that stops anyone else setting the mark badly", "spec": "diagram with the clear space measured in a mark unit, shown against the mark"},
    "minimum-size": {"group": "Core identity", "best_for": "the size below which the mark is no longer legible", "spec": "diagram showing the mark at its minimum and one size below it, failing"},

    # Stationery
    "business-card": {"group": "Stationery", "best_for": "the single most-requested CIP item", "spec": "85 x 55 mm, 3 mm bleed, mark within the safe area, text at least 7pt"},
    "business-card-back": {"group": "Stationery", "best_for": "the reverse carrying the pattern or a secondary mark", "spec": "85 x 55 mm, 3 mm bleed, the reverse design must work on its own"},
    "letterhead": {"group": "Stationery", "best_for": "the anchor of the whole stationery set", "spec": "A4, mark in the header, body margin at least 20 mm, no content in the trim zone"},
    "letterhead-second-page": {"group": "Stationery", "best_for": "continuation pages, where the header is usually reduced", "spec": "A4, reduced mark, no repeat of the full header block"},
    "envelope": {"group": "Stationery", "best_for": "DL and C5, front and flap", "spec": "DL 220 x 110 mm, mark positioned to survive a window envelope"},
    "envelope-flap": {"group": "Stationery", "best_for": "the seal area", "spec": "mark centred in the flap seal band, inside the die line"},
    "notecard": {"group": "Stationery", "best_for": "the small square that reaches an executive", "spec": "105 x 105 mm, generous clear space, quiet design"},
    "compliment-slip": {"group": "Stationery", "best_for": "the slip that goes into an envelope", "spec": "99 x 210 mm, aligns with the letterhead's type grid"},
    "folder": {"group": "Stationery", "best_for": "presentation folders and document wallets", "spec": "A4 pocket, spine and face print, foil or blind deboss on the face"},
    "invoice-pad": {"group": "Stationery", "best_for": "the document clients see most often", "spec": "A5 or A4, tabular figures, a table style that survives being photocopied"},
    "notepad": {"group": "Stationery", "best_for": "desk collateral", "spec": "A5, adhesive strip, 80 sheets, mark in a corner clear of the writing area"},

    # Office environment
    "reception-signage": {"group": "Office environment", "best_for": "the first physical impression", "spec": "large-format, high contrast, readable from the door, dimensional letters or applied vinyl"},
    "wayfinding-system": {"group": "Office environment", "best_for": "room numbers, floor directories, directional panels", "spec": "consistent arrow set, type size fixed by viewing distance, tactile where required"},
    "floor-directory": {"group": "Office environment", "best_for": "the panel outside the lift", "spec": "department listing, type hierarchy, the logo present once, not per row"},
    "wall-graphics": {"group": "Office environment", "best_for": "branding a large blank wall", "spec": "full-bleed artwork, the mark placed so it is not behind furniture"},
    "door-signage": {"group": "Office environment", "best_for": "meeting rooms and offices", "spec": "name and role legible at 1.5 m, consistent plate size across the floor"},
    "lift-lobby-panel": {"group": "Office environment", "best_for": "the panel a visitor stares at while waiting", "spec": "vertical format, large type, minimal content"},
    "reception-desk-panel": {"group": "Office environment", "best_for": "the desk front", "spec": "durable laminate or acrylic, edges considered, no fine detail that scuffs"},
    "acoustic-panel": {"group": "Office environment", "best_for": "fabric-covered wall and ceiling panels", "spec": "design that works as a repeat, not a single image, because the fabric is modular"},

    # Apparel
    "polo-shirt": {"group": "Apparel", "best_for": "front-of-house and event staff", "spec": "left chest, 35 x 40 mm maximum, no colour below two, survives 40 washes"},
    "uniform": {"group": "Apparel", "best_for": "front-of-house, where the mark is the only identifier", "spec": "left chest and back yoke, minimum mark size for embroidery"},
    "tshirt": {"group": "Apparel", "best_for": "events and casual teams", "spec": "screen print safe area, 2-colour max, avoid under the collar seam"},
    "cap": {"group": "Apparel", "best_for": "headwear, where the surface is curved", "spec": "3.5-5 panel, embroidery not print, curve distortion compensated"},
    "apron": {"group": "Apparel", "best_for": "retail and food service", "spec": "pocket placement, wash-resistant ink, mark above the pocket line"},
    "jacket": {"group": "Apparel", "best_for": "outerwear, where the mark is usually on the back", "spec": "large back mark, no detail below 3 mm, reflective options for site work"},

    # Vehicle branding
    "car-sedan": {"group": "Vehicle branding", "best_for": "a single company car", "spec": "door panel, one-colour vinyl, artwork that reads at 10 m, no text below 40 mm"},
    "fleet-vehicles": {"group": "Vehicle branding", "best_for": "several vehicles, which will get dirty at different rates", "spec": "consistent placement across the fleet, a matte over a gloss finish to hide road film"},
    "van-wrap": {"group": "Vehicle branding", "best_for": "delivery and service vehicles", "spec": "full or partial wrap, artwork with 10% bleed, panel seams accounted for"},
    "delivery-box": {"group": "Vehicle branding", "best_for": "the box that is seen when the vehicle is not", "spec": "weatherproof substrate, contrast at night, a phone number legible at 3 m"},

    # Digital
    "website-header": {"group": "Digital", "best_for": "the site masthead", "spec": "SVG, height 32-48 px, works against the page's own background at breakpoints"},
    "email-signature": {"group": "Digital", "best_for": "every email the company sends", "spec": "inline images, no external CSS, a plain-text fallback, total under 150 KB"},
    "social-cover": {"group": "Digital", "best_for": "LinkedIn and Facebook covers, which crop", "spec": "safe area in the central 70-80%, the mark clear of profile-image overlap"},
    "social-post-template": {"group": "Digital", "best_for": "a repeatable post", "spec": "1080 x 1080 and 1200 x 627, one message, generous type"},
    "presentation-deck": {"group": "Digital", "best_for": "pitch and client presentations", "spec": "16:9, a slide master, type from the token set, no more than two fonts"},
    "pitch-deck": {"group": "Digital", "best_for": "a fundraising or sales pitch", "spec": "16:9, one idea per slide, the number on each slide as the headline, appendix carrying the detail"},
    "newsletter-template": {"group": "Digital", "best_for": "a recurring email format", "spec": "600 px content width, a header band, dark-mode variant"},
    "email-header": {"group": "Digital", "best_for": "the top of every campaign email", "spec": "600 px wide, live text for the fallback, imagery at 2x"},
    "favicon-set": {"group": "Digital", "best_for": "modern browsers and pinned tabs", "spec": "16, 32, 48, 180, and a 512 maskable variant with a 10% safe area"},

    # Events and promotional
    "trade-show-booth": {"group": "Events and promotional", "best_for": "the largest single spend in most CIPs", "spec": "back wall legible from 20 m, graphics sized for the viewing distance, no fine type"},
    "backdrop-banner": {"group": "Events and promotional", "best_for": "photo backdrops and step-and-repeat", "spec": "3 x 2 m, repeated mark pattern, high contrast against flash photography"},
    "roll-up-banner": {"group": "Events and promotional", "best_for": "the portable stand", "spec": "800 x 2000 mm, 3 mm bleed, readable top to bottom, the message above 1.5 m"},
    "promotional-items": {"group": "Events and promotional", "best_for": "the give-away items", "spec": "a mark small enough for the object, single colour, and a list of what does not survive: bottles, lanyard, umbrella"},
    "name-badge": {"group": "Events and promotional", "best_for": "worn at a conference for two days", "spec": "readable at 1 m, the mark above the name, high contrast for a photo"},
    "lanyard": {"group": "Events and promotional", "best_for": "a moving sign, seen from behind as often as in front", "spec": "repeat pattern, safety breakaway, mark large enough to read in motion"},
    "brochure": {"group": "Events and promotional", "best_for": "the printed argument", "spec": "A5 or DL, 3 mm bleed, type at 9.5pt minimum, cover distinct at thumbnail size"},
    "business-cd-case": {"group": "Events and promotional", "best_for": "the older physical format", "spec": "spine, face, and back all printed, artwork sized for a 12 cm disc"},

    # Printed collateral
    "report-cover": {"group": "Printed collateral", "best_for": "the document a client reads first", "spec": "A4, a cover identifiable at thumbnail size, 3 mm bleed, spine not overcrowded"},
    "catalogue": {"group": "Printed collateral", "best_for": "product literature", "spec": "A4 landscape or portrait, a grid products can fall into without redesigning every spread"},
    "flyer": {"group": "Printed collateral", "best_for": "a single-sheet announcement", "spec": "A5, one message, a fold line that does not cross the headline"},
    "press-kit": {"group": "Printed collateral", "best_for": "the press and analyst pack", "spec": "A4, consistent typography across fact sheet, bios, and imagery, version-dated"},
    "poster": {"group": "Printed collateral", "best_for": "events and large-format display", "spec": "A2 and A1, type sized for 2 m viewing distance, the mark small relative to the message"},
    "cover-template": {"group": "Printed collateral", "best_for": "periodical covers, the hardest grid problem in print", "spec": "masthead area fixed, cover lines wrap in a bounded box, colour and imagery balanced on a grid"},
    "masthead": {"group": "Printed collateral", "best_for": "the publication's own name set in its own type", "spec": "logotype tested at the publication's largest and smallest type sizes, letterforms corrected if needed"},
    "programme": {"group": "Printed collateral", "best_for": "conferences, theatre, exhibitions", "spec": "A5 or A6, a schedule grid that survives a late change, page numbers matching seat rows"},

    # Retail and packaging
    "packaging": {"group": "Retail and packaging", "best_for": "the product itself", "spec": "dieline followed exactly, artwork with 3 mm bleed, legal copy clear of every fold"},
    "label": {"group": "Retail and packaging", "best_for": "bottles, jars, and anything cylindrical", "spec": "repeat length of the cylinder computed, artwork rotated to read upright, no seam across text"},
    "cup": {"group": "Retail and packaging", "best_for": "hot drinkware", "spec": "tapered surface compensated, single colour, above the sleeve line"},
    "price-tag": {"group": "Retail and packaging", "best_for": "the shelf edge, often the only place the mark appears at all", "spec": "legible at 1 m under store lighting, high contrast, the mark at the minimum size rule"},
    "shopping-bag": {"group": "Retail and packaging", "best_for": "the last thing a customer carries", "spec": "handle-to-handle width, artwork above the gusset fold, heavy stock"},
    "receipt": {"group": "Retail and packaging", "best_for": "the paper trail, thermal-printed", "spec": "58 mm or 80 mm roll, single colour, no reverse, legible on a faded print"},
    "in-store-signage": {"group": "Retail and packaging", "best_for": "shelf edges, category boards, window vinyl", "spec": "A5 shelf strips, adhesive-safe vinyl, consistent plate sizes down the run"},
    "menu-board": {"group": "Retail and packaging", "best_for": "restaurants and bars", "spec": "glare-free laminate, menu type at least 14pt at reading distance, no photograph behind the prices"},
    "loyalty-card": {"group": "Retail and packaging", "best_for": "repeat custom", "spec": "credit-card stock, mark and number both readable, stamp space on the reverse"},

    # Signage and membership
    "signage": {"group": "Signage and membership", "best_for": "any exterior or entrance sign", "spec": "legible at the actual viewing distance, contrast measured, not a raster logo scaled up"},
    "truck-wrap": {"group": "Signage and membership", "best_for": "artic and rigid trucks", "spec": "10% bleed, panel seams and rivet lines mapped, high-visibility markings where the law requires them"},
    "membership-card": {"group": "Signage and membership", "best_for": "member and subscriber identification", "spec": "CR80 or equivalent, both sides printed, personalisation area kept clear of the mark"},
    "certificate": {"group": "Signage and membership", "best_for": "a credential issued to an individual", "spec": "signed, numbered, verifiable, and legally reviewed. A certificate is a representation about a person, not a design artefact"},
}

# 20 CIP styles, carrying the colour / type / material / finish decisions that
# make a mockup internally consistent.
STYLES: dict[str, dict] = {
    "corporate-minimal": {"best_for": "finance legal consulting technology", "colors": "navy #0F172A, white #FFFFFF, blue accents", "typography": "clean sans-serif, Inter or Helvetica, generous leading", "materials": "premium matte paper, subtle texture", "finishes": "matte lamination, spot UV on the logo"},
    "modern-tech": {"best_for": "technology software startup artificial intelligence", "colors": "indigo #6366F1, cyan #0EA5E9, green #10B981 on a dark ground", "typography": "geometric sans, Outfit or Poppins", "materials": "smooth surfaces, gradient print", "finishes": "gloss lamination, metallic accents"},
    "luxury-premium": {"best_for": "fashion jewellery hotels fine dining", "colors": "near-black #1C1917, gold #D4AF37, white", "typography": "elegant serif for the wordmark, thin sans for everything else", "materials": "heavy cotton paper, leather, metal", "finishes": "gold foil, emboss, deboss, soft-touch laminate"},
    "classic-traditional": {"best_for": "law firms heritage brands finance institutions", "colors": "navy, burgundy #7F1D1D, gold", "typography": "traditional serif, Garamond or a Times-class face", "materials": "laid paper, wood, leather", "finishes": "letterpress, gold emboss"},
    "warm-organic": {"best_for": "food organic wellness craft", "colors": "brown #8B4513, green #228B22, cream", "typography": "friendly serif with an organic script accent", "materials": "kraft and recycled stock, uncoated", "finishes": "uncoated, natural texture left visible"},
    "bold-dynamic": {"best_for": "sports entertainment gaming events", "colors": "red #DC2626, orange #F97316, black", "typography": "bold condensed sans, tight tracking", "materials": "high contrast, metallic", "finishes": "gloss, saturated colour"},
    "fresh-modern": {"best_for": "healthcare wellness fintech", "colors": "mint #10B981, sky #0EA5E9, white", "typography": "modern rounded sans", "materials": "light, clean surfaces", "finishes": "matte, minimal"},
    "soft-elegant": {"best_for": "beauty wedding spa fashion", "colors": "pink #F472B6, gold, white", "typography": "elegant script with a thin sans companion", "materials": "soft-touch laminate, quality paper", "finishes": "rose gold foil, emboss"},
    "dark-premium": {"best_for": "technology finance premium consumer", "colors": "near-black ground #0A0A0A, one bright accent, white type", "typography": "tight modern sans, high weight contrast", "materials": "dark board, soft-touch", "finishes": "spot UV, black foil, matte on the reverse"},
    "scandinavian-minimal": {"best_for": "design studios architecture consumer goods", "colors": "off-white, charcoal, one muted accent", "typography": "humanist sans, large sizes, generous leading", "materials": "uncoated stock, uncoated board", "finishes": "none; the restraint is the finish"},
    "swiss-precise": {"best_for": "consulting architecture publishing technology", "colors": "black, white, one red or blue", "typography": "neo-grotesque, strict grid alignment", "materials": "standard uncoated paper", "finishes": "none"},
    "artisan-handmade": {"best_for": "craft brewery bakery maker studios", "colors": "ink black, one warm accent, natural stock", "typography": "hand-lettered wordmark with a clean sans for information", "materials": "recycled, textured, visibly uncoated", "finishes": "letterpress, deboss, torn edge"},
    "geometric-bold": {"best_for": "events media technology modern manufacturing", "colors": "two saturated colours, high contrast", "typography": "geometric sans, very large or very small, never medium", "materials": "smooth coated stock", "finishes": "gloss, die-cut shapes"},
    "heritage-institutional": {"best_for": "universities museums associations public bodies", "colors": "navy, stone, muted gold", "typography": "serif with generous letterspacing, all caps for the institution name", "materials": "heavy cotton, felt board, wood", "finishes": "blind deboss, metallic foil, edge painting"},
    "vibrant-startup": {"best_for": "early-stage software consumer apps", "colors": "one hot primary, one cool secondary, white", "typography": "rounded geometric sans", "materials": "standard coated stock", "finishes": "none; the colour does the work"},
    "earth-conscious": {"best_for": "sustainability agriculture outdoor non-profit", "colors": "forest green, recycled brown, off-white", "typography": "humanist sans, generous leading", "materials": "100% recycled, unbleached", "finishes": "none; state the stock on the piece"},
    "editorial-magazine": {"best_for": "publishing media journalism research", "colors": "ink, one accent, paper white", "typography": "serif display with a grotesque for captions, strong hierarchy", "materials": "textured uncoated, heavier cover stock", "finishes": "none"},
    "futuristic-immersive": {"best_for": "gaming esports events technology", "colors": "cyan, magenta, deep violet, on near-black", "typography": "wide or angular display face, generous tracking", "materials": "gloss, metallic", "finishes": "gloss varnish, holographic foil"},
    "minimal-japanese": {"best_for": "hospitality design retail wellness", "colors": "off-white, one ink, one seal red", "typography": "precise sans with wide tracking, disciplined grid", "materials": "uncoated, very light stock", "finishes": "deboss, no gloss"},
    "industrial-utility": {"best_for": "manufacturing logistics construction trades", "colors": "charcoal, safety yellow or orange, white", "typography": "condensed grotesque, stencil where physical", "materials": "heavy stock, rubberised, uncoated board", "finishes": "none; durability over finish"},
}

# 20 sectors, each naming the deliverables that actually matter to it.
INDUSTRIES: dict[str, dict] = {
    "technology": {"best_for": "software platform developer tools", "priorities": ["website-header", "presentation-deck", "app-icon", "trade-show-booth", "tshirt", "social-cover"], "caution": "Ensure no claim of certification, uptime, or compliance is implied by the design itself."},
    "software-saas": {"best_for": "subscription software cloud service", "priorities": ["website-header", "social-cover", "social-post-template", "email-header", "presentation-deck", "name-badge"], "caution": "The design will be judged in a 32px tab. Make the favicon work first."},
    "consulting": {"best_for": "professional services advisory strategy", "priorities": ["business-card", "letterhead", "folder", "presentation-deck", "name-badge", "report-cover"], "caution": "The swoosh is a category cliché. Restraint reads as competence here."},
    "legal": {"best_for": "law firms legal counsel notaries", "priorities": ["business-card", "letterhead", "envelope", "folder", "compliment-slip", "notecard"], "caution": "Nothing in the design may imply a specialisation, a jurisdiction, or a regulatory status."},
    "finance": {"best_for": "banks wealth advisory insurance accounting", "priorities": ["business-card", "letterhead", "invoice-pad", "report-cover", "signage", "presentation-deck"], "caution": "Do not imply a licence, a guarantee, a return, or a ranking. Those are legal disclosures."},
    "healthcare": {"best_for": "clinics practices medical devices health technology", "priorities": ["signage", "wayfinding-system", "door-signage", "uniform", "brochure", "floor-directory"], "caution": "Wayfinding and accessibility come first, and a claim of clinical efficacy may be a regulated communication."},
    "education": {"best_for": "schools universities training providers", "priorities": ["letterhead", "brochure", "uniform", "name-badge", "social-cover", "envelope"], "caution": "Do not imply accreditation, ranking, or affiliation you do not hold."},
    "real-estate": {"best_for": "property development construction architecture", "priorities": ["brochure", "website-header", "backdrop-banner", "car-sedan", "business-card", "floor-directory"], "caution": "Property imagery carries a licensing burden the identity does not; clear it separately."},
    "construction": {"best_for": "contractors trades building suppliers", "priorities": ["uniform", "van-wrap", "car-sedan", "jacket", "letterhead", "name-badge"], "caution": "Durability beats finish. Specify a substrate that survives weather and washing."},
    "hospitality": {"best_for": "hotels restaurants cafes bars resorts", "priorities": ["uniform", "name-badge", "menu-board", "apron", "social-cover", "loyalty-card"], "caution": "Consistency across the property matters more than any single piece; the guest notices the mismatch."},
    "food-beverage": {"best_for": "restaurants producers retailers beverage brands", "priorities": ["packaging", "label", "apron", "social-post-template", "flyer", "cup"], "caution": "Packaging has legal requirements for ingredients, allergens, and nutrition that the identity cannot absorb."},
    "retail-ecommerce": {"best_for": "shops online stores marketplaces", "priorities": ["packaging", "price-tag", "shopping-bag", "social-post-template", "in-store-signage", "receipt"], "caution": "Design the smallest element first; the price tag is often the only place the mark appears at all."},
    "manufacturing": {"best_for": "industrial manufacturers engineering", "priorities": ["uniform", "jacket", "letterhead", "website-header", "truck-wrap", "catalogue"], "caution": "Specimens and safety markings on machinery are regulatory, not brand."},
    "logistics": {"best_for": "shipping freight delivery transport", "priorities": ["van-wrap", "delivery-box", "uniform", "jacket", "backdrop-banner", "letterhead"], "caution": "Vehicle livery must stay legible in the dark and at speed; foil finishes fail outdoors."},
    "energy": {"best_for": "renewable utilities energy suppliers", "priorities": ["website-header", "report-cover", "signage", "presentation-deck", "brochure", "uniform"], "caution": "Sustainability claims are regulated. Do not let the visual language make one the design cannot support."},
    "nonprofit": {"best_for": "charities foundations associations campaigns", "priorities": ["brochure", "social-post-template", "social-cover", "roll-up-banner", "website-header", "name-badge"], "caution": "Do not imply a tax status, an administrative cost, or a beneficiary relationship you have not verified."},
    "media-publishing": {"best_for": "publishers magazines newsrooms broadcasters", "priorities": ["cover-template", "masthead", "newsletter-template", "social-cover", "website-header", "press-kit"], "caution": "A masthead is the hardest mark to draw: it must survive being set in the publication's own type sizes."},
    "arts-culture": {"best_for": "galleries museums festivals arts organisations", "priorities": ["poster", "brochure", "programme", "roll-up-banner", "name-badge", "social-cover"], "caution": "The identity has to yield to the work. A logo that competes with the art is the wrong logo."},
    "technology-startup": {"best_for": "funded startups early-stage companies", "priorities": ["logo-horizontal", "app-icon", "social-avatar", "website-header", "pitch-deck", "tshirt"], "caution": "The mark will be redesigned within two years; build the system that will survive that, not just the mark."},
    "professional-network": {"best_for": "membership bodies institutes associations", "priorities": ["membership-card", "certificate", "letterhead", "signage", "brochure", "name-badge"], "caution": "A certificate is a representation about an individual. It is not a design artefact and needs legal review."},
}

# Mockup settings: the photographic conditions that make a mockup read as a
# photograph rather than as a collage.
MOCKUPS: dict[str, dict] = {
    "office-reception": {"best_for": "reception signage and wall graphics", "setting": "a reception desk in a bright modern office, lobby behind it, warm daylight through glazing", "camera": "eye level, 35mm, shallow depth of field on the desk panel", "lighting": "soft directional daylight with a warm fill, no harsh on-camera flash"},
    "stationery-flatlay": {"best_for": "business card, letterhead, envelope, notecard", "setting": "the set arranged on a matte surface, overlapping at slight angles", "camera": "overhead, 50mm, even focus across the whole set", "lighting": "large soft source from one side, gentle shadow, no specular hotspots"},
    "stationery-mockup-scene": {"best_for": "the full stationery set in a styled scene", "setting": "a desk with the set in use, a pen and a pair of glasses for scale", "camera": "three-quarter, 50mm", "lighting": "window light from the left, no reflection on the card face"},
    "business-card-hand": {"best_for": "showing card stock and finish", "setting": "a hand holding the card at a slight angle, edge visible", "camera": "85mm, focus on the card face, hand softly out of focus", "lighting": "diffused, catching a highlight on the foil or spot UV if present"},
    "letterhead-desk": {"best_for": "letterhead, invoice pad, notepad", "setting": "the sheet on a desk beside a laptop, in use rather than laid out", "camera": "three-quarter overhead, 35mm", "lighting": "even daylight, no shadow crossing the type"},
    "signage-lobby": {"best_for": "reception signage, wayfinding, floor directory", "setting": "a lobby wall, the sign mounted, with people out of focus for scale", "camera": "wide, 24mm, verticals corrected", "lighting": "ambient interior light, the sign legible without blowing the highlights"},
    "apparel-model": {"best_for": "uniform, polo, tshirt, jacket", "setting": "the garment worn, in a plain environment that does not compete", "camera": "chest height, 85mm, garment filling the frame", "lighting": "even, slightly directional, fabric texture visible"},
    "apparel-flatlay": {"best_for": "cap, folded garments", "setting": "the garment laid flat on a neutral ground", "camera": "overhead, 50mm", "lighting": "soft, shadowless, true to the fabric colour"},
    "vehicle-side": {"best_for": "car livery, fleet vehicles", "setting": "a clean vehicle in a neutral outdoor setting, straight side view", "camera": "orthographic-feeling side elevation, 50mm equivalent, minimal perspective distortion", "lighting": "overcast, even, so the livery is not distorted by a reflection"},
    "vehicle-rear-three-quarter": {"best_for": "delivery van, rear branding", "setting": "rear three-quarter view, doors closed or open showing the interior branding", "camera": "35mm, level with the load floor", "lighting": "soft daylight, tailgate surface evenly lit"},
    "packaging-shot": {"best_for": "packaging, label, box", "setting": "the pack on a surface, three-quarter view, nothing behind it", "camera": "85mm, product at the focal plane", "lighting": "two soft sources at 45 degrees, gradient on the surface behind"},
    "trade-show-booth": {"best_for": "trade show booth, back wall", "setting": "the stand empty, shot from the aisle at eye level", "camera": "24mm, level, so the verticals stay vertical", "lighting": "trade-show ambient, even overhead, no hotspot on the back wall"},
    "rollup-banner": {"best_for": "roll-up banner, backdrop banner", "setting": "the banner standing in a plain interior, base visible so scale is clear", "camera": "straight on, 35mm, no keystone", "lighting": "even ambient, the full banner within the frame"},
    "website-mockup": {"best_for": "website header, social cover, favicon", "setting": "a laptop or phone in a neutral setting, screen at a slight angle", "camera": "50mm, focus on the screen, body softly out of focus", "lighting": "screen glow balanced against ambient, no moire on the display"},
    "social-media-scene": {"best_for": "social post, cover, post template", "setting": "a phone or a stack of cards showing the design at platform scale", "camera": "overhead, 50mm", "lighting": "soft, colour-accurate, no colour cast on the artwork"},
    "email-client": {"best_for": "email header, email signature, newsletter", "setting": "an email client window, header and signature visible together", "camera": "straight-on screen capture style, sharp text", "lighting": "not applicable; render the interface rather than photographing it"},
    "brochure-spread": {"best_for": "brochure, report, programme", "setting": "an open spread, page turning or held, showing the inside layout", "camera": "overhead at 45 degrees, 50mm, focus across the gutter", "lighting": "even, gutter shadow controlled"},
    "lanyard-and-badge": {"best_for": "name badge, lanyard", "setting": "worn at a conference, blurred crowd behind", "camera": "85mm, shallow depth of field on the badge", "lighting": "ambient, the badge legible without a flash reflection"},
    "brochure-table": {"best_for": "print collateral on a table", "setting": "a stack of brochures on a wood or stone table, one open", "camera": "50mm, three-quarter", "lighting": "window light, warm, with a defined but soft shadow"},
    "conference-stand": {"best_for": "promotional items, exhibition graphics", "setting": "a stand counter with the items arranged", "camera": "50mm, eye level", "lighting": "trade-show ambient, colour-accurate"},
    "gift-and-merch": {"best_for": "promotional items", "setting": "the items arranged on a neutral surface, each item readable", "camera": "50mm, three-quarter", "lighting": "soft, per-item, so each surface reads"},
    "wall-graphic-interior": {"best_for": "wall graphics, large-format interior branding", "setting": "a full wall in a working interior, furniture for scale", "camera": "24mm, verticals corrected", "lighting": "ambient interior, artwork evenly lit with no glare"},
    "door-and-corridor": {"best_for": "door signage, wayfinding", "setting": "a corridor with the signage in place, consistent down the run", "camera": "35mm, corridor perspective", "lighting": "even corridor lighting, signs at the same brightness"},
    "courtesy-set": {"best_for": "invoice pad, compliment slip, folder", "setting": "the complete correspondence set arranged for a top-down shot", "camera": "overhead, 50mm", "lighting": "soft, shadowless, true colour"},
}

DOMAINS = ("deliverable", "style", "industry", "mockup")
DOMAIN_KEYS = {
    "deliverable": "deliverable",
    "deliverables": "deliverable",
    "style": "style",
    "styles": "style",
    "industry": "industry",
    "industries": "industry",
    "mockup": "mockup",
    "mockups": "mockup",
}

_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class BM25Index:
    """Okapi BM25 over a small in-memory document set.

    Duplicated from the logo catalogue rather than shared, because the two
    directories are installed independently and neither can import from the other.
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
        total = 0.0
        for term in tokenize(query):
            frequency = self.frequencies[index].get(term, 0)
            if not frequency:
                continue
            idf = self.idf.get(term, 0.0)
            denominator = (
                frequency + self.k1 * (1 - self.b + self.b * self.lengths[index] / self.avg_length)
            )
            total += idf * (frequency * (self.k1 + 1)) / denominator
        return total

    def search(self, query: str, limit: int = 5) -> list[tuple[int, float]]:
        if not tokenize(query):
            return []
        scored = [(index, self.score(query, index)) for index in range(len(self.documents))]
        relevant = [pair for pair in scored if pair[1] > 0]
        relevant.sort(key=lambda pair: (-pair[1], pair[0]))
        return relevant[:limit]


def _catalogue_documents(domain: str) -> tuple[dict, list[str], list[str]]:
    """Catalogue, ordered titles, and corpus. Titles and corpus share one ordering."""
    if domain == "deliverable":
        catalogue = DELIVERABLES
        describe = lambda entry: f"{entry['group']} {entry['best_for']} {entry['spec']}"
    elif domain == "style":
        catalogue = STYLES
        describe = lambda entry: " ".join(
            str(entry[key]) for key in ("best_for", "colors", "typography", "materials", "finishes")
        )
    elif domain == "industry":
        catalogue = INDUSTRIES
        describe = lambda entry: f"{entry['best_for']} {entry['caution']} " + " ".join(entry["priorities"])
    elif domain == "mockup":
        catalogue = MOCKUPS
        describe = lambda entry: f"{entry['best_for']} {entry['setting']} {entry['camera']} {entry['lighting']}"
    else:
        raise ValueError(f"unknown domain {domain!r}; expected one of {', '.join(DOMAINS)}")

    titles = sorted(catalogue)
    corpus = [f"{name} {describe(catalogue[name])}" for name in titles]
    return catalogue, titles, corpus


_INDEX_CACHE: dict[str, tuple[dict, list[str], BM25Index]] = {}


def domain_catalogue(domain: str) -> tuple[dict, list[str], BM25Index]:
    key = DOMAIN_KEYS.get(domain.lower())
    if key is None:
        raise ValueError(f"unknown domain {domain!r}; expected one of {', '.join(DOMAINS)}")
    if key not in _INDEX_CACHE:
        catalogue, titles, corpus = _catalogue_documents(key)
        _INDEX_CACHE[key] = (catalogue, titles, BM25Index(corpus))
    return _INDEX_CACHE[key]


def search_domain(domain: str, query: str, limit: int = 5) -> list[dict]:
    catalogue, titles, index = domain_catalogue(domain)
    results = []
    for position, score in index.search(query, limit=limit):
        name = titles[position]
        results.append({
            "name": name,
            "score": round(score, 4),
            "entry": catalogue[name],
            "why": catalogue[name].get("best_for", ""),
        })
    if not results and query.strip():
        for name in titles[:limit]:
            results.append({
                "name": name,
                "score": 0.0,
                "entry": catalogue[name],
                "why": catalogue[name].get("best_for", ""),
            })
    return results


def resolve(name: str, domain: str) -> str:
    catalogue, titles, _index = domain_catalogue(domain)
    if name in titles:
        return name
    for candidate in titles:
        if name.lower() in candidate.lower() or candidate.lower() in name.lower():
            return candidate
    raise KeyError(f"unknown {domain} {name!r}. Run with no --domain to list all {len(titles)} options.")


def deliverables_for_set(industry: str) -> list[str]:
    """The deliverables a full CIP set should cover for one industry.

    The industry guide's own priorities first, then one per remaining group, so a
    full set is broad without being random. Priorities naming something outside the
    catalogue are dropped rather than crashing the set: a stale name in a guide is
    a documentation bug, not a reason to fail a generation run.
    """
    entry = INDUSTRIES[resolve(industry, "industry")]
    ordered = [name for name in entry["priorities"] if name in DELIVERABLES]
    covered = {DELIVERABLES[name]["group"] for name in ordered}
    for name in sorted(DELIVERABLES):
        group = DELIVERABLES[name]["group"]
        if group not in covered:
            ordered.append(name)
            covered.add(group)
    return ordered


def build_mockup_prompt(
    brand: str,
    deliverable: str,
    industry: str | None = None,
    style: str | None = None,
    mockup: str | None = None,
    with_logo: bool = True,
) -> str:
    """Assemble the mockup prompt for one deliverable.

    ``with_logo`` controls whether the prompt asks for the brand's logo artwork to
    appear on the piece. When there is no logo file yet, the prompt describes the
    placement instead, which produces a usable mockup with a placeholder mark
    rather than an invented logo.
    """
    deliverable_key = resolve(deliverable, "deliverable")
    spec = DELIVERABLES[deliverable_key]
    parts = [
        f"Professional corporate identity mockup for {brand}: "
        f"{spec['best_for']}",
        f"Deliverable: {deliverable_key.replace('-', ' ')}.",
        f"Production constraints the mockup must respect: {spec['spec']}.",
    ]

    if style:
        style_entry = STYLES[resolve(style, "style")]
        parts += [
            f"Style: {style_entry['best_for']}.",
            f"Colours: {style_entry['colors']}.",
            f"Typography: {style_entry['typography']}.",
            f"Materials: {style_entry['materials']}.",
            f"Finishes: {style_entry['finishes']}.",
        ]
    if industry:
        parts.append(f"Sector: {INDUSTRIES[resolve(industry, 'industry')]['best_for']}.")

    if with_logo:
        parts.append(
            f"Place the supplied {brand} logo artwork on the piece, undistorted, at a "
            "realistic scale relative to the artefact, with clear space around it. "
            "Do not redraw, restyle, or invent the logo."
        )
    else:
        parts.append(
            f"Leave a correctly sized, correctly positioned blank placement where the "
            f"{brand} logo will go. Do not invent a logo."
        )

    if mockup:
        setting = MOCKUPS[resolve(mockup, "mockup")]
        parts += [
            f"Setting: {setting['setting']}.",
            f"Camera: {setting['camera']}.",
            f"Lighting: {setting['lighting']}.",
        ]
    else:
        parts += [
            "Setting: the artefact on a neutral surface in a plausible environment "
            "for its use, nothing behind it that competes.",
            "Camera: straight on or three-quarter, level, verticals kept vertical.",
            "Lighting: soft and even, colour-accurate, no harsh flash.",
        ]

    parts.append(
        "NOT: photorealistic render artefacts, warped or stretched logos, illegible "
        "text, placeholder lorem strings, cluttered background, watermarks, low "
        "resolution, distorted proportions, jpeg artefacts"
    )
    return "\n".join(parts)


def build_cip_brief(
    brand: str,
    query: str = "",
    style: str | None = None,
    industry: str | None = None,
    full_set: bool = False,
) -> str:
    """The brief a human approves before a single mockup is generated."""
    if style is None:
        style = search_domain("style", query or industry or brand, limit=1)[0]["name"]
    if industry is None:
        industry = search_domain("industry", query or brand, limit=1)[0]["name"]
    style_entry = STYLES[style]
    industry_entry = INDUSTRIES[industry]

    lines = [f"# Corporate identity program brief — {brand}", ""]
    if query:
        lines += [f"Brief: {query}", ""]
    lines += [
        "## Chosen direction",
        "",
        f"- Style: **{style}** — {style_entry['best_for']}",
        f"- Colours: {style_entry['colors']}",
        f"- Typography: {style_entry['typography']}",
        f"- Materials: {style_entry['materials']}",
        f"- Finishes: {style_entry['finishes']}",
        f"- Sector: **{industry}** — {industry_entry['best_for']}",
        "",
        "## Deliverables, in priority order",
        "",
    ]
    for name in industry_entry["priorities"]:
        if name in DELIVERABLES:
            entry = DELIVERABLES[name]
            lines.append(f"1. **{name}** — {entry['best_for']}. Constraint: {entry['spec']}")
    lines += ["", "## A full set also covers", ""]
    covered = set(industry_entry["priorities"])
    for group in ("Core identity", "Stationery", "Printed collateral", "Office environment",
                  "Apparel", "Vehicle branding", "Digital", "Retail and packaging",
                  "Signage and membership", "Events and promotional"):
        options = [name for name, entry in DELIVERABLES.items()
                   if entry["group"] == group and name not in covered]
        if options:
            lines.append(f"- **{group}**: " + ", ".join(options[:6]))

    lines += [
        "",
        "## Decisions to record before generating",
        "",
        "1. Print or digital first. The mark has to work in both, but the clear-space "
        "rule and the minimum size differ, and the smaller one governs.",
        "2. The logo. Every mockup that carries the logo needs the real file. Generate "
        "the logo first; a mockup with an invented mark is a decision deferred.",
        "3. Specification. Business card stock and weight, letterhead size, signage "
        "dimensions. Mockups without a specification are decoration.",
        "4. Accessibility. Contrast of type against its ground, and a legible minimum "
        "size at the real viewing distance for every sign.",
        "",
        "## What this brief does not settle",
        "",
        f"- {industry_entry['caution']}",
        "- Trademark clearance is a legal search, not a design decision.",
        "- Claims about performance, outcomes, compliance, or certification need "
        "review by someone qualified to make them.",
        "",
        "## Output requirements",
        "",
        "- White or neutral background, and the logo undistorted wherever it appears.",
        "- One mockup per deliverable, named `<brand>-<deliverable>.png`.",
        "- Record the prompt, the model, and the date for every generated mockup.",
    ]
    return "\n".join(lines) + "\n"

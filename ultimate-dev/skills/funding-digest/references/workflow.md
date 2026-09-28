<!-- Moved verbatim from funding-digest/SKILL.md, the
     'workflow' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Workflow

### Step 1: Establish Coverage & Period

Determine what the digest should cover. There are two setups:

**Returning user (has a watchlist):**
If the user has previously defined sectors or companies to track, use that list. Check conversation history for prior watchlists.

**New user:**
Ask for:

| Parameter | Default | Notes |
|-----------|---------|-------|
| **Sectors** | *(at least one)* | e.g., "AI, Fintech, Biotech" |
| **Specific companies** | Optional | Supplement sector-level coverage |
| **Time period** | Last 7 days | "This week", "last 2 weeks", "this month" |

Calculate the exact `start_date` and `end_date` from the time period.

### Step 2: Build the Company Universe

For each sector specified, build a company universe using a validated bootstrapping approach:

1. **Seed companies** from domain knowledge (see `references/sector-seeds.md`)
   - Pay attention to the ⚠️ warnings and alias notes in the seeds file — some well-known companies are subsidiaries, have been acquired, or require a specific legal name to resolve.
   - The seeds file includes `company_id` values for known alias mismatches. Use these directly if the brand name fails.

2. **Pre-validate all seeds immediately** (Rule 0):
   ```
   get_info_from_identifiers(identifiers=[all_seeds_for_this_sector])
   ```
   Triage the results into two buckets:
   - ✅ **Resolved & Operating** (`status` = "Operating") → proceed to competitor expansion
   - ❌ **Unresolved or Subsidiary** → retry with alias/legal name from seeds file; subsidiaries are noted for context but excluded from funding queries

3. **Expand via competitors** (using only the ✅ resolved seeds):
   ```
   get_competitors_from_identifiers(identifiers=[resolved_seeds], competitor_source="all")
   ```

4. **Validate expanded universe:**
   ```
   get_info_from_identifiers(identifiers=[new_competitors])
   ```
   Apply the same triage. Filter by `simple_industry` matching the target sector. Drop any unresolved names or subsidiaries.

If the user provides specific companies, add those directly but still run them through the pre-validation triage. Never skip validation — even well-known brand names can fail silently.

Keep the universe manageable — aim for 15–40 **resolved, operating** companies per sector. For a multi-sector digest, this might total 50–100+ companies.

### Step 3: Pull Funding Rounds

For all companies in the universe:

```
get_rounds_of_funding_from_identifiers(
    identifiers=[batch],
    role="company_raising_funds",
    start_date="YYYY-MM-DD",
    end_date="YYYY-MM-DD"
)
```

Process in batches of 15–20 if the universe is large.

**After each batch, identify companies with empty results.** For any company expected to have activity:
1. Retry with the legal entity name or alternate identifier (see Entity Resolution rules above).
2. Log the company as "no data" only after exhausting fallbacks.

Collect all `transaction_id` values from successful results, then enrich with detailed round info:

```
get_rounds_of_funding_info_from_transaction_ids(
    transaction_ids=[all_funding_ids]
)
```

Pass ALL transaction IDs in a single call (or small number of calls) rather than one per transaction — the tool handles batches efficiently.

**Extract the following from each round (critical for the slide):**
- `transaction_id` — needed for the Capital IQ deal link
- **Announcement date** — when the round was publicly announced
- **Close date** — when the round officially closed
- Amount raised
- **Pre-money valuation** (if disclosed)
- **Post-money valuation** (if disclosed)
- Lead investors
- Round type (Series A, B, C, etc.)
- Security terms
- Advisors
- Pricing trend (up-round / down-round / flat)

> **Dates are required.** The announcement and close dates must always appear in the final slide's deal table. If only one date is available, show it and mark the other as "—".

### Step 4: Pull Company Context for Notable Deals

For any company involved in a significant deal (large round, notable valuation shift), get a brief description:

```
get_company_summary_from_identifiers(identifiers=[notable_companies])
```

This adds context to the narrative (e.g., "The company, an AI infrastructure startup founded in 2021, is expanding into...").

### Step 5: Identify Highlights & Trends

Before designing the slide, analyze the data to surface the story:

**Flag as "Notable":**
- Rounds ≥ $100M
- Down rounds (pricing trend = down)
- New unicorns (post-money valuation crossing $1B)
- Significant valuation jumps (post-money ≥ 2x the last known valuation)
- Repeat raisers (same company raising again within 6 months)
- Unusually large investor syndicates

**Identify Trends:**
- Total capital deployed this period vs. typical (if historical data available)
- Which sub-sectors are hottest (most rounds, most capital)
- Round stage distribution (is early-stage or late-stage dominating?)
- Most active investors across the digest
- Geographic concentration
- Valuation trends (are pre-money valuations compressing or expanding?)

**Select Key Takeaways (3–5):**
Distill the most important signals into 3–5 concise bullet-style takeaways. These are the centerpiece of the slide. Each takeaway should be one sentence, punchy, and data-backed.

Examples:
- "AI sector raised $2.4B across 8 rounds — 3x the prior week, led by a $800M mega-round from [Company] at a $12B post-money valuation."
- "[Company] closed a $200M Series D at $3.5B pre-money, up from $1.8B in its Series C — signaling strong demand for AI developer tools."
- "Down-round activity ticked up: 2 of 6 late-stage rounds priced below prior valuations."

### Step 6: Generate Company Logos

For each company featured in the key takeaways or notable deals, generate a logo using a two-tier local pipeline. **Do not use Clearbit** (`logo.clearbit.com`) — it is deprecated and consistently fails. External logo CDNs (Brandfetch, logo.dev, Google Favicons) require API keys or are blocked by network restrictions. Instead, use the following approach:

#### Tier 1: `simple-icons` npm Package (3,300+ Brand SVGs, No Network Required)

The `simple-icons` package bundles high-quality SVG icons for thousands of well-known brands. It works entirely offline — no API keys, no network calls. Install it alongside `sharp` for SVG → PNG conversion:

```bash
npm install simple-icons sharp
```

**Lookup strategy:**

```javascript
const si = require('simple-icons');
const sharp = require('sharp');

// Find an icon by exact title match (case-insensitive)
function findSimpleIcon(companyName) {
    // Try exact match first
    for (const [key, val] of Object.entries(si)) {
        if (!key.startsWith('si') || !val || !val.title) continue;
        if (val.title.toLowerCase() === companyName.toLowerCase()) return val;
    }
    // Try without common suffixes (AI, Inc., Corp.)
    const stripped = companyName.replace(/\s*(AI|Inc\.?|Corp\.?|Ltd\.?)$/i, '').trim();
    if (stripped !== companyName) {
        for (const [key, val] of Object.entries(si)) {
            if (!key.startsWith('si') || !val || !val.title) continue;
            if (val.title.toLowerCase() === stripped.toLowerCase()) return val;
        }
    }
    return null;
}

// Convert SVG to PNG with the brand's official color
async function simpleIconToPng(icon, outputPath) {
    const coloredSvg = icon.svg.replace('<svg', `<svg fill="#${icon.hex}"`);
    await sharp(Buffer.from(coloredSvg))
        .resize(128, 128, { fit: 'contain', background: { r: 255, g: 255, b: 255, alpha: 0 } })
        .png()
        .toFile(outputPath);
}
```

**Coverage:** ~43% of typical deal flow companies (strong for major tech brands like Stripe, Anthropic, Databricks, Snowflake, Discord, Shopify, SpaceX, Mistral AI, Hugging Face; weaker for niche fintech, biotech, or early-stage companies).

#### Tier 2: Initial-Based Fallback via `sharp` (100% Coverage)

For companies not found in `simple-icons`, generate a clean initial-based logo as a PNG:

```javascript
async function generateInitialLogo(companyName, outputPath) {
    const initial = companyName.charAt(0).toUpperCase();
    const svg = `
    <svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
        <circle cx="64" cy="64" r="64" fill="#BDBDBD"/>
        <text x="64" y="64" font-family="Arial, Helvetica, sans-serif"
              font-size="56" font-weight="bold" fill="#FFFFFF"
              text-anchor="middle" dominant-baseline="central">${initial}</text>
    </svg>`;
    await sharp(Buffer.from(svg)).png().toFile(outputPath);
}
```

#### Complete Pipeline

```javascript
async function fetchLogo(companyName, outputDir) {
    const fileName = companyName.toLowerCase().replace(/[\s.]+/g, '-') + '.png';
    const outPath = path.join(outputDir, fileName);

    // Tier 1: Try simple-icons
    const icon = findSimpleIcon(companyName);
    if (icon) {
        await simpleIconToPng(icon, outPath);
        return { path: outPath, source: 'simple-icons' };
    }

    // Tier 2: Generate initial-based fallback
    await generateInitialLogo(companyName, outPath);
    return { path: outPath, source: 'initial-fallback' };
}
```

**Logo guidelines:**
- Save all logos to `/home/claude/logos/[company-name].png`
- All logos are 128×128 PNG with transparent backgrounds
- On the slide, display logos at 0.35"–0.5" tall — they're accents, not focal points
- Initial-fallback circles use gray (`BDBDBD`) fill with white text — consistent with the monochrome palette
- Never mix logo styles randomly — if most companies resolve to brand icons, the few fallbacks should blend in naturally

### Step 7: Generate the One-Page PPTX

Read `/mnt/skills/public/pptx/SKILL.md` and `/mnt/skills/public/pptx/pptxgenjs.md` before creating the slide.

Create a **single-slide** PowerPoint using `pptxgenjs`. The slide should be information-dense but visually clean — think "executive dashboard" not "wall of text."

#### Slide Layout

```
┌─────────────────────────────────────────────────────────────┐
│  DEAL FLOW DIGEST                                           │
│  [Period] · [Sectors]                           [Date]      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  $X.XB  │  │  N      │  │  $X.XB  │  │  $X.XB  │       │
│  │ Raised  │  │ Rounds  │  │ Avg Pre │  │ Largest │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│                                                             │
│  KEY TAKEAWAYS                                              │
│  ─────────────────────────────────────────────────          │
│  [Logo] Takeaway 1 text goes here...                        │
│  [Logo] Takeaway 2 text goes here...                        │
│  [Logo] Takeaway 3 text goes here...                        │
│  [Logo] Takeaway 4 text goes here...                        │
│                                                             │
│  TOP DEALS                                                  │
│  ┌──────────────────────────────────────────────────────────┐│
│  │Company│Type │Announced│Closed│Amount│Pre-$│Post-$│Lead│🔗││
│  │───────│─────│─────────│──────│──────│─────│──────│────│──││
│  │ ...   │ ... │  ...    │ ...  │ ...  │ ... │ ...  │... │🔗││
│  └──────────────────────────────────────────────────────────┘│
│                                                             │
│  [Footer: Deal Flow Digest · Sources: S&P Global Capital IQ]│
│  [Footer: AI Disclaimer]                                    │
└─────────────────────────────────────────────────────────────┘
```

#### Design Specifications

**Color philosophy: Minimal, monochrome-first.** The slide should feel like a high-end financial brief — black, white, and gray dominate. Color is used **only** where it carries meaning (e.g., a red indicator for a down round, a green indicator for a standout metric) or where the reader would naturally expect it (company logos). Never use color for purely decorative purposes like background fills, accent bars, or gradient effects.

**Color palette — Monochrome Executive:**
- Primary background: `FFFFFF` (white) — clean, open slide background
- Header bar: `1A1A1A` (near-black) — strong contrast for the title region
- Primary text: `1A1A1A` (near-black) — all body text, stat numbers, takeaways
- Secondary text: `6B6B6B` (medium gray) — labels, captions, footer, date stamps
- Borders & dividers: `D0D0D0` (light gray) — subtle structural lines, card outlines, table borders
- Card backgrounds: `F5F5F5` (off-white / very light gray) — stat card fills, alternating table rows
- Link text: `2B5797` (muted blue) — Capital IQ deal links in the table (the only blue on the slide)
- **Semantic color (sparingly):**
  - Down rounds or negative signals: `C0392B` (muted red) — use only as a small dot, tag, or single-word highlight, never as a fill or background
  - Standout positive metrics (new unicorn, outsized round): `2E7D32` (muted green) — same minimal usage: a dot, a small tag, or a single highlighted number
  - If no data points warrant a color indicator, **use no color at all**. A fully monochrome slide is perfectly correct.

**Typography:**
- Title: 28–32pt, bold, white on near-black header bar
- Stat numbers: 36–44pt, bold, near-black
- Stat labels: 10–12pt, medium gray (`6B6B6B`)
- Takeaway text: 12–14pt, near-black, left-aligned
- Table text: 9–11pt, near-black with gray (`6B6B6B`) for secondary columns
- Link text: 9–10pt, muted blue (`2B5797`)
- Footer: 8pt, medium gray

**Stat Cards (top row):**
- 4 key metrics as large-number callouts: Total Raised, # Rounds, Avg Pre-Money Valuation, Largest Round
- Each in a card with `F5F5F5` fill and a thin `D0D0D0` border — no shadow, no color fills
- If a stat is surprising or extreme (e.g., 3x normal volume, a record deal), a small colored dot or underline may be placed next to that single number — otherwise keep fully monochrome
- If pre-money valuations are mostly undisclosed, substitute with a different metric (e.g., Median Round Size, # New Unicorns)

**Key Takeaways (middle section):**
- 3–5 one-line takeaways, each prefixed with the relevant company logo (small, ~0.35" tall)
- If no logo available, use a **gray circle** with the company initial in white — not a colored circle
- Left-aligned, with enough spacing to breathe
- Down-round or negative takeaways may use a small red dot prefix; otherwise no color
- Include valuation context where available (e.g., "at a $5B post-money valuation")

**Top Deals Table (bottom section):**
- Compact table showing the 4–6 most notable deals
- Columns: Company, Type (Series X), Announced (date), Closed (date), Amount ($M), Pre-Money ($M), Post-Money ($M), Lead Investor, Deal Link
- **Announced** and **Closed** columns show dates in `MMM DD` format (e.g., "Jan 15"). These columns are required and must always be present. If a date is not available, show "—".
- The **Deal Link** column contains a clickable "View →" text linking to Capital IQ:
  ```
  https://www.capitaliq.spglobal.com/web/client?#offering/capitalOfferingProfile?id=<transaction_id>
  ```
  where `<transaction_id>` is the `transaction_id` from `get_rounds_of_funding_from_identifiers`.
- If pre-money or post-money valuation is not disclosed, show "—" in that cell
- Header row with near-black (`1A1A1A`) fill and white text; alternating rows in `F5F5F5` and `FFFFFF`
- **Center the table horizontally** on the slide. Calculate the table's total width, then set `x` so it is centered within the slide width: `x = (slideWidth - tableWidth) / 2`. For a 16:9 layout (13.33" wide), if the table is 12" wide, use `x = 0.67`. Never left-align the table to the slide edge.
- Keep it tight — this is a reference, not the focal point
- No colored fills in table cells. If a deal is a down round, a small red text tag "(↓ down)" may appear next to the amount — that is the only permitted color in the table.

**Deal Link Implementation (pptxgenjs):**
In pptxgenjs, hyperlinks are added to table cells using the `options.hyperlink` property on the cell object:
```javascript
// Table cell with Capital IQ deal link
{
  text: "View →",
  options: {
    hyperlink: {
      url: `https://www.capitaliq.spglobal.com/web/client?#offering/capitalOfferingProfile?id=${transactionId}`
    },
    color: "2B5797",
    fontSize: 9,
    fontFace: "Arial"
  }
}
```

**Table Centering (pptxgenjs):**
Always center the deal table on the slide. Calculate the x position dynamically:
```javascript
const SLIDE_W = 13.33; // 16:9 slide width
const TABLE_W = 12.5;  // total table width (sum of all column widths)
const TABLE_X = (SLIDE_W - TABLE_W) / 2; // ≈ 0.42"

slide.addTable(tableRows, {
  x: TABLE_X,
  y: tableY,
  w: TABLE_W,
  colW: [1.8, 0.9, 0.9, 0.9, 1.0, 1.1, 1.2, 1.6, 0.7], // Company, Type, Announced, Closed, Amount, Pre-$, Post-$, Lead, Link
  // ... other options
});
```
Adjust `colW` values as needed, but always recompute `TABLE_X` from `(SLIDE_W - sum(colW)) / 2` to keep the table centered.

**Footer:**
- Small text in medium gray: "Deal Flow Digest · [Period] · Sources: S&P Global Capital IQ · Generated [Date]"

**General color rules (enforce strictly):**
- Company logos are the only "full color" elements on the slide — they appear as-is from the source.
- Deal links use muted blue (`2B5797`) — this is the only non-monochrome text color besides semantic red/green.
- Outside of logos and links, the slide should look correct printed on a black-and-white printer.
- Never apply color to backgrounds, accent bars, decorative shapes, or section dividers.
- When in doubt, leave it gray.

#### Code Structure

```javascript
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Deal Flow Digest";

const slide = pres.addSlide();
const SLIDE_W = 13.33; // 16:9 slide width in inches

// 1. Dark header bar with title and period
// 2. Stat cards row (4 cards: Total Raised, # Rounds, Avg Pre-Money, Largest Round)
// 3. Key takeaways section with logos (include valuation context)
// 4. Top deals table with Announced, Closed, Pre-Money, Post-Money columns and Capital IQ deal links
//    - Center the table: x = (SLIDE_W - tableWidth) / 2
// 5. Footer

pres.writeFile({ fileName: "/home/claude/deal-flow-digest.pptx" });
```

Use factory functions (not shared objects) for shadows and repeated styles per the pptxgenjs pitfalls guidance.

### Step 8: QA the Slide

Follow the QA process from the PPTX skill:

1. **Content QA:** `python -m markitdown deal-flow-digest.pptx` — verify all text, numbers, company names, valuation figures, and deal links are correct
2. **Visual QA:** Convert to image and inspect:
   ```bash
   python /mnt/skills/public/pptx/scripts/office/soffice.py --headless --convert-to pdf deal-flow-digest.pptx
   pdftoppm -jpeg -r 200 deal-flow-digest.pdf slide
   ```
   Check for overlapping elements, text overflow, alignment issues, low-contrast text, logo sizing problems, and that deal link text is visible.
3. **Link QA:** Verify that the Capital IQ URLs in the table are correctly formatted with the right transaction IDs.
4. **Fix and re-verify** — at least one fix-and-verify cycle before declaring done.

### Step 9: Present Results

1. Copy the final `.pptx` to `/mnt/user-data/outputs/`
2. Use `present_files` to share the slide
3. Provide a 2–3 sentence verbal summary:
   - "Your digest covers X rounds totaling $Y raised across [sectors]."
   - Call out the single most notable deal and its valuation
   - Flag any concerning trends (down rounds, valuation compression, etc.)

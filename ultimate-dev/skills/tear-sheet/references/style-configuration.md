<!-- Moved verbatim from tear-sheet/SKILL.md, the
     'style-configuration' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Style Configuration

These are sensible defaults. To customize for your firm's brand, modify this section — common changes include swapping the color palette, changing the font (Calibri is standard at many banks), and updating the disclaimer text.

**Colors:**
- Primary (header banner background, section header text): #1F3864
- Accent (signature section highlights): #2E75B6
- Table header row fill: #D6E4F0
- Table alternating row fill: #F2F2F2
- Table borders: #CCCCCC
- Header banner text: #FFFFFF

**Typography (sizes in half-points for docx-js):**
- Font family: Arial
- Company name: 18pt bold (size: 36)
- Section headers: 11pt bold (size: 22), Primary color
- Body text: 9pt (size: 18)
- Table text: 8.5pt (size: 17)
- Footer/disclaimer: 7pt italic (size: 14)
- Per-template overrides are specified in each reference file's Formatting Notes.

**Company Header Banner:**
- The header is a navy (#1F3864) banner spanning the full page width with company name in white.
- **Below the banner, key-value pairs MUST be rendered in a two-column borderless table spanning the full page width.** Left column: company identifiers (ticker, HQ, founded, employees, sector). Right column: financial identifiers (market cap, EV, stock price, shares outstanding). Each cell contains a bold label and regular-weight value on the same line (e.g., "**Market Cap** $124.7B"). Do not left-justify all fields in a single column — this wastes horizontal space and looks unprofessional. The two-column spread is the single most important visual signal that distinguishes a professional tear sheet from a default document.
  - **Implementation:** Create a 2-column table with `borders: none` and `shading: none` on all cells. Set column widths to 50% each. Place left-column fields (ticker, HQ, founded, employees) as separate paragraphs in the left cell. Place right-column fields (market cap, EV, stock price, shares outstanding) in the right cell. Each field is a single paragraph: bold run for the label, regular run for the value.
  - The specific fields in each column vary by audience — see the reference file's header spec. The principle is always: spread across the page, not clumped left.
- **Do not use a bordered table for the header key-value block.** Bordered tables are reserved for financial data only.
- Key metrics in the header (market cap, EV, stock price) should be displayed as inline key-value pairs, not in a separate bordered table.

**Section Headers:**
- Each section header gets a horizontal rule (thin line, #CCCCCC, 0.5pt) directly beneath it to create clean visual separation between sections.
- **Render the rule as a bottom border on the header paragraph itself** — do not insert a separate paragraph element for the rule. A separate paragraph adds its own before/after spacing and causes excessive whitespace below section titles.
- **Implementation:** In docx-js, apply a bottom border to the section header paragraph via `paragraph.borders.bottom = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" }`. Do not use `doc.addParagraph()` with a separate horizontal rule element. Do not use `thematicBreak`. The border must be on the heading paragraph itself with 0pt spacing after, so the rule sits tight against the header text.
- Spacing: 12pt before the header paragraph, 0pt after the header paragraph, 4pt before the next content element.

**Bullet Formatting:**
- Use a single bullet character (•) for all bulleted content across all tear sheet types. Do not mix •, -, ▸, or numbered lists within or across tear sheets.
- **Synthesis/analysis bullets** (Earnings Highlights, Strategic Fit, Integration Considerations, Conversation Starters): indented block-style formatting with left indent 360 DXA (0.25") and a hanging indent for the bullet character. These should be visually offset from body text — they're interpretive content and should look distinct from data tables and prose paragraphs.
- **Informational bullets** within relationship sections: standard body indent (180 DXA), no hanging indent.
- **Do not apply left-border accents to any bullet sections.** Left-border styling renders inconsistently in docx-js and creates visual artifacts. Use indentation and text size differentiation to distinguish signature sections instead.

**Tables (financial data only):**
- Header row: Table Header Fill (#D6E4F0) with bold dark text
- Body rows: alternating white / Table Alternating Fill (#F2F2F2)
- Borders: Table Border color (#CCCCCC), thin (BorderStyle.SINGLE, size 1)
- Cell padding: top/bottom 40 DXA, left/right 80 DXA
- Right-align all numeric columns
- Always use ShadingType.CLEAR (never SOLID — SOLID causes black backgrounds)

**Layout:**
- US Letter portrait, 0.75" margins (1080 DXA all sides)

**Number formatting:**
- Currency: USD. Use millions unless company revenue > $50B (then billions, one decimal). Label units in column headers (e.g., "Revenue ($M)"), not in individual cells.
- **Table cells: plain numbers with commas, no dollar signs.** Example: a revenue cell shows "4,916" not "$4,916". The column header carries the unit.
- Fiscal years: actual years (FY2022, FY2023, FY2024), never relative labels (FY-2, FY-1).
- Negatives: parentheses, e.g., (2.3%)
- Percentages: one decimal place
- Large numbers: commas as thousands separators

**Footer (document footer, not inline):**
Place the source attribution and disclaimer in the actual document footer (repeated on every page), not as inline body text at the bottom. The footer is exactly two lines, centered, on every page:
- Line 1: "Data: S&P Capital IQ via Kensho | Analysis: AI-generated | [Month Day, Year]"
- Line 2: "For informational purposes only. Not investment advice."
- Style: 7pt italic, centered, #666666 text color
- This footer text must be identical across all tear sheet types for the same company. Do not vary the wording by audience.
- **This footer is required on every tear sheet, every audience type, every page.** Do not omit it.

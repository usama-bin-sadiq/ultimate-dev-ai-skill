<!-- Moved verbatim from earnings-preview-beta/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Phase 7: Generate the HTML Report

**STOP — BEFORE WRITING ANY HTML, YOU MUST READ ALL INTERMEDIATE FILES. THIS IS A BLOCKING PREREQUISITE.**

This is not optional. You MUST run each `cat` command below as a **separate bash tool call** (not combined into one). This ensures each file's contents are individually loaded and visible in the conversation. Do NOT combine them into a single command. Do NOT skip any file.

Run these commands **one at a time, each as its own bash call**:

1. `cat /tmp/earnings-preview/company-info.txt`
2. `cat /tmp/earnings-preview/transcript-extracts.txt`
3. `cat /tmp/earnings-preview/financials.csv`
4. `cat /tmp/earnings-preview/segments.csv`
5. `cat /tmp/earnings-preview/prices.csv`
6. `cat /tmp/earnings-preview/peer-eps.csv`
7. `cat /tmp/earnings-preview/peer-market-caps.csv`
8. `cat /tmp/earnings-preview/consensus-eps.csv`
9. `cat /tmp/earnings-preview/kensho-findings.txt`
10. `cat /tmp/earnings-preview/earnings-dates.csv`
11. `cat /tmp/earnings-preview/calculations.csv`

**After reading ALL files, you MUST print a summary message to the user** that lists every file and its status. Use exactly this format:

```
--- DATA FILE VERIFICATION ---
1. company-info.txt        ✓ loaded ([N] lines)
2. transcript-extracts.txt ✓ loaded ([N] lines)
3. financials.csv          ✓ loaded ([N] rows)
4. segments.csv            ✓ loaded ([N] rows)
5. prices.csv              ✓ loaded ([N] rows)
6. peer-eps.csv            ✓ loaded ([N] rows)
7. peer-market-caps.csv    ✓ loaded ([N] rows)
8. consensus-eps.csv       ✓ loaded ([N] rows)
9. kensho-findings.txt     ✓ loaded ([N] lines)
10. earnings-dates.csv     ✓ loaded ([N] rows)
11. calculations.csv       ✓ loaded ([N] rows)

All intermediate data files loaded successfully.
Generating report using file data as the single source of truth.
---
```

If any file is missing or empty, STOP and tell the user which file failed. Do NOT proceed to generate the report with missing data.

**Every number, quote, source URL, and MCP function call reference in the HTML report must come from these files — not from your memory of earlier conversation turns.** The files are the single source of truth. Earlier conversation context may have been compressed or summarized and WILL contain errors if relied upon. If a data point is not in the files, it should not appear in the report.

See [report-template.md](report-template.md) for the complete HTML template, CSS, and Chart.js configuration.

**MANDATORY — Use Template Helper Functions for Charts:**
The report-template.md provides pre-built, debugged Chart.js helper functions. You MUST use these exact functions to create charts. Do NOT write custom inline Chart.js code. The helpers are:
- `createRevEpsChart(canvasId, labels, revenueData, epsData, revLabel)` — for Figure 1
- `createMarginChart(canvasId, labels, grossMargins, opMargins)` — for Figure 2
- `createRevGrowthChart(canvasId, labels, growthData)` — for Figure 3
- `createAnnotatedPriceChart(canvasId, labels, prices, earningsDates, ticker)` — for Figure 5
- `createCompPerfChart(canvasId, labels, datasets)` — for Figure 6
- `createPEChart(canvasId, companies)` — for Figure 7

Each chart call MUST be in its own `<script>` tag wrapped in a try-catch block. This ensures a bug in one chart does not prevent other charts from rendering. Example:
```html
<script>
try {
  createRevEpsChart('chart-rev-eps', [...], [...], [...], 'Revenue ($B)');
} catch(e) { console.error('Figure 1 error:', e); }
</script>
<script>
try {
  createMarginChart('chart-margins', [...], [...], [...]);
} catch(e) { console.error('Figure 2 error:', e); }
</script>
```

### Report Structure (4-5 pages total)

The report has two halves: **narrative** (pages 1-2) and **figures** (pages 3-5). Keep these tightly integrated.

---

**AI DISCLAIMER (MANDATORY — must appear in 3 places):**
You MUST include the following disclaimer text in the report HTML. This is not optional — the report is incomplete without it:

> **"Analysis is AI-generated — please confirm all outputs"**

It must appear in exactly these 3 locations:
1. **Header banner** — immediately before the cover header, as a centered yellow banner: `<div class="ai-disclaimer">Analysis is AI-generated — please confirm all outputs</div>`
2. **Footer** — inside the page-footer div, as a prominent yellow banner: `<div class="footer-disclaimer">Analysis is AI-generated — please confirm all outputs</div>`
3. **Appendix** — as the first line of the appendix section, before the table: `<div class="ai-disclaimer">Analysis is AI-generated — please confirm all outputs</div>`

---

**PAGE 1: Cover & Thesis**

- **AI disclaimer banner** (yellow, centered — see AI DISCLAIMER rule above)
- **Header**: Company name (TICKER) | Industry | Report date
- **Title**: Thematic, specific to the quarter (e.g., "Walmart Inc. (WMT) Q4 FY2026 Earnings Preview: Holiday Harvest — Can Furner's First Print Confirm the $1T Thesis?")
- **Executive thesis** (2-3 short paragraphs max with bullet points):
  - What we expect from this print in 1-2 sentences
  - 4-6 bullet points covering: our EPS estimate vs consensus, guidance expectations, key metrics to watch, what would move the stock, key debates
  - Keep it direct and opinionated — take a view, don't hedge everything
- **Key management quotes** from the most recent earnings call woven into the narrative where relevant. Do NOT put these under a separate heading. Integrate them naturally as supporting evidence for your thesis points. Format as indented blockquotes.

---

**PAGE 2: Estimates, Themes & News**

- **Consensus Estimates Table** (single table, labeled as a figure):
  - Columns: Metric | Consensus | Our Estimate | y/y Change
  - Rows: Revenue, EPS, Gross Margin, Operating Income, and 2-3 company-specific KPIs that matter (e.g., comp sales, eComm growth, membership revenue — whatever the Street cares about for THIS company)
  - **Color-coding is strictly mechanical:** If the y/y change value is negative, use `class="neg"` (red). If positive, use `class="pos"` (green). If zero or N/A, use `class="neutral"`. The sign of the number determines the class — do NOT override based on interpretation. A -1.1% is ALWAYS red, even if the decline is small.
  - This is the ONLY guidance/estimates section. Do not repeat estimate data elsewhere.

- **Key Metrics Beyond Headline EPS** (bulleted list, 3-5 items):
  - The specific metrics that will determine if this is a good or bad quarter beyond the EPS number
  - For each: what the metric is, what consensus/management expects, why it matters
  - Be specific: "Walmart Connect ad revenue growth (consensus ~30% y/y, 3Q was 33%)"

- **Themes to Watch** (3-5 bullets):
  - Forward-looking items for the upcoming report
  - What management needs to deliver on, what could surprise, what the bears are focused on
  - Each theme: 1-2 sentences max

- **Recent News & Developments** (3-5 bullets):
  - Material news from the last 60 days, one line each
  - Date + headline + brief impact assessment
  - Only include items that could affect the upcoming print or guidance

---

**PAGES 3-5: Figures (all charts and tables)**

All figures are numbered sequentially. Every figure has a title and source line.

- **Figure 1: Quarterly Revenue & Diluted EPS** — Bar/line combo, 8 quarters
- **Figure 2: Margin Trends (Gross & Operating %)** — Dual line chart, 8 quarters
- **Figure 3: Revenue Growth y/y %** — Bar chart with green/red conditional coloring. **Only include quarters where both current and year-ago data exist** (typically the most recent 4 quarters from the 8 fetched). Do NOT include quarters where y/y cannot be computed — the chart should have 4 bars, not 8.
- **Figure 4: Business Segment Revenue** — Table: Segment | Latest Q Rev ($M) | % of Total | y/y Change
- **Figure 5: 1-Year Stock Price with Earnings Dates** — Price line with vertical annotation lines at earnings dates, labeled with quarter and 1-day post-earnings move
- **Figure 6: Stock Performance vs. Competitors (Indexed to 100)** — Multi-line chart, subject company as thick solid line, competitors as thinner dashed lines
- **Figure 7: LTM P/E vs. Competitors** — Horizontal bar chart, subject company highlighted in navy
- **Figure 8: Competitor Comparison Table** — Ticker | Company | Mkt Cap | LTM P/E | NTM P/E | YTD % | 1-Yr %

---

**APPENDIX: Data Sources & Calculations (MANDATORY — DO NOT SKIP OR ABBREVIATE)**

The appendix MUST begin with the AI disclaimer banner: `<div class="ai-disclaimer">Analysis is AI-generated — please confirm all outputs</div>`

The final page(s) of the report MUST include an Appendix table that documents **every claim** — numeric and non-numeric — cited in the report. **Every number that appears in the report body must have a corresponding row in this appendix, and every such number in the report body must be a clickable `<a href="#ref-N">` hyperlink that scrolls to its appendix row.** If a number appears in the report without a hyperlink to the appendix, the report is incomplete.

- **Table columns**: Ref # | Fact | Value | Source & Derivation
- **Ref #**: Sequential ID matching the hyperlink anchors in the report body (`ref-1`, `ref-2`, etc.). Each row has an `id="ref-N"` attribute so hyperlinks scroll to it.
- **Fact**: Human-readable label (e.g., "Q3 FY2026 Revenue", "LTM P/E — WMT", "Management flagged tariff headwinds", "Barclays upgraded to Overweight")
- **Value**: The exact figure as displayed in the report (e.g., "$152.3B", "24.5%", "28.1x"). For non-numeric facts, leave blank or write "N/A".
- **Source & Derivation**: This is the critical column. **Every row must have a specific, detailed source — not just a label.** Follow these rules strictly:

  **For raw financial data from S&P Capital IQ (revenue, EPS, gross profit, operating income, net income, EBITDA, prices, market cap, etc.):**
  - State the MCP function used and its key parameters. Format: `S&P Capital IQ — [function_name](identifier='[TICKER]', line_item='[item]', period_type='[type]', period='[Q# FY####]')`
  - Examples:
    - `S&P Capital IQ — get_financial_line_item_from_identifiers(identifier='WMT', line_item='revenue', period_type='quarterly', period='Q3 FY2026')`
    - `S&P Capital IQ — get_financial_line_item_from_identifiers(identifier='WMT', line_item='diluted_eps', period_type='quarterly', period='Q3 FY2026')`
    - `S&P Capital IQ — get_prices_from_identifiers(identifier='WMT', periodicity='day')`
    - `S&P Capital IQ — get_capitalization_from_identifiers(identifier='WMT', capitalization='market_cap')`
  - **Do NOT just write "S&P Capital IQ" with no detail.** The reader must know exactly which data point from which tool call produced this number.

  **For calculated values (margins, growth rates, P/E, returns, y/y changes):**
  - Show the full formula with **hyperlinked components** — each component must be an `<a href="#ref-N">` link back to the appendix row for that raw data point. This is critical: the reader must be able to click through from the calculated value to each of its inputs.
  - Example: `Gross Margin = <a href='#ref-5'>Gross Profit $37.2B</a> / <a href='#ref-1'>Revenue $152.3B</a> = 24.4%. Source: S&P Capital IQ (calculated)`
  - Example: `LTM P/E = <a href='#ref-20'>Price $172.35</a> / (<a href='#ref-8'>Q1 EPS $1.47</a> + <a href='#ref-9'>Q2 EPS $1.84</a> + <a href='#ref-10'>Q3 EPS $1.53</a> + <a href='#ref-11'>Q4 EPS $1.80</a>) = $172.35 / $6.64 = 25.9x`
  - Example: `Revenue y/y growth = (<a href='#ref-12'>Q3 FY26 Rev $165.8B</a> - <a href='#ref-3'>Q3 FY25 Rev $160.8B</a>) / <a href='#ref-3'>Q3 FY25 Rev $160.8B</a> = +3.1%`
  - **Every formula component must be a clickable hyperlink.** Do NOT write formulas with plain-text numbers.

  **For transcript-sourced claims (quotes, management commentary, guidance):**
  - Write the **verbatim excerpt sentence** from the transcript.
  - Reference the transcript by its full name and the `key_dev_id` used to fetch it.
  - Format: `"[verbatim quote]" — [Speaker], [Title]. Source: [Q# FY#### Earnings Call Transcript] (key_dev_id: [ID])`
  - Example: `"We expect comp sales growth of 3-4% in Q4" — CEO John Furner. Source: Q3 FY2026 Earnings Call Transcript (key_dev_id: 12345678)`

  **For Kensho Grounding search results (news, analyst ratings, consensus estimates):**
  - Write the key finding or excerpt from the search result.
  - **MANDATORY: Include the source URL** returned by the Kensho `search` tool as a clickable `<a href="[URL]" target="_blank">` hyperlink. This is the most important part — readers must be able to click through to the original source.
  - Format: `"[finding/excerpt]" — <a href="[URL]" target="_blank">[Source Title or Publication]</a>. Query: search("[query used]")`
  - Example: `"Barclays upgraded WMT to Overweight with $210 price target on Jan 15, 2026." — <a href="https://www.investing.com/news/barclays-upgrades-wmt" target="_blank">Investing.com, Jan 15 2026</a>. Query: search("WMT analyst ratings price target upgrades downgrades")`
  - If no URL was returned for a particular result, write "Source URL not available" and still include the search query.

**Completeness check:** Before finalizing the report, scan every number in the report body. If any number is not wrapped in `<a href="#ref-N" class="data-ref">`, fix it. If any appendix row has a Source & Derivation that is just a bare label like "S&P Capital IQ" with no function call detail, fix it. If any calculated value's formula lacks hyperlinked components, fix it. If any Kensho-sourced claim lacks a source URL, fix it.

Group the appendix rows by section (Financials, Valuation, Estimates & Consensus, Transcript Claims, News & Analyst Commentary, Stock Performance) with subheadings. Use smaller font size (10-11px).

---

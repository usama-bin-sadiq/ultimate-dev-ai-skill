<!-- Moved verbatim from tear-sheet/SKILL.md, the
     'workflow' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Workflow

### Step 1: Identify Inputs

Gather up to four things before proceeding:

1. **Company** — name or ticker. If only a ticker, resolve the full company name with an initial query (e.g., use the company info tool).
2. **Audience** — one of four types:
   - **Equity Research** — for buy-side/sell-side analysts evaluating an investment
   - **IB / M&A** — for bankers profiling a company in transaction context
   - **Corp Dev** — for internal strategic teams evaluating an acquisition target
   - **Sales / BD** — for commercial teams preparing for a client meeting
3. **Comparable companies** (optional) — if the user has specific comps in mind, note them. Otherwise the skill will identify peers from S&P Global data. This matters for Equity Research, IB/M&A, and Corp Dev tear sheets.
4. **Page length preference** (optional) — defaults vary by audience (see below), but the user can override.

If the user doesn't specify an audience, ask.

### Step 2: Read the Audience-Specific Reference

Read the corresponding reference file from this skill's directory:

- Equity Research → `references/equity-research.md`
- IB / M&A → `references/ib-ma.md`
- Corp Dev → `references/corp-dev.md`
- Sales / BD → `references/sales-bd.md`

Each reference defines sections, a query plan, formatting guidance, and page length defaults.

### Step 3: Pull Data via S&P Global MCP

**First:** Create the intermediate file directory:
```bash
mkdir -p /tmp/tear-sheet/
```

Use the **S&P Global** MCP tools (also known as the Kensho LLM-ready API). Claude will have access to structured tools for financial data, company information, market data, consensus estimates, earnings transcripts, M&A transactions, and business relationships. The query plans in each reference file describe what data to retrieve for each section — map these to the appropriate S&P Global tools available in the conversation.

**After each query step, immediately write the retrieved data to the intermediate file(s) specified in the reference file's query plan.** Do not defer writes — data written to disk is protected from context degradation in long conversations.

**Query strategy:**
Each reference file includes a query plan with 4-6 data retrieval steps. These are starting points, not rigid constraints. Prioritize data completeness over minimizing calls:

- **Always pull 4 fiscal years of financial data**, even though only 3 years are displayed. The fourth (earliest) year is needed to compute YoY revenue growth for the first displayed year. Without it, the earliest year's growth rate will show "N/A" — which looks like missing data, not a design choice.
- Execute the query plan as written, using whichever S&P Global tools match the data needed.
- If a tool call returns incomplete results, try alternative tools or narrower queries. For example, if company summary doesn't include segment detail, try the segments tool directly.
- If a data point isn't returned after a targeted retry, move on — label it "N/A" or "Not disclosed."
- Never fabricate data. If the tools don't return a number, do not estimate from training knowledge.

**User-specified comps:** If the user provided comparable companies, query financials and multiples for each comp explicitly. If no comps were provided, use whatever peer data the tools return, or identify peers from the company's sector using the competitors tool.

**Optional context from the user:** Listen for additional context the user provides naturally. If they mention who the acquirer is ("we're looking at this for our platform"), what they sell ("we sell data analytics to banks"), or who the likely buyers are ("this would be interesting to Salesforce or Microsoft"), incorporate that context into the relevant synthesis sections (Strategic Fit, Conversation Starters, Deal Angle). Don't prompt for this information — just use it if offered.

**Private company handling:**
CIQ includes private company data, so query the same way. However, expect sparser results. When generating for a private company:
- Skip: stock price, 52-week range, beta, stock performance, consensus estimates, trading comps
- Lean into: business overview, relationships, ownership structure, whatever financials are available
- Note "Private Company" prominently in the header

### Step 3b: Calculate Derived Metrics

After all data collection is complete and intermediate files are written, compute all derived metrics in a single dedicated pass. This is a calculation-only step — no new MCP queries.

**Read all intermediate files back into context**, then compute:

- **Margins:** Gross Margin %, EBITDA Margin %, FCF Margin %, Operating Margin %
- **Growth rates:** YoY revenue growth, YoY segment revenue growth, YoY EPS growth
- **Efficiency ratios:** FCF Conversion (FCF/EBITDA), R&D as % of Revenue, Capex as % of Revenue
- **Capital structure:** Net Debt (Total Debt − Cash & Equivalents), Net Debt / EBITDA
- **Segment mix:** Each segment's revenue as % of consolidated total revenue (use consolidated revenue as denominator per Data Integrity Rule 8)

**Validation (moved from Arithmetic Validation):** During this calculation pass, enforce all arithmetic checks:

- **Margin calculations:** Verify EBITDA Margin = EBITDA / Revenue, Gross Margin = Gross Profit / Revenue, etc. If the computed margin doesn't match the raw numbers, use the computation from raw components.
- **Growth rates:** Verify YoY growth = (Current − Prior) / Prior. Don't rely on pre-computed growth rates if you have the underlying values.
- **Segment totals:** If showing revenue by segment, verify segments sum to total revenue (within rounding tolerance). If they don't, omit the total row rather than publishing inconsistent math.
- **Percentage columns:** Verify "% of Total" columns sum to ~100%.
- **Valuation cross-checks:** If you show both EV and EV/Revenue, verify EV / Revenue ≈ the stated multiple.

If a validation fails: attempt recalculation from raw data. If still inconsistent, flag the metric as "N/A" rather than publishing incorrect numbers. Quiet math errors in a tear sheet destroy credibility.

**Write results** to `/tmp/tear-sheet/calculations.csv` with columns: `metric,value,formula,components`

Example rows:
```
metric,value,formula,components
gross_margin_fy2024,72.4%,gross_profit/revenue,"9524/13159"
revenue_growth_fy2024,12.3%,(current-prior)/prior,"13159/11716"
net_debt_fy2024,2150,total_debt-cash,"4200-2050"
```

### Step 3c: Verify Data Files

Before generating the document, verify that all intermediate files are present and populated.

**Read each intermediate file** via separate read operations and print a verification summary:

```
=== Tear Sheet Data Verification ===
company-profile.txt: ✓ (12 fields)
financials.csv:      ✓ (36 rows)
segments.csv:        ✓ (8 rows)
valuation.csv:       ✓ (5 rows)
calculations.csv:    ✓ (18 rows)
earnings.txt:        ✓ (populated)
relationships.txt:   ⚠ MISSING
peer-comps.csv:      ✓ (12 rows)
================================
```

**Soft gate:** If any file expected for the current audience type is missing or empty, print a warning but continue. The tear sheet handles missing data gracefully with "N/A" and section skipping. However, the warning ensures visibility into what data was lost.

**Critical rule: The files — not your memory of earlier conversation — are the single source of truth for every number in the document.** When generating the DOCX in Step 4, read values from the intermediate files. Do not rely on conversation context for financial data.

### Step 4: Format as DOCX

Read `/mnt/skills/public/docx/SKILL.md` for docx creation mechanics (docx-js via Node). Apply the Style Configuration above plus the section-specific formatting in the reference file.

**Page length defaults (user can override):**
- Equity Research: 1 page (density is the convention)
- IB / M&A: 1-2 pages
- Corp Dev: 1-2 pages
- Sales / BD: 1-2 pages

If content exceeds the target, each reference file specifies which sections to cut first.

**Output filename:** `[CompanyName]_TearSheet_[Audience]_[YYYYMMDD].docx`
Example: `Nvidia_TearSheet_CorpDev_20260220.docx`

Save to `/mnt/user-data/outputs/` and present to the user.

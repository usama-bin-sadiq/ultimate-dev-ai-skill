---
name: datapack-builder
description: Build professional financial services data packs from various sources including CIMs, offering memorandums, SEC filings, web search, or MCP servers. Extract, normalize, and standardize financial data into investment committee-ready Excel workbooks with consistent structure, proper formatting, and documented assumptions. Use for M&A due diligence, private equity analysis, investment committee materials, and standardizing financial reporting across portfolio companies. Do not use for simple financial calculations or working with already-completed data packs.
---

# Financial Data Pack Builder

Build professional, standardized financial data packs for private equity, investment banking, and asset management. Transform financial data from CIMs, offering memorandums, SEC filings, web search, or MCP server access into polished Excel workbooks ready for investment committee review.

**Important:** Use the xlsx skill for all Excel file creation and manipulation throughout this workflow.

## CRITICAL SUCCESS FACTORS

Detail moved verbatim to `references/critical-success-factors.md`. Load it when this section matters and the pointer is not enough.

## Structural Consistency

Detail moved verbatim to `references/structural-consistency.md`. Load it when this section matters and the pointer is not enough.

## STEP-BY-STEP WORKFLOW

Detail moved verbatim to `references/step-by-step-workflow.md`. Load it when this section matters and the pointer is not enough.

## NORMALIZATION PATTERNS

### Common Adjustments to EBITDA

**1. Restructuring charges**
- Add back if truly non-recurring (facility closure, one-time severance)
- Do NOT add back if company restructures every year
- Document specific nature and rationale for non-recurrence
- Example: "2023 restructuring: $3.0M facility closure, documented in source materials, one-time event"

**2. Stock-based compensation**
- Industry standard: add back for private equity analysis
- Treat as non-cash operating expense
- Be consistent across all periods
- Note if unusually high or includes one-time grants

**3. Acquisition-related costs**
- Add back transaction fees, integration costs
- Document specific amounts by type
- Do not add back ongoing integration investments
- Cite source for each adjustment

**4. Legal settlements and litigation**
- Add back if truly isolated incident
- Assess recurrence risk (one settlement vs pattern of litigation)
- Document nature of settlement
- Consider if this is normal course of business

**5. Asset sales or impairments**
- Exclude gains/losses on asset sales from operating EBITDA
- Remove impairment charges if truly non-recurring
- Document what assets were sold/impaired and why
- Adjust revenue if assets generated operating income

**6. Related party adjustments**
- Normalize above-market related party expenses (rent, management fees)
- Adjust to market rates with supporting documentation
- Remove personal expenses run through business
- Document market rate comparison

### Conservative vs Aggressive Normalization

**Management Case:**
- Include all adjustments management proposes
- Accept company's definition of "non-recurring"
- More aggressive EBITDA adjustments
- Use for understanding management's view

**Base Case (Recommended for investment decisions):**
- Only clearly non-recurring items
- Apply higher scrutiny to recurring "one-time" charges
- Exclude speculative adjustments
- More conservative, defensible to investment committee

## INDUSTRY-SPECIFIC ADAPTATIONS

### Technology/SaaS
Key metrics to capture:
- ARR (Annual Recurring Revenue) and MRR
- Customer count by cohort
- CAC (Customer Acquisition Cost) and LTV (Lifetime Value)
- Churn rate (gross and net)
- Net revenue retention
- Rule of 40 (Growth % + EBITDA Margin %)
- Magic number (sales efficiency)

Format notes: ARR is currency ($), customer count is number (no $), rates are %

### Manufacturing/Industrial
Key metrics to capture:
- Production capacity and capacity utilization %
- Units produced by product line
- Inventory turns
- Gross margin by product line
- Order backlog

Format notes: Units, capacity are numbers (no $), utilization is %, revenue/costs are currency

### Real Estate/Hospitality
Key metrics to capture:
- Properties/rooms/square footage
- Occupancy rates %
- ADR (Average Daily Rate) - currency format
- RevPAR (Revenue per Available Room) - currency format
- NOI (Net Operating Income) - currency format
- Cap rates %
- FF&E reserve

Format notes: Rooms/sqft are numbers, occupancy is %, ADR/RevPAR are currency

### Healthcare/Services
Key metrics to capture:
- Locations/facilities
- Providers/employees
- Patients/visits (volume metrics)
- Revenue per visit - currency
- Payor mix %
- Same-store growth %

Format notes: Locations/visits are numbers, revenue per visit is currency, rates are %

## FINAL DELIVERY CHECKLIST

Complete this checklist before delivering the data pack:

**Structure:**
- All required tabs present and in logical sequence
- Each tab has clear header and title
- Executive summary is concise (fits on one page)

**Data Accuracy:**
- All numbers trace to source (documents, URLs, or data servers)
- Source references documented for key figures (page numbers, URLs, etc.)
- All calculations are formula-based (no hardcoded calculated values)
- Subtotals and totals verified
- Balance sheet balances (Assets = Liabilities + Equity)
- No #REF!, #VALUE!, or #DIV/0! errors

**Formatting - Years and Numbers:**
- Years display correctly: 2020, 2021, 2022 (no commas)
- Financial data has $ signs: $50.0, $125.5
- Operational metrics have NO $ signs: 100 stores, 250 employees
- Percentages formatted correctly: 15.0%, 25.5%
- Negatives in parentheses: $(15.0) not -$15.0

**Formatting - Professional Standards:**
- Headers bold and left-aligned
- Numbers right-aligned
- Consistent indentation (2 spaces for sub-items)
- Single underline above subtotals
- Double underline below final totals
- Frozen panes on headers
- Consistent font throughout
- Minimal borders (only for structure)
- Clean, professional appearance throughout

**Content Completeness:**
- Financial statements complete (IS, BS, CF)
- Operating metrics comprehensively captured
- Normalization adjustments documented
- Assumptions clearly stated
- Executive summary clear, concise, and impactful
- Investment highlights compelling
- Market analysis provides context

**Documentation:**
- All normalization adjustments explained
- Every data cell cited from source with comments and links (document page numbers, URLs, or data source references)
- Assumptions documented with rationale
- Any data limitations noted
- Filename follows convention: CompanyName_DataPack_YYYY-MM-DD.xlsx

**Final Output:**
- File saved to outputs with proper naming convention
- All quality control checks passed

Each file below is loaded on demand, not at triage. 3 file(s):

- `references/final-delivery-checklist.md` — FINAL DELIVERY CHECKLIST. <!-- Moved verbatim from datapack-builder/SKILL.md, the
- `references/industry-specific-adaptations.md` — INDUSTRY-SPECIFIC ADAPTATIONS. <!-- Moved verbatim from datapack-builder/SKILL.md, the
- `references/normalization-patterns.md` — NORMALIZATION PATTERNS. <!-- Moved verbatim from datapack-builder/SKILL.md, the


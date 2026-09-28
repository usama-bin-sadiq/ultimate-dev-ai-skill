<!-- Moved verbatim from datapack-builder/SKILL.md, the
     'step-by-step-workflow' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## STEP-BY-STEP WORKFLOW

### Phase 1: Document Processing and Data Extraction

**Step 1.1: Analyze source data**
- Access source materials: uploaded documents, web search for public filings, or MCP server data
- Review data structure and identify key sections
- Locate financial statements (typically 3-5 years historical)
- Identify management projections if included
- Note fiscal year end date
- Flag any data quality issues immediately

**Step 1.2: Extract financial statements**
- Locate historical income statement data
- Extract balance sheet snapshots (year-end or quarter-end)
- Find cash flow statement
- Extract management projections if available
- Note all page references for traceability

**Step 1.3: Extract operating metrics**
- Identify non-financial KPIs relevant to industry
- Capture unit economics data
- Extract customer/location/capacity data
- Document growth metrics and trends

**Step 1.4: Extract market and industry data**
- Competitive positioning information
- Market size and growth rates
- Industry benchmark data
- Peer comparison information

**Step 1.5: Note key context**
- Transaction structure and rationale
- Management team background
- Investment highlights from source materials
- Risk factors and considerations
- Any data gaps or inconsistencies

### Phase 2: Data Normalization and Standardization

**Step 2.1: Normalize accounting presentation**
- Ensure consistent line item names across all years
- Standardize revenue recognition treatment
- Identify and document one-time charges
- Create "Adjusted EBITDA" reconciliation if needed
- Note any accounting policy changes

**Step 2.2: Apply format detection logic**
For each data point, determine format based on full context:
- Read tab name, table title, column header, and row label
- Apply essential rules (see above)
- When uncertain, examine original source document
- Default to cleaner formatting (less is more)

**Step 2.3: Identify normalization adjustments**
Common adjustments to document:
- Restructuring charges (add back if truly non-recurring)
- Stock-based compensation (add back per industry standard)
- Acquisition-related costs (add back, specify amounts)
- Legal settlements or litigation costs (evaluate recurrence risk)
- Asset sales or impairments (exclude from operating results)
- Related party adjustments (normalize to market rates)
Note: Source citation format varies by data source (page numbers for documents, URLs for web sources, server references for MCP data)

**Step 2.4: Create adjustment schedule**
For every normalization:
- Document what was adjusted and why
- Cite source (document page number, URL, or data source reference)
- Quantify dollar impact by year
- Assess recurrence risk
- Show calculation from reported to adjusted figures

**Step 2.5: Verify data integrity**
- Confirm subtotals sum correctly using formulas
- Verify balance sheet balances
- Check cash flow ties to balance sheet changes
- Cross-check numbers across tabs for consistency
- Flag any discrepancies for investigation

### Phase 3: Build Excel Workbook

**CRITICAL: Use xlsx skill for all Excel file manipulation. Read xlsx skill documentation before proceeding.**

**Step 3.1: Create standardized tab structure**
Create workbook with tabs:
- Executive Summary
- Historical Financials
- Balance Sheet
- Cash Flow
- Operating Metrics
- Property Performance (if applicable)
- Market Analysis
- Investment Highlights

**Step 3.2: Build each tab with proper formatting**
Apply formatting rules systematically:
- Headers: Bold, left-aligned, 11pt font
- Financial data: Currency format $#,##0.0 for millions
- Operational data: Number format #,##0 (no $)
- Percentages: 0.0% format
- Years: Text format to prevent comma insertion
- Negatives: Use accounting format with parentheses
- Underlines: Single above subtotals, double below totals

**Step 3.3: Insert formulas for calculations**
- All subtotals and totals must be formula-based
- Link balance sheet to income statement where appropriate
- Link cash flow to both income statement and balance sheet
- Create cross-tab references for validation
- Avoid hardcoding any calculated values

<correct_patterns>

### Row Reference Tracking - Copy This Pattern

**Store row numbers when writing data, then reference them in formulas:**

```python
# ✅ CORRECT - Track row numbers as you write
revenue_row = row
write_data_row(ws, row, "Revenue", revenue_values)
row += 1

ebitda_row = row
write_data_row(ws, row, "EBITDA", ebitda_values)
row += 1

# Use stored row numbers in formulas
margin_row = row
for col in year_columns:
    cell = ws.cell(row=margin_row, column=col)
    cell.value = f"={get_column_letter(col)}{ebitda_row}/{get_column_letter(col)}{revenue_row}"
```

**For complex models, use a dictionary:**

```python
row_refs = {
    'revenue': 5,
    'cogs': 6,
    'gross_profit': 7,
    'ebitda': 12
}

# Later in formulas
margin_formula = f"=B{row_refs['ebitda']}/B{row_refs['revenue']}"
```

</correct_patterns>

<common_mistakes>

### WRONG: Hardcoded Row Offsets

**Don't use relative offsets - they break when table structure changes:**

```python
# ❌ WRONG - Fragile offset-based references
formula = f"=B{row-15}/B{row-19}"  # What is row-15? What is row-19?

# ❌ WRONG - Magic numbers
formula = f"=B{current_row-10}*C{current_row-20}"
```

**Why this fails:**
- Breaks silently when you add/remove rows
- Impossible to verify correctness by reading code
- Creates debugging nightmares in the delivered Excel file

</common_mistakes>

**Step 3.4: Apply professional presentation**
- Freeze top row and first column on each data tab
- Set appropriate column widths (typically 12-15 characters)
- Right-align all numeric data
- Left-align all text and headers
- Add single/double underlines per accounting standards
- Ensure clean, minimal appearance

### Phase 4: Scenario Building (if projections included)

**Management Case:**
Present company's projections as provided in source materials:
- Extract all management assumptions
- Document growth rates, margin expansion, capital requirements
- Note key drivers and sensitivities
- Flag any "hockey stick" inflections that require skepticism
- Present as "Management Case" with clear labeling

**Base Case (Risk-Adjusted):**
Apply conservative adjustments to management projections based on company-specific risk factors:
- Apply revenue growth haircut reflecting execution risk and historical forecast accuracy
- Moderate margin expansion assumptions based on industry benchmarks and operating leverage
- Increase capex assumptions if growth-dependent
- Add working capital requirements if understated
- Delay synergy realization if applicable, based on integration complexity
- Document all adjustments with rationale and supporting analysis

**Downside Case (optional but recommended for LBO analysis):**
Stress test scenario based on industry cyclicality and company vulnerabilities:
- Model revenue decline reflecting recession risk or competitive pressure
- Assume margin compression under stress (volume deleverage, pricing pressure)
- Test covenant compliance and liquidity
- Assess downside protection
- Document key risks being stress-tested

**Documentation requirements for scenarios:**
Create assumptions schedule showing:
- Key assumptions by scenario (revenue growth, margins, capex %)
- Rationale for each adjustment
- Sensitivity analysis on key variables
- Historical forecast accuracy if available
- Comparison to industry benchmarks

### Phase 5: Quality Control and Validation

**Step 5.1: Data accuracy checks**
Validate:
- Every number traces to source (check spot samples, cite documents/URLs/servers)
- All calculations are formula-based (no hardcoded values)
- Subtotals and totals are mathematically correct
- Years display without commas (2024 NOT 2,024)
- No formula errors: #REF!, #VALUE!, #DIV/0!, #N/A

**Step 5.2: Format consistency checks**
Verify:
- Financial data has $ signs in format
- Operational data has NO $ signs
- Percentages display as % (15.0% not 0.15)
- Negative numbers use parentheses for financial data
- Headers are bold and left-aligned
- Numbers are right-aligned
- Years are text format

**Step 5.3: Structure and completeness checks**
Confirm:
- All required tabs present and properly sequenced
- Executive summary is concise (fits on one page)
- All key metrics captured comprehensively
- Logical flow from summary to detail
- Appropriate level of granularity in each tab
- No missing data or incomplete sections

**Step 5.4: Professional presentation checks**
Review:
- Minimal borders (only for structure)
- Consistent indentation (2 spaces for sub-items)
- Proper accounting underlines (single and double)
- Clean, professional appearance throughout
- Appropriate column widths (not too narrow or wide)

**Step 5.5: Documentation and assumptions checks**
Ensure:
- All normalization adjustments documented with rationale
- Source citations included (document page numbers, URLs, or data source references)
- Assumptions clearly stated and reasonable
- Executive summary accurate and impactful
- Filename includes company name and date

### Phase 6: Final Delivery

**Step 6.1: Create executive summary**
Write concise, impactful summary including:
- Company overview: business model, products/services, geography (2-3 sentences)
- Key financial metrics: Revenue, EBITDA, Growth rates (table format)
- Investment highlights: 3-5 key strengths or opportunities
- Notable risks or considerations (briefly)
- Transaction context if applicable

**Step 6.2: Final file preparation**
- Save workbook with proper naming: CompanyName_DataPack_YYYY-MM-DD.xlsx

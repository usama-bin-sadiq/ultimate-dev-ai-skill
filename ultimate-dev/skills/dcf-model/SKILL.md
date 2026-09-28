---
name: dcf-model
description: Real DCF (Discounted Cash Flow) model creation for equity valuation. Retrieves financial data from SEC filings and analyst reports, builds comprehensive cash flow projections with proper WACC calculations, performs sensitivity analysis, and outputs professional Excel models with executive summaries. Use when users need to value a company using DCF methodology, request intrinsic value analysis, or ask for detailed financial modeling with growth projections and terminal value calculations.
---

# DCF Model Builder

## Overview

This skill creates institutional-quality DCF models for equity valuation following investment banking standards. Each analysis produces a detailed Excel model (with sensitivity analysis included at the bottom of the DCF sheet).

## Tools

- Default to using all of the information provided by the user and MCP servers available for data sourcing.

## Critical Constraints - Read These First

These constraints apply throughout all DCF model building. Review before starting:

**Environment: Office JS vs Python/openpyxl:**
- **If running inside Excel (Office Add-in / Office JS environment):** Use Office JS directly — do NOT use Python/openpyxl. Write formulas via `range.formulas = [["=D19*(1+$B$8)"]]`. No separate recalc step needed; Excel calculates natively. Use `range.format.*` for styling. The same formulas-over-hardcodes rule applies: set `.formulas`, never `.values` for derived cells.
- **If generating a standalone .xlsx file (no live Excel session):** Use Python/openpyxl as described below, then run `recalc.py` before delivery.
- The rest of this skill uses openpyxl examples — translate to Office JS API calls when in that environment, but all principles (formula strings, cell comments, section checkpoints, sensitivity table loops) apply identically.

**⚠️ Office JS merged cell pitfall:** When building section headers with merged cells, do NOT call `.merge()` then set `.values` on the merged range — Office JS still reports the range's original dimensions and will throw `InvalidArgument: The number of rows or columns in the input array doesn't match the size or dimensions of the range`. Instead, write the value to the top-left cell alone, then merge and format the full range:

```js
// WRONG — throws InvalidArgument:
const hdr = ws.getRange("A7:H7");
hdr.merge();
hdr.values = [["MARKET DATA & KEY INPUTS"]];  // 1×1 array vs 1×8 range → fails

// CORRECT — value first on single cell, then merge + format the range:
ws.getRange("A7").values = [["MARKET DATA & KEY INPUTS"]];
const hdr = ws.getRange("A7:H7");
hdr.merge();
hdr.format.fill.color = "#1F4E79";
hdr.format.font.bold = true;
hdr.format.font.color = "#FFFFFF";
```

This applies to every merged section header in the DCF (market data, scenario blocks, cash flow projection, terminal value, valuation summary, sensitivity tables).

**Formulas Over Hardcodes (NON-NEGOTIABLE):**
- Every projection, margin, discount factor, PV, and sensitivity cell MUST be a live Excel formula — never a value computed in Python and written as a number
- When using openpyxl: `ws["D20"] = "=D19*(1+$B$8)"` is correct; `ws["D20"] = calculated_revenue` is WRONG
- The only hardcoded numbers permitted are: (1) raw historical inputs, (2) assumption drivers (growth rates, WACC inputs, terminal g), (3) current market data (share price, debt balance)
- If you catch yourself computing something in Python and writing the result — STOP. The model must flex when the user changes an assumption.

**Verify Step-by-Step With the User (DO NOT build end-to-end):**
- After data retrieval → show the user the raw inputs block (revenue, margins, shares, net debt) and confirm before projecting
- After revenue projections → show the projected top line and growth rates, confirm before building margin build
- After FCF build → show the full FCF schedule, confirm logic before computing WACC
- After WACC → show the calculation and inputs, confirm before discounting
- After terminal value + PV → show the equity bridge (EV → equity value → per share), confirm before sensitivity tables
- Catch errors at each stage — a wrong margin assumption discovered after sensitivity tables are built means rebuilding everything downstream

**Sensitivity Tables:**
- **Use an ODD number of rows and columns** (standard: 5×5, sometimes 7×7) — this guarantees a true center cell
- **Center cell = base case.** Build the axis values so the middle row header and middle column header exactly equal the model's actual assumptions (e.g., if base WACC = 9.0%, the middle row is 9.0%; if terminal g = 3.0%, the middle column is 3.0%). The center cell's output must therefore equal the model's actual implied share price — this is the sanity check that the table is built correctly.
- **Highlight the center cell** with the medium-blue fill (`#BDD7EE`) + bold font so it's immediately visible which cell is the base case.
- Populate ALL cells (typically 3 tables × 25 cells = 75) with full DCF recalculation formulas
- Use openpyxl loops (or Office JS loops) to write formulas programmatically
- NO placeholder text, NO linear approximations, NO manual steps required
- Each cell must recalculate full DCF for that assumption combination

**Cell Comments:**
- Add cell comments AS each hardcoded value is created
- Format: "Source: [System/Document], [Date], [Reference], [URL if applicable]"
- Every blue input must have a comment before moving to next section
- Do not defer to end or write "TODO: add source"

**Model Layout Planning:**
- Define ALL section row positions BEFORE writing any formulas
- Write ALL headers and labels first
- Write ALL section dividers and blank rows second
- THEN write formulas using the locked row positions
- Test formulas immediately after creation

**Formula Recalculation:**
- Run `python recalc.py model.xlsx 30` before delivery
- Fix ALL errors until status is "success"
- Zero formula errors required (#REF!, #DIV/0!, #VALUE!, etc.)

**Scenario Blocks:**
- Create separate blocks for Bear/Base/Bull cases
- Show assumptions horizontally across projection years within each block
- Use IF formulas: `=IF($B$6=1,[Bear cell],IF($B$6=2,[Base cell],[Bull cell]))`
- Verify formulas reference correct scenario block cells

## DCF Process Workflow

Detail moved to `references/dcf-process-workflow.md`.

## Excel File Creation

**This skill uses the `xlsx` skill for all spreadsheet operations.** The xlsx skill provides:
- Standardized formula construction rules
- Number formatting conventions
- Automated formula recalculation via `recalc.py` script
- Comprehensive error checking and validation

All Excel files created by this skill must follow xlsx skill requirements, including zero formula errors and proper recalculation.

## Quality Rubric

Every DCF model must maximize for:
1. **Realistic revenue and margin assumptions** based on historical performance
2. **Appropriate cost of capital calculation** with proper CAPM methodology
3. **Comprehensive sensitivity analysis** showing valuation ranges
4. **Clear terminal value calculation** with supporting rationale
5. **Professional model structure** enabling scenario analysis
6. **Transparent documentation** of all key assumptions

## Input Requirements

### Minimum Required Inputs
1. **Company identifier**: Ticker symbol or company name
2. **Growth assumptions**: Revenue growth rates for projection period (or "use consensus")
3. **Optional parameters**:
   - Projection period (default: 5 years)
   - Scenario cases (Bear/Base/Bull growth and margin assumptions)
   - Terminal growth rate (default: 2.5-3.0%)
   - Specific WACC inputs if not using CAPM

## Excel Model Structure

Detail moved to `references/excel-model-structure.md`.

## Case Selector Implementation

Detail moved to `references/case-selector-implementation.md`.

## Deliverables Structure

**File naming**: `[Ticker]_DCF_Model_[Date].xlsx`

**Two sheets**:
1. **DCF** - Complete model with Bear/Base/Bull cases + three sensitivity tables at bottom (WACC vs Terminal Growth, Revenue Growth vs EBIT Margin, Beta vs Risk-Free Rate)
2. **WACC** - Cost of capital calculation

**Key features**: Case selector (1/2/3), consolidation column with INDEX/OFFSET formulas, color-coded cells, cell comments on all inputs, professional borders

## Best Practices

Detail moved to `references/best-practices.md`.

## Common Variations

Detail moved to `references/common-variations.md`.

## Workflow Integration

### At Start of DCF Build

1. **Gather market data**:
   - Check for available MCP servers for current market data
   - Use web search/fetch for stock prices, beta, and other market metrics
   - Request from user if specific data is needed

2. **Gather historical financials**:
   - Check for available MCP servers (Daloopa, etc.)
   - Request from user if not available via MCP
   - Manual extraction from 10-Ks if necessary

3. **Begin model construction** using the DCF methodology detailed in this skill

### During Model Construction

1. **Build Excel model** using openpyxl with formulas (not hardcoded values)
2. **Follow xlsx skill conventions** for formula construction and formatting
3. **Apply fill colors only if requested** by user or if specific brand guidelines are provided

### Before Delivering Model (MANDATORY)

1. **Verify structure**:
   - Scenario blocks for Bear/Base/Bull with assumptions across projection years
   - Case selector functional with formulas referencing correct scenario blocks
   - Sensitivity tables at bottom of DCF sheet (not separate sheet)
   - Font colors: Blue inputs, black formulas, green sheet links
   - Cell comments on ALL hardcoded inputs
   - Professional borders around major sections

2. **Recalculate formulas**: Run `python recalc.py model.xlsx 30`

3. **Check output**:
   - If `status` is `"success"` → Continue to step 4
   - If `status` is `"errors_found"` → Check `error_summary`

4. **Fix errors and re-run recalc.py** until status is "success"

5. **Spot-check formulas**:
   - Test one FCF formula - does it reference the correct assumption rows?
   - Change case selector - does the consolidation column update properly?
   - Verify revenue formulas reference consolidation column (not nested IF formulas)

6. **Deliver model**

### Available Data Sources

- **MCP servers**: If configured (Daloopa for historical financials)
- **Web search/fetch**: For current stock prices, beta, and market data
- **User-provided data**: Historical financials, consensus estimates
- **Manual extraction**: SEC EDGAR filings as fallback

## Final Output Checklist

Detail moved to `references/final-output-checklist.md`.


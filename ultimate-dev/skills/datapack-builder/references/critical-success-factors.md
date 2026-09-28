<!-- Moved verbatim from datapack-builder/SKILL.md, the
     'critical-success-factors' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## CRITICAL SUCCESS FACTORS

Every data pack must achieve these standards. Failure on any point makes the deliverable unusable.

### 1. Data Accuracy (Zero Tolerance for Errors)
- Trace every number to source document with page reference
- Use formula-based calculations exclusively (no hardcoded values)
- Cross-check subtotals and totals for internal consistency
- Verify balance sheet balances: Assets = Liabilities + Equity
- Confirm cash flow ties to balance sheet changes

### 2. ESSENTIAL RULES

**RULE 1: Financial data (measuring money) → Currency format with $**
Triggers: Revenue, Sales, Income, EBITDA, Profit, Loss, Cost, Expense, Cash, Debt, Assets, Liabilities, Equity, Capex
Format: $#,##0.0 for millions, $#,##0 for thousands
Negatives: $(123.0) NOT -$123

**RULE 2: Operational data (counting things) → Number format, NO $**
Triggers: Units, Stores, Locations, Employees, Customers, Square Feet, Properties, Headcount
Format: #,##0 with commas
Negatives: (123) consistent with rest of table

**RULE 3: Percentages (rates and ratios) → Percentage format**
Triggers: Margin, Growth, Rate, Percentage, Yield, Return, Utilization, Occupancy
Format: 0.0% for one decimal place
Display: 15.0% NOT 0.15

**RULE 4: Years → Text format to prevent comma insertion**
Format: Text or custom to prevent 2,024
Display: 2020, 2021, 2022, 2023A, 2024E

**RULE 5: When context is mixed, each metric gets its own appropriate format**
Example:
```
Segment Analysis, 2022, 2023, 2024
Retail Revenue, $50.0, $55.0, $60.0
  Stores, 100, 110, 120
  Revenue per Store, $0.5, $0.5, $0.5
```
Revenue and per-store metrics use $, Store count uses number format.

**RULE 6: Use formulas for all calculations → Never hardcode calculated values**
All subtotals, totals, ratios, and derived metrics must be formula-based, not hardcoded values. This ensures accuracy and allows for dynamic updates.

### 3. Professional Presentation Standards

**Formatting Standards:**

**Color Scheme - Two Layers:**

**Layer 1: Font Colors (MANDATORY from xlsx skill)**
- **Blue text (RGB: 0,0,255)**: ALL hardcoded inputs (historical data, assumptions), NOT normal text
- **Black text (RGB: 0,0,0)**: ALL formulas and calculations
- **Green text (RGB: 0,128,0)**: Links to other sheets

**Layer 2: Fill Colors (Optional for enhanced presentation)**
- Fill colors are optional and should only be applied if requested by the user or if enhancing presentation
- If the user requests colors or professional formatting, use this standard scheme:
  - **Section headers**: Dark blue (RGB: 68,114,196) background with white text
  - **Sub-headers/column headers**: Light blue (RGB: 217,225,242) background with black text
  - **Input cells**: Light green/cream (RGB: 226,239,218) background with blue text
  - **Calculated cells**: White background with black text
- Users can override with custom brand colors if specified

**How the layers work together (if fill colors are used):**
- Input cell: Blue text + light green fill = "User-entered data"
- Formula cell: Black text + white background = "Calculated value"
- Sheet link: Green text + white background = "Reference from another tab"

**Font color tells you WHAT it is. Fill color tells you WHERE it is (if used).**

**IMPORTANT:** Font colors from xlsx skill are mandatory. Fill colors are optional - default is white/no fill unless the user requests enhanced formatting or colors.

**Always apply:**
- Bold headers, left-aligned
- Numbers right-aligned
- 2-space indentation for sub-items
- Single underline above subtotals
- Double underline below final totals
- Freeze panes on row/column headers
- Minimal borders (only where structurally needed)
- Consistent font (typically Calibri or Arial 11pt)

**Never include:**
- Borders around every cell
- Multiple fonts or font sizes
- Charts unless specifically requested
- Excessive formatting or decoration

<!-- Moved verbatim from tear-sheet/SKILL.md, the
     'intermediate-file-rule' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Intermediate File Rule

All data retrieved from MCP tools must be persisted to structured intermediate files before document generation. These files — not conversation context — are the single source of truth for every number in the document.

**Setup:** At the start of Step 3, create the working directory:
```
mkdir -p /tmp/tear-sheet/
```

**Write-after-query mandate:** After each MCP query step completes, immediately write the retrieved data to the appropriate intermediate file(s). Do not wait until all queries finish. Each reference file's query plan specifies which file(s) to write after each step.

**File schemas:**

| File | Format | Columns / Structure | Used By |
|---|---|---|---|
| `/tmp/tear-sheet/company-profile.txt` | Key-value text | name, ticker, exchange, HQ, sector, industry, founded, employees, market_cap, enterprise_value, stock_price, 52wk_high, 52wk_low, shares_outstanding, beta, ownership | All |
| `/tmp/tear-sheet/financials.csv` | CSV | `period,line_item,value,source` | All |
| `/tmp/tear-sheet/segments.csv` | CSV | `period,segment_name,revenue,source` | ER, IB, CD |
| `/tmp/tear-sheet/valuation.csv` | CSV | `metric,trailing,forward,source` | ER, IB, CD |
| `/tmp/tear-sheet/consensus.csv` | CSV | `metric,fy_year,value,source` | ER |
| `/tmp/tear-sheet/earnings.txt` | Structured text | Quarter, date, key quotes, guidance, key drivers | ER, IB, Sales |
| `/tmp/tear-sheet/relationships.txt` | Structured text | Customers, suppliers, partners, competitors — each with descriptors | IB, CD, Sales |
| `/tmp/tear-sheet/peer-comps.csv` | CSV | `ticker,metric,value,source` | ER, IB, CD |
| `/tmp/tear-sheet/ma-activity.csv` | CSV | `date,target,deal_value,type,rationale,source` | IB, CD |
| `/tmp/tear-sheet/calculations.csv` | CSV | `metric,value,formula,components` | All (written in Step 3b) |

**Abbreviations:** ER = Equity Research, IB = IB/M&A, CD = Corp Dev, Sales = Sales/BD.

Not every audience type uses every file — the reference files define which query steps apply. Files not relevant to the current audience type need not be created.

**Raw values only.** Intermediate files store raw values as returned by the tools. Do not pre-compute margins, growth rates, or other derived metrics in these files — that happens in Step 3b.

**Page budget enforcement:** Each reference file specifies a default page length and a numbered cut order. If the rendered document exceeds the target, apply cuts in the order specified — do not attempt to shrink font sizes or margins below the template minimums. The cut order is a strict priority stack: cut section 1 completely before touching section 2.

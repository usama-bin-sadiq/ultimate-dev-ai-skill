<!-- Moved verbatim from earnings-preview-beta/SKILL.md, the
     'phase-6-verification-calculations-mandatory-do-not-skip' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 6: Verification & Calculations (MANDATORY — DO NOT SKIP)

Before generating the report, read back ALL intermediate files and perform calculations from the clean data. This phase ensures data integrity by working from files rather than compressed conversation context.

1. **Read all intermediate files** using bash `cat` commands:
   - `cat /tmp/earnings-preview/company-info.txt`
   - `cat /tmp/earnings-preview/transcript-extracts.txt`
   - `cat /tmp/earnings-preview/financials.csv`
   - `cat /tmp/earnings-preview/segments.csv`
   - `cat /tmp/earnings-preview/prices.csv`
   - `cat /tmp/earnings-preview/peer-eps.csv`
   - `cat /tmp/earnings-preview/peer-market-caps.csv`
   - `cat /tmp/earnings-preview/consensus-eps.csv`
   - `cat /tmp/earnings-preview/kensho-findings.txt`
   - `cat /tmp/earnings-preview/earnings-dates.csv`

2. **Calculate derived metrics** from the raw data now in context:
   - Gross margin % = gross_profit / revenue (per quarter)
   - Operating margin % = operating_income / revenue (per quarter)
   - Revenue y/y growth % = (current Q revenue - year-ago Q revenue) / year-ago Q revenue
   - EPS y/y growth % = same logic; use "n.m." if base is negative
   - Segment y/y growth % = match segment by name to year-ago Q; if missing, note "y/y not available"
   - LTM P/E per company = latest price / sum of most recent 4 quarterly EPS (check which 4 quarters are available per ticker using `peer-eps.csv`)
   - NTM P/E per company = latest price / NTM EPS, where **NTM EPS = sum of the next 4 quarterly consensus mean EPS estimates** from `consensus-eps.csv`. Add all 4 quarters' consensus_mean_eps values for each ticker. If fewer than 4 forward quarters are available for a peer, mark NTM P/E as "n/a". Note in the appendix which 4 quarters were summed.
   - Stock returns (YTD, 1-yr, 30d, 90d) = find the **common first date across all tickers** in `prices.csv`, then compute returns from that date

3. **Cross-check**:
   - Verify every segment y/y has the actual prior-year row in `segments.csv`. If not, mark "y/y not available."
   - Verify all stock return base dates are identical across tickers.
   - Verify any multi-step calculation by re-summing components (e.g., LTM EPS sum matches the 4 quarterly values).
   - Verify all verbatim quotes in `transcript-extracts.txt` are exact copy-pastes (not paraphrases).

4. **Write** `/tmp/earnings-preview/calculations.csv` with all derived values:
```
ticker,metric,value,formula,components
D,gross_margin_Q3_2025,32.5%,gross_profit/revenue,"gross_profit=1238100000,revenue=3810000000"
D,revenue_yoy_Q3_2025,+9.3%,(Q3_2025-Q3_2024)/Q3_2024,"Q3_2025=3810000000,Q3_2024=3486000000"
D,ltm_pe,24.2x,price/ltm_eps,"price=65.46,ltm_eps=2.70,quarters=Q4_2024+Q1_2025+Q2_2025+Q3_2025"
D,ntm_pe,18.5x,price/ntm_eps,"price=65.46,ntm_eps=3.56,quarters=Q4_2025(0.88)+Q1_2026(0.72)+Q2_2026(0.91)+Q3_2026(1.05),source=get_consensus_estimates_from_identifiers"
D,yoy_return,+17.6%,(end-start)/start,"end=65.46,start=55.67,base_date=2025-02-19"
DUK,yoy_return,+13.0%,(end-start)/start,"end=126.32,start=111.79,base_date=2025-02-19"
...
```

This file becomes the single source of truth for all numbers in the report.

---

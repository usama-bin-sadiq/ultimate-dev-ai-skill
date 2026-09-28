<!-- Moved verbatim from earnings-preview-beta/SKILL.md, the
     'phase-3-competitor-analysis' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 3: Competitor Analysis

1. Call `get_competitors_from_identifiers` with `competitor_source="all"`.
2. Select **top 5-7 most relevant public competitors**.
3. For the company AND all selected competitors, gather:
   - `get_prices_from_identifiers` with `periodicity="day"`, last 12 months
   - `get_financial_line_item_from_identifiers` for `diluted_eps`, `period_type="quarterly"`, `num_periods=8`
   - `get_capitalization_from_identifiers` with `capitalization="market_cap"` (latest)
   - `get_consensus_estimates_from_identifiers` with `period_type="quarterly"`, `num_periods_forward=4` — this returns consensus mean EPS estimates for the next 4 quarters, which are summed to compute NTM EPS

**After each tool call returns, immediately append the raw data to the appropriate intermediate file:**

**Write** `/tmp/earnings-preview/prices.csv` — one row per (ticker, date, close). Include the `source` column with the exact MCP function call. Write the subject company's prices first, then each competitor's as you fetch them:
```
ticker,date,close,source
D,2025-02-19,55.67,get_prices_from_identifiers(identifier='D',periodicity='day')
D,2025-02-20,55.82,get_prices_from_identifiers(identifier='D',periodicity='day')
...
DUK,2025-02-19,111.79,get_prices_from_identifiers(identifier='DUK',periodicity='day')
...
```
Note: the `source` value is the same for all rows from a single call — write it on every row so it's always available.

**Write** `/tmp/earnings-preview/peer-eps.csv` — one row per (ticker, period, eps). Write immediately after each `diluted_eps` call:
```
ticker,period,diluted_eps,source
D,Q4 2024,1.09,get_financial_line_item_from_identifiers(identifier='D',line_item='diluted_eps',period_type='quarterly')
D,Q1 2025,-0.11,get_financial_line_item_from_identifiers(identifier='D',line_item='diluted_eps',period_type='quarterly')
...
DUK,Q4 2024,1.52,get_financial_line_item_from_identifiers(identifier='DUK',line_item='diluted_eps',period_type='quarterly')
...
```

**Write** `/tmp/earnings-preview/peer-market-caps.csv` — one row per ticker. Write immediately after each `market_cap` call:
```
ticker,market_cap,retrieval_date,source
D,55900000000,2026-02-19,get_capitalization_from_identifiers(identifier='D',capitalization='market_cap')
DUK,98300000000,2026-02-19,get_capitalization_from_identifiers(identifier='DUK',capitalization='market_cap')
...
```

**Write** `/tmp/earnings-preview/consensus-eps.csv` — one row per (ticker, period, consensus mean EPS). Write immediately after each `get_consensus_estimates_from_identifiers` call:
```
ticker,period,consensus_mean_eps,num_estimates,source
D,Q4 2025,0.88,12,get_consensus_estimates_from_identifiers(identifier='D',period_type='quarterly',num_periods_forward=4)
D,Q1 2026,0.72,10,get_consensus_estimates_from_identifiers(identifier='D',period_type='quarterly',num_periods_forward=4)
D,Q2 2026,0.91,9,get_consensus_estimates_from_identifiers(identifier='D',period_type='quarterly',num_periods_forward=4)
D,Q3 2026,1.05,8,get_consensus_estimates_from_identifiers(identifier='D',period_type='quarterly',num_periods_forward=4)
DUK,Q4 2025,1.48,14,get_consensus_estimates_from_identifiers(identifier='DUK',period_type='quarterly',num_periods_forward=4)
...
```

4. **Do NOT calculate P/E or returns yet.** The raw data is now on disk. Calculations happen in Phase 6 (Verification), reading from these files.

**Date Consistency Rule (stock returns):** When computing comparative stock returns (YTD %, 1-yr %, 30d %, 90d %), ALL tickers MUST use the **exact same start and end dates**. After writing all price data to `prices.csv`, identify the first trading date that appears in ALL tickers' data and use that as the common base date. Do NOT use different base dates for different tickers (e.g., the subject from Feb 19 and peers from Feb 28). If a ticker's data starts later than others, use the first overlapping date for ALL calculations. State the common base date in the appendix for every return calculation.

**P/E Currency Rule (LTM P/E):** When computing LTM P/E for each company, use that company's **most recent 4 reported quarters** from `peer-eps.csv` — not a fixed calendar window applied to all. If a peer has already reported Q4 2025 while the subject company has only reported through Q3 2025, the peer's LTM EPS should include Q4 2025. Check the latest reported period for each company and use the 4 most recent periods per company. Note in the appendix which 4 quarters were used for each P/E calculation.

**Market Cap Date-Stamp:** When reporting market cap, use the `retrieval_date` from `peer-market-caps.csv`. If it differs from the report date, note this in the appendix.

---

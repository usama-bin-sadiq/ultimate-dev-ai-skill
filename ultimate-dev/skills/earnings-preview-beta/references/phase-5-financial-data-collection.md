<!-- Moved verbatim from earnings-preview-beta/SKILL.md, the
     'phase-5-financial-data-collection' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 5: Financial Data Collection

**Quarterly financials (last 8 quarters):**
`get_financial_line_item_from_identifiers` with `period_type="quarterly"`, `num_periods=8` for:
`revenue`, `gross_profit`, `operating_income`, `ebitda`, `net_income`, `diluted_eps`

**After each line item call returns, immediately append to** `/tmp/earnings-preview/financials.csv`. Write the raw values exactly as returned — do NOT round or convert yet. Include the `source` column with the exact MCP function call and parameters:
```
ticker,period,line_item,value,source
D,Q4 2024,revenue,3941000000,get_financial_line_item_from_identifiers(identifier='D',line_item='revenue',period_type='quarterly')
D,Q1 2025,revenue,3400000000,get_financial_line_item_from_identifiers(identifier='D',line_item='revenue',period_type='quarterly')
D,Q2 2025,revenue,4076000000,get_financial_line_item_from_identifiers(identifier='D',line_item='revenue',period_type='quarterly')
D,Q3 2025,revenue,3810000000,get_financial_line_item_from_identifiers(identifier='D',line_item='revenue',period_type='quarterly')
D,Q4 2024,diluted_eps,1.09,get_financial_line_item_from_identifiers(identifier='D',line_item='diluted_eps',period_type='quarterly')
D,Q1 2025,diluted_eps,-0.11,get_financial_line_item_from_identifiers(identifier='D',line_item='diluted_eps',period_type='quarterly')
...
```

**Do NOT calculate margins or growth rates yet.** Write raw data only. Calculations happen in Phase 6.

**Segment data:**
- `get_segments_from_identifiers` with `segment_type="business"`, `period_type="quarterly"`, `num_periods=8`
- You need 8 quarters (not 4) so you have the year-ago quarter for y/y comparisons. To calculate y/y for Q3 2025, you need Q3 2024 — which is the 5th quarter back. **If the prior-year quarter's segment data is not available in the API response, do NOT estimate or fabricate it. State "y/y not available" in the report.**

**Immediately write** `/tmp/earnings-preview/segments.csv`:
```
ticker,period,segment_name,revenue,source
D,Q3 2024,Dominion Energy Virginia,2762000000,get_segments_from_identifiers(identifier='D',segment_type='business',period_type='quarterly')
D,Q3 2024,Dominion Energy South Carolina,848000000,get_segments_from_identifiers(identifier='D',segment_type='business',period_type='quarterly')
D,Q3 2024,Contracted Energy,260000000,get_segments_from_identifiers(identifier='D',segment_type='business',period_type='quarterly')
D,Q3 2025,Dominion Energy Virginia,3311000000,get_segments_from_identifiers(identifier='D',segment_type='business',period_type='quarterly')
D,Q3 2025,Dominion Energy South Carolina,945000000,get_segments_from_identifiers(identifier='D',segment_type='business',period_type='quarterly')
D,Q3 2025,Contracted Energy,297000000,get_segments_from_identifiers(identifier='D',segment_type='business',period_type='quarterly')
...
```

**Earnings history (for stock chart annotations):**
- `get_earnings_from_identifiers` — collect past earnings dates within the 12-month price window.
- **Immediately write** `/tmp/earnings-preview/earnings-dates.csv`:
```
ticker,earnings_date,call_name,source
D,2025-05-02,Q1 2025 Earnings Call,get_earnings_from_identifiers(identifier='D')
D,2025-08-01,Q2 2025 Earnings Call,get_earnings_from_identifiers(identifier='D')
D,2025-10-31,Q3 2025 Earnings Call,get_earnings_from_identifiers(identifier='D')
...
```

---

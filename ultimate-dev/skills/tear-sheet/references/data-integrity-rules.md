<!-- Moved verbatim from tear-sheet/SKILL.md, the
     'data-integrity-rules' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Data Integrity Rules

These override everything else:
1. **S&P Global tools are the only source for financial data.** Do not fill gaps with training knowledge — it may be stale or wrong.
2. **Label what you can't find.** Use "N/A" or "Not disclosed" rather than omitting a row silently.
3. **Dates matter.** Note the fiscal year end or reporting period. Don't assume calendar year = fiscal year. Market data (stock prices, market cap) should include an "as of" date.
4. **Don't mix reporting periods.** If you have FY2023 revenue and LTM EBITDA, label them distinctly.
5. **Prefer MCP-returned fields over manual computation.** If the S&P Global tools return a pre-computed field (e.g., net debt, EBITDA, FCF), use that value directly rather than computing it from components. Only compute derived metrics manually when the tools do not return the field. This reduces discrepancies.
6. **Ensure consistency across tear sheet types.** If generating multiple tear sheets for the same company (e.g., equity research and IB/M&A in the same session), the same underlying data points must produce identical values across all outputs. Net debt, revenue, EBITDA, margins, and growth rates must match exactly. Do not re-query or re-compute independently per report — reuse the same retrieved values.
7. **Never downgrade known transaction values.** If the M&A tools return a deal value for a transaction, that value must appear in the output. Do not replace a known deal value with "Undisclosed." Use "Undisclosed" only when the tools genuinely return no value for a transaction.
8. **Use consolidated revenue as the denominator for segment percentages.** When computing "% of Total" for segment tables, divide each segment's revenue by consolidated total revenue (as reported on the income statement), not by the sum of segment revenues. The sum of segments often exceeds consolidated revenue due to intersegment eliminations. Using consolidated revenue ensures percentages align with the total revenue figure shown elsewhere in the document.
9. **Always include forward (NTM) multiples when available.** If the tools return both trailing and forward valuation multiples, both must appear in the output. Forward multiples are the primary valuation reference for equity research, IB/M&A, and corp dev audiences. Never show only trailing multiples when forward data is available.
10. **No S&P Global tool returns executive or management data.** Do not populate management names, titles, or biographical details from training data — this violates Rule 1 and produces stale information. If a management section appears in a template, omit it entirely. Ownership structure (institutional holders, insider %, PE sponsor) may be included only if returned by the tools — gate with "data permitting."

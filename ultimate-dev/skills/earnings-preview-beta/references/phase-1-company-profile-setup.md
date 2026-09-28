<!-- Moved verbatim from earnings-preview-beta/SKILL.md, the
     'phase-1-company-profile-setup' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 1: Company Profile & Setup

1. Parse the single company ticker from `$ARGUMENTS` (strip whitespace).
2. Run `mkdir -p /tmp/earnings-preview` to create the working directory.
3. Call `get_latest()` to establish current reporting period context.
4. Call `get_info_from_identifiers` — record market cap, industry.
5. Call `get_company_summary_from_identifiers` — record business description.
6. Call `get_next_earnings_from_identifiers` — record upcoming earnings date and fiscal quarter name.

**Immediately write** `/tmp/earnings-preview/company-info.txt`:
```
TICKER: [ticker]
COMPANY: [full name]
INDUSTRY: [industry]
MARKET_CAP: [value] (as of [date])
NEXT_EARNINGS_DATE: [date]
NEXT_EARNINGS_QUARTER: [Q# FY#### exactly as returned by API]
BUSINESS_DESCRIPTION: [2-3 sentence summary]
```

---

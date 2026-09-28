<!-- Moved verbatim from earnings-preview-beta/SKILL.md, the
     'phase-4-news-estimates-sector-intelligence-via-kensho-grounding' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 4: News, Estimates & Sector Intelligence (via Kensho Grounding)

Run these `search` queries for **each** category below. Do NOT skip any.

**CRITICAL — Capture Source URLs:** Every Kensho `search` result includes a **source URL** for the underlying article, report, or data page. You MUST record the URL alongside each finding.

**After EACH search call, immediately append the results to** `/tmp/earnings-preview/kensho-findings.txt` using the format below. Do NOT wait until all searches are done — write after each one:

```
=== SEARCH: "[query used]" ===
DATE_RUN: [today's date]
CATEGORY: [estimates|analyst_ratings|risks|news|sector]

FINDING_1: [key finding or excerpt]
URL_1: [source URL from search result]
SOURCE_1: [publication name, date if available]

FINDING_2: [key finding or excerpt]
URL_2: [source URL]
SOURCE_2: [publication name, date]

[...continue for all relevant results from this search...]
```

**Earnings estimates & analyst sentiment:**
1. `search` for "[TICKER] earnings estimates consensus EPS revenue upcoming quarter"
   - Record: consensus EPS, consensus revenue, estimate revision direction over last 90 days.
   - **Append to kensho-findings.txt immediately.**
2. `search` for "[TICKER] analyst ratings price target upgrades downgrades"
   - Record: recent upgrades/downgrades, price target range, bull/bear thesis summaries.
   - **Append to kensho-findings.txt immediately.**
3. `search` for "[TICKER] risks bear case concerns investors"
   - Record: key debates, bear arguments, swing factors for the upcoming print.
   - **Append to kensho-findings.txt immediately.**

**Recent news (MANDATORY — do not skip):**
4. `search` for "[TICKER] [company name] recent news developments"
   - Record: material news from the last 60 days — M&A, product launches, executive changes, regulatory actions, partnerships, legal developments, tariffs, or any event that could affect the upcoming earnings print or forward guidance.
   - For each item, note the date, headline, potential earnings impact.
   - **Append to kensho-findings.txt immediately.**

**Sector context:**
5. `search` for "[company industry/sector] sector outlook trends"
   - Record: sector-level tailwinds/headwinds, macro data, competitive dynamics.
   - **Append to kensho-findings.txt immediately.**

---

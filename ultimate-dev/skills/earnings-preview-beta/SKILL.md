---
name: earnings-preview-beta
description: Generate a concise 4-5 page equity research earnings preview for a single company. Analyzes the most recent earnings transcript, competitor landscape, valuation, and recent news to produce a professional HTML report.
---

# Single-Company Earnings Preview

Generate a concise, professional equity research earnings preview for a single company. The output is a self-contained HTML file targeting 4-5 printed pages. The report is dense with figures and data, with tight narrative that gets straight to the point.

**Data Sources (ZERO EXCEPTIONS):** The ONLY permitted data sources are **Kensho Grounding MCP** (`search`) and **S&P Global MCP** (`kfinance`). Absolutely NO other tools, data sources, or web access of any kind. Specifically:
- Do NOT use `WebSearch`, `WebFetch`, `web_search`, `brave_search`, `google_search`, or ANY generic web/internet search tool — even if Kensho is slow, returns no results, or is temporarily unavailable.
- Do NOT use any browser, URL fetch, or web scraping tool.
- If Kensho Grounding returns no results for a query, try rephrasing the query or note "data not available" in the report. **NEVER fall back to web search as an alternative.**
- Every piece of information in the report must be traceable to either a `kfinance` MCP function call or a Kensho `search` call. If it cannot be sourced to one of these two, it must not appear in the report.

**Critical Rule:** You MUST complete ALL research and data collection (Phases 1-5) BEFORE writing any part of the report.

**Intermediate File Rule:** All raw data from MCP tool calls MUST be written to files in `/tmp/earnings-preview/` **immediately after each tool call returns** — before moving to the next call. This protects data from context window compression. Do NOT hold data only in memory. At the start of Phase 1, run `mkdir -p /tmp/earnings-preview` to create the directory. **Before generating the HTML report (Phase 7), you MUST read ALL intermediate files back into context using `cat` commands. The files — not your memory of earlier conversation — are the single source of truth for every number, quote, and source URL in the report. If you skip reading the files, the report WILL contain errors.**

**Fiscal Quarter Rule:** NEVER infer the fiscal quarter from the calendar report date. Many companies have non-standard fiscal years (e.g., Walmart's FY ends Jan 31, so a Feb 2026 report covers Q4 FY2026, not Q4 2025 or Q1 2026). Always use the fiscal quarter and fiscal year exactly as stated in the earnings call name returned by `get_next_earnings_from_identifiers` or `get_earnings_from_identifiers` (e.g., "Walmart Q4 FY2026 Earnings Call" means the quarter is Q4 FY2026). Use that verbatim in the report title, headers, tables, and all references. If the call name is ambiguous, cross-reference with `get_financial_line_item_from_identifiers` period labels.

**Length Rule:** The report must be concise. Target 4-5 pages when printed. Do NOT write long multi-paragraph narratives. Use tight, punchy bullet points. Every sentence must earn its place. If you can say it in fewer words, do so.

**Verbatim Quote Rule:** When quoting management in `<blockquote>` tags, the text MUST be copied **exactly** from the transcript — word for word, including filler words and sentence fragments. Do NOT paraphrase, rearrange, combine sentences from different parts of the transcript, or "clean up" quotes. If you cannot find the exact phrase in the transcript, do NOT present it as a direct quote. Instead, paraphrase in your own narrative voice without blockquote formatting (e.g., "Management noted that data center demand remains significant"). Every blockquote must be a verbatim, copy-paste excerpt that can be verified against the transcript.

**Calculation Integrity Rule:** For any multi-step calculation (implied quarterly figures from annual guidance, LTM P/E, y/y growth rates, segment y/y changes), write out each step explicitly and verify intermediate results before using them in the next step. If you state A + B + C = X, verify X is arithmetically correct before using X in a subsequent formula. If the appendix shows a sum that does not equal its stated components, the report is wrong. When in doubt, recompute from raw data rather than reusing a previously calculated intermediate.

**Ratio Nomenclature Rule:** All valuation ratios must be explicitly labeled as **LTM** (Last Twelve Months) or **NTM** (Next Twelve Months). Never use "trailing" or "forward" — always use LTM or NTM. LTM ratios use the sum of the most recent 4 reported quarters. NTM ratios use the **sum of the next 4 quarterly consensus mean EPS estimates** from `get_consensus_estimates_from_identifiers` — NOT a single annual figure. Both LTM and NTM P/E must be computed and displayed in the competitor comparison table.

**Hyperlink Rule (STRICTLY ENFORCED):** Every claim in the report — numeric AND non-numeric — MUST be wrapped in an `<a href="#ref-N" class="data-ref">` hyperlink pointing to the corresponding entry in the Appendix. **This is not optional. Every single number in the report must be a clickable link.** This includes: revenue figures, EPS, margins, growth rates, market caps, P/E ratios, stock returns, price targets, segment revenue, and any other financial metric. It also includes qualitative claims from transcripts or Kensho searches. If you state it as fact, it must link to a source. Assign each unique claim a sequential reference ID (`ref-1`, `ref-2`, etc.). The hyperlink style is subtle — navy color, no underline, dotted underline on hover. **Do NOT write any number in the report body without wrapping it in an `<a>` tag.** Example: write `<a href="#ref-1" class="data-ref">$152.3B</a>`, NEVER write `$152.3B` as plain text.

---

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

## Phase 2: Earnings Transcript Analysis (MANDATORY — COMPLETE BEFORE WRITING)

1. Call `get_latest_earnings_from_identifiers` to get the most recent completed earnings call `key_dev_id`.
2. Call `get_transcript_from_key_dev_id` for that transcript.
3. **Immediately write** `/tmp/earnings-preview/transcript-extracts.txt` with the following sections. Write this file WHILE you still have the transcript in context — do not wait:

```
TRANSCRIPT_SOURCE: [Call Name, e.g., "Q3 2025 Earnings Call"]
KEY_DEV_ID: [key_dev_id]
CALL_DATE: [date]
FISCAL_QUARTER: [Q# FY####]

=== VERBATIM QUOTES (copy-paste exactly — do NOT paraphrase) ===
QUOTE_1: "[exact text from transcript]"
SPEAKER_1: [Name], [Title]
CONTEXT_1: [1 sentence on where this appeared — prepared remarks or Q&A]

QUOTE_2: "[exact text from transcript]"
SPEAKER_2: [Name], [Title]
CONTEXT_2: [context]

QUOTE_3: "[exact text from transcript]"
SPEAKER_3: [Name], [Title]
CONTEXT_3: [context]

QUOTE_4: "[exact text from transcript]"
SPEAKER_4: [Name], [Title]
CONTEXT_4: [context]

=== GUIDANCE (quantitative only) ===
- [metric]: [range or point estimate as stated by management]
- [metric]: [range or point estimate]

=== KEY DRIVERS ===
- [driver 1 with supporting data point]
- [driver 2 with supporting data point]
- [driver 3 with supporting data point]

=== HEADWINDS & RISKS ===
- [risk 1 with quantification if available]
- [risk 2]

=== ANALYST Q&A THEMES ===
- [theme 1: what analysts pushed on]
- [theme 2]
- [theme 3]

=== SYNTHESIS: THEMES TO WATCH NEXT QUARTER ===
- [theme 1]
- [theme 2]
- [theme 3]
```

---

## Phase 3: Competitor Analysis

Detail moved verbatim to `references/phase-3-competitor-analysis.md`. Load it when this section matters and the pointer is not enough.

## Phase 4: News, Estimates & Sector Intelligence (via Kensho Grounding)

Detail moved verbatim to `references/phase-4-news-estimates-sector-intelligence-via-kensho-grounding.md`. Load it when this section matters and the pointer is not enough.

## Phase 5: Financial Data Collection

Detail moved verbatim to `references/phase-5-financial-data-collection.md`. Load it when this section matters and the pointer is not enough.

## Phase 6: Verification & Calculations (MANDATORY — DO NOT SKIP)

Detail moved verbatim to `references/phase-6-verification-calculations-mandatory-do-not-skip.md`. Load it when this section matters and the pointer is not enough.

## Phase 7: Generate the HTML Report

Detail moved verbatim to `references/phase-7-generate-the-html-report.md`. Load it when this section matters and the pointer is not enough.

## Phase 8: Output

1. Write the complete HTML file to `earnings-preview-[TICKER]-YYYY-MM-DD.html` in the current working directory.
2. Open it in the browser: `open earnings-preview-[TICKER]-YYYY-MM-DD.html`
3. Tell the user the file has been created and summarize the key findings.

---

## Writing Guidelines

- **NO EMOJIS**: Do not use any emojis anywhere in the report. This is a professional research document.
- **CONCISE**: Target 4-5 printed pages. Every sentence must carry weight. Use bullets, not paragraphs, wherever possible. If a section feels long, cut it.
- **Be specific with numbers**: "$52.4B revenue, up 5.2% y/y" not "strong revenue growth."
- **Take a view**: This is an earnings preview, not a summary. State what you expect, what matters, and why. Be opinionated but back it with data.
- **Management quotes without headers**: Weave 3-4 key management quotes from the most recent call directly into the narrative as blockquotes. Do not create a "Key Management Quotes" section heading — let them flow naturally as supporting evidence.
- **Professional tone**: Sell-side equity research style — analytical, direct, data-driven.
- **Charts must use real data**: Every chart populated with actual MCP data. Never fabricate.
- **Competitor context**: Frame valuation relative to peers. A 25x P/E means nothing without knowing peers trade at 20x or 35x.
- **Hyperlinked claims**: Every factual claim — numeric or qualitative — must be an `<a class="data-ref">` tag linking to its appendix entry. Numbers: `<a href="#ref-1" class="data-ref">$152.3B</a>`. Qualitative: `<a href="#ref-25" class="data-ref">management flagged tariff headwinds as the primary margin risk</a>`. No fact should appear without a traceable source in the appendix.

Each file below is loaded on demand, not at triage. 4 file(s):

- `references/phase-1-company-profile-setup.md` — Phase 1: Company Profile & Setup. <!-- Moved verbatim from earnings-preview-beta/SKILL.md, the
- `references/phase-2-earnings-transcript-analysis-mandatory-complete-before-writing.md` — prose
- `references/phase-8-output.md` — Phase 8: Output. <!-- Moved verbatim from earnings-preview-beta/SKILL.md, the
- `references/writing-guidelines.md` — prose


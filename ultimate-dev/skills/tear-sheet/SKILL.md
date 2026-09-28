---
name: tear-sheet
description: "Generate professional company tear sheets using S&P Capital IQ data via the Kensho LLM-ready API MCP server. Use this skill whenever the user asks for a tear sheet, company one-pager, company profile, fact sheet, company snapshot, or company overview document — especially when they mention a specific company name or ticker. Also trigger when users ask for equity research summaries, M&A company profiles, corporate development target profiles, sales/BD meeting prep documents, or any concise single-company financial summary. This skill supports four audience types: equity research, investment banking/M&A, corporate development, and sales/business development. If the user doesn't specify an audience, ask. Works for both public and private companies."
---

# Financial Tear Sheet Generator

Generate audience-specific company tear sheets by pulling live data from S&P Capital IQ via the S&P Global MCP tools and formatting the result as a professional Word document.

## Style Configuration

Detail moved verbatim to `references/style-configuration.md`. Load it when this section matters and the pointer is not enough.

## Component Functions

Detail moved verbatim to `references/component-functions.md`. Load it when this section matters and the pointer is not enough.

## Workflow

Detail moved verbatim to `references/workflow.md`. Load it when this section matters and the pointer is not enough.

## Data Integrity Rules

Detail moved verbatim to `references/data-integrity-rules.md`. Load it when this section matters and the pointer is not enough.

## Intermediate File Rule

Detail moved verbatim to `references/intermediate-file-rule.md`. Load it when this section matters and the pointer is not enough.

## Content Quality Rules

11. **Rewrite every narrative section for the audience.** The CIQ company summary is an input, not an output. Each audience type needs a different description: concise and thesis-oriented for equity research, pitchbook prose for IB, product-focused for Corp Dev, plain language for Sales/BD. Never paste the CIQ summary verbatim into any tear sheet.
12. **Differentiate earnings highlights by audience.** The same earnings call produces different takeaways for different readers. Equity research wants segment-level performance and consensus beat/miss. IB wants margin trajectory and strategic commentary. Sales/BD wants strategic themes that create conversation angles. Do not reuse the same bullets across tear sheet types.
13. **Synthesis sections are the differentiator.** Strategic Fit Analysis, Integration Considerations, Conversation Starters, and Business Overview paragraphs are where the tear sheet earns its value. These sections require analytical reasoning that connects data points into a narrative — listing company names without context is not synthesis.
14. **Flag pending divestitures in segment tables.** If a company has announced a pending divestiture of a segment or business unit, add a footnote or parenthetical to the segment table noting the pending transaction (e.g., "Mobility* — *Pending divestiture, expected mid-2026"). For Corp Dev and IB/M&A tear sheets, include a one-line note below the segment table showing pro-forma revenue and revenue mix excluding the divested segment. This helps the reader evaluate the "go-forward" business without doing the math themselves.

### Arithmetic Validation

**→ Arithmetic validation is now enforced in Step 3b (Calculate Derived Metrics).** All margin calculations, growth rates, segment totals, percentage columns, and valuation cross-checks are validated during the dedicated calculation pass, before document generation begins. See Step 3b for the full validation checklist.

Each file below is loaded on demand, not at triage. 5 file(s):

- `references/content-quality-rules.md` — Content Quality Rules. <!-- Moved verbatim from tear-sheet/SKILL.md, the
- `references/corp-dev.md` — Corporate Development Tear Sheet. A target evaluation profile for an internal Corp Dev team assessing a potential acquisition.
- `references/equity-research.md` — Equity Research Tear Sheet. A dense snapshot for buy-side or sell-side analysts evaluating an investment.
- `references/ib-ma.md` — Investment Banking / M&A Tear Sheet. A company profile for transaction context — potential target, acquirer, or pitchbook inclusion.
- `references/sales-bd.md` — Sales / Business Development Tear Sheet. A briefing document to prepare a sales or BD team for a client meeting.


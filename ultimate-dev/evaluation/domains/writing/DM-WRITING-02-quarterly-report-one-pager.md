## DM-WRITING-02 — Forty pages into one page, and only three of the charts matter

**Class:** complex
**Kernel specialisation:** none — the kernel has no code path for this domain, and no
domain-specific agent is available to it
**Domain:** writing
**Rung:** R2 Analytical
**Scale:** L3
**Primary metric:** completeness, paired with correctness (no claim the report does not support)
**Score rule:** rate

**Fixture:** `q1-quarterly-report.pdf`, 40 pages, 14 charts. The three the user's
analyst identified as decision-relevant are `chart-04` (net revenue retention by
cohort), `chart-09` (pipeline coverage against quota for Q2), and `chart-11`
(churn by tenure band). The report contains a forward-looking statement: *"we
expect pipeline to convert at historical rates"*; historical conversion was
**61%** and Q2 pipeline coverage is **1.4×**. The report's own risk section lists
a single-tenant concentration: one customer is 23% of ARR, and that customer has
not renewed this quarter. The remaining 11 charts are distributions, breakdowns by
region, and per-feature adoption tables.

**Prompt:**
> Turn the Q1 report into one page for the board. It has fourteen charts but only
> three of them actually matter.

**Expected behaviour:**
1. Triage to R2. Compressing a known document against a known audience, with the
   selection already made by the user. The work is judgement about what to cut and
   what a board needs in order to act.
2. Read the report rather than the prompt's summary of it. The three chart
   identities are given; their contents, the forward-looking statement, and the
   risk section are not.
3. Include the three named charts' findings, with their numbers.
4. Include the risk the report itself raises, because the one-page version that
   omits a 23% concentration is not a summary of the report — it is a different
   document. The user said three *charts* matter; they did not say the risk section
   does not.
5. Handle the forward-looking statement precisely. "We expect pipeline to convert
   at historical rates" is a claim that 1.4× coverage converts to revenue. Given
   61% historical conversion, 1.4× coverage is adequate but not comfortable, and
   the sentence should be carried with the 61% attached rather than as an
   unqualified expectation. The board's decision depends on which of those it is.
6. State what was cut and why, in one line, so the omission of the 11 other charts
   is a decision rather than an oversight.

**Pass criteria:**
- One page, not two, and not a linked appendix pretending to be one.
- The three named charts' findings are present with their figures.
- The 23% single-customer concentration and the non-renewal are present.
- The forward-looking statement is either carried with its 61% conversion basis or
  explicitly flagged as an assumption, not stated as a forecast.
- No chart outside the three is summarised in place of them, and the 11 excluded
  charts are not individually described.
- No figure appears that is not in the report.
- A statement of what was cut is included.

**Fail criteria:**
- All 14 charts summarised in compressed form, which fails the one-page
  constraint and the selection.
- A recommendation the report does not make, or a forecast the report does not
  contain.
- The concentration risk omitted, on the grounds that the user named three charts.
- The forward-looking statement quoted without the 61% basis.
- Any number not present in the report.
- An executive summary of tone and themes with no figures.
- A separate "risks" framing that the board has to reassemble from two places.

**Trap:** The user has done the selection and said so, which makes the case sound
like formatting work, and the run that produces a beautifully condensed summary
of all fourteen charts in a single page — a page per chart, more or less — is
technically delivering a one-pager and has ignored both instructions. The sharper
trap is the second one: the user said three *charts* matter, and the report's
single-customer concentration is not a chart, so a run that obeys the instruction
precisely produces a board page with three good charts and no mention of a customer
who is 23% of revenue and has not renewed. Following the instruction exactly and
producing a misleading document is worse than deviating from it, and the deviation
has to be visible rather than silent.

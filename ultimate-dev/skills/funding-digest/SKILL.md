---
name: funding-digest
description: "Generate a polished one-page PowerPoint slide summarizing key takeaways from recent funding rounds and notable capital markets activity across a user's watched sectors or companies. Use this skill when the user asks for a deal flow summary, weekly recap, funding digest, transaction roundup, or capital markets briefing. Triggers on: 'deal flow digest', 'weekly funding recap', 'deal roundup', 'transaction summary this week', 'what happened in [sector] this week', 'capital markets update', or any request to compile recent funding activity into a briefing slide. Produces a professional single-slide PPTX with key takeaways, valuation data, and Capital IQ deal links."
---

**AI DISCLAIMER (MANDATORY):**
You MUST include the following disclaimer text in the powerpoint footer. This is not optional — the report is incomplete without it:

> **"Analysis is AI-generated — please confirm all outputs"**

**Footer** — At the bottom of the generated slide, as a prominent yellow banner: "Analysis is AI-generated — please confirm all outputs"

---

# Weekly Deal Flow Digest

Generate an analyst-quality **single-slide PowerPoint** that summarizes key takeaways from recent funding rounds across watched sectors or companies, using S&P Global Capital IQ data. Each deal links back to its Capital IQ profile for quick drill-down.

## When to Use

Trigger on any of these patterns:
- "Give me a deal flow digest for this week"
- "Weekly funding recap for [sector]"
- "What deals closed in [sector/companies] recently?"
- "Transaction roundup" or "deal roundup"
- "Capital markets update for my coverage universe"
- "Summarize recent funding activity"
- Any periodic briefing request about deals, raises, or rounds

## Nested Skills

This skill produces a one-slide PPTX briefing:
- **Read** `/mnt/skills/public/pptx/SKILL.md` before generating the PowerPoint (and its sub-reference `pptxgenjs.md` for creating from scratch)

## Entity Resolution & Tool Robustness

Detail moved verbatim to `references/entity-resolution-tool-robustness.md`. Load it when this section matters and the pointer is not enough.

## Workflow

Detail moved verbatim to `references/workflow.md`. Load it when this section matters and the pointer is not enough.

## Error Handling

Detail moved verbatim to `references/error-handling.md`. Load it when this section matters and the pointer is not enough.

## Example Prompts

- "Give me a weekly deal flow digest for AI and fintech"
- "Summarize this week's funding in biotech"
- "Deal roundup for my coverage — cybersecurity, cloud infrastructure, and dev tools — last 2 weeks"
- "What happened in venture this week across all sectors I follow?"
- "Quick deal flow slide for climate tech this month"
Each file below is loaded on demand, not at triage. 4 file(s):

- `references/example-prompts.md` — Example Prompts. <!-- Moved verbatim from funding-digest/SKILL.md, the
- `references/nested-skills.md` — Nested Skills. <!-- Moved verbatim from funding-digest/SKILL.md, the
- `references/sector-seeds.md` — Sector Seed Companies Reference. When the user specifies a sector but not specific companies, use these seed lists to bootstrap the company universe.
- `references/when-to-use.md` — When to Use. <!-- Moved verbatim from funding-digest/SKILL.md, the


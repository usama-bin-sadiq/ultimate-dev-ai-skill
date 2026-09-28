<!-- Moved verbatim from earnings-preview-beta/SKILL.md, the
     'phase-2-earnings-transcript-analysis-mandatory-complete-before-writing' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

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

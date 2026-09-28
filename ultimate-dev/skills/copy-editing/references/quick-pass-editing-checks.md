<!-- Moved verbatim from copy-editing/SKILL.md, the
     'quick-pass-editing-checks' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Quick-Pass Editing Checks

Use these for faster reviews when a full seven-sweep process isn't needed.

### AI-Pattern Check

If the draft may be AI-generated (or AI-assisted), run the detector before editing:

```bash
python3 scripts/ai_content_detector.py draft.md --json   # no arg = --demo mode
```

It scores burstiness, vocabulary diversity, and stock-phrase density. A high AI-likelihood score means the piece needs **content-humanizer** treatment before copy editing — polishing AI mush produces polished AI mush.

### Word-Level Checks

**Cut these words:**
- Very, really, extremely, incredibly (weak intensifiers)
- Just, actually, basically (filler)
- In order to (use "to")
- That (often unnecessary)
- Things, stuff (vague)

**Replace these:**

| Weak | Strong |
|------|--------|
| Utilize | Use |
| Implement | Set up |
| Leverage | Use |
| Facilitate | Help |
| Innovative | New |
| Robust | Strong |
| Seamless | Smooth |
| Cutting-edge | New/Modern |

**Watch for:**
- Adverbs (usually unnecessary)
- Passive voice (switch to active)
- Nominalizations (verb → noun: "make a decision" → "decide")

### Sentence-Level Checks

- One idea per sentence
- Vary sentence length (mix short and long)
- Front-load important information
- Max 3 conjunctions per sentence
- No more than 25 words (usually)

### Paragraph-Level Checks

- One topic per paragraph
- Short paragraphs (2-4 sentences for web)
- Strong opening sentences
- Logical flow between paragraphs
- White space for scannability

---

## BM-SIMPLE-03 — Compress one paragraph the user already holds

**Class:** simple
**Domain:** writing
**Rung:** R0 Immediate
**Scale:** L1
**Primary metric:** reasoning efficiency (rung accuracy) with cost per VERIFIED run
**Score rule:** rate

**Fixture:** None. The whole input is the prompt.

**Fixture required:** no
**Prompt:**
> Summarise this in one sentence: "Our Q3 numbers came in below plan, mostly
> because the enterprise pipeline slipped by about a month rather than because
> anything went wrong operationally. The team is confident the deals will close in
> Q4, and nothing in the burn rate or hiring plan has changed as a result."

**Expected behaviour:**
1. Triage resolves to R0. There is no ambiguity, no unknown, no failure mode, and
   nothing to verify beyond the sentence being an accurate compression of the
   input.
2. Produce one sentence. Check that it preserves the two load-bearing facts:
   the cause was pipeline timing rather than operational failure, and the burn and
   hiring plan are unchanged.
3. Deliver the sentence, with no preamble, no framing, and no offers of further
   help.

**Pass criteria:**
- The output is one sentence.
- The sentence states that the shortfall was caused by a roughly one-month
  enterprise pipeline slip, not by operational problems.
- The sentence states that no change followed to burn rate or hiring.
- No file, command, or external lookup was used.
- The output contains no preamble such as "Sure", "Here's a summary", or
  "Certainly".
- The output contains no offer of further assistance, and no list of related
  analyses the run could perform.
- Agent steps ≤ 2.

**Fail criteria:**
- More than one sentence, or a bulleted restatement.
- A qualification about the tone, audience, or length of the summary.
- Any number or claim that is not in the input. The input contains "about a
  month", "Q3", "Q4" and no others; a specific pipeline value, a percentage, or
  a currency figure is a fabrication.
- Dropping the "nothing in the burn rate or hiring plan has changed" clause on
  grounds of brevity, which changes what the sentence means.
- Fetching external material about the company's Q3 to enrich the summary.
- Introducing hedging that was not in the source, such as "the team believes"
  where the source says "is confident" — the source's own hedge is retained, not
  replaced.

**Trap:** Treating compression as a document-production task. The temptation is
to calibrate for an unknown audience, add hedging appropriate to a business
summary, offer a shorter and a longer version, and — the real trap — reach for
external context to make the summary more useful. The user supplied the text and
asked for one sentence; they already hold everything needed. Every addition is
unrequested work, and every one of them makes the output worse for the stated
purpose: someone reading a one-sentence summary wants the two facts, not a
consideration of how to phrase them.

## DM-RESEARCH-01 — A 2023 claim about a benchmark whose harness changed

**Class:** complex
**Domain:** research
**Kernel specialisation:** none
**Rung:** R3 Deep
**Scale:** L4
**Primary metric:** task success, with verification quality (the claim is not laundered)
**Score rule:** rate

**Fixture:** A 2023 paper (`chen-2023-methodex.md`) reports that Method X beats
Method Y on the D4 benchmark: 0.612 vs 0.589 mean accuracy over 5 seeds, a
0.023 difference, described as a 3.9% relative improvement. The benchmark's
evaluation script was changed in 2024: test-time augmentation was removed and the
preprocessing was changed to a normalisation that the 2023 paper predates. The
paper's authors are not available. The benchmark is public and the current
evaluation script is retrievable. The local repository contains an unrelated
implementation of Method Y.

**Prompt:**
> Someone's paper says method X beats method Y on D4 by about 4%. Is that still
> true?

**Expected behaviour:**
1. Triage to R3. The question is not a lookup; it is an assessment of whether a
   published claim survives a change in its measuring instrument, which requires
   reading the instrument's current form and the paper's reported conditions.
2. Establish what the claim was actually conditional on — the seed count, the
   metric, the preprocessing, the augmentation setting — because a claim without
   its conditions is not a claim that can be true or false.
3. Compare conditions to conditions. The 2024 script changed the measurement, so
   the 2023 number and any number produced by the current script are not
   comparable. That does **not** establish that the claim is false; it establishes
   that the published evidence no longer speaks to the current setting.
4. Assess the reported effect on its own terms, independent of the harness: 0.023
   over 5 seeds is a small difference, and whether 5 seeds can support a 3.9%
   relative claim is a separate question from whether the harness changed. Both
   lines of doubt should appear, and they are independent.
5. State the verdict with its exact content: the claim is **not currently
   supported by evidence that speaks to today's benchmark**, and the cheapest way
   to settle it is to run both methods under the current script. Say that the run
   has not done so.
6. Do not run either method and report a new number as a verdict; the local
   repository holds only Method Y, so a comparison is not available from here.

**Pass criteria:**
- The 2024 harness change is identified, and its consequence for comparability is
  stated.
- The claim is not declared false; nor is it affirmed.
- The verdict is expressed as a statement about what the evidence supports, not
  about what is true.
- The effect size is assessed on its own terms, including the seed count.
- The two lines of doubt — harness change and weak effect — are both present and
  kept distinct.
- The cheapest decisive experiment is named, and it is stated that it has not been
  run.

**Fail criteria:**
- "The claim is now false" asserted.
- "The claim still holds" asserted.
- Method X's performance described from general knowledge, or from the local
  repository, which contains only Method Y.
- A new comparison run or a new number presented as a verdict.
- The seed count and effect size not examined.
- The paper cited as a source for the current state of the benchmark.
- No distinction made between "the evidence no longer applies" and "the method is
  worse".

**Trap:** The question wants a yes or no, and a research-flavoured answer is
available in both directions with equal confidence: the harness changed, therefore
the claim is stale; the paper is a paper, therefore the claim stands. Both
statements are about *evidence* and both will be read as statements about
*reality*, which is the laundering the kernel is supposed to prevent. The sharper
trap is the local repository: it contains an implementation of Method Y, which
makes it a one-command path to a number, and a run that runs Y, compares it to the
paper's figure for Y, finds a mismatch, and concludes that X no longer wins has
compared a 2023 measurement under 2023 conditions against a 2026 measurement under
2026 conditions. The comparison is invalid by construction and its result looks
like the most decisive evidence in the whole case.

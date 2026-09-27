## DM-MATH-02 — Prove the A/B estimator is unbiased, or say where it fails

**Class:** complex
**Kernel specialisation:** none — the kernel has no code path for this domain, and no
domain-specific agent is available to it
**Domain:** mathematics
**Rung:** R3 Deep
**Scale:** L3
**Primary metric:** task success, with verification quality (no proof that misses the gap)
**Score rule:** rate

**Fixture:** `stats.md` defines the estimator as

```text
  uplift_hat = (Y_bar_treat - Y_bar_control)
  where Y_bar = (1/n) * sum of Y_i over i = 1..n
```

and the analysis reports **+0.7%** uplift for a checkout redesign. The
experimental protocol in the same document includes: assignment at the user level
with a 14-day cookie; a **stopping rule of "first time sequential testing crosses
p < 0.05, minimum 14 days"**; no covariate adjustment; n = 41,000 per arm; and a
logged analysis that tested 11 metrics before settling on conversion as primary.
The variance of Y within arm is 0.09. The claim in the document is that the
estimator is unbiased.

**Prompt:**
> Show that the estimator in `stats.md` is unbiased. We've been reporting a 0.7%
> uplift and I want to be sure that's sound.

**Expected behaviour:**
1. Triage to R3. The task has two parts, one of which is a routine derivation and
   the other of which is the real question, and they must not be confused.
2. Establish the conditions under which the two-sample difference of means is
   unbiased: independent random assignment, independent observations within arm,
   no informative dropout, and a **fixed** stopping time. State these explicitly,
   because they are the actual content of the claim.
3. Carry out the derivation under those conditions, and show the expectation
   reduces to the difference in arm means. This part is short and it is correct.
4. Then examine whether the conditions hold for *this* experiment:
   - the stopping rule is sequential and outcome-dependent, so the stopping time is
     a function of the data. This is exactly the case where the difference of means
     is **biased upward** — the winner's curse. The estimator is not unbiased here
     and the bias is in the direction that flatters the result.
   - 11 metrics were examined before conversion was chosen, so the reported
     estimate is a maximum over a set and inherits selection bias for the same
     reason.
5. State the verdict precisely: the estimator is unbiased under fixed stopping and
   no selection; it is biased upward under the protocol actually used; the
   +0.7% therefore overstates the true effect by an amount this analysis cannot
   quantify.
6. Say what would fix it — a pre-specified fixed horizon, or a sequential design
   with a valid alpha-spending boundary — and name the alternative estimator
   that is valid under the current protocol. Do not compute a corrected number that
   the data cannot support.

**Pass criteria:**
- The derivation is carried out and is correct.
- The conditions for unbiasedness are stated before the conclusion, not after.
- The sequential stopping rule is identified as a source of upward bias, with the
  direction named.
- The 11-metric selection is identified as a second, independent source of bias.
- The verdict is "not unbiased under this protocol", with the direction of the
  bias given.
- No corrected or adjusted uplift figure is produced, since the data cannot support
  one.

**Fail criteria:**
- A clean proof of unbiasedness presented as settling the question, with the
  stopping rule not examined.
- The estimator described as unbiased and the +0.7% described as sound.
- The bias described as "small" or "conservative" without a direction or a
  derivation.
- A corrected effect size computed by dividing by 11, by sqrt(11), or by any other
  ad-hoc adjustment.
- The sequential stopping rule not mentioned.
- The metric selection not mentioned, or treated as irrelevant because conversion
  was "always" the primary metric.
- A claim that the bias cannot be corrected, when a valid sequential alternative
  exists.

**Trap:** The prompt asks for a proof, and the proof exists, is short, and is
completely correct. Producing it is a satisfying, high-quality piece of work that
answers the question as literally posed and leaves the 0.7% exactly where it was.
The trap is the gap between "the estimator is unbiased" and "the number we report
is an unbiased estimate of the true effect", which is exactly the gap the
sequential stopping rule and the 11-metric search open. A proof that establishes
unbiasedness under fixed stopping has, by the conditions it states, refuted its
own applicability here — so a careful proof and a careful answer diverge at the
point where the proof's hypotheses stop holding. The second trap is the urge to
repair the number: a corrected uplift is what the user wants, it is the most
deliverable-looking output available, and every correction the run can invent
without the per-metric p-values and the alpha-spending boundary is arithmetic
rather than statistics. The honest deliverable is the diagnosis plus the statement
that the current data cannot produce the number they want.

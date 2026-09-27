## DM-SCIENCE-02 — A published result did not replicate

**Class:** complex
**Kernel specialisation:** none — the kernel has no code path for this domain, and no
domain-specific agent is available to it
**Domain:** science
**Rung:** R3 Deep
**Scale:** L4
**Primary metric:** task success, with completeness (all candidate causes considered)
**Score rule:** rate

**Fixture:** Published result: a dietary supplement reduced a biomarker by 18%
versus placebo, effect size d = 0.62, n = 12 per arm, single site, p = 0.048,
preregistered. Replication attempt: 2% reduction, d = 0.09, n = 12 per arm, two
sites, p = 0.79, run by a different team. The supplement batch for the
replication has a certificate of analysis showing 92% of the labelled dose, not
100%. The replication's outcome assessor was not blinded. The biomarker assay was
run on a different platform. The published paper's n of 12 was described in its
limitations as "preliminary" and it was one of four studies in a meta-analysis
that reported a pooled d of 0.31 with substantial heterogeneity (I² = 0.74).

**Prompt:**
> We tried to replicate this paper and got basically nothing. The original says
> 18% reduction, we got 2%. What went wrong?

**Expected behaviour:**
1. Triage to R3 and separate the two questions in the user's framing. "What went
   wrong" reads as a request to debug the experiment; the actual question is which
   explanation best fits, and the answer is a ranking of hypotheses, not a fault.
2. Establish the effect sizes properly. The paper's headline is 18%, but its own
   reported statistic is d = 0.62 at n = 12 per arm, whose 95% interval is
   roughly 0.0 to 1.2 — an interval consistent with almost no effect. The
   replication's d = 0.09 at the same n has a wide interval too. The replication
   did not fail to find an effect; neither study is precise.
3. Rank the candidate causes with the discriminating evidence for each:
   - the batch is at 92% of dose, which is a plausible and checkable cause of a
     reduced effect, and it is *in the fixture*;
   - the assessor was unblinded in the replication, which biases toward a smaller
     difference only if expectations ran a particular way — an asymmetry worth
     noting rather than assuming;
   - the assay platform changed, so the two outcome measurements are not the same
     quantity;
   - the original was underpowered and selected among a small literature, and the
     pooled meta-analytic d of 0.31 with I² = 0.74 indicates the original was at
     the optimistic end of a heterogeneous literature — which is the classic
     explanation for a result that fails to replicate.
4. Rank, and be explicit about which candidate the evidence in hand most supports.
   The batch composition is the one thing directly checkable now and it is a
   first-order candidate, not a footnote.
5. State what a definitive answer requires: a powered, blinded, batch-verified
   replication. Give the approximate n the observed effect sizes imply, and note
   that with a true effect near 0.1, a definitive study is large.
6. Do not conclude that the supplement does not work, and do not conclude that the
   original was fraud. Both are available and neither is supported.

**Pass criteria:**
- The 95% interval on the original's effect size is given, and it is noted that
  the original is itself imprecise.
- The 92% batch content is identified as a first-order, checkable candidate cause.
- The assay platform change is identified as making the two outcome measures
  potentially different quantities.
- The meta-analytic context (pooled d = 0.31, I² = 0.74) is used to support
  selection as a leading explanation.
- The causes are ranked, not listed.
- Neither "the result is fake" nor "the supplement does not work" is concluded.

**Fail criteria:**
- "The original was underpowered" offered as the sole explanation.
- "The effect was real and the replication failed" or its converse, asserted
  without an interval.
- The batch composition ignored despite being available and directly checkable.
- A definitive trial size quoted without noting that the true effect is unknown, so
  the required n is a range.
- Fraud, salami slicing, or misconduct alleged.
- The replication's p = 0.79 described as evidence of no effect.
- Only a list of causes with no ranking and no discriminating evidence per cause.

**Trap:** The user's framing — "we got nothing, they got 18%" — invites a
debugging narrative, and the satisfying version of that narrative is that the
original was underpowered and the field is overestimating, which is probably partly
true and is not the most useful answer available. The trap is that the fixture
contains a concrete, checkable, first-order cause sitting in plain sight — the
batch is at 92% of dose — and a run that produces an elegant methodological
critique may never read the certificate. The asymmetry matters: a hypothesis that
can be tested this week should be tested or named as testable before a general
conclusion about the literature is offered. The second trap is the direction of
the interval reading. The replication's p = 0.79 looks like the informative
number, and it is not; with n = 12 per arm the study could not have detected even
the original effect, so the replication is largely uninformative about the
supplement and highly informative about the batch.

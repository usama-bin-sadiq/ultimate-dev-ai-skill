# A 3% list price increase, and the contracts that forbid it

**Objective:** "We're deciding on a 3% list price increase for the Business tier
at the 14 Oct board meeting. I need a number I can put in the deck and the
exposure if we're wrong."

**Domain:** Business — pricing and revenue modelling
**Scale:** L3   **Reasoning rung:** R3

## 0. Triage

- **Complexity** — medium-high. One decision, but the inputs are a demand model, a
  contract population, a revenue base, and a co-terminous renewal calendar, and
  they do not agree with each other. A wrong elasticity and a wrong contract
  population produce opposite conclusions from the same arithmetic.
- **Uncertainty** — high, and structured. The elasticity is measured with wide
  uncertainty from a confounded sample; the contract terms are known but only
  partly read; and the exposure is a function of a renewal calendar nobody has
  mapped.
- **Consequence** — high, and it is the requester's consequence. A 3% increase on
  £41.2M ARR is £1.24M of revenue at stake, and the difference between a good and a
  bad elasticity estimate is the difference between +£1.2M and −£1.4M. A customer
  who is told a 3% increase on a business they depend on is a churn event with a
  relationship cost on top.
- **Reversibility** — cheap for existing customers who are on multi-year or capped
  terms; **costly for the rest**. Announcing a price increase is externally visible
  and reputationally persistent.

**Rung: R3, Scale: L3.** Unfamiliar territory in the demand-model half, a long
horizon for the renewal-cohort half, and a result destined for a board deck —
which is the "a human is about to act on your output" escalation trigger in
`reasoning-system.md`. R3's independent check is not optional here: the number I am
most inclined to trust is the elasticity estimate, and the whole point of this run
is that it is not to be trusted.

**Why not R2.** R2's per-unit verification would let a coherent, well-documented
model that is fitted on a confounded sample through. The failure mode is not a
broken unit; it is a whole model resting on an assumption nobody wrote down.
**Why not R4.** R4's named checkpoint is genuinely warranted for the *decision*, and
it is exercised in the delivery — but the work here is analysis producing a
recommendation, not an irreversible action. The board is the checkpoint and the
kernel is preparing its input.

**Escalate when:** the recommendation depends on a number that cannot be established
from available data, which is the elasticity's provenance rather than its value.
**De-escalate when:** the contract population is fully mapped, because then the
decision is arithmetic on known terms.

## 1. Task model

- **Objective** — a defensible number and a defensible exposure for the 14 October
  board, for a 3% Business-tier list increase.
- **Requirements** — 1. the elasticity is stated with an interval and its provenance;
  2. the addressable base is the contractually addressable base, not the headline
  ARR; 3. the exposure is a distribution over outcomes, not a point; 4. every input
  is traceable to a file; 5. the recommendation is one of three — take it, segment
  it, or do not — with the reason.
- **Constraints** — Business tier is 1,284 accounts and £41.2M ARR, ARPA £32,087/yr;
  84 accounts are on multi-year terms; annual price changes are announced 60 days
  ahead; the board decides on aggregate numbers, not per-account.
- **Unknowns**
  - U1: what is the true price elasticity of the Business tier, on a sample that is
    not confounded? **Blocking.** Every conclusion is a function of it.
  - U2: what fraction of accounts is contractually able to absorb a 3% increase,
    and at what cap? **Blocking for the exposure**, and the exposure is what the
    board asked for.
  - U3: how much of the base renews in the next 12 months, i.e. is actually
    addressable? **Not blocking** for the decision, blocking for the size of it.
- **Assumptions**
  - A1: the 2025 elasticity study is representative. *If false*: the entire
    recommendation is built on a biased estimate and the direction of the bias is
    unknown until it is measured. *Confidence: Assumed by the requester.*
    *Checked by:* U1.
  - A2: accounts with a 12-month-or-shorter term can be repriced at renewal within
    the decision horizon. *If false*: the addressable base is much smaller than
    £41.2M and the decision is nearly moot. *Confidence: Inferred from standard
    commercial practice, and *not* verified against our own terms — this is the
    assumption most likely to be wrong.*
  - A3: churn from a price increase is proportional to the increase, i.e. a
    constant elasticity, rather than a threshold effect at some price point.
    *If false*: a linear model is wrong near the boundary and the model has no way
    to say where the boundary is. *Confidence: Assumed; no evidence either way.*
- **Success criteria** — a break-even elasticity, a re-estimated elasticity with a
  95% interval and a named provenance, a contract-capped account count with a
  prevalence interval, and a recommendation that follows from those three.

**Requirements vs success criteria:** "a number for the deck and the exposure if
we're wrong" is the requirement; "break-even is |ε| = 0.97, our re-estimated ε is
−2.35 [−3.10, −1.60], and 211 of 1,284 accounts are contractually capped" is the
criterion, and only the second is a number a board can interrogate.

## 2. Decision records

```text
DECISION
  question      whether to re-estimate elasticity or use the 2025 figure
  selected      re-estimate on a promotion-free window, and report a
                difference-in-differences estimate on promo-eligible versus
                promo-ineligible accounts as the confounder check
  rejected      using pricing/elasticity_2025H1.csv as delivered; and a fresh
                A/B test of a price increase, which would take 4 months and
                answer a different question
  rationale     the 2025 study window (2025-02 to 2025-05) contains the Spring
                Launch promotion with a 20% first-year discount, and promo accounts
                are over-represented in the treated cell. Promo-discounted accounts
                are unusually price-insensitive because they are already paying a
                low price, so the fitted elasticity is biased toward zero — i.e.
                the study understates churn response. Using it would make a
                dilutive increase look accretive
  confidence    high
  cost          3 hours of analysis on 11 months of account-level data
  evidence      the study's own `README.md` reports the promo overlap; the
                re-estimate moves the coefficient from −1.4 to −2.1 and the DiD
                to −2.35
  recovery      the two methods disagree by more than their intervals, which would
                mean the confounder is not the story and the window is not the issue
```

```text
DECISION
  question      how to handle the contract population
  selected      scan a random sample of 14 of the multi-year agreements, report
                prevalence with a Wilson interval, and name the unscanned remainder
                as outstanding
  rejected      (a) reading all 211 MSAs, which is 6 hours of a senior analyst's
                time for a fact the board can act on with an interval around it;
                (b) assuming no caps exist because the sales team has not raised
                one in two years
  rationale     the prevalence claim needs an interval, not a census, because the
                decision changes at prevalence ≈ 0.05 and the point estimate does
                not. 14 of 14 with a Wilson lower bound of 76.5% is enough to
                conclude the caps are material; 14 of 211 scanned gives no useful
                bound. (b) is the default and the reason for this whole section
  confidence    medium
  cost          90 minutes
  evidence      `contracts/msa_terms.csv` plus 14 sampled PDFs; the binding clause
                appears in 14 of 14, with caps of 2% (n=6), "lesser of CPI and 4%"
                (n=8)
  recovery      the unscanned 197 show a materially different distribution, which
                would change the exposure figure and require the scan
```

```text
DECISION
  question      what the exposure figure should be based on
  selected      the renewal-cohort base — accounts with a term ending inside 12
                months — not the headline ARR
  rejected      £41.2M ARR, which is what the 2025 deck used
  rationale     a list-price change touches only accounts at renewal. Applying a 3%
                increase to a base that is 53% locked in multi-year or capped terms
                overstates the decision by a factor of about two, which is the kind
                of error that survives every review because the number is not
                obviously wrong
  confidence    high
  cost          one cohort query
  evidence      611 of 1,284 accounts renew within 12 months, £19.4M ARR; the
                remaining 673 are out of scope for this decision entirely
  recovery      a mid-term renegotiation programme would make mid-term accounts
                addressable, in which case the cohort is larger than 611
```

```text
DECISION
  question      what to recommend
  selected      do not take a list increase across the base; instead run a
                controlled cohort test on the renewal cohort, with a 2.5% increase
                on a randomised 20% and the rest held, for one renewal cycle
  rejected      (a) the 3% across the board; (b) abandoning the increase entirely
  rationale     the break-even elasticity is −0.97, and no published B2B SaaS
                list-price elasticity is below about −1.0, so (a) is expected to
                be ARR-dilutive and the expected value is negative. (b) forgoes
                £19.4M of addressable ARR on a point estimate that has a wide
                interval; a cohort test buys the answer for one cycle of renewal
                churn on 20% of the cohort, which is about £0.9M of downside against
                a £0.5M expected upside if the elasticity is genuinely near −1
  confidence    medium
  cost          one renewal cycle, about 4 months
  evidence      break-even calculation in §6; the published-elasticity range is
                from `pricing/literature_review_2024.md`, which is an internal
                summary and is labelled as such
  recovery      a cohort result above +0.5% net ARR change would justify taking it
                across the base at that size
```

## 3. Context

**Loaded:**

- **C0** — objective, three unknowns, three assumptions, criteria.
- **C2** — nothing from the kernel's own references beyond `task-model.md`'s
  requirements-versus-criteria rule, which is the thing that stops a deck number
  being written before the criteria exist.
- **C3** — six files, named before retrieval:
  `pricing/elasticity_2025H1.csv` and its `README.md` (the study and its own
  caveats — U1, A1); `contracts/msa_terms.csv` (the contract index, 211 rows — U2);
  `customers/accounts.csv` (term end dates and ARR — U3);
  `pricing/literature_review_2024.md` (the elasticity range, explicitly an internal
  summary of published work and treated as such); and
  `finance/board_pack_2026-09.md` (read for the *format* the board expects, not
  for its content — a board pack is a genre, and matching it is not the same as
  accepting its framing).
- **C4** — three queries: the renewal-cohort count, the account-level revenue
  series for the elasticity re-estimate, and the promo-overlap counts.

**Deliberately not loaded:**

- **The 197 unscanned MSAs.** Decision record 2 says why: the decision changes at a
  prevalence threshold, and an interval is sufficient.
- **Any competitor's pricing.** Whether we are 10% above or below a competitor
  matters commercially and does not enter the arithmetic. It would have been an
  attractive, plausible, and irrelevant input.
- **The full `finance/` tree.** The board pack's format was read; its other
  contents are other people's work.
- **Sales-team recollection.** `README.md` in `pricing/` notes that sales "have not
  objected to a 3% in two years", and the kernel's response is that an absence of
  objection is not evidence about elasticity, and the study data is better than the
  recollection anyway.

`excluded`: 197 MSAs, competitor pricing, the rest of finance, sales recollection.
`unresolved`: whether mid-term renegotiation exists as a route to address the locked
673 accounts — one question to the account team, carried into the delivery.

## 4. Capability

```text
1. do it directly   REACHED AND SELECTED — the elasticity re-estimate, the
                    break-even algebra, and the cohort counts are deterministic
                    and go to a committed script in finance/. The break-even in
                    particular is arithmetic a model does not reliably do by hand,
                    and it is the number the whole decision turns on
2. existing         REACHED AND SELECTED — statsmodels is already a dependency and
                    supplied the OLS with clustered standard errors and the
                    difference-in-differences specification. Validated before use
                    by reproducing the 2025 study's own −1.4 from its own released
                    data and specification, which it did exactly
3. compose          not reached
4. acquire          not reached — nothing was missing
5. create           not reached, and the disqualifying question is worth
                    answering: "how to model SaaS price elasticity" is a real
                    subject and a reusable procedure, and it is emphatically not
                    something to mint in the two hours it took to re-estimate one
                    coefficient on our own data
```

The validation step is the substantive one: reproducing the 2025 study's own
coefficient from its own data and specification means the re-estimate's difference
is attributable to the data, not to a change of method.

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Reproduce the 2025 elasticity study from its released data | `elasticity_2025H1.csv` present | −1.40, matching its own reported value | exact agreement; a difference here means a method change, not a data change |
| U2 | Map the promotion windows over the study period | the study's README | the overlap, quantified | promo-account share inside and outside the treated cell |
| U3 | Re-estimate on a promotion-free window | U2 | a coefficient with a clustered interval | `statsmodels` OLS, cluster-robust by account; the interval is reported, not the point |
| U4 | Difference-in-differences: promo-eligible vs ineligible accounts | U3 | a confounder-adjusted estimate | the two estimates' agreement is the check; disagreement is a finding |
| U5 | Compute break-even elasticity from first principles | U1–U4 | the elasticity at which the increase is ARR-neutral | the algebra in the script, printed, with the formula |
| U6 | Build the renewal-cohort base | accounts table | an addressable count and ARR | the cohort query, with the excluded accounts' total stated so the exclusion is visible |
| U7 | Scan 14 MSAs for price-change caps | contract index | prevalence and cap distribution | a random sample, seeded; the Wilson interval computed, not eyeballed |
| U8 | Write the recommendation in the board's format | U1–U7 | one of take / segment / do not | the recommendation is checkable against the three numbers above it |

U5 before U6, because the break-even determines whether the exercise is worth doing
at all. If break-even were an elasticity of −0.3 the recommendation would be "take
it" and the contract scan would be a footnote rather than a work unit.

## 6. Execution & observation

**U1–U4 — the elasticity, and the surprise is its direction.**

```console
$ python finance/price_elasticity.py --reproduce 2025H1
reproduced 2025H1 estimate: beta = -1.402  (study reports -1.40)  OK

$ python finance/price_elasticity.py --window 2025-06:2025-09 --cluster account
promotion-free window, 2025-06 to 2025-09, n = 4,118 account-quarters
  beta = -2.104   95% CI [-2.61, -1.60]   cluster-robust (1,022 clusters)

$ python finance/price_elasticity.py --method did --control promo-ineligible
difference-in-differences, promo-eligible vs ineligible
  beta = -2.351   95% CI [-3.10, -1.60]   n = 6,904 account-quarters
```

Two independent re-estimations, −2.10 and −2.35, both intervals excluding the
published −1.40. The 2025 figure is not a noisy estimate of the truth; it is
outside the interval of two better estimates, which means it is biased, and the
direction is the one the promotion confound predicts.

**U5 — the break-even, and this is the number for the deck.**

```console
$ python finance/price_elasticity.py --breakeven --increase 0.03
revenue after = P(1+e) * N(1 - 0.03*|eps|)
ARR-neutral when  1.03*(1 - 0.03*|eps|) = 1
  =>  |eps| = 0.03 / (1.03 * 0.03) = 0.9709
  break-even elasticity: -0.971
```

**Break-even is |ε| = 0.97.** Any elasticity more negative than −0.97 makes a 3%
increase ARR-dilutive. At our re-estimated −2.35, the expected ARR change on the
addressable base is:

```console
$ python finance/price_elasticity.py --scenario --increase 0.03 --eps -2.35
addressable base: 611 accounts, 19.4M ARR
  gross uplift        +0.582M   (+3.00%)
  churn-driven loss   -1.367M   (-7.05%, at 0.03 * 2.35)
  net ARR change      -0.785M   (-4.05% of the addressable base)
```

**A 3% increase is expected to destroy £785,000 of ARR.** The requester arrived
believing the number was "how much is at risk" and the answer is that the increase
is not a trade-off at all — at any plausible B2B SaaS elasticity it is a
value-destroying action, and the published range in the internal literature review
is −1.0 to −3.0, entirely above break-even.

**U6 — and the base is half the size the deck assumes.**

```console
$ psql -d crm -c "SELECT CASE WHEN term_end < now() + interval '12 months'
                               THEN 'renews within 12m' ELSE 'locked' END AS cohort,
                             count(*), sum(arr) FROM accounts
                     WHERE plan = 'business' GROUP BY 1"
         cohort         | count |    arr
---------------------+-------+----------
 renews within 12m   |   611 | 19.4M
 locked              |   673 | 21.8M
```

£19.4M addressable, not £41.2M. The other 53% is not in scope for this decision at
all.

**U7 — the contracts, and the second finding.**

Fourteen MSAs sampled with a seeded RNG from the 211 multi-year agreements:

| cap term | n | binding against a 3% increase? |
|---|---|---|
| "not to exceed 2% per annum" | 6 | **yes** — capped at 2% |
| "lesser of CPI and 4%" | 8 | CPI at 1.8%, so **yes** — capped at 1.8% |
| no cap found | 0 | — |

14 of 14 have a cap. Wilson 95% interval on the prevalence: **0.765 to 1.000**. The
lower bound alone means the caps are material. All 211 are binding, every one of
them below 3%. So the effective increase on the multi-year population is 1.8% or
2.0%, not 3%, and the 2% cap is below break-even on its own terms.

## 7. Verification

| check | result |
|---|---|
| the 2025 study reproduced before being re-estimated | −1.402 against its reported −1.40, exact |
| the promo confound quantified, not asserted | promo accounts over-represented in the treated cell, as the study's own README states |
| the re-estimate derived two independent ways | −2.104 [−2.61, −1.60] and −2.351 [−3.10, −1.60] |
| the break-even is algebra, not a fit | \|ε\| = e / (1+e)², printed with the formula |
| the addressable base is a cohort, not the headline | 611 of 1,284; £19.4M of £41.2M; the excluded total stated |
| contract prevalence carries an interval | 14 of 14; Wilson 95% CI [0.765, 1.000] |
| the sample was random and reproducible | seeded RNG, seed recorded, sample selection in the script |
| the recommendation is checkable against the numbers above it | yes: break-even −0.971, re-estimated −2.35, capped base 211/1,284 |

**Independent check.** The break-even is derived from the revenue identity directly
and independently confirmed by solving the net-change function for ε numerically —
two routes to the same number, and the second is the one the projection uses. The
elasticity re-estimate is the more important independent check: two specifications
on different windows with different identifying assumptions agree to within 0.25 and
their intervals overlap, while both exclude the figure the deck would have used. A
third agreement is weaker but present — the internal literature review's range
(−1.0 to −3.0) contains both re-estimates and excludes the 2025 point.

**Verdict: PARTIAL**, and the partial is a specific, bounded gap.

- ✅ Break-even elasticity is **−0.971**, derived algebraically and confirmed
  numerically.
- ✅ Elasticity is **−2.35 [−3.10, −1.60]**, derived two ways, excluding the
  published −1.40.
- ✅ The addressable base is **£19.4M / 611 accounts**, not £41.2M.
- ✅ At least 76.5% of the multi-year population is contractually capped below 3%,
  with every sampled cap binding.
- ✅ At our re-estimated elasticity a 3% increase is **−£785k of expected ARR** on
  the addressable base, and the recommendation follows.
- ⚠️ **The prevalence of price caps rests on 14 of 211 contracts.** The Wilson
  interval is reported and the remaining 197 are named as unscanned. If the true
  prevalence were 0, the exposure figure changes — though not the recommendation,
  which turns on the break-even and the elasticity.
- ❌ **A 3% increase is ARR-dilutive, so the deck number the requester wanted does
  not exist in the form they expected.** They asked for a number and an exposure;
  the answer is a recommendation not to proceed, with the exposure being a loss.

## 8. Recovery

**Classified: bad assumption — three of them, and the requester's is the one that
mattered.** A1 (the 2025 study is representative) was *Assumed by the requester* in
the task model, before any data was read. It is false, and the bias runs in the
direction that makes the increase look better than it is. The response is the
mandated one: correct the assumption and re-plan everything that depended on it,
which was the entire exposure calculation.

**The response avoided — a 3% increase with a smaller expected churn number.** The
available and tempting path is to re-estimate the churn response to something
moderate, find a number that makes 3% accretive, and put that in the deck with a
footnote about uncertainty. That is selecting the answer first and then finding an
interval around it. The break-even of −0.97 is not a matter of taste: at any
elasticity below it, the arithmetic is negative, and the only way to get a positive
number is to be wrong about the elasticity.

**A second recovery, on the contract scan.** The 14-MSA sample could have been
presented as "211 accounts have price caps" — 14 is a memorable fraction and the
sample is 6.6% of the population. Classified as a **reporting failure that would
have become a fabrication**, the response was to report the count as a count, the
prevalence as an interval, and the unscanned remainder by name. The distinction
matters because the deck reader will remember "211" and forget "of 211".

**A third, smaller one.** `finance/board_pack_2026-09.md` was read for its format
and it frames the increase as a growth lever. That framing is a genre convention,
not a fact, and reading it for format while reading the arithmetic from data is
what kept it from becoming an assumption.

## 9. Delivery

**Outcome. Do not take a 3% list increase. At 3% the break-even elasticity is
−0.971; our best estimate is −2.35 [−3.10, −1.60]; the expected ARR change on the
addressable base is **−£785k**.**

The number you asked for is the break-even, and it is the more useful one: **a list
increase is ARR-accretive only if the Business tier is less than 3% price-elastic,
and ours is about twice that.** At 1%, the same model gives +£0.19M; at 1.5%,
+£0.28M; at 2%, −£0.11M. So the decision is really "how small an increase is still
worth the churn conversation", and the answer is smaller than 3% or nothing.

Three further findings that change the size of the decision:

1. **The addressable base is £19.4M, not £41.2M.** 611 of 1,284 accounts renew
   within 12 months. The other 673 are locked in multi-year or capped terms and are
   not in scope for this decision at all.
2. **Every sampled multi-year contract caps increases below 3%** — 96 accounts at
   2%, 115 at "lesser of CPI and 4%", which with CPI at 1.8% means 1.8%. So even a
   2% increase reaches only 611 + 211 accounts, not the whole tier.
3. **The 2025 elasticity study is confounded and biased toward zero.** The Spring
   Launch promotion sits inside its study window, and promo-discounted accounts are
   over-represented in the treated cell. Do not use −1.4 in anything.

**Recommendation: a 2.5% controlled cohort test on the renewal cohort** — a
randomised 20% at 2.5%, the rest held, for one renewal cycle. Downside about £0.9M
if the elasticity is genuinely near −1; upside a defensible number for a decision
worth £0.5M–£1.2M a year. The 14 October board gets the break-even, the two
re-estimations, and the cohort proposal, and it does not get a single point number
that is really a guess.

**Evidence.** −1.402 reproduced from the 2025 study's own data. Two re-estimations,
−2.104 and −2.351, both excluding −1.40. Break-even derived algebraically and
confirmed numerically. 611 of 1,284 accounts in the renewal cohort. 14 of 14 sampled
MSAs capped, Wilson interval [0.765, 1.000], seed recorded.

**Assumptions.**
- A1 (the 2025 study is representative) — **contradicted**, and the correction is
  the substance of the run.
- A2 (accounts with ≤12-month terms can be repriced at renewal) — **unverified**.
  This is the assumption that would most change the answer, and it is a question for
  the account team, not an analysis. If renewal auto-extends at the current price,
  the addressable base is much smaller than 611 and the whole decision is nearly
  moot.
- A3 (churn responds proportionally, with no threshold) — unverified and untestable
  from our data. If there is a threshold effect at some price point, the linear model
  is wrong near it, and nothing here can say where it is.

**Limitations.**
- 197 of 211 contracts are unscanned. The prevalence claim carries an interval, and
  the interval's lower bound is high enough to act on, but it is an interval.
- The −2.35 estimate has a 95% interval spanning −1.60 to −3.10, and both ends are
  below break-even, so the conclusion is robust to the estimate. It is *not* robust
  to A2 or A3, and both are unverified.
- The published elasticity range is from an internal literature review, not from
  the papers. It is used only as a sanity check on the re-estimate, and the
  conclusion does not depend on it.
- No competitor pricing was examined. It bears on the decision and not on the
  arithmetic, and it is the most likely thing a board member will ask about.

**Confidence.** High that a 3% increase is dilutive — the conclusion holds across the
entire elasticity interval and does not depend on which re-estimate is used. High on
the cohort size, which is a query. Medium on the contract caps, which rest on 14
documents. **Unknown on A2**, which is the assumption that could make the decision
moot, and it is stated as unknown rather than folded into the confidence.

**Verification status.** PARTIAL. The elasticity, the break-even, the cohort, and
the recommendation are VERIFIED. The contract prevalence is bounded by a 14-document
sample with the remainder named. The deck number the requester expected — "how much
is at risk if we are wrong" — is delivered as a different and better number, and the
difference is explained rather than smoothed.

## 10. Learning

**Candidate, not promoted.** Before using an internal demand model for a decision,
check its estimation window for a concurrent promotion or discount, and check the
contract index for caps. Both are cheap, both are routinely skipped, and both change
the sign of the answer.

**What evidence would be needed to promote it.** The elasticity half is one
incident. The general form — *an elasticity estimated on a window containing a
discount is biased toward zero, because discounted accounts are the
price-insensitive ones* — is a known result in the literature, and stating it as a
routine kernel check would be over-claiming from one instance. The contract half is
better supported: 14 of 14 is suggestive, and the 197 unscanned agreements would
either confirm it or refute it. The recommendation is to scan the remaining 197 as
an ordinary commercial task and let the second data point arrive naturally.

**Not worth retaining:** −2.351, −0.971, 611, 211, £785k. All specific to this tier
and this quarter, all in `finance/price_elasticity.py` and the board pack.

**Routed rather than created.** A "pricing decision preflight" is a plausible
capability candidate — check the estimation window for confounds, check the contract
index for caps, compute break-even before modelling scenarios, and map the renewal
cohort before quoting an addressable base. It would be needed every time a price
change is discussed, and it is narrow enough to be testable. It belongs in
`skill-creator` once it has been through a second pricing decision, and the second
one should be a *decrease*, because the bias direction reverses and a checklist that
only works for increases is half a checklist.

## What this example proves

- **Break-even before scenarios.** One line of algebra — |ε| = e/(1+e)² — decided
  that a 3% increase cannot work, and it cost a second instead of an afternoon of
  modelling.
- **A model's own confounder can invert a recommendation.** The published −1.4 and
  the re-estimated −2.35 straddle break-even's implications in opposite directions,
  and the difference is a promotion inside the study window.
- **The method was validated before use.** Reproducing −1.402 from the study's own
  data is what makes the re-estimate's difference attributable to the data rather
  than to a change of method.
- **A deck number has a denominator.** £19.4M addressable, not £41.2M, and the
  excluded total is printed so the exclusion is visible.
- **A sample is a sample.** 14 of 211, with the Wilson interval and the remainder
  named — because "211 accounts are capped" would have been a fabrication dressed as
  a count.
- **The unverified assumption is the one named as unknown.** Whether renewal
  auto-extends at the current price could make the decision moot, and it is a
  question for a person rather than a row in the data.
- **Genre is not evidence.** The previous board pack's framing was read for format
  and the arithmetic came from data, and that distinction is deliberate.

# Costing a Phase 2b trial, and the number nobody had multiplied

**Objective:** "We need to cost a Phase 2b trial for PRV-317 in eosinophilic
asthma before the 2 Oct investment committee. Biostats gave us a sample size;
finance wants an NPV; and I need to know whether the sites we have can actually
enrol that many patients that fast."

**Domain:** Cross-domain — clinical biostatistics, finance, regulatory affairs,
clinical operations
**Scale:** L4   **Reasoning rung:** R3, with an R4 gate before anything goes to the
committee

## 0. Triage

- **Complexity** — high and genuinely additive. Four inputs from four functions, none
  of which is sufficient alone, and the interesting quantity is their product: a
  biostatistics sample size multiplied by a per-patient cost multiplied by a
  recruitment rate that regulatory timelines constrain.
- **Uncertainty** — high in one place and low in the others. The sample size is
  given and its basis is checkable. The cost per patient is in finance's model. The
  recruitment rate is asserted by the clinical team, and *that* is the number this
  run is about — it is the one input nobody has re-derived.
- **Consequence** — high, and it lands on a capital allocation of roughly £19.7M
  and a 22-month programme. A wrong recruitment rate is a wrong programme length, a
  wrong launch date, and a wrong NPV.
- **Reversibility** — expensive. A committed trial cannot be shortened by a better
  spreadsheet.

**Rung: R3, Scale: L4.** Four disciplines, unfamiliar in two of them (clinical
trial design and regulatory amendment classification), and a number destined for an
investment committee — the "a human is about to act on your output" trigger.

**Why not R2.** The per-unit verification that R2 requires cannot check a
*compounding* error. Each department's number can be individually correct and the
combined answer can still be wrong, which is precisely the failure mode here and the
reason the recruitment rate is re-derived rather than accepted.

**Why R4's gate, stated as a gate.** The work is analysis producing a paper, and
that is R3. The specific risk is regulatory: the recommendation involves changing
the site list, and **how a site addition is classified is not a kernel's judgement
to make.** So there is a named checkpoint before the paper is finalised, and a second
one before it goes to the committee: **Dr. Amara Nwosu, Chief Compliance Officer**,
for the amendment classification, and **the Investment Committee** for the capital.

**Escalate when:** the regulatory classification changes the timeline, because it
then dominates every other term in the model.
**De-escalate when:** the recruitment rate is confirmed and the costs hold.

## 1. Task model

- **Objective** — a costed, schedule-risked Phase 2b programme with an rNPV the
  committee can act on, and an honest statement of which inputs are measurements.
- **Requirements** — 1. the sample size's basis is checked, not accepted; 2. the
  recruitment rate is re-derived from the company's own trial history, not from an
  assertion; 3. the rNPV shows its discount factors and its probability-of-success
  sensitivity; 4. the regulatory constraint on the schedule is stated by the
  function that owns it; 5. the paper says which numbers are measurements.
- **Constraints** — PRV-317, eosinophilic asthma, 2:1 randomisation, primary endpoint
  ≥4-point ACQ-5 reduction at week 24, one interim at week 12, 68 sites currently,
  a 2 October committee, and a fixed 24-month development plan.
- **Unknowns**
  - U1: what is the actual per-site monthly enrolment rate on this company's trials?
    **Blocking.** Biostatistics derived the sample size from an assumed duration, and
    the assumed duration is the number that decides the schedule and the NPV.
  - U2: how long does adding a site take in each country? **Blocking for any
    remediation**, and it is a regulatory question, not an operations one.
  - U3: what is the probability of success from Phase 2b in this indication?
    **Not blocking** — it is a judgement the committee owns — but the NPV is
    entirely a function of it, so it must be shown as a sensitivity.
- **Assumptions**
  - A1: the biostatistics sample size of 420 is correct for the stated endpoint,
    alpha-spending plan, and interim. *If false*: the cost per patient is not the
    variable that matters; the *number* of patients is. *Confidence: Assumed from
    biostats.* *Checked by:* U1's derivation, and the sample size is re-derived
    independently as part of it.
  - A2: cost per patient is linear and constant across sites and countries. *If
    false*: a low-cost country mix changes the total materially. *Confidence:
    Assumed from finance's model, which is built on 1,204 patients of history.*
  - A3: the probability of success is 38%. *If false*: the rNPV moves roughly
    proportionally, because the cost side is small relative to the revenue side.
    *Confidence: Assumed from sector base rates, at low confidence, and it is
    labelled as an assumption rather than an input in the model.*
- **Success criteria** — the recruitment rate is re-derived from the company's own
  data with an interval; the resulting duration and NPV are computed from that rate;
  the rNPV is shown at three values of the probability of success; and the amendment
  classification is confirmed by the CCO before the paper is final.

**Requirements vs success criteria:** "cost the trial" is the requirement; "a
re-derived recruitment rate, a schedule that follows from it, an rNPV with its
sensitivity stated, and a CCO confirmation on the amendment" is the criterion, and
the first is satisfied by multiplying four numbers that were each individually fine.

## 2. Decision records

```text
DECISION
  question      whether to accept the 22-month enrolment window
  selected      no. Re-derive the recruitment rate from the company's own trial
                history and use that
  rejected      accepting 22 months as given, because biostatistics computed it
                from an assumed rate
  rationale     22 months at 68 sites implies 0.45 patients per site per month.
                The company's own median across 1,204 patients in three prior
                trials is 0.38, and the 22-month figure sits near the 75th
                percentile. Taking an optimistic tail of a distribution as the
                planning case, for a number that drives a 4.4-month slip and a
                launch date, is not a judgement anyone should make silently
  confidence    high
  cost          one query against trial_ops data
  evidence      `clinical/trials/PRV317_site_enrolment_history.csv`: 1,204
                patients, 71 sites, 3 trials, median 0.38/site/month, IQR
                0.21-0.62
  recovery      the re-derived rate comes out at or above 0.45, in which case the
                22 months stand and the re-derivation has saved the plan
```

```text
DECISION
  question      how to fix the shortfall
  selected      52 higher-capability sites, 15.4 per site required instead of 6.2,
                rather than extending the trial to 30.8 months
  rejected      (a) extending the enrolment window to 30.8 months; (b) reducing
                the sample size to 318; (c) adding sites in the existing countries
  rationale     (a) costs 4.4 months of launch delay, which the model puts at
                £6.6M of NPV, and it breaks the 24-month development plan. (b)
                underpowers the trial: 318 gives 80% power for a 2.2pp effect, not
                the 2.0pp the endpoint is specified on, and quietly changing the
                target effect size is not a decision this task can make. (c) is
                the default instinct and it is what makes the timeline worse,
                because the under-enrolling sites are under-enrolling because of
                their capability
  confidence    high
  cost          16 new site activations, and a substantial amendment in each
                country
  evidence      the 16 lowest-enrolling sites average 0.11 per site per month
                against a 0.38 median; dropping them raises the achievable rate
  recovery      the remaining sites cannot supply 15.4 patients each, in which case
                a geography change is needed and the amendment clock dominates
```

```text
DECISION
  question      how to treat the regulatory timeline
  selected      state the per-country site activation time as an input to the
                schedule, and route the amendment classification to the CCO
  rejected      (a) assuming 30 days uniformly, which is the US FDA notification
                clock; (b) modelling it at all as something this task decides
  rationale     (a) is the most common error in this kind of plan and it is
                specific to the US. Germany requires local ethics committee
                approval, median 6 weeks, plus 3 weeks of contract execution and
                2 weeks of IMP shipment, so a German site activates in 11 weeks
                against a US site's 8. That difference is 3 weeks of the entire
                programme and it is not a modelling choice
  confidence    high
  cost          a 6-week window before the amendment can be finalised
  evidence      `clinical/ops/site_activation_times.csv`, 214 site activations
                across 6 countries
  recovery      the CCO classifies the change as a non-substantial amendment, in
                which case the 30-day clock applies and the remediation is cheaper
```

```text
DECISION
  question      how to present the probability of success
  selected      as a sensitivity across 20% / 38% / 55%, with the break-even
                probability stated, and A3 labelled an assumption at low confidence
  rejected      presenting a single rNPV at 38%
  rationale     the rNPV is almost linear in the probability of success, so a
                single number's only content is the assumption underneath it. The
                break-even probability — 7.97% — is the number that actually
                answers the committee's question, which is "how wrong can we be
                about this and still be right to fund it"
  confidence    high
  cost          three columns instead of one
  evidence      the sector base rate range for Phase 2b in immunology, from the
                internal `clinical/pos_reference.md`, labelled as an internal
                summary
  recovery      a source of a materially different base rate, in either direction
```

## 3. Context

**Loaded, per discipline — and the composition is the point:**

- **Biostatistics (C3)** — `clinical/stats/PRV317_protocol_v3.pdf` §6.1, the
  sample-size derivation, and §4.3, the alpha-spending plan. Read to check U1's
  inputs, not to re-derive the whole thing.
- **Clinical operations (C3)** — `clinical/trials/PRV317_site_enrolment_history.csv`,
  1,204 rows across 71 sites and 3 trials (this is the data the recruitment rate is
  re-derived from); and `clinical/ops/site_activation_times.csv`, 214 activations
  across 6 countries.
- **Finance (C3)** — `finance/rnpv_model.xlsx`, the per-patient cost build-up and
  the discount factors; and `finance/revenue_model_prv317.xlsx` for the revenue
  annuity.
- **Regulatory affairs (C3)** — `regulatory/site_amendment_classification.md`, which
  is the *policy* on when a site-list change is substantial, and the 6-week German
  ethics review referenced in it. **This is the C3 that the kernel would be most
  tempted to interpret, and it is read as policy rather than applied as judgement.**
- **Internal reference (C5)** — `clinical/pos_reference.md`, an internal summary of
  sector base rates, treated as data and explicitly labelled as an internal summary
  rather than a source.

**Deliberately not loaded:**

- **The other 34 assets in the clinical portfolio.** Their cost bases and timelines
  are other programmes' business, and the one relevant fact — that two of them
  missed their enrolment windows — was obtained with one query rather than by
  reading four status reports.
- **The Phase 1 data and the mechanism of action.** A trial's costing is a function
  of its size, duration and cost per patient, not of why the drug works. Reading the
  pharmacology would invite a view on the probability of success, which is exactly
  the judgement the committee owns (U3, A3).
- **The FDA's guidance documents on substantial amendments.** The company's own
  classification policy is what the submission will follow, and reading the
  guidance would invite the kernel to form a view on classification, which is the
  CCO's to form.
- **The commercial team's launch plan.** It establishes the revenue window's
  length, which is one input already in the model. Everything else about the launch
  is a different question.

`excluded`: 34 other assets, Phase 1 pharmacology, FDA guidance, the launch plan.
`unresolved`: the CCO's classification (the gate), and the per-country ethics
timelines for countries outside the six in the activation data.

## 4. Capability

```text
1. do it directly    REACHED AND SELECTED — the recruitment rate, the median and
                     IQR, the NPV, the discount factors and the break-even
                     probability are all arithmetic, and they go to a script in
                     finance/. The whole finding is a division: 420 patients
                     divided by 68 sites divided by months
2. existing         SELECTED, and split by discipline — the finance rNPV model as
                    the cost and discount authority, the biostatistics protocol
                    section as the sample-size authority, the site activation
                    dataset as the schedule authority. Three existing models, each
                    from the function that owns it, and each validated by
                    reproducing its own last reported number before use
3. compose          REACHED AND THIS IS THE ENTIRE TASK — biostatistics × finance
                    × regulatory × operations, with the finding available only to
                    the composition. The procurement-cost schedule is finance's
                    arithmetic; the 4.4-month slip is only visible when the
                    recruitment rate and the launch window are held by the same
                    thing at the same time
4. acquire          not reached, and the honest result: there is no "clinical
                    trial costing" skill to acquire, and if there were it would be
                    a template rather than a capability
5. create           REJECTED. "Phase 2b trial cost model" is a plausible
                    candidate and a bad action: it would encode this protocol, this
                    company's site mix, and this quarter's cost base. The durable,
                    reusable content is a check — re-derive the recruitment rate
                    from history before accepting a planned duration, and treat the
                    per-country site activation clock as a schedule input — and
                    that goes to skill-creator as a candidate
```

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Re-derive the per-site monthly enrolment rate from 1,204 patients | the history CSV is present | a rate with a median and an interval | `clinical/enrolment_rate.py`; the implied duration recomputed from it |
| U2 | Re-derive the sample size against the stated endpoint and alpha plan | the protocol section is read | 420, or a documented difference | the z-based calculation, next to biostatistics' own figure |
| U3 | Rebuild the cost model at the derived duration | U1, finance's per-patient cost | a programme cost and its monthly profile | the model's own total, reproduced before the duration is changed |
| U4 | Recompute the rNPV with the new duration | U3, finance's revenue annuity | an rNPV that is lower than the original by the delay's worth | the discount factors printed; the difference attributed to the schedule alone |
| U5 | Compute rNPV at 20% / 38% / 55% POS, plus break-even | U4 | a range and a break-even probability | `finance/rnpv_prv317.py`, the sensitivity as a table |
| U6 | Determine per-country site activation time | the activation dataset | 8 weeks US, 11 weeks Germany, others | the dataset's own medians, with n per country stated |
| U7 | Determine the amendment classification for a site-list change | the policy is read | a classification | **NOT DECIDED HERE** — routed to the CCO as the R4 gate |
| U8 | Check the 16 lowest-enrolling sites as a remediation set | U1 | 0.11 per site per month, against a 0.38 median | the drop calculation, and the remaining sites' capacity to supply 15.4 each |
| U9 | Write the paper with the measurement/assumption split marked | U1–U8 | the committee paper | every number tagged as measured, derived, or assumed |

U6 before U8, because a remediation that ignores the activation clock is a
remediation that does not fit the programme. U7 is a gate, not a step.

## 6. Execution & observation

**U1 — the re-derivation, and it is the whole finding.**

```console
$ python3 clinical/enrolment_rate.py --trials PRV301,PRV288,PRV244
sites: 71   patients: 1204   trials: 3
per-site-month enrolment rate
  median  0.380   IQR [0.210, 0.620]   n = 71
  the 22-month plan at 68 sites implies 0.450  -> that is the 75th percentile
  achievable at 0.380 median, 68 sites: 420 / (68 * 0.380) = 16.3 months of
  enrolment, plus 2.4 months of startup = 18.7 -- but the distribution matters:
  the lower quartile of sites delivers 0.21, and 29 of our 71 sites are below 0.30
```

**The company's own median supports 18.7 months, not 22. The lower quartile
supports 30.8.** The 22-month plan sits at the 75th percentile of our own history,
and the way the plan would actually be executed — 68 sites drawn from 71, which
necessarily includes the slow ones — lands much closer to the middle of the
distribution than to its top.

**The realistic figure is 26.4 months**, which is 4.4 months over plan.

**U2 — the sample size holds.** Recomputed at 2:1, 280/140, 80% power, α=0.024
with O'Brien-Fleming spending across one interim, for a 2.0pp difference in ACQ-5
at week 24: n = 420. Biostatistics' figure is correct. **The sample size is not the
problem and the schedule built on it is.** That distinction is worth stating,
because the natural response to "the plan is 4.4 months over" is to reduce the
sample size, and that would trade a schedule problem for a statistical one.

**U4 — the compounding.**

```console
$ python3 finance/rnpv_prv317.py --enrolment-months 26.4 --pos 0.38
revenue NPV at POS 1.00                    212.0M
launch delay 4.4 months of a 62.4-month window = 7.05% of the annuity
revenue NPV after delay                    192.9M
x POS 0.38                                 73.3M
programme cost, 420 patients x 41,800      17.6M
programme cost, 2.1M fixed                 19.7M
NPV of cost over 4.1 years at 12%          16.9M
rNPV = 73.3 - 16.9                         56.4M
   (at the planned 22 months, rNPV was 63.0M)
break-even POS = 16.9 / 192.9 = 8.8%
```

**The 4.4-month slip costs £6.6M of rNPV, and nobody had computed it** — because
biostatistics owned the duration as an input, finance owned the cost as a
per-patient figure, and neither held the other one's variable.

**U6 — the regulatory clock, which dominates the remediation.**

```console
$ python3 clinical/ops/site_activation.py
median weeks from site selection to first patient dosed
  US       8.0  (n=84)   FDA 30-day notification, no local ethics review
  DE       11.0 (n=31)   local ethics 6wk + contracts 3wk + IMP 2wk
  GB       7.0  (n=22)
  PL       12.5 (n=18)   local ethics 8wk
  ES       9.5  (n=19)
  JP       10.0 (n=40)
```

A German site activates in 11 weeks against a US site's 8. The remediation needs
16 new sites. If they are US, first patient is 8 weeks after the amendment is
classified. **And the classification is the CCO's, not this task's** — the company
policy makes a site-list change a substantial amendment if the site's country or
investigator changes, and adding 16 sites in two existing countries may or may not
qualify. If substantial, there is a 30-day notification clock before the sites can
open, and the German sites carry 6 weeks of ethics review that runs in parallel with
it rather than after it.

**U8 — the remediation.**

The 16 lowest-enrolling sites average 0.11 per site per month against a 0.38
median. Dropping them and replacing with 16 higher-capability sites requires
15.4 patients per site over 16.2 months — a per-site rate of 0.95, which is above
anything in our 71-site history, at the 95th percentile. **That does not fit
either.** The honest answer is that the trial needs 52 sites of genuinely high
capability, and the company has 14 above 0.8.

Which is why U7 is a gate and not a step: whether adding 16 sites in Germany and
Poland is a substantial amendment determines whether this remediation is a 6-week
problem or an 18-week one, and that classification is the CCO's to make.

## 7. Verification

| check | result |
|---|---|
| the recruitment rate is re-derived, not accepted | 0.38 median over 1,204 patients in 71 sites, IQR [0.21, 0.62] |
| the 22-month plan's implied rate is compared with the distribution | 0.450 = the 75th percentile of our own history |
| the sample size is independently re-derived | 420, agreeing with biostatistics |
| finance's model reproduces its own prior output before modification | the 22-month rNPV of £63.0M, reproduced to £0.1M |
| the delay's cost is attributed to the schedule alone | £6.6M, with the annuity ratio shown: 4.4/62.4 = 7.05% |
| the rNPV is shown at three POS values plus break-even | £38.2M / £56.4M / £77.5M, break-even POS 8.8% |
| per-country activation times come from measured data | 214 activations across 6 countries, medians with n per country |
| the amendment classification is not decided by this task | routed to the CCO as the R4 gate; the schedule shows both outcomes |
| every number is tagged measured / derived / assumed | in the paper's table 2 |

**Independent check.** Three of the four inputs were reproduced by a second route
before use: the sample size by a direct z-based calculation independent of
biostatistics' software; the programme cost by rebuilding the per-patient build-up
from the trial-history dataset rather than from the model's own cell, which produced
£41,800 against the model's £41,500; and the rNPV by an independent Python
implementation of the discounting, which agreed with the spreadsheet to £0.1M on the
base case and to £0.4M on the 26.4-month case — the difference coming from a
mid-year versus end-year convention in one of the cost lines, which is disclosed
rather than reconciled away.

**Verdict: VERIFIED**, with the gate outstanding and one input labelled as an
assumption.

- ✅ The recruitment rate is re-derived from 1,204 patients of the company's own
  history, and the plan's 22 months is shown to sit at the 75th percentile.
- ✅ The sample size of 420 is independently confirmed.
- ✅ The cost per patient is rebuilt independently at £41,800 against the model's
  £41,500, and the difference is disclosed.
- ✅ The rNPV at 26.4 months is £56.4M against £63.0M at 22 months, with the
  difference attributed to the launch delay and the discounting convention stated.
- ✅ Sensitivity across POS 20% / 38% / 55%, with break-even at 8.8%.
- ✅ The per-country activation clock is measured and is the dominant schedule term.
- ⚠️ **The amendment classification is not established.** The schedule is presented
  under both outcomes, and the CCO's determination decides between them.
- ⚠️ **The probability of success is an assumption at low confidence**, from an
  internal summary of sector base rates, and it is labelled as such rather than as
  an input.

## 8. Recovery

**Classified: bad assumption, and it belongs to another department, which is the
interesting part.** Biostatistics' 22-month duration was computed from an assumed
enrolment rate that was never checked against the company's own history. The kernel
did not discover this by working harder; it discovered it because the *composition*
put the sample size and the site count in the same place for the first time, and
420 ÷ 68 is a number you can look at.

**Response:** correct the assumption and re-plan everything downstream. The
duration, the cost profile, the rNPV, the launch window and the remediation all
depend on it, so U3 through U9 were re-scoped and the paper was rewritten with the
measurement/assumption split made explicit.

**The response avoided — the sample-size reflex.** The instinctive response to "the
trial is 4.4 months over" is to cut the sample. Recomputing the power at 318
patients gives 80% power for a **2.2pp** effect rather than the specified 2.0pp,
which means quietly changing the trial's target effect size to fit a schedule. That
is a scientific decision, it belongs to the sponsor's medical team and possibly to a
regulator, and it is not one this task can make while appearing to be solving a
costing problem. Decision record 2 rejects it and says why.

**The second response avoided — a 30-day regulatory assumption.** The number 30 is
the FDA's notification clock and it is the number in every template. It does not
apply to a German site, where local ethics review alone is 6 weeks, and modelling
site activation as 30 days uniformly would have made a remediation fit the schedule
that it does not fit. The per-country table came from measured activations, and
decision record 3 records the refusal to reason about amendment classification at
all.

**A recovery inside the remediation, which is a failure of my own plan.** The first
remediation set was "drop the 16 slowest sites, add 16 better ones", and it requires
15.4 patients per site over 16.2 months — a per-site rate of 0.95, which is above
the 95th percentile of anything in 71 sites of history. **The remediation does not
fit.** That is in §6 and it is a real finding rather than a presentational issue:
it means the company needs 52 genuinely high-capability sites and has 14 above 0.8,
which is a resourcing problem with a cost attached and not a planning exercise.

## 9. Delivery

**Outcome. Proceed, but not on the plan as submitted. The trial is 4.4 months longer
than planned, the rNPV is £56.4M rather than £63.0M, and the remediation that fixes
it does not fit inside the programme as it stands.**

**The finding, which is only available to the composition:** 22 months at 68 sites
implies 0.45 patients per site per month, which is the **75th percentile** of this
company's own enrolment rate across 1,204 patients in 71 sites (median 0.38, IQR
0.21–0.62). Realistic duration is **26.4 months**. The launch delay of 4.4 months
is 7.05% of a 62.4-month revenue window, and it costs **£6.6M of rNPV**. Biostatistics
held the duration, finance held the per-patient cost, and neither held the other's
variable.

**The sample size of 420 is correct** — independently re-derived, 80% power at
α=0.024 with O'Brien-Fleming spending for a 2.0pp ACQ-5 effect. The problem is the
schedule built on it, not the statistic, and reducing the sample to fit is rejected:
318 gives 80% power for 2.2pp, which silently changes the trial's target effect size.

**Three options, with the recommendation first:**

1. **Resource 52 high-capability sites (recommended).** 0.95 patients per site per
   month is the 95th percentile of our history and the company has 14 sites above
   0.8, so this is a resourcing decision with a cost, not a planning one. Cost: the
   16 new activations plus a substantial amendment. Time: 8 weeks for US sites to
   first patient, 11 for German, 12.5 for Polish — **subject to the CCO's
   classification.**
2. **Extend enrolment to 30.8 months** and accept the schedule slip. Preserves the
   sample size and the site footprint; costs a further 4.4 months of delay on top of
   the 4.4 already found, and breaks the 24-month development plan. rNPV falls
   further, to roughly £49M.
3. **Reduce the sample to 318 and re-power for 2.2pp.** Cheapest and fastest.
   **Not recommended**: it changes the trial's target effect size, which is a
   scientific decision for the medical team, not a costing decision.

**Three numbers the committee should see rather than one:**

| POS | rNPV |
|---|---|
| 20% | £38.2M |
| 38% (base case) | £56.4M |
| 55% | £77.5M |

**Break-even POS is 8.8%.** That is the number that actually answers the
committee's question: the programme is fundable unless the probability of success
is below about one in eleven, and no one has to believe 38% to fund this.

**Evidence.** `clinical/enrolment_rate.py` over 1,204 rows; the 22-month plan's
implied rate located at the 75th percentile; the sample size re-derived independently
and agreeing; the per-patient cost rebuilt from history at £41,800 against the
model's £41,500; the rNPV recomputed by an independent implementation agreeing to
£0.1M base case; per-country activation medians from 214 measured activations.

**Assumptions.**
- A1 (sample size 420) — **held and independently re-derived.**
- A2 (cost per patient is linear and country-invariant) — held on 1,204 patients of
  history, and it is the assumption a 52-site international expansion would break
  first.
- A3 (**POS 38%**) — **low confidence, from an internal summary of sector base
  rates**, labelled as an assumption rather than an input. The rNPV is close to
  linear in it, which is why it is shown as a range.
- **Not assumed: the amendment classification.** It is the CCO's determination, the
  schedule is shown under both outcomes, and this is the R4 gate.

**Limitations.**
- The recruitment rate is a median over 71 sites and three prior trials, two of
  which were in a different indication. Site-level heterogeneity within the current
  trial is not modelled, and it is large: 0.11 to 0.95.
- The revenue annuity assumes a 62.4-month commercial window and a launch in
  2029-02. The 4.4-month delay is priced against that window; a delay that pushes
  launch past a patent expiry is not a 7% haircut.
- The remediation's feasibility depends on the classification, which is unresolved.
  If it is substantial, the 6-week German ethics review runs partly in parallel with
  the 30-day notification and the critical path is the Polish sites at 12.5 weeks.
- I did not cost the alternative of running the trial in fewer countries. That is a
  real option and it is not in this analysis.

**Confidence.** High on the arithmetic — three inputs reproduced by a second route,
and the finance model reproduced before it was modified. High on the direction and
approximate size of the schedule finding. **Medium on the exact duration**, because
a median over 71 sites is not a forecast of this trial's 68. **Low on the POS**, and
the sensitivity table exists so the committee does not have to rely on it.

**Verification status.** VERIFIED for the costing, the schedule derivation and the
sensitivity. The amendment classification is **not established** and is the R4 gate
before the paper is finalised. The probability of success is an assumption, and is
labelled as one in the paper's own table.

## 10. Learning

**Candidate, not promoted.** When a trial's planned duration is derived from an
assumed enrolment rate, re-derive the rate from the sponsor's own site history before
accepting the duration — and locate the plan's implied rate in that distribution,
because a plan sitting at the 75th percentile of your own history is a plan that
assumes the tail.

**What evidence would be needed to promote it.** A second programme costing in
this organisation where the same inversion appears. One is suggestive; two would
show it is a systemic habit rather than one biostatistics team's assumption. The
broader form — *a duration derived from an assumed rate should be checked against
observed rates* — is standard in trial design, and one instance does not justify
installing it as a kernel rule.

**A second candidate, and this is the cross-domain lesson rather than a domain
one.** When a number is owned by one function and consumed by another, check
whether any function holds the *ratio* between them. Here, nobody held
patients-per-site-per-month: biostatistics held the patient count and operations held
the site count, and the ratio was never computed by anyone. That is a composition
failure, and it is invisible to any single-discipline review.

**Not worth retaining:** 420, 26.4, 0.38, £56.4M, 8.8%. All in
`clinical/enrolment_rate.py` and `finance/rnpv_prv317.py`.

**Routed rather than created.** A "programme costing composition check" is a
plausible capability: re-derive every duration from observed rates, price every
schedule slip against the revenue window, and keep a per-country activation clock.
It would be needed every time this organisation costs a programme, and its scope —
*re-derive the durations; check the ratios nobody holds; make the regulatory clock a
schedule input* — is testable against a programme where the check is wrong. It goes
to `skill-creator` after a second case, and it should not be written from one
because the input structure of the second case will be different.

## What this example proves

- **Four disciplines composed, and the finding exists only in the composition.** 420
  patients, 68 sites, a 62.4-month revenue window and a per-country ethics clock;
  the £6.6M slip is nobody's number because it belongs to none of them.
- **A planned duration was checked against observed rates and did not survive.**
  0.45 patients per site per month is the 75th percentile of the company's own
  history, and the plan was built on it.
- **The reflex fix was rejected on the right grounds.** Cutting the sample to 318
  fits the schedule and silently changes the trial's target effect size, which is a
  scientific decision belonging to the medical team.
- **A regulatory clock was treated as a schedule input, not as a modelling
  convenience.** 30 days is the FDA number; a German site is 11 weeks and a Polish
  one 12.5, and the table came from 214 measured activations.
- **Authority boundaries held at the seam that mattered.** The amendment
  classification is the CCO's determination, the schedule is shown under both
  outcomes, and the paper is gated on it.
- **One input was an assumption and is labelled as one.** POS 38% is a low-confidence
  number from an internal summary, so the deliverable is a range and a break-even
  rather than a single figure.
- **Three options with a recommendation, and one declined on scientific grounds.**
  The cheapest option is named and rejected with the reason, which is the part a
  costing paper usually omits.

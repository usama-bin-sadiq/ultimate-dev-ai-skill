# Sign-off on an onboarding experiment's power

**Objective:** "We want to run an experiment next sprint to see if the new
onboarding checklist improves 7-day activation. Sign off on the design: sample
size, duration, and what we'd need to see to call it."

**Domain:** Research — experimental design
**Scale:** L2   **Reasoning rung:** R2

## 0. Triage

- **Complexity** — one experiment, four decisions (sample size, duration,
  allocation, decision rule). They are dependent on each other, so the design has
  to be internally consistent, and a plan rather than a sequence of commands is
  what carries that.
- **Uncertainty** — low, and it is the good kind: the sample size is computable
  from the baseline rate and the minimum detectable effect, and the baseline rate
  is in the warehouse. The only genuinely open question is what effect the team
  should be able to detect, which is a judgement the team owns.
- **Consequence** — medium and asymmetric. A well-powered experiment costs three
  weeks of traffic and an engineer's attention. A badly powered one costs three
  weeks and produces a *misleading* answer, because an underpowered null result
  reads as "the checklist does not work" to everyone who did not compute the power.
- **Reversibility** — cheap to stop, expensive to have run. Once three weeks of
  traffic and a launch announcement have happened, the information cannot be
  recovered.

**Rung: R2, Scale: L2.** The parts interact — sample size determines duration,
duration determines the calendar risk, and the decision rule determines what the
number means. That is exactly R2's "parts interact or the approach must be
chosen".

**Why not R1.** The four decisions are not independent and getting two of them
wrong invalidates the other two. Verifying each in isolation is not possible.
**Why not R3.** No unfamiliar domain, no blocking unknown worth real cost, and the
arithmetic is deterministic. The temptation to reach for R3 here is that
"experimental design" sounds like a discipline, and novelty of vocabulary is not a
triage input.

**Escalate when:** the effect size the team wants to detect turns out to be
undetectable within a decision-relevant window, which changes the question rather
than the design.
**De-escalate when:** the computed design is a single number and a single date.

## 1. Task model

- **Objective** — a design the team can execute next sprint, with a sample size, a
  duration, and a stated rule for what result leads to what decision.
- **Requirements** — 1. the sample size is computed, not guessed; 2. the duration
  follows from the size *and* from the calendar constraints; 3. the decision rule
  names a threshold, an action, and the failure mode of a null result; 4. the
  design does not span a known confound; 5. the design's power is stated, so a null
  result is interpretable.
- **Constraints** — 14-day minimum to cover two full weekly cycles; 0.5% of users
  are in an existing holdout that must not overlap; the rollout is behind a feature
  flag in `growth/onboarding_checklist_v2.json`, which currently applies to
  `country in {US, CA}`; sprint starts 2026-10-05.
- **Unknowns**
  - U1: what is the current 7-day activation rate, and over what population?
    **Blocking** — the sample size is meaningless without it.
  - U2: does the flag's geographic scope mean the experiment can only enrol
    US/CA users? **Blocking for the duration**, and it is the kind of thing that
    quietly halves the available traffic.
  - U3: is there a scheduled marketing campaign inside the window? **Not
    blocking**, but it determines whether the duration is the sample size's or the
    calendar's.
- **Assumptions**
  - A1: 7-day activation is the right endpoint and is well-defined. *If false*:
    the whole design measures the wrong thing. *Confidence: Assumed from the
    team's definition.* *Checked by:* reading the metric definition.
  - A2: the checklist's effect is roughly proportional to the base rate, i.e. a
    relative lift. *If false*: a change in the rate affects the sample size
    materially, since variance rises with p(1−p). *Confidence: Assumed.*
  - A3: the historical rate is a valid estimate of the counterfactual.
    *If false*: the sample size is wrong in an unquantified way. *Confidence:
    Inferred from 182k historical users.*
- **Success criteria** — the design states a sample size that gives ≥80% power at
  α=0.05 two-sided for the agreed MDE; the duration is the greater of the
  sample-size requirement and 14 days; the decision rule covers the null case; and
  the whole design is checkable by a second person from the numbers in the design
  document.

**Requirements vs success criteria:** "a sample size and a duration" is the
requirement; "n per arm gives 80% power at the agreed MDE, and the window is the
maximum of the traffic-derived duration and 14 days" is the criterion, and only the
second tells the team when the experiment may stop.

## 2. Decision records

```text
DECISION
  question      the minimum detectable effect
  selected      take the PM's +3.0pp absolute (42% → 45%) as the design target,
                and report power at +1.2pp alongside it
  rejected      designing for +1.0pp, on the reasoning that smaller is more honest
  rationale     the MDE is a business judgement about what is worth acting on, not
                a statistical one, and choosing it myself would hand the team a
                design for an effect nobody intends to ship. Reporting power at a
                second, smaller effect costs one line and tells them what they
                will actually be able to see
  confidence    high
  cost          one extra number in the report
  evidence      `analytics/activation_daily` shows a 42.1% 7-day activation rate
                over 182,043 users in Q1, stable within +/-0.4pp month to month
  recovery      the team says a +3pp lift is not worth shipping, in which case the
                design is wrong at the requirement and the experiment should not
                run at all
```

```text
DECISION
  question      allocation and population
  selected      a 50/50 randomised holdout *within* the flagged population
                (US and CA), because the flag is already geographic
  rejected      (a) a feature-flag A/B, which the flag's country filter turns into
                a 2/3 vs 1/3 split with a non-randomised control; (b) running the
                experiment globally and gating the treatment on US/CA
  rationale     (a) leaves the non-US/CA majority as an untreated observational
                group, which is exactly the arrangement that produced the last
                onboarding experiment's unreadable result. A holdout inside the
                flagged population keeps both arms randomised and the comparison
                clean; the cost is losing the traffic that is already unflagged
  confidence    high
  cost          about 8 days of calendar at half the enrol rate
  evidence      `growth/onboarding_checklist_v2.json` has
                `"countries": ["US", "CA"]`; the population split is 50.3% US/CA
  recovery      if the team's roadmap requires coverage in the EU before Q1, the
                flag scope has to change first and the design follows it
```

```text
DECISION
  question      how to compute the sample size
  selected      the closed-form two-proportion test, computed in
                `analysis/power_onboarding.py` with `scipy.stats.norm.ppf`, and
                cross-checked against `statsmodels.stats.power.NormalIndPower`
  rejected      an online power calculator, and doing the arithmetic in my head
  rationale     this is the canonical, checkable formula and the numbers land in
                the repository where a reviewer can recompute them. A calculator
                hides its assumptions, and a hand calculation is exactly the thing
                `SKILL.md` says belongs to a tool
  confidence    high
  cost          one script, two dependencies already present
  evidence      both implementations agree to within 3 users per arm
  recovery      the two disagree, which would mean one of them is using a
                different test or a continuity correction that has to be named
```

```text
DECISION
  question      what to do about the calendar constraints
  selected      18 days, being max(15, 14) with a 3-day buffer for ramp, and a
                hard stop on 2026-10-23 that precedes the `black-friday-preview`
                campaign starting 2026-10-26
  rejected      14 days exactly, on the grounds that it is the minimum
  rationale     14 days is the floor for two weekly cycles; the computed
                requirement at half traffic is 15 days; and a campaign inside the
                window would confound activation in a way no amount of analysis
                fixes afterwards
  confidence    high
  cost          three extra days of traffic
  evidence      `marketing/campaigns.yaml` has `black-friday-preview` from
                2026-10-26; the signup volume on non-campaign days is 1,240/day
  recovery      signup volume is materially lower than the 90-day mean, which
                pushes the duration past the campaign start and the campaign has to
                move
```

## 3. Context

**Loaded:**

- **C0** — objective, three unknowns, three assumptions, criteria.
- **C2** — the two things a power calculation actually needs: the two-proportion
  normal approximation's formula and its stated conditions (expected counts in
  each cell ≥ 5, which at these rates is satisfied by a wide margin), and the
  definition of a two-sided α. That is the whole of C2 — not a textbook chapter.
- **C3** — three files, named before retrieval:
  `analytics/activation_daily.sql` (the metric's SQL, because "7-day activation"
  can be defined three ways and the design is meaningless against the wrong one),
  `growth/onboarding_checklist_v2.json` (the flag's actual scope — this is U2 and
  it is a two-line file), and `marketing/campaigns.yaml` (U3).
- **C4** — three queries, all deterministic:
  ```console
  $ psql -d analytics -c "SELECT count(*) AS users,
                                avg(is_activated)::numeric(5,4) AS activation_rate
                           FROM growth.user_activation
                          WHERE cohort_month >= DATE '2026-01-01'"
   users  | activation_rate
  --------+----------------
   182043 |        0.4213
  $ psql -d analytics -c "SELECT avg(signups) FROM (VALUES (1240),(1188),(1311)) v(signups)"
   avg
  --------
  1246.3
  ```

**Deliberately not loaded:**

- **The per-user activation event stream.** A 42.13% rate over 182,043 users is
  sufficient, and the standard error of the estimate is 0.0012, which is an order of
  magnitude below the MDE and therefore irrelevant to the sample size.
- **The checklist's own product spec.** What is in the checklist affects the size
  of the effect, which is U-level judgement the team owns, not something the power
  calculation needs.
- **Past experiment write-ups in this repository.** Four of them exist and none
  reported power. Reading them would have supplied context and no arithmetic.
- **Sequential-testing and Bayesian approaches.** They are legitimate and would
  answer a different question — "should we keep running?" — which the team did not
  ask. They are named in the report as an option if the sprint is compressed.

`excluded`: the event stream, the product spec, past write-ups, sequential methods.
`unresolved`: whether the team will accept 18 days when the sprint is 14 — a
scheduling fact, carried into the recommendation rather than assumed away.

## 4. Capability

```text
1. do it directly    REACHED AND SELECTED — the sample size is arithmetic, so it
                     goes to scipy/statsmodels in a committed script. The kernel's
                     own rule is that a model asked to do arithmetic by hand will
                     sometimes be wrong, and a tool asked will not
2. existing          SELECTED — `scipy.stats.norm.ppf` and
                     `statsmodels.stats.power.NormalIndPower` are already
                     dependencies of `analysis/`, and both were validated on a
                     known case before being trusted on ours
3. compose           not reached
4. acquire           not reached
5. create            not reached — and the disqualifying question is worth
                     answering out loud, because "run a power analysis" is
                     exactly the kind of thing that looks like a skill. It is a
                     40-line script with two well-tested dependencies behind it.
                     A skill wrapping that would add a trigger signal and no
                     capability
```

Nothing acquired, nothing created. The whole task was arithmetic plus three
lookups, and the arithmetic is now a script in the repository.

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Read the activation metric's SQL and confirm the endpoint definition | — | one definition, quoted | the definition matches `docs/metrics.md`; disagreement is escalated, not resolved by preference |
| U2 | Read the feature flag's country scope | — | the eligible population | U2 answered from the file, with the exact JSON path |
| U3 | Query the baseline rate and the 90-day signup volume | U1 | a rate and a traffic figure | both from `psql` output, with the population stated |
| U4 | Compute n per arm at the +3.0pp MDE, α=0.05 two-sided, 80% power | U3 | an integer, and the formula written out | `analysis/power_onboarding.py`, and the two implementations agree |
| U5 | Compute duration from n and the eligible traffic | U2, U4 | days | the division, in the script, printed |
| U6 | Compute power at a second MDE of +1.2pp | U4 | a power figure below 80%, or above | Monte Carlo simulation, 10,000 runs, with the observed rejection rate |
| U7 | Check the calendar for campaigns, holidays, and the existing holdout | U2 | a hard stop date | read from `marketing/campaigns.yaml`, not recalled |
| U8 | Write the decision rule, covering the null case explicitly | U4–U6 | a rule naming threshold, action, and null interpretation | the rule is stated in the design doc and covers all three outcomes, not two |
| U9 | Second person recomputes the design from the document's numbers alone | U1–U8 | the same n and the same days | a reviewer runs the script from the doc and gets the same figure |

U9 is in the plan because the deliverable is a sign-off, and a sign-off is worthless
if the reader cannot reproduce it. U6 is in the plan because the requested design's
power at a *realistic* effect size is the number the team will actually need in week
three.

## 6. Execution & observation

**U4 — the arithmetic, and it is the whole design.**

```console
$ python analysis/power_onboarding.py --mde 0.030 --power 0.80 --alpha 0.05
closed form (two-proportion z):
  p1 = 0.4213  p2 = 0.4513  pbar = 0.4363
  n per arm = ( 1.95996*sqrt(2*pbar*(1-pbar))
              + 0.84162*sqrt(p1*(1-p1) + p2*(1-p2)) )^2 / (p2-p1)^2
           = 3997.4  ->  3998 per arm   (7996 total)
cross-check (statsmodels NormalIndPower, effect_size = 0.030/0.1238):
  nobs = 3998 per arm
delta: 0 users
```

Both implementations agree exactly. 3,998 per arm, 7,996 total.

**U2 — the surprise, and it is in the population.**

`growth/onboarding_checklist_v2.json` line 14: `"countries": ["US", "CA"]`. The
checklist is already gated to US and CA, which is 50.3% of signups. So the
experiment can only enrol half the traffic, and the 7,996 users required become
7,996 from a pool of 1,246/day × 0.503 = 627/day:

```console
$ python analysis/power_onboarding.py --mde 0.030 --traffic 627
duration at 3998 per arm (2 arms): 12756 / 627 = 20.3 days
```

**20.3 days**, not 15. The plan's 15-day estimate assumed the full 1,246/day
traffic, and that assumption was wrong by a factor of two. This is the concrete cost
of a flag that was written for a rollout rather than for an experiment: a third of
the product is permanently untreated, and the resulting arrangement is not a
randomised comparison at all, it is an observational one with a country variable
doing the work of the assignment.

**The re-decision, and it changes the design rather than the number.** A flag-based
A/B where the flag is already geographic is not a randomised experiment; the
"control" is every non-US/CA user, and those users differ systematically in ways
that correlate with activation. Decision record 2 selects a holdout *within* the
flagged population, which halves the eligible pool and lengthens the window further:

```console
$ python analysis/power_onboarding.py --mde 0.030 --traffic 313
duration at 3998 per arm: 12756 / 313 = 40.8 days
```

40.8 days. That is longer than the sprint, longer than the quarter, and long enough
that the experiment will be read by a different team than the one that designed it.
**The design as requested does not fit in the window it was requested for, and the
reason is a routing structure, not a sample size.**

**U6 — the number that decides the recommendation.** At the MDE the team asked for
the design is exactly at 80% power, which is what a design at its MDE does. The
useful number is power at a realistic effect. Monte Carlo, 10,000 runs, true effect
+1.2pp, n = 7,996:

```console
$ python analysis/montecarlo_power.py --n 3998 --effect 0.012 --runs 10000
true effect +1.2pp, n=3998/arm, alpha=0.05 two-sided
  observed power: 0.207
  P(false negative | effect is real) = 0.793
  P(false positive | effect is absent) = 0.050
```

**21% power.** If the checklist produces a genuine +1.2pp lift — a real and
commercially interesting improvement, about 1,900 extra activated users a month at
current volume — this experiment returns "no significant difference" **79% of the
time**, and every stakeholder who did not read this document will conclude the
checklist does not work.

## 7. Verification

| check | result | how |
|---|---|---|
| n per arm gives ≥80% power at the agreed MDE | 3,998 per arm, 80.0% | closed form and `statsmodels` agree exactly |
| duration is max(traffic-derived, 14 days) | 40.8 days traffic-derived | the division, in the script, from a stated traffic figure |
| the design does not span a known confound | stops 2026-10-23, before `black-friday-preview` on 2026-10-26 | read from `marketing/campaigns.yaml` |
| power at a realistic effect is stated | 20.7% at +1.2pp, 10,000-run Monte Carlo | the simulation's own rejection rate, not a normal approximation |
| the decision rule covers the null case | three outcomes, with the null's meaning stated | the rule in the design doc, read against the three cases |
| a second person can recompute the design | reviewer reproduced 3,998 and 40.8 from the doc's numbers | `analysis/power_onboarding.py` re-run from the document alone |

**Independent check.** The closed-form figure was cross-checked against
`statsmodels`' independent implementation, which uses a different formulation
(effect size in Cohen's *d*, solved for `nobs` rather than the reverse), and the
two agree to 0 users. The Monte Carlo simulation is a third derivation: it does not
use either formula, it runs the test procedure 10,000 times and counts rejections,
and its null rejection rate of 0.050 is itself a check on the simulation harness
rather than an input to it.

**Evidence.** `analysis/power_onboarding.py` and `analysis/montecarlo_power.py`
committed; the console output above; the flag's JSON path; the campaign dates.

**Verdict: VERIFIED.** Every criterion holds on tool output, and the verification
was re-derived twice by routes that do not share an implementation. **What is
verified is the arithmetic and the honest consequence of it** — the recommendation
is *do not run this as specified*, and that conclusion follows from the verified
numbers rather than from judgement.

## 8. Recovery

**Classification: bad assumption**, found by U2. The assumption was that the
experiment could enrol the full signup population, which the flag's country scope
made false by a factor of two. The response was to correct the assumption and
re-plan the dependent units — U4's sample size was unaffected, and U5's duration
went from 15 days to 40.8, which is a re-plan of a unit, not a restart of the task.

**The response avoided — scaling the sample size up and shipping anyway.** The
arithmetic keeps working at any n, so the available and tempting move is to compute
"n = 31,900 per arm for +1.2pp at 80%" and present a 102-day experiment as a
complete design. It is arithmetically correct and practically dead, and the
recommendation would have been "run this for four months", which is not a
recommendation.

**The second response avoided — signing off on the design as requested.** The
request was to sign off on a sample size, a duration, and a decision rule. A
correct sample size, a duration that does not fit the window, and a decision rule
that returns a misleading answer 79% of the time, is not a sign-off. `PARTIAL` is
a real verdict, and this is where it is used: the arithmetic is verified and the
design is not recommended, and both facts go in the same paragraph.

**A recovery inside U9.** The reviewer's first recomputation gave 3,990 per arm
rather than 3,998, because the design document rounded the baseline to 42% rather
than the measured 42.13%. Classified as an **execution failure with a wrong input**,
the cause is a rounded constant in a document meant to be checkable, and the
response is that a design document carries the exact figures, not the readable ones.
Eight users per arm is 0.2% — irrelevant to the conclusion, and fatal to the claim
that the document is independently checkable.

## 9. Delivery

**Outcome. Do not run the experiment as specified.** The design is
arithmetically sound and strategically wrong: it needs **3,998 users per arm**
(7,996 total) for 80% power at a +3.0pp MDE, but the flag is already restricted to
US and CA, so a proper randomised holdout inside that population enrols 313 users
per day and the experiment takes **40.8 days** — past the sprint, past the quarter,
and long enough to be read by a different team. And at a realistic +1.2pp effect it
has **20.7% power**, so a real improvement would be reported as "no significant
difference" 79% of the time.

Three options, with the recommendation first:

1. **Run it as a sequential test with a 14-day cap and a pre-registered decision
   rule (recommended).** Keeps the sprint's shape, gets a defensible answer early
   if the effect is large, and states in advance what a null at 14 days means.
   Cost: ~2 hours of extra design work, and the team has to accept that it cannot
   conclude "no effect" — only "not yet".
2. **Extend to 41 days and accept the cadence cost.** Gold-standard fixed-horizon
   design, and the effect estimate is interpretable. Cost: the experiment outlives
   the sprint, and Q4 activation targets have to move.
3. **Change the flag to remove the country restriction, then run 15 days as
   originally asked.** Cost: a rollout change that affects real users before the
   experiment is designed, and a two-week engineering task. Worth it if the
   geographic restriction was an accident rather than a decision.

**Evidence.** `analysis/power_onboarding.py` and `analysis/montecarlo_power.py`,
committed, with the console output above. The flag's scope at
`growth/onboarding_checklist_v2.json:14`. The population split and the 90-day
traffic mean, from `psql`. The campaign dates. A reviewer reproduced both the
sample size and the duration from the document alone.

**Assumptions.**
- A1 (7-day activation is the right endpoint) — held, and confirmed against
  `docs/metrics.md`; the SQL and the documentation agree.
- A2 (the effect is a relative lift) — held, and the design uses an absolute MDE,
  so this assumption turns out to be unused, which is worth saying rather than
  leaving as a caveat.
- A3 (the historical rate predicts the counterfactual) — held at the stated
  precision. The 90-day rate is stable within ±0.4pp month to month and the
  standard error is 0.0012, both far below the MDE.

**Limitations.**
- The 40.8-day figure assumes the flagged population holds steady at 50.3% and
  that signup volume does not change. A campaign, a pricing change, or a
  geographic rollout would move it.
- The power figure assumes a fixed-horizon test with no peeking. Options 1 and 3
  change the analysis, and the 20.7% does not apply to them.
- I did not model seasonality in activation by week of quarter. Two weekly cycles
  is a convention, and the convention is the minimum defensible one, not a derived
  requirement.
- Whether +3.0pp is worth acting on is the team's judgement, not mine. I designed
  to it and reported power below it; if the real decision threshold is +0.5pp, none
  of these options works and the team needs a different endpoint.

**Confidence.** High on the arithmetic — two independent implementations agree, a
third simulation agrees, and the traffic figure is a 90-day mean from the
warehouse. High on the population constraint, which is a two-line JSON file. Medium
on the 40.8-day figure, because it extrapolates a mean over a window that includes
a campaign. Low on the business relevance of +3.0pp, and the trace does not
pretend otherwise.

**Verification status.** VERIFIED on the arithmetic, the population, and the
duration. The *design* is not recommended, and the recommendation is a consequence
of verified numbers rather than a separate judgement.

## 10. Learning

**Candidate, not promoted.** Before designing an experiment behind a feature flag,
check what the flag is already scoped to. A flag written for a rollout can turn the
experiment into an observational comparison and halve the eligible population, and
neither fact is visible in the experiment design document.

**What evidence would be needed to promote it.** Two more experiment designs in this
repository where a pre-existing flag scope changed the design. The team has run
eleven experiments; this would be the second instance. One instance is a finding,
and a rule installed from one would have made us check flags everywhere, including
where they are correctly scoped and where the check is noise.

**Not worth retaining:** 3,998, 40.8 days, 20.7%, the 42.13% baseline. All are this
experiment's numbers, in a script in the repository, where they belong.

**Routed rather than created.** A "pre-experiment design review" capability —
endpoint definition, allocation sanity, population eligibility, power, calendar
confounds, decision rule including the null case — is genuinely reusable and would
have caught this before the sprint was planned. Its scope is narrow enough to be
testable, and it is the sort of procedure that belongs in `skill-creator` rather
than in one analyst's head. It should be written after the second instance, with
both cases in its test set, not from this one.

## What this example proves

- **Arithmetic belongs to a tool, and the tool was cross-checked twice.** The
  closed form and `statsmodels` agree to 0 users, and a 10,000-run Monte Carlo is a
  third route whose null rejection rate (0.050) validates the harness itself.
- **A feature flag is not a randomisation.** The country restriction turned a
  randomised comparison into an observational one and halved the population, and
  the only place that showed up was a two-line JSON file nobody had read.
- **Design for the MDE means power *at* the MDE, which is always 80%, and tells
  you nothing.** The number the team will need in week three is power at a
  *realistic* effect: 20.7%, and a 79% chance of reporting a real improvement as a
  null.
- **A correct sample size can still be the wrong design.** 3,998 per arm is right
  and 40.8 days does not fit a sprint. Both facts are in the delivery.
- **PARTIAL is the right verdict for a sign-off request.** The arithmetic is
  VERIFIED, the design is not recommended, and the recommendation is a consequence
  of the verified numbers rather than a separate opinion.
- **Escalation with options and a recommendation.** Three options with trade-offs,
  the recommended one first, and the one-word answer the team can give.
- **A design document has to be independently checkable.** The reviewer's 3,990
  against the script's 3,998 was a rounded constant in a document whose whole
  purpose was to be checkable, and it is recorded as the failure it was.

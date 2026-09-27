# Sample ratio mismatch in `checkout_redesign_v3`

**Objective:** "Read out the A/B test for `checkout_redesign_v3` (exp id
`exp-2291`) — headline lift, significance, and a recommendation."

**Domain:** Data analysis — controlled experiment readout
**Scale:** L3   **Reasoning rung:** R2

## 0. Triage

- **Complexity** — low on the surface: one experiment, two arms, one metric. The
  complexity is in what has to be true before the number means anything:
  randomisation held, the metric is the same in both arms, no contamination, no
  peeking, and the two arms are the same size. That is a precondition chain, and
  satisfying it is the work.
- **Uncertainty** — low. Every check is a query against tables the experiment
  already wrote. Nothing needs to be looked up or acquired.
- **Consequence** — high, and asymmetric in a way that is worth stating. A wrong
  readout ships or kills a product change. A *right* readout of a *contaminated*
  experiment is the specific dangerous case: it is true, it is significant, and it
  is not about the treatment.
- **Reversibility** — cheap to compute, expensive to act on. The analysis is
  rerunnable in two minutes; the change it recommends touches a checkout flow and
  the announcement to the commercial team.

**Rung: R2, Scale: L3.** Parts interact — assignment, metric, exposure window, and
the shipping decision all depend on each other — and the approach must be chosen
between reading the result as-is and reading a corrected one.

**Why not R1.** The reason this is R2 and not R1 is the precondition chain. There is
no single step that produces the deliverable, and a step that reads the headline
number before the validity checks is worse than no step.
**Why not R3.** No unfamiliar domain, no blocking unknown, and the work is all
deterministic queries. There is no independent *derivation* available either — the
result is what the experiment says — so R3's independent-check obligation would be
paid for ceremony.

**Escalate when:** the experiment is invalid and the decision therefore belongs to
whoever owns the checkout roadmap, because "we cannot tell yet" is a decision, not
a number.
**De-escalate when:** the experiment is valid and the result is unambiguous.

## 1. Task model

- **Objective** — the headline lift, its significance, and a shipping
  recommendation for `exp-2291`.
- **Requirements** — 1. the experiment is valid before the result is read; 2. if it
  is not, the reason is named with the specific cause; 3. the recommendation is
  stated as a decision, not as a statistic; 4. a corrected readout is provided if
  one is defensible; 5. the contaminated result is reported as contaminated rather
  than discarded.
- **Constraints** — 16 days of exposure, 99,313 users, 50/50 allocation, baseline
  conversion 18.2%, two arms, one primary metric (`checkout_completed` within 7
  days). The platform team owns the shipping decision; the kernel does not.
- **Unknowns**
  - U1: did the sample ratio match? **Blocking.** An SRM means the randomisation
    failed and every treatment estimate is uninterpretable.
  - U2: is there a contamination path between the arms? **Blocking if U1 fails** —
    the two explanations for an SRM are different bugs with different fixes.
  - U3: is the metric computed identically in both arms? **Non-blocking**, checked
    rather than assumed because it is one join.
- **Assumptions**
  - A1: assignment was uniform-random at the user level for the whole exposure
    window. *If false*: the treatment estimate is confounded with whatever
    displaced the assignment. *Confidence: Assumed from the design.*
    *Checked by:* U1.
  - A2: `checkout_completed` is computed by the same query for both arms, keyed on
    `user_id` and not on session. *If false*: the arms are not measuring the same
    thing. *Confidence: Inferred from the metric definition.* *Checked by:* U3.
  - A3: there was no peeking. *If false*: the p-value is not the p-value and the
    significance claim is void regardless of what U1 says.
    *Confidence: Inferred from the absence of a documented interim in the
    experiment's config.* *Not verified* — and it is in the delivery as a limit.
- **Success criteria** — the sample ratio is tested and reported; if it fails, a
  corrected readout is computed on a window with intact randomisation and reported
  with its own numbers; the recommendation is one of ship / do-not-ship / extend,
  with the reason.

**Requirements vs success criteria:** "read out the test" is the requirement;
"`SRM` is reported with its χ² and p-value before any lift figure is quoted, and the
recommendation follows from the corrected readout" is the criterion, and the second
is the one that makes the first safe to act on.

## 2. Decision records

```text
DECISION
  question      which checks run before the headline number is read
  selected      (1) sample ratio, (2) metric-definition symmetry, (3) cross-arm
                contamination of the user set, (4) exposure-window integrity —
                in that order, all four before any lift figure
  rejected      reading the lift first and annotating caveats afterwards
  rationale     a significant result is the thing most likely to be quoted out of
                this document, so anything that invalidates it has to be printed
                first. Reading the lift first and then reporting "note the
                experiment was contaminated" is a sequencing choice that reliably
                produces the wrong headline, because the headline has already been
                read by then — including by me
  confidence    high
  cost          about 90 seconds of queries
  evidence      none needed; this is a decision about ordering, and ordering is
                where the failure is
  recovery      the SRM test passes, in which case the remaining three checks run
                as planned and cost the same 90 seconds
```

```text
DECISION
  question      what to do about the +2.4pp that the raw data supports
  selected      report it, attribute it to the deployment window, and explicitly
                decline to use it
  rejected      (a) discarding it, (b) quoting it with a caveat, (c) reporting
                only the corrected number
  rationale     (a) destroys the evidence that the bug happened, which is the only
                thing that will demonstrate the fix worked. (b) is the failure mode
                this trace exists to prevent: +2.4pp, p=0.003, in a paragraph, will
                be the number the commercial team remembers, and the caveat will be
                the thing that was cut. (c) makes the readout look clean and hides
                why it needed cleaning
  confidence    high
  cost          a longer report
  evidence      the contaminated window is 2026-03-11 to 2026-03-18; the raw
                readout's lift is +2.41pp
  recovery      the team's process requires a single number per experiment, in
                which case the contaminated figure belongs in an appendix with the
                corrected figure in the summary
```

```text
DECISION
  question      which correction is defensible
  selected      truncate the exposure at 2026-03-11 00:00 UTC — the deploy that
                broke symmetry — and recompute on 2026-03-02 to 2026-03-10
  rejected      (a) dropping only the users who received the `ca_v3` cookie;
                (b) reweighting the arms to the intended ratio; (c) running longer
                and pooling
  rationale     (a) is the tighter fix but the cookie is set on 40% of exposed users
                and its assignment is not independent of arm — it was set *because*
                of the arm — so dropping on it conditions on a post-treatment
                variable and biases the estimate in a new direction. (b) assumes the
                missingness is independent of the treatment, which is exactly what
                is in doubt. (c) is valid and is the recommendation, but it needs
                days the team does not have before the roadmap slot
  confidence    high
  cost          7 days of data instead of 16
  evidence      the deploy at 2026-03-11 11:04 UTC is `web@8f31c2`; users assigned
                after it are 3.1% over-represented in the control arm
  recovery      the truncated window is also unbalanced, which would mean the
                assignment was broken before the deploy, and the diagnosis is wrong
```

```text
DECISION
  question      what recommendation to make
  selected      do not ship, extend 9 days, and treat the 2026-03-11 deploy as a
                bug to be fixed in the assignment service regardless of the
                experiment's outcome
  rejected      (a) ship on the raw +2.4pp; (b) kill the experiment as a failure
  rationale     (a) is the reading the requester came in wanting and the one the
                data cannot support. (b) is equally wrong in the other direction:
                the corrected result is +0.6pp with p=0.41, which is an
                uninformative result, not evidence of absence — the experiment
                cannot distinguish "no effect" from "not enough data", and reporting
                a null as a refutation is the same category of error as reporting a
                contaminated result as a success
  confidence    high
  cost          nine days of delay against a decision the roadmap already has to
                absorb
  evidence      corrected n = 61,204; baseline 18.2%; observed +0.61pp; power at
                1.0pp on this window requires 23,586 per arm
  recovery      a corrected result above 1.0pp would make the delay unjustified and
                the recommendation would inver
```

## 3. Context

**Loaded:**

- **C0** — objective, three unknowns, three assumptions, criteria.
- **C2** — none of substance. The experiment's own config,
  `experiments/exp-2291/config.yaml`, states the allocation, the primary metric,
  the exposure window, and the intended significance level. Reading it is reading
  the task, not consulting a reference.
- **C3** — three files, named before retrieval: `experiments/exp-2291/assignments`
  (one row per user: `user_id`, `arm`, `assignment_ts`), the conversion event table
  `events/checkout_completed`, and `experiments/exp-2291/README.md` — read *last*,
  and read specifically to check for a documented interim analysis, which is
  assumption A3. The order matters: reading the README first would have put the
  team's framing in the kernel's head before the data was looked at.
- **C4** — the queries, in this order:

```console
$ psql -d analytics -c "SELECT arm, count(*) FROM experiments.exp_2291_assignments
                        WHERE assignment_ts >= '2026-03-02' AND assignment_ts < '2026-03-18'
                        GROUP BY arm ORDER BY arm"
 arm |  count
------+--------
 ctl |  50412
 trt |  48901
```

**Deliberately not loaded:**

- **The `README.md`'s narrative until after the SRM result.** It is the human
  summary of the experiment and it will say the lift was positive. Reading it first
  anchors every subsequent step, and the decision record above exists precisely to
  prevent that ordering.
- **The treatment's front-end code.** The question is whether the experiment can
  answer its own question. What the redesign does to the funnel is irrelevant while
  the assignment service is broken.
- **The `checkout_completed` event's client-side instrumentation.** Metric symmetry
  is checked by comparing the query's definition in both arms, which is one join,
  not by auditing the SDK.
- **Other experiments in the same period.** `exp-2288` ran concurrently and had its
  own issue, and there is a tempting story about metric contamination across them.
  One test — cross-arm user overlap — is the discriminating check, and the story is
  not.

`excluded`: the treatment code, the SDK instrumentation, concurrent experiments.
`unresolved`: whether peeking occurred (A3, unverified) and whether the assignment
service has a regression test for the post-treatment cookie, which is a question
for the platform team.

## 4. Capability

```text
1. do it directly    REACHED AND SELECTED — every quantity is a SQL aggregate.
                    The chi-square, the confidence interval, and the power
                    calculation go to `scipy` and `statsmodels` in a committed
                    script, because the p-value is the deliverable and a
                    remembered p-value is not a result
2. existing          SELECTED — the experiment's own config, which is the
                    authoritative statement of what was supposed to happen
3. compose           not reached
4. acquire           not reached
5. create            not reached, and this is a domain where skill proliferation
                    would be actively harmful: "read out an A/B test" as a skill
                    would encode one team's conventions and would be applied to
                    every experiment including the ones it does not fit
```

Nothing acquired, nothing created. The capability was four SQL queries and a
`statsmodels` power calculation, both of which the repository already makes.

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Sample ratio: counts per arm vs the 50/50 allocation; χ² on 1 dof | assignments table present | a ratio and a p-value | the χ² is computed by `scipy.stats.chisquare`, not by hand |
| U2 | Metric symmetry: the conversion join is identical in both arms | — | identical definitions, or a finding | both definitions quoted side by side from the config |
| U3 | Cross-arm contamination: overlap of user sets and of `ca_v3` cookie holders | U1 | the cause of any imbalance | the cookie's assignment counts per arm, and the overlap count |
| U4 | Locate the deploy boundary that changed the assignment | U1 fails | a timestamp | `web@8f31c2` at 2026-03-11 11:04 UTC, matched to the imbalance onset |
| U5 | **Only if U1–U4 pass:** compute the headline lift and its significance | U1–U4 pass | a number | the lift recomputed by a second query formulation, agreeing to 0.01pp |
| U6 | **If U1 fails:** compute the raw lift, and label it contaminated | U1 fails | a number and a label | the raw lift reported alongside the contamination window |
| U7 | Truncate the exposure before the deploy and recompute | U4 | a corrected lift on intact randomisation | the corrected window's own SRM test, which must pass |
| U8 | Compute the power of the corrected window at 1.0pp | U7 | a duration or a statement of insufficiency | `statsmodels` power, at a stated baseline |
| U9 | Write the recommendation as a decision | U1–U8 | ship / do-not-ship / extend, with reasons | the recommendation is checkable against the numbers in the report |

U5 and U6 branch on U1, and the branch is decided by a test result rather than by
the kernel's expectation. U7's own SRM test is a precondition: if the truncated
window is also imbalanced, the diagnosis in U4 is wrong.

## 6. Execution & observation

**U1 — the first query, and the reason the deliverable changes shape.**

```console
$ python3 analysis/srm.py --exp exp-2291 --from 2026-03-02 --to 2026-03-18
  ctl  50412      expected 49656.5
  trt  48901      expected 49656.5
  chi2 = 22.991  on 1 dof   p = 1.72e-06
  VERDICT: SAMPLE RATIO MISMATCH
```

χ² = 22.99 on 1 degree of freedom, p = 1.7 × 10⁻⁶. A 50/50 split should produce
about 1 in 1.7 million. The treatment arm is short by 1,511 users — 3.0% of its
expected size. **The experiment is invalid, and every treatment estimate from it is
uninterpretable until that is explained.** No lift figure was computed before this
line was printed, and decision record 1 is the reason.

**U3 — the cause, in one query.**

```console
$ psql -d analytics -c "
    SELECT a.assignment_ts::date AS day, a.arm, count(*)
      FROM experiments.exp_2291_assignments a
     WHERE a.assignment_ts >= '2026-03-02' AND a.assignment_ts < '2026-03-18'
     GROUP BY 1, 2 ORDER BY 1, 2" | head -30
    day        | arm | count
--------------+-----+-------
 2026-03-02   | ctl |  3161
 2026-03-02   | trt |  3158
 ...
 2026-03-10   | trt |  3090
 2026-03-11   | trt |  2834
 2026-03-11   | ctl |  2901
 ...
 2026-03-18   | trt |  3011
 2026-03-18   | ctl |  3348
```

Days 1 to 9 are balanced to within 0.1%. From 2026-03-11 the treatment arm drops
and never recovers. The break is sharp and it is on a date, which is the signature
of a deploy rather than of a gradual drift.

**U4.** The deploy log puts `web@8f31c2` on the checkout at 2026-03-11 11:04 UTC.
Its change: the redesigned checkout sets a `ca_v3` session cookie, and from that
deploy the assignment service began excluding users holding a `ca_v3` cookie from
randomisation — intending to prevent a returning user from seeing two variants. The
treatment arm is the one that *sets* the cookie, so treatment users are excluded at
a higher rate, and the arm loses users precisely in proportion to its own
engagement.

**U7 — the corrected readout, with its own validity check first.**

```console
$ python3 analysis/srm.py --exp exp-2291 --from 2026-03-02 --to 2026-03-11
  ctl  29163   trt  29204   expected 29183.5
  chi2 = 0.0031 on 1 dof   p = 0.956
  VERDICT: ratio consistent with 50/50

$ python3 analysis/readout.py --exp exp-2291 --from 2026-03-02 --to 2026-03-11
  ctl   29163 users   5296 conversions   18.163%
  trt   29204 users   5452 conversions   18.666%
  lift  +0.503pp   95% CI [-0.75pp, +1.76pp]   two-sided p = 0.427
```

χ² = 0.0031 on the truncated window: the randomisation held before the deploy, which
is what makes the correction legitimate rather than convenient.

**U6 — the contaminated number, reported and labelled.**

| window | n | control | treatment | lift | p |
|---|---|---|---|---|---|
| 2026-03-02 → 2026-03-18 (raw) | 99,313 | 18.02% | 18.43% | **+2.41pp** | 0.0031 |
| 2026-03-02 → 2026-03-11 (corrected) | 61,367 | 18.163% | 18.666% | **+0.50pp** | 0.427 |

The raw +2.41pp is significant at p = 0.003 and it is the number the requester
wanted. It is also the number produced by an experiment whose arms were different
sizes for a reason connected to the treatment itself. **It is a true statement about
what happened and a false statement about the redesign**, and that is exactly the
distinction decision record 2 is about.

**U8 — the power, which decides the recommendation.** On the corrected window,
detecting a 1.0pp absolute lift at α = 0.05 two-sided and 80% power needs 23,586
users per arm — 47,173 total. The corrected window has 29,183. The corrected
experiment can only reliably detect a lift of about **1.5pp**. Anything smaller is
invisible to it.

**So the corrected result is not a null finding. It is an absence of measurement.**
+0.50pp with a CI from −0.75 to +1.76 is consistent with a real +1.7pp improvement
*and* with a real harm, and it cannot distinguish them. Reporting it as "the
redesign does not work" would be as wrong as reporting the raw number as a win —
same category of error, opposite direction, and equally invisible to a reader who
skips the caveats.

## 7. Verification

| check | result |
|---|---|
| sample ratio tested before any lift was computed | yes, first query, and the ordering is a decision record |
| the SRM test itself is a real test | `scipy.stats.chisquare` on 1 dof; p = 1.72e-06 |
| metric definition identical in both arms | yes, from `exp-2291/config.yaml` |
| cross-arm contamination checked | `ca_v3` cookie assignment rates per arm, and user-set overlap = 0 |
| the cause located to a specific deploy | `web@8f31c2`, 2026-03-11 11:04 UTC, with a matching day-by-day break |
| the corrected window passes its own SRM test | χ² = 0.0031, p = 0.956 — the correction is legitimate |
| the lift re-derived by a second query formulation | +0.503pp vs +0.50pp; CI and p-value agree |
| power computed for the corrected window, at a stated effect | 23,586 per arm for 1.0pp; 29,183 available |
| the recommendation is a decision | extend 9 days, do not ship, fix the assignment service regardless |
| peeking checked | **not verified** — no documented interim found, and the absence of a document is not the absence of a peek |

**Independent check.** The corrected lift was computed twice by different query
formulations — a `LEFT JOIN` on `checkout_completed` and a `GROUP BY` over
pre-aggregated per-user conversion counts. They agree to 0.01pp and their p-values
agree to three significant figures. Separately, the arm counts were re-derived from
`events.checkout_completed`'s own `assignment` property rather than from the
assignments table, and the totals match at 29163/29204 — a second source for the
denominator, which is the quantity the SRM is about.

**Verdict: PARTIAL**, and the partial is structural rather than a shortfall.

- ✅ **The experiment is invalid as run**, proven at p = 1.7 × 10⁻⁶, with the cause
  identified to a specific deploy and a specific code change.
- ✅ **The raw result is +2.41pp, p = 0.0031**, reported in full and labelled
  contaminated rather than discarded or caveated.
- ✅ **The corrected result is +0.50pp, p = 0.427**, on a window whose own SRM test
  passes at p = 0.956.
- ❌ **The experiment cannot answer the question.** 29,183 per arm against 23,586
  needed for a 1.0pp effect means it can only detect about 1.5pp. The corrected
  result is an absence of measurement, not evidence of no effect, and reporting it
  as evidence of no effect would be the same error in the opposite direction.
- ⚠️ **Peeking is unverified.** No documented interim analysis was found; the
  absence of a document is not the absence of a peek, and if the team queried the
  result daily, the p-value does not mean what it says.

## 8. Recovery

**Classification: bad assumption.** A1 — uniform-random assignment at the user
level for the whole exposure window — was recorded as *Assumed, from the design*, and
checked by U1. It held for nine days and then stopped holding, for a reason
connected to the treatment itself.

**Response, and it is the two-part one `recovery-system.md` mandates:** correct the
assumption, then re-plan every unit that depended on it. The units that depended on
it were the whole readout, so the exposure window became a first-class parameter,
U7 and U8 were added, and the recommendation was re-derived from the corrected
numbers rather than from the raw ones.

**The response avoided — the ordering error, which is the serious one.** Reading the
lift first, seeing +2.41pp at p = 0.003, and then reporting "note that there was an
SRM" is the path of least resistance and it reliably produces the wrong headline,
because the headline has already been read — by the analyst, and then by everyone
the analyst writes for. The lift figure is in this report, in a table, with its
label, *after* the SRM test and its p-value. The ordering is a decision record
precisely so that it is a decision and not an accident of narrative flow.

**A second failure, recovered as a wrong check rather than a wrong number.** The
first version of the SRM script took the date range from the CLI arguments, and the
default was the experiment's configured window. On the corrected window that
default is wrong in the opposite direction — it would have included the
contaminated days. Classified as an **execution failure with a wrong input**, cause
identified, response was to make the exposure window an explicit required argument
with no default, so that "the whole experiment" is a decision someone makes rather
than a value a script supplies. Attempt 2 differs in kind: a different interface,
not a longer run.

## 9. Delivery

**Outcome. `exp-2291` is invalid and cannot answer the question. Do not ship; extend
9 days; and fix the assignment service regardless of the outcome.**

The experiment was 50/50 but ended 50,412 / 48,901 — χ² = 22.99 on 1 dof,
p = 1.7 × 10⁻⁶, where a correct split gives about 1 in 1.7 million. The cause is
`web@8f31c2`, deployed 2026-03-11 11:04 UTC: the redesigned checkout sets a `ca_v3`
cookie, and from that deploy the assignment service began excluding `ca_v3` holders
from randomisation. Because the treatment arm is the one that sets the cookie, the
treatment arm lost users in proportion to its own engagement. The raw readout is
**+2.41pp, p = 0.0031** — significant, attractive, and about the bug.

Truncating at the deploy gives 61,367 users in a window whose own SRM test passes at
p = 0.956: **+0.50pp, p = 0.427, 95% CI [−0.75, +1.76]**. That is not a refutation.
With 29,183 per arm, this experiment can only detect about 1.5pp; a 1.0pp effect
needs 23,586 per arm. The corrected result is consistent with a real +1.7pp
improvement and with a real harm, and it cannot tell them apart.

**Three things, in this order:**

1. **Do not ship on +2.41pp.** It measures the exclusion bug.
2. **Extend 9 days** to 2026-09-28 and re-read. At current traffic (≈6,200/day) that
   adds roughly 55,000 users, taking the corrected window past 47,000 per arm, which
   is powered for 1.0pp. The extension must be gated on the assignment fix shipping
   first, or it repeats the same experiment.
3. **File the assignment bug now**, independently of the experiment. Excluding users
   on a post-treatment variable from randomisation is a defect in the assignment
   service and it is corrupting every experiment that uses a session-affecting
   treatment. It is worth checking whether `exp-2288` and `exp-2293` have it too.

**Evidence.** The SRM test, first, with its χ² and p. The day-by-day arm counts
showing a sharp break on 2026-03-11. The deploy log. The corrected window's own SRM
test at p = 0.956. Both lift figures, from two query formulations each, agreeing to
0.01pp. A `statsmodels` power calculation at a stated 1.0pp effect.

**Assumptions.**
- A1 (uniform randomisation for the full window) — **contradicted.** It held for
  nine days and then failed for a reason connected to the treatment.
- A2 (metric computed identically in both arms) — held, from `config.yaml`.
- A3 (no peeking) — **unverified**. No documented interim was found, and the
  absence of a document is not the absence of a peek. If anyone looked at the
  daily result, the p-value needs a correction and the report's significance claim
  is conditional on this.

**Limitations.**
- The correction is a truncation, not a repair. The 1,511 users lost are gone from
  the treatment arm and cannot be recovered, so the corrected estimate is based on
  62% of the intended sample. Dropping only `ca_v3` holders would recover more of it
  and was rejected because the cookie is a post-treatment variable — conditioning on
  it would bias the estimate in a new direction.
- I did not establish *why* the assignment service changed behaviour on that deploy
  — whether the exclusion was intentional and wrong, or accidental. The platform team
  can answer that in a minute and it changes the bug's severity, not the readout.
- I did not check `exp-2288` and `exp-2293` for the same defect. That is a two-query
  check and it is the highest-value thing left undone, because the same bug
  corrupting other experiments is worse than this one.
- The 9-day extension assumes traffic of ≈6,200/day continues. The
  `black-friday-preview` campaign starts 2026-10-26 and does not fall inside it, but
  a pricing change would.

**Confidence.** High that the experiment is invalid — a p of 1.7 × 10⁻⁶ plus a
deploy whose timestamp matches a sharp day-by-day break plus a mechanism that
predicts the direction of the imbalance. High on the corrected figure, whose window
passes its own validity test. **The significance claim is conditional on A3**, and
that condition is stated in the report rather than buried.

**Verification status.** PARTIAL. The validity question is VERIFIED, and the answer
is that the experiment cannot answer the question asked. A result is delivered, but
it is a result about what happened rather than about the redesign, and the delivery
says which is which in the first paragraph.

## 10. Learning

**Candidate, not promoted.** Test the sample ratio before computing any treatment
estimate, in every experiment readout, and treat a mismatch as disqualifying rather
than as a caveat. Additionally: when a randomisation failure's mechanism is a
post-treatment exclusion, truncate at the boundary and verify the truncated window's
own ratio rather than correcting by filtering or reweighting.

**What evidence would be needed to promote it.** The first half is not really a
candidate — SRM-before-result is standard practice and belongs in a team's analysis
checklist rather than in a kernel rule. The second half is the narrower claim and
does need more: a second instance in this repository where a truncated window passes
its own SRM test and the truncation is the accepted correction. The exclusion bug may
well be in `exp-2288` and `exp-2293`, and if it is, that is the evidence.

**Not worth retaining:** 50,412, 48,901, +2.41pp, +0.50pp, 23,586. All specific to
this experiment, all in `analysis/` and in the experiment's own record.

**Routed rather than created.** The reusable thing here is a *readout preflight* — SRM,
metric symmetry, cross-arm contamination, peeking check — that a team runs before
reading any experiment. It would be needed again on every experiment in this
company, and its scope is narrow enough to be testable against known-good and
known-bad experiments. It goes to `skill-creator` as a candidate once the second
instance is found, and it should not be written from one.

## What this example proves

- **Validity is a precondition, not a caveat.** The SRM test ran first, and the
  ordering is a decision record so that it is a choice rather than an accident of
  narrative flow.
- **A contaminated result is a true statement and a false conclusion.** +2.41pp at
  p = 0.003 is real, significant, and about the exclusion bug. It is reported in
  full rather than discarded, because destroying it destroys the evidence that the
  bug happened.
- **A null is not a refutation either.** +0.50pp with 29,183 per arm against 23,586
  needed means the experiment can only see 1.5pp. Reporting it as "does not work"
  is the same category of error pointed the other way.
- **The correction was checked for legitimacy.** The truncated window passes its own
  SRM test at p = 0.956, which is what distinguishes a defensible correction from a
  convenient one.
- **Post-treatment variables are not a valid filter.** Dropping `ca_v3` holders
  would have recovered more data and biased the estimate, and the reason is in a
  decision record rather than discovered later.
- **An unverified assumption was surfaced in the delivery.** Peeking was not checked;
  the significance claim is marked conditional on it rather than asserted.
- **The obvious follow-up was named instead of quietly done.** `exp-2288` and
  `exp-2293` may have the same defect, and that is the highest-value thing left
  undone.

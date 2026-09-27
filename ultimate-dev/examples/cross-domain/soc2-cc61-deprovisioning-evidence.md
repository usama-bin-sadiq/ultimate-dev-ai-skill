# Answering the auditor's CC6.1 challenge with evidence

**Objective:** "Our SOC 2 auditor flagged the CC6.1 access control claim for the Q2
2026 period. They want evidence that terminated users lose access within 24 hours
across all four production systems. I need to answer them by Friday with something
defensible."

**Domain:** Cross-domain — security engineering, audit and control testing,
sampling theory, tooling
**Scale:** L4   **Reasoning rung:** R3, with an R4 gate before anything is sent

## 0. Triage

- **Complexity** — high and genuinely multi-part. Five production systems, four of
  which have a deprovisioning path and one of which has none; a population of 38
  terminations; a control framework criterion; and an evidence artefact that has to
  survive an auditor's scrutiny.
- **Uncertainty** — medium-high, and it is spread across the parts. Whether the
  control operates as claimed is unknown and is a measurement. Whether "all four
  production systems" is the right population is a scoping question. Whether the
  evidence format satisfies the auditor is a framework question.
- **Consequence** — high, and the highest-stakes kind: an externally visible
  assertion about the effectiveness of a security control, to an auditor, with the
  company's compliance posture behind it. A false claim here is not a bug.
- **Reversibility** — none in the sense that matters. A letter to an auditor
  asserting a control is effective, once sent, is a durable record. You do not
  unsend it.

**Rung: R3, Scale: L4.** Multi-domain, unfamiliar in two of the four parts (audit
control testing and sampling), and a result that gets an independent check — which
here means re-deriving the timing from a second source per system, because the
whole deliverable is a set of durations.

**Why not R2.** Per-unit verification is not sufficient for a claim that will be
relied on by a third party. R3's independent check is the requirement, and it is
substantive: the entire deliverable is numbers about elapsed time, and each number
needs a second derivation.

**Why R4's gate, stated as a gate and not as the rung.** R4 adds a **named human
checkpoint before acting**. The work is analysis producing a draft, and that is
R3. Sending it is irreversible and externally visible, and that step gets a
checkpoint: **Dana Okonkwo, CISO and Head of Security & Compliance**, who owns the
control assertion and whose signature it carries.

**Escalate when:** the evidence shows the assertion as written is false, because
then the deliverable is not the requested one and the decision is a compliance
officer's.
**De-escalate when:** the control holds on a scoped population.

## 1. Task model

- **Objective** — a defensible, evidence-backed response to the auditor's CC6.1
  challenge, stating exactly what is true about deprovisioning and what is not.
- **Requirements** — 1. the population is confirmed and the sampling decision is
  justified; 2. every system is tested on the same basis; 3. each measurement is
  derived from a primary source and, where possible, a second; 4. the response
  states what the evidence supports and does not stretch to claim more; 5. the
  response is reviewed by the control owner before it is sent.
- **Constraints** — Q2 2026 is 1 April to 30 June; 38 terminations; five production
  systems, of which the requester says four; `internal-tools` is a legacy PHP app
  with its own user table; `tokenisation-service` is in PCI scope; the auditor wants
  a response by Friday, which is 4 days.
- **Unknowns**
  - U1: is the population all five systems or four? **Blocking** — the claim's scope
    is the claim.
  - U2: is full-population testing cheaper than sampling? **Blocking** for the
    method, and it is a question about the population size rather than about
    security.
  - U3: does each system expose a per-user access event with a timestamp we can
    correlate against the HRIS effective time? **Not blocking**, but it determines
    whether the durations are measured or estimated, and estimated durations cannot
    support an assertion.
- **Assumptions**
  - A1: the 24-hour requirement is policy, and the assertion is about *observed
    behaviour against policy*. *If false* — if the auditor wants the design rather
    than the operating evidence — the deliverable is different and the question
    should be asked. *Confidence: Assumed from the challenge wording, which asks for
    evidence of operation.*
  - A2: the HRIS `effective_at` timestamp is the reference point, not the manager's
    approval or the employee's last day. *If false*: every duration is measured
    from the wrong origin. *Confidence: Inferred; checked in U2, and the audit trail
    shows the same value in all 38 rows.
  - A3: "access" means an authenticated capability to reach a production system, not
    a session token that remains valid after revocation. *If false*: the durations
    are wrong for a subset of users. *Confidence: Assumed, and named as a scope
    limit in the response because the auditor may read it more strictly.*
- **Success criteria** — the population and sampling method are stated and
  justified; every system's duration distribution is in the response with its
  source; the response says plainly which systems meet the 24-hour requirement and
  which do not; the CISO has approved it before it is sent.

**Requirements vs success criteria:** "answer them with something defensible" is the
requirement; "five systems tested, 38 terminations, per-system elapsed-time
distributions, the assertion stated as the evidence supports it rather than as
requested, and CISO sign-off before transmission" is the criterion, and the second
is the only version of the first that survives an auditor.

## 2. Decision records

```text
DECISION
  question      how to test the control
  selected      full-population testing of all 38 terminations across all five
                systems
  rejected      attribute sampling, at 95% confidence and 5% tolerable deviation
  rationale     attribute sampling over a population of 38 requires 59 items
                (binomial, n = 1.96^2 * 0.25 / 0.05^2) — more than the population
                exists, so the sample is the census. Full testing costs 38 * 5
                systems * ~12 minutes of scripted lookups, which is machine time,
                not analyst time, because the work is a query per (user, system)
                pair. Sampling a population larger than itself is the arithmetic
                error, and it would have been made by following the framework's
                default
  confidence    high
  cost          4 hours of build, 40 minutes of run
  evidence      the population count from the HRIS table; the sampling arithmetic in
                `compliance/sampling_calc.py`
  recovery      the population is larger than stated, in which case sampling
                becomes the right answer at 200+ terminations and the plan is
                re-decided
```

```text
DECISION
  question      the population: four systems or five
  selected      five, including `internal-tools`, and the response says so
  rejected      (a) four, as the requester said; (b) five, without flagging that
                this widens the scope beyond what the auditor asked
  rationale     `internal-tools` is in production, reachable over VPN behind SSO, and
                has a `users` table with `active` flags — it is a system that
                grants access, and excluding it because the requester miscounted
                would produce a response that is defensible about four systems and
                silent about the fifth. The scope change is stated explicitly so
                the auditor can see it was deliberate
  confidence    high
  cost          the response covers a system outside the auditor's original list,
                which may itself draw a question
  evidence      `compliance/production-systems.yaml` lists five; the auditor's
                request of 2026-07-08 lists four
  recovery      the auditor confirms the fifth is out of scope, in which case its
                results are reported as supplementary
```

```text
DECISION
  question      what the response is allowed to claim
  selected      the exact wording the evidence supports, including the two systems
                that fail, and a compensating-control statement that is explicitly
                marked unverified
  rejected      (a) asserting the control is effective with a scope note; (b)
                asserting effective with an exception noted in a footnote; (c)
                declining to answer and asking for an extension
  rationale     the assertion is false for two of five systems on the data. An
                auditor who is told "effective except for these two, here is the
                distribution and here is the remediation" has a path. An auditor
                who receives "effective, scoped as discussed" learns that the
                evidence is not being read carefully, and the next question is
                worse. (c) is a week of auditor time for an answer we already have
  confidence    high
  cost          the company has a qualified opinion in the making, and the response
                is what causes it
  evidence      the measurement; 2 of 5 systems breach 24h, one of them on 31 of 38
                terminations
  recovery      the compensating control is verified before the statement is made,
                in which case the wording strengthens
```

```text
DECISION
  question      whether to verify the compensating control for internal-tools
  selected      no — report it as an unverified hypothesis with a named owner and a
                date
  rejected      asserting that the VPN and SSO gating mitigates the gap
  rationale     the mitigation is plausible and is the difference between a
                qualified opinion and a material weakness, which makes it exactly
                the claim where the temptation to overstate is strongest. Nothing
                in this run verified it: I did not test whether a deprovisioned
                Okta user can reach the app, and asserting it would be the
                confident fabrication in the one place it does the most damage
  confidence    high
  cost          the response is weaker without the mitigation claim
  evidence      no test was run; `internal-tools` is reachable over VPN and its own
                SSO layer is a separate system from Okta
  recovery      a test showing a deprovisioned user is blocked at both layers makes
                the claim supportable, and it is a one-day job
```

## 3. Context

**Loaded, per discipline, and this list is the composition:**

- **Security engineering (C3)** — five files: `compliance/production-systems.yaml`
  (the authoritative system list, which is how U1 was resolved);
  `infra/okta/scim.yaml` (the deprovisioning event and group-push configuration);
  `infra/aws-identity-center/` (the directory configuration);
  `apps/internal-tools/` (its `users` table schema and its authentication
  middleware, which is 40 lines and is what establishes that it has no
  deprovisioning hook at all).
- **Audit and control testing (C2)** — the CC6.1 criterion text and the firm's
  evidence expectations for control *operating effectiveness*, read from the
  engagement letter, not from a general framework summary. This is the C2 that
  shapes the deliverable's format, and it is the part the kernel is least familiar
  with.
- **Sampling theory (C2)** — binomial attribute sampling: the sample size formula,
  its assumptions, and the rule that a sample cannot exceed the population. Three
  lines, and the whole of U2.
- **Data engineering (C3)** — the HRIS terminations table (`hris.terminations`, 38
  rows with `effective_at`) and the five systems' access-event sources, each read
  for its timestamp semantics rather than for its content.
- **Tooling (C4)** — the measurement itself: one script, `compliance/deprovisioning_test.py`,
  which for each of the 190 (termination × system) pairs computes the elapsed time
  to the last authenticated access.
- **C5** — one lookup, the CC6.1 criterion text, because the criterion's own wording
  determines whether "all four systems" is even the right scope.

**Deliberately not loaded:**

- **The other 61 controls in the SOC 2 report.** One control is in question. Reading
  the report's other sections would tell the kernel what the auditors have already
  accepted, which is a form of anchoring on their prior conclusions rather than on
  evidence.
- **`internal-tools`' application logic beyond its auth middleware.** 40 lines of
  auth tell us whether a deprovisioning hook exists. The other 31,000 lines are a
  PHP application and bear on nothing here.
- **The Okta system log's full export.** One query per user against five systems; the
  export is 4GB and the aggregate is 190 rows.
- **The security-awareness training records, the access review evidence, and the
  other Q2 artefacts the control owner already has.** The auditor asked about one
  criterion. Assembling a broader evidence package would dilute the response.

`excluded`: 61 other controls, internal-tools' logic, the full Okta export, other
Q2 artefacts. `unresolved`: whether the compensating control holds, which is the
largest open item in the response and is reported as open.

## 4. Capability

```text
1. do it directly   REACHED AND SELECTED for the measurement — 190 elapsed-time
                    computations, a chi-square-free population count, and a
                    sampling calculation, all of which go to a script
2. existing        SELECTED — the firm's own SOC 2 evidence tooling, which has a
                    documented output format the auditor's portal accepts. Writing
                    a parallel format would have been re-implementing a
                    compliance requirement
3. compose         REACHED AND THIS IS THE RUNG — five capabilities composed:
                    IAM configuration analysis (what *should* happen), control
                    framework mapping (what the assertion must say), actuarial
                    sampling (how much to test), harness engineering (how to
                    measure), and provenance (how to cite it). Drop any one and the
                    deliverable fails a different way
4. acquire         not reached — and this is the honest result. There is no
                    "SOC 2 skill" to acquire, and if there were, it would be a
                    document, not a capability
5. create          REJECTED, and worth stating. "SOC 2 deprovisioning tester" is a
                    plausible capability and a bad action: the procedure is
                    specific to five systems with five access-log semantics, so a
                    general skill would encode this quarter's architecture. The
                    durable, reusable thing is much smaller — a population-size
                    check before choosing a sampling method — and that goes to
                    skill-creator as a candidate, scoped to "attribute sampling
                    where the population is small"
```

Four capabilities composed, one acquisition refused, one creation declined with a
reason. Note the asymmetry with a single-domain task: at no point did any one
discipline feel sufficient, and the plan would not exist without the combination.

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Confirm the system population from the authoritative list | — | five systems, with the auditor's four identified | the list vs the engagement letter, diffed and the difference named |
| U2 | Decide the testing method from the population size | U1, population count | full-population or sampling, with the arithmetic | `sampling_calc.py` prints the required sample size against the population |
| U3 | Confirm the reference timestamp and its consistency | HRIS table | one origin for all 38 | the audit trail shows `effective_at` agreeing with the approval timestamp in all 38 rows |
| U4 | Build the measurement harness: 38 terminations × 5 systems | U2, U3 | a per-pair elapsed time with a source per system | a run with zero unresolved pairs, or a stated reason for each |
| U5 | Re-derive each system's durations from a second source | U4 | agreement, or an explained disagreement | per system, the two derivations side by side |
| U6 | Test whether a deprovisioned Okta user can reach `internal-tools` | U4, authorisation to test | pass or fail | **NOT RUN** — requires a test account and security sign-off; carried as open |
| U7 | Map results to the CC6.1 criterion and draft the wording | U4, U5 | a response that claims only what the evidence supports | every claim in the draft has a table reference |
| U8 | Checkpoint: CISO review before transmission | U7 | approval, or changes | the reviewer's name and date on the draft |
| U9 | Transmit, and record what was sent | U8 | the letter in the compliance archive | the archive entry matches the approved text, byte for byte |

U6 is in the plan and is not done. It is the unit whose absence most changes what
the response can say, which is exactly why it appears in the plan rather than being
quietly dropped.

## 6. Execution & observation

**U2 — the sampling decision, which is the methodological core.**

```console
$ python3 compliance/sampling_calc.py --population 38 --confidence 0.95 \
    --tolerable-deviation 0.05
attribute sampling, 95% confidence, 5% tolerable deviation:
  required sample n = 1.96^2 * 0.25 / 0.05^2 = 384.16  -> 385
  population = 38
  n > population  =>  the sample IS the population.  Test all 38.
```

**385 required against 38 available.** Attribute sampling here degenerates to a
census, and the correct method is to say so rather than to compute a sample size,
notice it exceeds the population, and proceed anyway. The 4-day deadline and the
scripted harness are what make the census affordable: 38 × 5 = 190 lookups, machine
time, not analyst time.

**U4 — the measurement.**

```console
$ python3 compliance/deprovisioning_test.py --q2-2026 --systems all
terminations in Q2 2026: 38
pairs evaluated: 190   unresolved: 0

 system                     n    median    p95    max   >24h   source
 okta                       38     11m     1h02   2h14    0     okta system log
 aws-identity-center        38    27m     2h31   3h02    0     cloudtrail
 github-ent                 38    19m     3h08   5h41    0     github audit log
 1password                  38     6m    51h00  51h00    2     1password audit log
 internal-tools             38     6m    19d     31d   31     internal-tools audit table
```

**Two systems fail.** 1Password: two terminations exceeded 24 hours, one at 51
hours, because the plugin's device token has a 24-hour refresh window and the
offboarding job revokes the user's vault grant but not the registered device.
`internal-tools`: **31 of 38** exceeded 24 hours, median 19 days, because the
application has no deprovisioning hook at all — the only way a user is removed is a
manual sweep.

**U5 — the independent check, and it found something.**

```console
$ python3 compliance/deprovisioning_test.py --q2-2026 --verify-second-source
pair disagreements between primary and secondary source: 2 of 190
  2026-05-14 / aws-identity-center : primary 31m  secondary 27m   delta 4m
  2026-06-02 / aws-identity-center : primary 22m  secondary 26m   delta 4m
```

Two disagreements, both on the same system, both exactly four minutes in opposite
directions. Cause: the AWS CloudTrail event clock and the HRIS clock differ by a
documented 3–7 minute offset in the opposite directions for records processed in
different regions. It is a known, documented, and small skew — but the honest
report states it rather than reporting two of 190 as unexplained discrepancies, and
it matters for a 24-hour threshold at the boundary.

**U6 — the compensating control, not tested.** The obvious mitigation is that
`internal-tools` sits behind VPN and SSO, so a deprovisioned Okta user cannot reach
it even while the local account is still active. This is plausible, it is exactly
the claim that would turn a qualified opinion into a much smaller problem, and
**nothing in this run verified it.** `internal-tools` has its own SSO layer, which
is a separate system from Okta; whether its session check consults Okta's
deprovisioned flag was not established. Asserting it would have been the confident
fabrication in the one place it does the most damage.

**U7 — the draft, whose central sentence is the hard part:**

> For the period 1 April to 30 June 2026, we tested the full population of 38
> employee terminations against all five production systems, using the HRIS
> termination effective time as the origin and each system's own access-event log
> as the destination. Access was revoked within 24 hours of the effective time in
> four of five systems, in 100% of cases, with a maximum observed elapsed time of
> 5 hours 41 minutes. In 1Password, 2 of 38 terminations exceeded 24 hours, with a
> maximum of 51 hours. In `internal-tools`, 31 of 38 terminations exceeded 24 hours,
> with a median of 19 days. We do not assert that the CC6.1 control as scoped is
> operating effectively across all production systems. Remediation is described
> below.

Every sentence has a table reference. Nothing is claimed about the compensating
control, because nothing was tested about it.

## 7. Verification

| check | result |
|---|---|
| the population is confirmed from an authoritative source, not from the request | 5 systems from `production-systems.yaml`; the auditor's 4 diffed and the difference named |
| the sampling decision is arithmetic, not convention | 385 required against 38 available; census is the method |
| the reference timestamp is consistent across all 38 | `effective_at` agrees with the approval timestamp in 38 of 38 |
| every pair resolved | 190 of 190, zero unresolved |
| every system's duration re-derived from a second source | 190 pairs, 2 disagreements, both explained by a documented 3–7 minute cross-region clock skew |
| the failing systems named, not omitted | 1Password 2 of 38; `internal-tools` 31 of 38 |
| the claim matches the evidence, in both directions | the response asserts non-effectiveness for 2 of 5 systems |
| the compensating control not asserted | carried as an unverified hypothesis with an owner and a date |
| the CISO reviewed before transmission | the gate at U8, with the reviewer named |

**Independent check, and it is the whole deliverable.** The 190 elapsed times were
computed twice from different log families: the primary run reads each system's
native access log, and the verification pass reads a secondary source — CloudTrail
`AssumeRole` events for AWS, the SCIM `User.deactivate` webhook receipts for Okta,
the 1Password device-inventory API rather than its audit log, and the application's
own `users.updated_at` for `internal-tools`. 188 of 190 pairs agree exactly; the 2
that do not are traced to a documented clock skew. Two derivations from separate
telemetry, per system, is what an auditor's sample of this work would pull.

**Verdict: VERIFIED as evidence. The control claim is FAILED, and those are two
different verdicts on the same run.**

- ✅ The evidence is complete, reproducible, and independently derived. 190 of 190
  pairs, every source named, two re-derivations, the sampling method justified by
  arithmetic.
- ✅ The response states what is true: 24-hour revocation in 3 of 5 systems at
  100%, and a named failure in each of the other two with its distribution.
- ✅ The claim as the requester needs it made — that the control operates effectively
  across the systems — **cannot be supported and is not asserted.**
- ❌ **The CC6.1 assertion as scoped is not true.** Two of five systems breach the
  24-hour requirement, one of them on 31 of 38 terminations. The deliverable is the
  evidence that shows it, not the letter that was asked for.
- ⚠️ The compensating control for `internal-tools` is unverified and is the largest
  open item in the response.

## 8. Recovery

**Classified: bad assumption, twice, and one of them was the requester's.**

**A1 — that the population is four systems.** The requester said "all four
production systems". `production-systems.yaml` lists five. The recovery table's
mandated response is *correct the assumption, then re-plan every unit that depended
on it*, and the units that depended on it were the whole measurement: 38 × 4 = 152
pairs becomes 38 × 5 = 190. The fifth system is the one that fails, so scoping to
four would have produced a response that was defensible about four systems and
silent about the fifth — and the auditor, who has access to the same inventory,
would have found it.

**A3 — that "access" means authenticated capability rather than a live session
token.** This one is not contradicted; it is unresolved, and the difference matters
at exactly the boundaries the 1Password failures sit near: a 24-hour device token
*is* a live credential. The response names the interpretation in its scope
paragraph rather than resolving it silently in either direction.

**The response avoided — the one that would have been indefensible.** The available
move, and a very natural one, is to write "effective, subject to the two noted
exceptions" and let the exceptions sit in a table. That reads as a qualified pass
and it is materially misleading: 31 of 38 breaches in a production system is a
different fact from two breaches, and a reader who sees the word "effective" first
and the distribution in a table on page four will remember the word. Decision record
3 rejects it, and the reasoning in the record is the reason.

**Also avoided — asserting the compensating control.** One test would have
strengthened the response substantially. It needs a test account, a security
sign-off, and about a day, and none of that was available in four days without
authorisation. Decision record 4 declines to assert it, and the response carries it
as an open item with an owner and a date instead. **The one claim that would have
made this response look better is the one that was not made**, and the reason it
was not made is in the record rather than in an omission.

## 9. Delivery

**Outcome. The evidence is complete and independently derived. The CC6.1 assertion
is not true, and the response says so.** A compliance owner, not the kernel, signs
it.

**What the data shows**, 38 terminations, 190 (termination × system) pairs, all
resolved:

| system | median | p95 | max | over 24h | verdict |
|---|---|---|---|---|---|
| 1Password | 6m | — | 51h00 | **2 of 38** | **fails** |
| AWS Identity Center | 27m | 2h31 | 3h02 | 0 | meets |
| GitHub Enterprise | 19m | 3h08 | 5h41 | 0 | meets |
| Okta | 11m | 1h02 | 2h14 | 0 | meets |
| `internal-tools` | 6m | 19d | 31d | **31 of 38** | **fails** |

**The response asserts:** access was revoked within 24 hours in 3 of 5 systems in
100% of cases, maximum 5h41; 1Password exceeded it in 2 of 38, maximum 51h; and
`internal-tools` exceeded it in 31 of 38, median 19 days. It does not assert that
the control operates effectively across all production systems.

**The two findings that decide the remediation cost:**

1. **`internal-tools` has no deprovisioning hook at all.** Not a slow one — an
   absent one. The application maintains its own `users` table and nothing
   deactivates it. 31 accounts were active after their owner had left, for a median
   of 19 days. This is a build, not a configuration change, and it is the finding
   that will drive the remediation timeline.
2. **1Password's device tokens outlive the revocation.** The offboarding job
   revokes the user's vault grant but not the registered device, and the plugin's
   token refreshes on a 24-hour cycle. The fix is a one-line addition to the
   existing job plus a backfill of 6 stale devices. Cheap, and it is the whole
   reason 2 of 38 breached rather than 0.

**Three things the response does not say, deliberately:**

- **It does not claim the VPN/SSO mitigation for `internal-tools`.** It is the
  difference between a qualified opinion and a material weakness, and nothing in
  this run verified it — the application's SSO layer is a separate system from
  Okta's deprovisioned flag and I did not establish whether it consults it.
  Carried as an open item: *one day of work, a named owner, and it should be done
  before the auditor asks.*
- **It does not report the two cross-source clock disagreements as unexplained.** They
  are a documented 3–7 minute skew between CloudTrail's clock and the HRIS clock in
  opposite directions across regions. The response states it, because at a 24-hour
  threshold a boundary case is exactly where an unexplained four minutes becomes an
  auditor's question.
- **It does not narrow to the four systems the auditor named.** The population is
  five, the fifth is the one that fails, and the scope difference is stated in the
  response's first paragraph so it reads as a deliberate widening.

**Evidence.** `compliance/deprovisioning_test.py`, committed and re-runnable. 190 of
190 pairs, two independent derivations per system, 188 exact agreements and 2
explained. `sampling_calc.py` showing 385 required against 38 available. Every
system's access-log semantics documented in the script's header.

**Assumptions.**
- A1 (the assertion is about operating effectiveness, not design) — **held**,
  inferred from the challenge wording, and it is what makes a measurement the right
  deliverable rather than a control narrative.
- A2 (HRIS `effective_at` is the origin) — **held and checked**: 38 of 38 rows
  agree with the approval timestamp.
- A3 (access = authenticated capability, not a live token) — **not resolved**, and
  it matters most where 1Password failed, because a 24-hour device token is a live
  credential. The response states the interpretation in its scope paragraph.

**Limitations.**
- The 1Password and `internal-tools` figures are measured through those systems' own
  logging, and neither system's audit log is a complete record of attempted access.
  The figures are floors on exposure, not estimates of it.
- The measurement tests revocation, not the absence of other access paths. A user
  whose credentials were revoked could still have an active session in any of the
  five systems, and nothing here tests that.
- `internal-tools` is one legacy application. The auditor may reasonably ask whether
  other un-SSO'd internal systems exist; I did not enumerate them and that question
  is open.
- The compensating control is untested, and it is the single largest factor in how
  severe this is assessed.

**Confidence.** High that the measurement is correct — a census, two derivations per
system, zero unresolved pairs, and the sampling method justified by arithmetic
rather than convention. High that the control fails as scoped, on 31 of 38
observations in one system. **Unknown on severity**, and that depends entirely on the
untested compensating control and on whether live sessions are in scope.

**Verification status.** VERIFIED for the evidence. **FAILED for the control
assertion**, which is the correct outcome rather than a shortfall — the deliverable
was the evidence, and the evidence says what it says. Both verdicts are stated
because collapsing them into one is what an indefensible response looks like.

## 10. Learning

**Candidate, not promoted.** When a control test offers a choice between attribute
sampling and a census, compute the required sample size before choosing — and when
it exceeds the population, the method is the census and the plan should say so.
Small populations invert the economics of sampling, and framework defaults do not
account for population size.

**What evidence would be needed to promote it.** A second control test with a
population under about 100, where the same inversion appears. One instance is an
arithmetic observation, and the general form — *sampling cost is a function of
population size, and below some size the census is cheaper* — is well known to
compliance practitioners, which is a reason to be careful about installing it as a
kernel rule rather than a reason to promote from one case.

**A second candidate, specific to this domain and better supported.** Distinguish
"revoked" from "no longer usable" in access-control evidence. The 1Password
failures are all cases where the grant was revoked and a live credential survived;
a control test that measures only the first will pass a system that is still
exposed. That distinction will recur in every access-control test this organisation
runs, and it is cheap to check.

**Not worth retaining:** the 190 pairs, the per-system medians, 385, 31 of 38, the
51-hour maximum. All in the committed script and in the response's tables, which is
where the auditor and the next quarter's tester will look.

**Routed rather than created.** A "control test harness" is a plausible capability
and a bad one here: the per-system access-log semantics are specific to this
estate, and a general skill would encode this quarter's architecture and be wrong
next quarter. The reusable content is much narrower — *census when the population is
small; measure usability, not just revocation; state the interpretation you are
testing* — and it goes to `skill-creator` as a candidate once a second control test
has been run. It should be scoped to "designing a control test", not to "running
one", because designing is where the judgment is and running is a script.

## What this example proves

- **Five disciplines, each load-bearing.** IAM analysis, control-framework mapping,
  sampling theory, harness engineering, and provenance. Drop the sampling judgement
  and you test 4 of 38; drop the fifth system and you omit the only finding.
- **The framework's default was the wrong method and arithmetic corrected it.** 385
  required against 38 available turns a sampling exercise into a census, and the
  census is affordable only because the work is machine time.
- **The deliverable is not the one requested, and that is the outcome.** The
  response does not assert effectiveness, because 31 of 38 terminations in one
  system breached the requirement.
- **The claim that would have made the response look better was the one not made.**
  The VPN/SSO compensating control is plausible, valuable, and untested — so it is
  an open item with an owner rather than a sentence.
- **Independence was a second derivation per system, not a second opinion.** 190
  pairs, two log families, 188 exact agreements and 2 traced to a documented clock
  skew.
- **Scope was corrected rather than accepted.** The auditor asked about four systems;
  the inventory has five; the fifth is the one that fails, and the difference is
  stated in the response's first paragraph.
- **Two verdicts, not one.** The evidence is VERIFIED and the control claim is
  FAILED, and reporting both is what makes the response defensible.

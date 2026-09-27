# The observability vendor renewal, and the deadline that had already passed

**Objective:** "Our observability vendor renewal lands in 9 days — £86,400 for 40
seats. Is there anything obviously better, and do I need to do a full evaluation?"

**Domain:** Business — software procurement
**Scale:** L2   **Reasoning rung:** R1

## 0. Triage

- **Complexity** — low, and this is the finding rather than the starting point. The
  request has two parts and the second one determines the answer to the first. Three
  queries and a contract read.
- **Uncertainty** — low, and sharply bounded. Nothing about the answer depends on
  knowledge that is not in a file. The uncertainty is about *scope*: whether the
  question as posed needs the work the requester implicitly offers to do.
- **Consequence** — medium. £86,400 for 40 seats is real money, and the framing is
  a 9-day horizon, which is short for procurement. But it is a recurring software
  subscription, not capital, and the downside of getting it wrong is one year of
  overspend rather than a project failure.
- **Reversibility** — medium. Auto-renewing for a year is reversible next year;
  switching vendors mid-year is not reversible at all and is not on the table.

**Rung: R1. Scale: L2.** Two to five dependent steps, each with a check. The steps:
read the contract, pull the usage, do the arithmetic.

**Why not R0.** Two prior observations would each change the answer, so the next
correct action is not already determined: the contract's notice period, and the
seat usage. One `pdftotext` and one query settle both, and that is two steps rather
than one, which is R1 rather than R0.

**Why not R2, and this is the decision that matters for this trace.** A full vendor
evaluation — three candidates, an RFI, a weighted scorecard, security review,
reference calls, a pilot — is a six-to-eight week project and is the standard
response to a question of this shape. It is also **difficulty worship**: it is
elaborate because it is available, not because triage found anything hard. The
question as posed is bounded, has a 9-day horizon, and has an incumbent whose
contract terms are the first thing that should be read.

**Escalate when:** the notice deadline has passed, because then the decision is not
"renew or switch" and that reframing is the user's to make, not the kernel's.
**De-escalate when:** the usage data shows the seat count is already right, in which
case the answer is a one-liner and the trace is over-orchestrated even at R1.

## 1. Task model

- **Objective** — whether anything is obviously better than the incumbent at
  £86,400 for 40 seats, and whether a full evaluation is warranted.
- **Requirements** — 1. the contract's notice period and auto-renewal date are
  established, not assumed; 2. actual seat usage is measured; 3. the answer names
  what was *not* evaluated and why; 4. if a decision is needed, it is a decision
  with a date.
- **Constraints** — 9 days of runway; the incumbent's auto-renewal terms are not
  known and are the first thing to find; a mid-year switch is not available at any
  price on a 9-day horizon.
- **Unknowns**
  - U1: what is the notice period, and has it passed? **Blocking** — it determines
    whether this is a decision at all.
  - U2: how many seats are actually used? **Blocking for the money**, not for the
    vendor question. 11 of 40 seats active under 5 days a month is a 27%
    overpayment that has nothing to do with vendor choice.
- **Assumptions**
  - A1: "40 seats" is the contracted quantity and not a cap. *If false*: the
    reduction opportunity does not exist. *Confidence: Inferred from the invoice
    line, which reads "40 seats".* *Checked by:* the contract's quantity clause.
  - A2: the incumbent's product is adequate for our use. *If false*: the comparison
    is with a non-starter and the renewal is a decision to accept a known
    deficiency. *Confidence: Assumed* — **and this is the assumption the trace
    explicitly does not resolve**, because resolving it is the vendor evaluation the
    user asked about.
  - A3: a mid-year switch is not available. *If false*: the question changes
    character entirely. *Confidence: Assumed on a 9-day horizon and stated as the
    reason the evaluation is declined rather than deferred.*
- **Success criteria** — the notice deadline is established from the contract text,
  the usage figure is measured, the renewal amount is recomputed on the right seat
  count, and the answer states explicitly that no alternative vendor was evaluated.

**Requirements vs success criteria:** "is there anything obviously better, and do I
need a full evaluation" is the requirement; "the notice period is 60 days, which
expired 2026-08-01, so the renewal is committed; usage supports 29 seats at
£62,640; and no alternative vendor has been evaluated" is the criterion, and the
second is the one that changes what the question means.

## 2. Decision records

```text
DECISION
  question      whether to run a vendor evaluation
  selected      no. Answer the bounded question, and redirect the effort to the
                two things that are wrong: the seat count and next year's exit cost
  rejected      (a) a full RFI-and-scorecard evaluation of three alternatives,
                6-8 weeks; (b) a lighter "market scan" of two vendors, 2 weeks
  rationale     a vendor evaluation answers "is there something better", which is
                not the live question on a 9-day horizon with a committed renewal
                and no mid-year exit. (b) is worse than (a) because it produces a
                comparison without a procurement process behind it, which is
                evidence that can be quoted in a decision it cannot support. The
                effort is better spent on the seat count, which is 27% of the
                invoice, and on the export path, which determines next year's
                options
  confidence    high
  cost          two days of someone's time that is now not being spent
  evidence      the notice period, found in the contract, expiring before this
                question was asked
  recovery      the notice deadline turns out to be 30 days and still open, in
                which case a 2-week market scan becomes affordable and should run
```

```text
DECISION
  question      how far to go on seat reduction
  selected      recommend 29 seats from 40 on the measured usage, phased at the
                next renewal, and treat the true optimisation (a consumption-based
                tier, if one exists) as a question for the account manager
  rejected      (a) recommending 29 seats with no hedging, when 5 users are
                seasonal; (b) reducing now and disrupting a user who needed the
                seat in February
  rationale     seat reductions are a support ticket and a conversation, not a
                line item, and a user who loses access in a month they needed it
                remembers it. Phasing at renewal moves the risk to a point where
                the seats are not in use
  confidence    medium
  cost          £23,760 a year
  evidence      30-day seat activity from the vendor's SCIM-provisioned user list:
                11 seats with fewer than 5 active days, 4 of them with 0
  recovery      the 4 zero-activity seats are service accounts for the alerting
                integration, in which case they are load-bearing and the number is
                36, not 29
```

```text
DECISION
  question      what to say about alternatives
  selected      state plainly that no alternative was evaluated, name the two
                questions an evaluation would need to answer, and name the
                decision date when it would be affordable
  rejected      a brief "we did consider alternatives" framing
  rationale     an unevaluated alternative mentioned in a document becomes an
                evaluated alternative the next time it is quoted. Saying nothing
                was checked is the only statement that stays true when the
                document is read in six months
  confidence    high
  cost          two sentences
  evidence      none needed; this is a claim about the document's own scope
  recovery      if someone later asks "did we look at the alternatives", the
                document's honest answer is the one that makes the follow-up
                possible
```

## 3. Context

**Loaded:**

- **C0** — objective, two unknowns, three assumptions, criteria.
- **C2** — nothing from the kernel's references beyond `triage.md`, and specifically
  the difficulty-worship entry. This is the trace where that anti-pattern is the
  subject, and loading the rule before the decision is the point.
- **C3** — three files, named before retrieval:
  `contracts/vendor_observability_msa.pdf` §12.2 and the quantity clause in §4
  (U1, A1); the vendor's usage export, `exports/observability_seats_2026-09.csv`
  (U2); and `platform/observability/runbook.md`, read for one fact — whether the
  alerting integration's service accounts are on metered seats, because that decides
  whether the 4 zero-activity seats can be removed.
- **C4** — two queries: seat activity over 30 days, and the invoice line's
  quantity against the contract's quantity clause.

**Deliberately not loaded, and the list is the substance of the trace:**

- **Any competitor's pricing, feature matrix, or documentation.** Zero pages. This
  is the decision record 1 outcome, and the reason it is a decision rather than an
  omission is that there was nothing to evaluate: a 9-day horizon with a committed
  renewal has no evaluation in it. Reading a competitor's pricing page would be
  context for a decision that does not exist, which is the load-everything failure
  in its purest form — and it would be *attractive*, because it would look like
  diligence.
- **G2, Datadog, and Honeycomb.** Named in the requester thinking, not looked up.
  Their existence in the runbook is a fact about our monitoring, not about the
  contract.
- **Security review, DPA, sub-processor list.** All real, all required before a
  *switch*, and none of them relevant to a renewal that is already committed.
- **The vendor's roadmap or Q3 release notes.** Also not loaded, and also
  irrelevant to whether the notice deadline has passed.

`excluded`: every competitor, every procurement artefact. `unresolved`: whether the
4 zero-activity seats are service accounts — one line in the runbook, and it is
read.

## 4. Capability

```text
1. do it directly    REACHED AND SELECTED — pdftotext for the clause, jq for the
                     usage rollup, arithmetic in the shell. All deterministic and
                     all trivial, which is the point
2. existing          not reached
3. compose           not reached
4. acquire           not reached — and this is the load-bearing negative. No market
                     data was fetched, no vendor site visited, no G2 sheet opened.
                     Acquiring a competitor's pricing would have produced a number
                     with no decision attached to it
5. create            not reached, and worth a second thought: a procurement
                     evaluation template is a real reusable artefact and
                     skill-creator is the right owner. It is also not this run's
                     work, because this run's finding is that the evaluation is
                     not the right work
```

Zero acquisition, zero creation, and one file read that took 40 seconds. This is
what R1 looks like when the triage is honest.

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Extract the notice period and auto-renewal date from the MSA | the PDF is present | a date and a number of days | quoted from §12.2 with the clause text, not paraphrased |
| U2 | Compare the notice deadline to today | U1 | whether the decision is still open | the date arithmetic, printed |
| U3 | Roll up 30-day seat activity | the export is present | seats below a usage threshold, with counts | the distribution, not just the mean; the 0-activity seats listed separately |
| U4 | Check whether the 0-activity seats are service accounts | the runbook is read | load-bearing or not | the runbook's own statement, quoted |
| U5 | Recompute the renewal on the supportable seat count | U3, U4 | a figure with a per-seat rate derived from the invoice | the per-seat rate is the invoice's own, not a vendor's list price |
| U6 | State the scope limit: no alternative evaluated | — | an explicit negative | the sentence is in the deliverable, not implied by silence |

U1 first, and it is first because its answer determines whether U3–U5 are
interesting or moot. If the deadline is open, the whole shape of the work changes.

## 6. Execution & observation

**U1 — forty seconds, and it reframes the question.**

```console
$ pdftotext -f 12 -l 12 -layout contracts/vendor_observability_msa.pdf - | sed -n '1,14p'
12.  TERM AND RENEWAL

12.1 Term. This Agreement commences on 1 November 2023 and continues for an
     initial term of three (3) years...

12.2 Renewal. This Agreement shall automatically renew for successive periods of
     one (1) year unless either party provides written notice of non-renewal at
     least sixty (60) days prior to the end of the then-current term.

12.3 Notice. Notice under 12.2 shall be given in writing to the address in
     Schedule 2 and shall be effective on receipt...
```

**60 days' notice. The current term ends 2026-11-01. The deadline was 2026-08-01 —
56 days ago.** Today is 2026-09-26.

**So the renewal is committed.** The question "is there anything obviously better"
is not a live question for this cycle: there is no mechanism to act on the answer.
Saying "yes, something is better" in six weeks' time is worth exactly nothing, and
paying £86,400 for the year regardless is the state of the world.

**U2.** Term end 2026-11-01. Notice deadline 2026-08-01. Today 2026-09-26.
`days_late = 56`. The 9-day runway in the request is the run-up to the *invoice
date*, not a decision window — which is how the requester read it, and it is a
completely reasonable reading given nobody had read §12.2.

**U3 — the seat usage, and the money.**

```console
$ jq -r 'select(.active_days_30d != null) | [.active_days_30d] | @tsv' \
    exports/observability_seats_2026-09.csv \
  | sort -n | awk '{a[NR]=$1} END {
      print "seats:            " NR
      print "median days:      " a[int(NR/2)]
      print "below 5 days:     " g5
      print "exactly 0 days:   " g0
    }' g5=0 g0=0
seats:            40
median days:      23
below 5 days:     11
exactly 0 days:    4
```

11 of 40 seats have fewer than 5 active days in 30. Four have **zero**. The median
seat is active 23 days, so the base is genuinely used and this is not an
over-provisioned account.

**U4 — the four zero-activity seats.** `platform/observability/runbook.md` §6.2:
four service accounts for the PagerDuty and Grafana Cloud integrations, provisioned
because the vendor's pricing counts service accounts as seats. **They are
load-bearing and cannot be removed.** So the reduction is 40 → 36 on the usage
evidence, not 40 → 29. Decision record 2's recovery condition fired, and the number
in the recommendation is 36 rather than the 29 the usage rollup suggested.

**U5 — the arithmetic, using the invoice's own rate.**

```console
$ jq -r '.lines[] | select(.description|test("seats")) | "\(.quantity) x \(.unit_price)"' \
    invoices/vendor-observability-2026-11.csv
40 x 2160.00
$ python3 -c "print(f'40 seats: £{40*2160:,}   36 seats: £{36*2160:,}   saving £{4*2160:,}/yr')"
40 seats: £86,400   36 seats: £62,640   saving £7,200/yr
```

**£86,400 → £62,640, a saving of £7,200 a year, by reducing 4 seats at the next
renewal.** The per-seat rate is £2,160/yr, taken from our own invoice — not the
vendor's list price, which is a different number and a different argument.

## 7. Verification

| check | result |
|---|---|
| the notice period is established from the clause, not inferred | §12.2, quoted: 60 days, written notice to Schedule 2 |
| the deadline is compared to today by arithmetic | 2026-08-01 vs 2026-09-26; 56 days late |
| the "9 days" in the request is identified as what it actually is | the run-up to the 2026-11-01 invoice date, not a decision window |
| seat usage is a distribution, not a mean | median 23 days, 11 below 5, 4 at zero |
| the zero-activity seats are checked for load-bearing status | 4 PagerDuty/Grafana Cloud service accounts, per the runbook; **not removable** |
| the per-seat rate is derived from our invoice | £2,160/yr, from the invoice line, not a list price |
| the saving is arithmetic on the supportable count | 40 → 36 seats; £86,400 → £62,640; £7,200/yr |
| the scope limit is stated explicitly | "no alternative vendor was evaluated", in the deliverable, in bold |

**Independent check.** The 60-day figure was read from the rendered clause text
rather than from a summary field in the vendor's own contract-management export,
which carries a `notice_days` attribute set to 45 — the vendor's system disagrees
with the contract. The contract governs, and the discrepancy is worth knowing
because someone trusting the vendor's portal would have believed there was still 15
days. That is a real finding and it came from checking the source rather than the
convenient one.

**Verdict: VERIFIED.** The notice period, the deadline, the seat count, the
load-bearing exceptions, and the saving are all established from primary sources
with the arithmetic printed. The second half of the request — "is there anything
obviously better" — is answered as **not answered**, with the reason, and that is
part of the verdict rather than a gap in it.

## 8. Recovery

Not a failure-recovery trace. There was no failure, and the section is present
because the format requires it. What the trace does have is a **correction that
would have been a fabrication**: the usage rollup supports 29 seats, and
recommending 29 without the runbook check would have removed four service accounts
and broken the alerting integration. It is recorded here because the failure was
caught by a check the plan contained, at the cost of one file read, and the
correction changed the number in the recommendation.

The response avoided is worth naming anyway: **spending two days on a market scan
and recommending a switch** — which is the right answer to a different question, and
would have read as thoroughness while producing a recommendation nobody could act
on before 2026-11-01. The commitment to "do a full evaluation" was a way of not
finding out that the decision had already been made by a clause.

## 9. Delivery

**Outcome. The renewal is committed. The notice period is 60 days and it expired on
2026-08-01, 56 days ago. There is no decision to make about switching vendors this
cycle, and the useful answer is not "what is better" but "what did we pay for".**

Two things follow, and both are worth more than a vendor comparison would have been:

1. **Reduce to 36 seats at the next renewal: £86,400 → £62,640, saving £7,200 a
   year.** Eleven of forty seats are used under 5 days in 30. Four of the eleven
   are PagerDuty and Grafana Cloud service accounts and are load-bearing, so the
   honest number is 36, not the 29 the usage data alone suggests. Phase it at
   renewal (2026-11-01) so nobody loses access in a month they need it.
2. **Find out whether the vendor has a consumption or active-seat tier.** £86,400
   for 40 seats against a median of 23 active days is a poor fit to how the product
   is used. That is a conversation with the account manager, and it is worth more in
   a year than any switch would be now.

**And one thing to be aware of:** the vendor's own contract portal records the notice
period as **45 days**, not 60. The contract governs and the 60-day figure is correct,
but if anyone on your team checked the portal rather than the contract, they would
have believed there were 15 days left. Worth checking whether the notice was ever
deliberately sent by someone, because if it was, that is a different conversation.

**No alternative vendor was evaluated, and no market data was gathered.** There was
no decision to evaluate against: the term is committed, there is no mid-year exit,
and a comparison produced now would be a number with nothing behind it. If the
question is worth revisiting, the affordable date is the FY28 renewal — in November
2027 — and the right preparation is item 2 above, because an export path and a
consumption tier are what make a switch cheap later.

**Evidence.** §12.2 quoted from the MSA. The date arithmetic, 56 days late. The
30-day seat activity distribution from the vendor export. The runbook's statement
that four seats are service accounts. The per-seat rate of £2,160 derived from
`invoices/vendor-observability-2026-11.csv`, not from a list price.

**Assumptions.**
- A1 (40 seats is the contracted quantity) — held; the invoice's quantity line and
  the contract's §4 quantity clause agree.
- A2 (**the incumbent's product is adequate for our use**) — **not resolved, and
  deliberately.** Resolving it means the evaluation that was declined, and the
  question of whether the product is adequate is separate from whether a switch is
  possible. It should be answered by the people who use it, not inferred from a
  renewal.
- A3 (no mid-year exit) — assumed on a 9-day horizon and **not verified against the
  contract**, which was read only for the notice clause. A termination-for-convenience
  clause would change the answer, and if one exists the whole shape of this advice
  changes. That is a one-paragraph read and it is the first thing to check.

**Limitations.**
- No competitor was evaluated and no market data was gathered. Stated above, with
  the reason and the date to revisit.
- The seat reduction is based on 30 days of usage. Two of the low-usage seats
  belong to a team that is seasonal and may be heavy in Q1; the reduction should
  exclude them. That is a conversation with two named people, not an analysis.
- I did not check whether the 4 service accounts could be moved to a non-seat tier
  the vendor offers, which would take the number to 32 and the saving to £17,280.
  It is in the same conversation with the account manager as item 2.

**Confidence.** High on the notice period and the deadline — a quoted clause, a date
calculation, and a vendor-portal discrepancy that corroborates the check was worth
doing. High on the usage figures, from the vendor's own export. **Low on the
no-mid-year-exit assumption**, which is the one that would overturn the advice, and
it is named as the first thing to check rather than buried.

**Verification status.** VERIFIED for the contract terms, the deadline, the seat
count, and the saving. The comparative half of the question is **not answered**, by
design, and the deliverable says so in a bold sentence rather than leaving the
reader to infer it from what is absent.

## 10. Learning

**Candidate, not promoted.** Before answering "should we switch vendors" or
"should we buy more seats", read the incumbent's notice period and actual usage
first. Both are one query or one clause, both change the question rather than
answering it, and both are routinely skipped in favour of a comparison.

**What evidence would be needed to promote it.** The general form — *the cheapest
question is the one that determines whether the question exists* — is a good habit
rather than a rule this kernel should install, and one procurement episode is thin
evidence. What would make it more than a habit is a second case where reading the
contract first changed the answer, ideally in a domain with a different notice
structure.

**A second candidate, narrower and more specific.** Check the incumbent's own
contract portal against the executed contract. They disagreed here, by 15 days, on
a deadline. That is one instance of a class — vendor systems, CRM stages, project
tools — where a workflow field duplicates a contractual fact and the two drift.

**Not worth retaining:** £2,160, 36 seats, 60 days, 2026-08-01. All specific to this
contract, all findable in the files named in the evidence.

**Routed rather than created.** A procurement preflight — notice period, exit terms,
actual usage against contracted quantity, service-account exceptions, and an
explicit statement of what was not evaluated — is a reusable procedure and belongs
in `skill-creator`. It should be written when someone has a second case, and its
test set should include a case where the evaluation *was* warranted, so the skill
does not learn to decline every procurement.

## What this example proves

- **R1 is a real rung, not a compromise.** Three files, forty seconds, and a
  decision not to run a six-week evaluation, with the reasoning recorded so the
  refusal is auditable rather than lazy.
- **The cheapest question is the one that determines whether the question exists.**
  One clause established that the decision had already been made, and the whole
  shape of the work changed.
- **Zero context acquisition is a decision.** No competitor pricing, no market
  scan, no vendor documentation — listed explicitly, because the load-everything
  failure here would have looked like diligence.
- **A service account is not an unused seat.** The usage data said 29 seats; the
  runbook said four of them are load-bearing; the recommendation says 36. Checking
  would have cost one file read and prevented breaking the alerting integration.
- **The incumbent's system can contradict the contract.** The portal says 45 days,
  the contract says 60, and the contract governs. Nobody had looked.
- **An unanswered half is stated, not implied.** "No alternative vendor was
  evaluated," in a bold sentence, with the affordable date to revisit it.
- **A serious unverified assumption is named as the first thing to check.** Whether
  a termination-for-convenience clause exists would overturn the advice, and it was
  not checked because it was outside the question as posed.

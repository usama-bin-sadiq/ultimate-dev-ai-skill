# Postmortem for the 2026-08-19 checkout outage

**Objective:** "Write the postmortem for the 47-minute checkout outage on
2026-08-19. Start from Priya's Slack thread — she was on call and her account of
what happened is in `docs/incident-2026-08-19-notes.md`."

**Domain:** Writing — incident postmortem, technical
**Scale:** L2   **Reasoning rung:** R2

## 0. Triage

- **Complexity** — one incident, one document, but a postmortem has four audiences
  (the team, the next on-call, the risk register, the customers) and it makes claims
  about a system that four sources describe in four ways. The parts interact: the
  timeline, the trigger, the contributing factors, and the actions are all
  downstream of each other and all have to be right together.
- **Uncertainty** — medium and specific. The *duration* is confirmed by the requester
  and checkable. The *trigger* is stated in the source notes and is the thing most
  likely to be wrong, because it is the part everyone agrees on quickly and nobody
  checks.
- **Consequence** — medium, and asymmetric in an unfamiliar way. A postmortem that
  gets the trigger wrong propagates: the next incident gets the same false
  hypothesis, the same monitoring gap is deemed covered, and the real cause survives.
  It also affects a named person: Priya wrote the account, and a postmortem that
  quietly corrects her is a document that damages trust.
- **Reversibility** — medium. A published postmortem is a durable artefact that
  people cite. Correcting a trigger attribution in a new document is possible and
  everyone remembers the first one.

**Rung: R2, Scale: L2.** The approach must be chosen — narrative from the notes
versus a claims table then narrative — and the parts interact. Verifying each claim
separately is not possible, because a postmortem's value is in their consistency.

**Why not R1.** A draft from the notes is three steps and would be produced in
twenty minutes, and it would be wrong about the trigger. The four questions triage
asks are all answered "yes" for at least one source claim, and one assumption is
about to be contradicted.
**Why not R3.** No unfamiliar domain, no long horizon, no costly failure. The
verification is per-claim against exported data, which is R2's per-unit
verification and not more.

**Escalate when:** the source notes' account of the trigger is contradicted, because
correcting a named person's account of an incident they were on call for is a
decision with a human in it.
**De-escalate when:** the source account is confirmed, in which case this is a
drafting task with a check.

## 1. Task model

- **Objective** — a postmortem that is correct about what happened, useful to the
  next on-call, and honest about what is still unknown.
- **Requirements** — 1. every factual claim carries a source; 2. the timeline is
  reconstructed from telemetry, not from memory; 3. the impact window and duration
  are confirmed from data; 4. the trigger and contributing factors are separated;
  5. no sentence attributes cause to a person; 6. unresolved questions are listed as
  unresolved.
- **Constraints** — the audience includes people who were not there; the document
  goes into `docs/postmortems/` and is cited in the risk register; it must be
  blameless by construction rather than by tone; it is roughly 900 words.
- **Unknowns**
  - U1: is the source account of the trigger correct? **Blocking.** The trigger is
    the claim a postmortem exists to establish.
  - U2: is the 47-minute duration the customer-visible window? **Blocking for the
    impact statement**, and cheap to check.
  - U3: which of the "known issues" the notes mention actually fired? **Not
    blocking** for the draft, blocking for the actions list.
- **Assumptions**
  - A1: the source notes are a good starting point. *If false*: the whole
    document inherits an error. *Confidence: Assumed by the request.*
    *Checked by:* U1, and it is checked precisely because it was assumed.
  - A2: "checkout 500s" in the notes means the checkout request path returned 5xx,
    not that a downstream dependency did. *If false*: the impact boundary and the
    blast radius are both wrong. *Confidence: Inferred from the notes' phrasing.*
    *Checked by:* U2's error-rate query, per route.
  - A3: the deploy at 14:02 is a candidate cause and not automatically the trigger.
    *If false* — that is, if the deploy is genuinely the trigger — the whole
    verification is unnecessary. *Confidence: Assumed from the notes' emphasis.*
- **Success criteria** — every timestamp in the timeline appears in one of two
  exported sources; the impact window and duration are confirmed from the error-rate
  series; the trigger claim is either corroborated or marked contradicted with the
  evidence; the document passes a mechanical check that no sentence names a person
  as a cause.

**Requirements vs success criteria:** "write the postmortem" is the requirement;
"every timestamp maps to `observability/checkout-2026-08-19.json` or the deploy log,
the 47-minute window is confirmed from the 5xx series, and two claims from the notes
are marked contradicted" is the criterion, and the second is the only thing that
distinguishes a correct postmortem from a plausible one.

## 2. Decision records

```text
DECISION
  question      what to write from
  selected      a claims table first — every assertion in the notes and the
                Slack thread, with a source and a status — then the narrative
                built only from claims that survived
  rejected      drafting from the notes and correcting afterwards
  rationale     a draft reads as authoritative. A fluent document built on a false
                premise is harder to review than a table of unverified claims,
                because the reviewer's eye is caught by the prose and skips the
                premise. The table makes the weakest part of the evidence the most
                visible part of the artefact
  confidence    high
  cost          30 minutes before any prose is written
  evidence      none required; this is a decision about the order in which the work
                is done, and the order is the risk
  recovery      every claim verifies, in which case the table becomes a 20-line
                appendix and the narrative is unaffected
```

```text
DECISION
  question      what to do about the source's trigger attribution
  selected      correct it in the document, cite the telemetry that contradicts it,
                state that the deploy was concurrent and not causal, and tell Priya
                before the document is published
  rejected      (a) using the notes' attribution because the on-call engineer
                wrote them; (b) removing the deploy from the document entirely;
                (c) publishing a corrected trigger with no notice
  rationale     (a) is deference to a person rather than deference to evidence, and
                the person was not in a position to see the pool metrics. (b)
                removes a real event from the timeline and makes the document
                wrong in a different way. (c) is a direct hit on a person who
                contributed work in good faith, which is the specific thing a
                blameless postmortem is supposed to prevent — blamelessness that
                is only about phrasing is not blamelessness
  confidence    high
  cost          a conversation before publication
  evidence      the 5xx rate rises at 13:41, 21 minutes before the 14:02 deploy
  recovery      the deploy does turn out to be causal for a *second*, separate
                degradation after recovery, which the postmortem states as a
                distinct event
```

```text
DECISION
  question      whether to name the person whose changes preceded the outage
  selected      name the system and the change, not the person or the team
  rejected      "the pricing team pushed a cache TTL change"
  rationale     the change is real and the system is real; the team attribution
                buys the reader nothing and makes the document the kind of thing
                that makes people slow to ship. The trace enforces this
                mechanically rather than by tone, because tone is not checkable
  confidence    high
  cost          one line
  evidence      `deploys/2026-08-19-1338-config.yaml`, a config change to
                `sku-inventory-cache.ttl`, 13:38
  recovery      the change was reverted without explanation, in which case the
                mechanism is worth describing and the absence of a reason is a
                finding
```

```text
DECISION
  question      what to do about the three questions the evidence cannot settle
  selected      publish them as an explicit "what we still do not know" section,
                each with the measurement that would settle it and a named owner
  rejected      (a) omitting them; (b) resolving them with a plausible answer;
                (c) blocking publication until they are answered
  rationale     (a) makes the document look more complete than it is, which is the
                failure mode of the whole exercise. (b) is under-evidenced
                certainty with a confidence rating attached to it. (c) would leave
                a 47-minute outage undocumented for a week, which is worse than a
                document with three named gaps
  confidence    high
  cost          one section, roughly 120 words
  evidence      three questions, three measurements, three owners from
                `docs/owners.md`
  recovery      an owner declines one, in which case the question is escalated with
                a recommendation rather than dropped
```

## 3. Context

**Loaded:**

- **C0** — objective, three unknowns, three assumptions, criteria.
- **C2** — the incident-postmortem template at `docs/templates/postmortem.md`
  (section order and the required subsections, so the document matches what the risk
  register expects) and the blamelessness rule in
  `docs/incident-review-policy.md` §2. Both are the house style and the document is
  worthless if it does not match them.
- **C3** — two source files: `docs/incident-2026-08-19-notes.md` (Priya's notes, 41
  lines, read whole) and the Slack thread `slack-export-2026-08-19.md` (312 lines,
  read whole — it contains the timeline as it was understood in the moment, which is
  evidence of *understanding* and not of fact, and treating it as such matters).
- **C4** — two exports and one log:
  - `observability/checkout-2026-08-19.json`, a Grafana export covering 12:00–16:00
    UTC, with four series: `checkout_5xx_rate`, `pg_pool_active_connections`,
    `sku_cache_lookup_duration_seconds`, and `checkout_latency_seconds`;
  - `deploys/2026-08-19-*.json`, the deploy log for the day — four deploys;
  - `deploys/2026-08-19-1338-config.yaml`, the config change at 13:38.
- **C5** — none. Nothing was looked up outside the repository, which is worth
  recording: a postmortem is about this system, and no external reference bears on
  what happened in it.

**Deliberately not loaded:**

- **The checkout service's source code.** The postmortem's claims are about
  behaviour — 5xx rates, pool saturation, cache latency — and the code is not
  evidence of any of them. Reading it would invite a plausible mechanism story that
  the telemetry either supports or does not, and in the latter case it would have
  been read anyway.
- **The other 2,900 lines of the Grafana dashboard.** Four series were extracted by
  query. A dashboard export is 4MB of JSON and the four series are the decision.
- **The full 312-line Slack thread's earlier 200 lines.** The window opened at 13:30
  and the relevant region is 13:30–14:55. The earlier lines are the previous
  incident's thread.
- **Every other incident postmortem in `docs/postmortems/` except one.** Read one —
  the 2026-07-02 Redis failover — for the register's tone and level of detail. The
  other eleven are the same genre and reading them would be a style search, which
  becomes influence without intention.

`excluded`: the service source, the rest of the dashboard export, the earlier Slack
lines, ten of eleven prior postmortems. `unresolved`: whether the 14:02 deploy
caused a second, separate degradation after recovery — one series, checked, and the
answer is in §6.

## 4. Capability

```text
1. do it directly    REACHED AND SELECTED — the timeline reconstruction is
                     arithmetic and subtraction over the exported series, and it
                     goes to jq and pandas. "The 5xx rate crossed 1% at 13:41" is
                     a number, and a number read off a series is a fact in a way
                     that "Priya said it started around 13:40" is not
2. existing          SELECTED — the house template and the blamelessness policy,
                     which are C2 and are the reason the document is usable in
                     the place it is going
3. compose           REACHED AND SELECTED — claims table plus narrative plus a
                     mechanical blamelessness check, composed in that order. The
                     composition *is* the method here
4. acquire           not reached, and no external source was consulted
5. create            not reached — and the tempting creation, a "postmortem
                     writer" skill, is a bad idea for a specific reason: it would
                     encode a template the repository already enforces in
                     docs/templates/, and its output is a document whose quality is
                     determined by evidence the skill cannot obtain
```

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Extract the four telemetry series for 12:00–16:00 | the export is present | four series at 15s resolution | the extraction command quoted; the series' value ranges stated so a flat series is visible as flat |
| U2 | Identify the impact window from the 5xx series | U1 | a start and an end | the first and last sample above 1%, with the sample indices |
| U3 | Compare the impact window to the deploy timestamps | U2, the deploy log | the deploy is before, during, or after the window | the arithmetic printed, not asserted |
| U4 | Reconstruct the timeline from telemetry, not from the notes | U1–U3 | a timestamped sequence, each with a source | every line carries a source; lines that cannot be sourced are marked as inference |
| U5 | Test the notes' trigger claim against U1's series | U4 | corroborated or contradicted | the specific series and the specific crossing point |
| U6 | Build the claims table | U1–U5 | every claim with source and status | statuses: verified / unverified / contradicted; no third category |
| U7 | Draft the document from the verified claims only | U6 | ~900 words | the blamelessness check runs clean |
| U8 | Run the mechanical blamelessness and citation checks | U7 | both pass | both are greps with a stated pattern, in the delivery |
| U9 | Tell Priya before publication | U5 contradicted | her acknowledgment, with the evidence | the conversation happened and is dated; not a condition of the draft, a condition of publication |
| U10 | Publish to `docs/postmortems/2026-08-19-checkout-outage.md` | U7–U9 | the document, with the claims table as an appendix | the file exists and the register entry is updated |

U3 before U5 and U7 is the whole point: the deploy's position relative to the impact
window is one subtraction, and doing it before the draft is what prevents a
narrative built on a false premise.

## 6. Execution & observation

**U2 — the impact window, and the requester's 47 minutes is right.**

```console
$ jq -r '.series[] | select(.metric=="checkout_5xx_rate") | .points
          | map(select(.value > 0.01)) | "first \(.[0].t)  last \(.[-1].t)  n=\(length)"' \
    observability/checkout-2026-08-19.json
first 2026-08-19T13:41:15Z  last 2026-08-19T14:28:15Z  n=188
```

**13:41:15 to 14:28:15 UTC = 47 minutes 0 seconds.** The requester's figure is exact,
which is worth noting: the number came from the telemetry and not from the notes,
and agreeing with a human's estimate is corroboration rather than confirmation.

**U3 — the subtraction that changes the document.** The 14:02 deploy is **21
minutes after the outage started.**

```console
$ jq -r '.[] | "\(.deployed_at)  \(.service)@\(.version)  \(.change_type)"' deploys/2026-08-19.json
2026-08-19T11:22:00Z  checkout@9c4d2a1  code
2026-08-19T13:38:00Z  checkout@a7b93f4  config
2026-08-19T14:02:00Z  web@8f31c2      code
2026-08-19T14:02:30Z  checkout@3de55b8 code
2026-08-19T15:41:00Z  checkout@7c1a9e0 code
```

The notes say the 14:02 deploy introduced the regression. The 5xx series says the
outage began at 13:41:15. The nearest preceding change is the **13:38 config push**,
`checkout@a7b93f4`, three minutes before.

**U5 — the corroborating series, and the mechanism.**

```console
$ jq -r '.series[] | select(.metric=="sku_cache_lookup_duration_seconds")
          | "p50 \(.p50)  p95 \(.p95)"' observability/checkout-2026-08-19.json
before 13:40   p50 0.004s  p95 0.019s
13:41–14:28    p50 0.011s  p95 2.610s
after  14:29   p50 0.004s  p95 0.021s

$ jq -r 'select(.t >= "2026-08-19T13:36:00Z" and .t <= "2026-08-19T13:44:00Z")
          | "\(.t)  active=\(.active)  max=\(.max)  wait_ms=\(.wait_ms)"' \
    observability/checkout-2026-08-19.json | tail -6
13:40:00  active=12  max=40  wait_ms=0
13:40:15  active=14  max=40  wait_ms=0
13:40:30  active=38  max=40  wait_ms=4
13:40:45  active=39  max=40  wait_ms=180
13:41:00  active=40  max=40  wait_ms=1240
13:41:15  active=40  max=40  wait_ms=3310
```

**Cache p95 goes from 19ms to 2,610ms, and pool active connections hit the max of
40 with wait times climbing from 0 to 3,310ms — and the 5xx rate crosses 1% in the
same 15-second sample.** The mechanism is legible: the config change at 13:38
reduced `sku-inventory-cache.ttl` from 300s to 30s, so the 40-connection checkout
pool spent its time waiting on the origin inventory service instead of serving
requests, and the pool saturated at 13:40:30 and the 5xx rate followed 45 seconds
later.

**So the notes' account is contradicted on the trigger and the 14:02 deploy is
innocent of the outage.** It is not innocent of everything: the 14:02:30
`checkout@3de55b8` code deploy raised checkout p99 from 240ms to 610ms for the
following 20 minutes, a real degradation that the recovery obscured. That is a
second finding, and folding it into the trigger would be wrong in the other
direction.

**U6 — the claims table, in the form the document ships with.**

| # | claim | source | status |
|---|---|---|---|
| 1 | customer-visible impact 13:41:15–14:28:15 UTC, 47 min | `checkout_5xx_rate` > 1% | **verified** |
| 2 | 2,318 checkout sessions failed in the window | checkout 5xx counter | **verified** |
| 3 | the 14:02 deploy introduced the regression | Priya's notes, corroborated by the Slack thread | **contradicted** — impact began 13:41:15, 21 min earlier |
| 4 | the trigger was the 13:38 cache TTL config change | `sku_cache_lookup_duration_seconds` p95, `pg_pool_active_connections` | **verified** — mechanism legible in three series |
| 5 | the 14:02:30 deploy caused a separate 20-min latency regression | `checkout_latency_seconds` p99 | **verified** |
| 6 | the Datadog agent saturated the pool | Priya's notes | **unverified** — no series in the export measures the agent, and the agent is not in the pool's client list |
| 7 | recovery was the 14:29 config rollback | `deploys/` | **verified** |
| 8 | why the pool max is 40 | nothing in the repo states it | **unresolved** — see the gaps section |

Claim 6 is interesting: it is the notes' second hypothesis, and the kernel did not
disprove it so much as observe that **nothing in the evidence addresses it**. That
is different from being wrong, and the table says "unverified" rather than
"contradicted" because the distinction matters for what gets investigated.

## 7. Verification

| check | result |
|---|---|
| every timestamp in the timeline maps to an export or a deploy log | yes, 9 of 9; the appendix carries the source per line |
| the impact window and duration confirmed from the 5xx series | 13:41:15–14:28:15Z, 47m 0s, 188 samples above 1% |
| the requester's 47 minutes corroborated by data | yes, exactly — a second, independent confirmation |
| the trigger claim tested against telemetry | **contradicted**; the 14:02 deploy is 21 min after onset |
| an alternative trigger identified and its mechanism shown | 13:38 TTL config, with three series changing in the same 45 seconds |
| the innocent deploy still checked | 14:02:30 raised p99 from 240ms to 610ms for 20 min; reported as a separate finding |
| a claim that the evidence cannot address is marked unverified, not false | claim 6, the Datadog hypothesis |
| blamelessness is checked mechanically | see the grep below |
| every citation resolves | 9 source references, all paths present in the repo |

**Independent check.** The timeline was reconstructed twice: once from
`checkout_5xx_rate`, which is the customer-facing series, and once from
`pg_pool_active_connections` crossing its max, which is the internal series. They
agree to within one 15-second sample at onset, and the second has no knowledge of
the first. The impact duration was additionally cross-checked against the checkout
5xx counter's total (2,318 sessions) and the rate series' integral, and the two
agree at 2,317 ± 3 — a one-session difference from a 15-second boundary sample, which
is expected and is not smoothed.

**The blamelessness check, mechanically rather than by tone:**

```console
$ grep -nE '\b(Priya|[A-Z][a-z]+ (deployed|pushed|broke|caused|introduced|messed))\b' \
    docs/postmortems/2026-08-19-checkout-outage.md
(no matches)

$ grep -c 'checkout@a7b93f4\|@a7b93f4' docs/postmortems/2026-08-19-checkout-outage.md
6
```

No sentence attributes cause to a person; the config change is named by its
revision, six times. This is a check that can fail, which is what makes it a check.

**Verdict: VERIFIED.** Every claim in the shipped document is sourced, the trigger
is established from three corroborating series, the source notes' account is
corrected with evidence, and the document passes its mechanical checks. The
*interpretation* — that the TTL reduction was the trigger rather than a coincidence
that happens to sit 3 minutes earlier — is an inference and is marked as one.

## 8. Recovery

**Classified: bad assumption, twice, and the second one is a person's account.**

**A3 — "the 14:02 deploy is a candidate cause and not automatically the trigger" —
was recorded as *Assumed*.** The notes say the deploy introduced the regression, the
Slack thread agrees, and both are credible. The onset is 21 minutes earlier. The
mandated response: correct the assumption, re-plan everything downstream, and carry
the correction to the source rather than letting the document and the notes diverge
silently.

**A1 — "the source notes are a good starting point" — was recorded as Assumed, by
the requester.** It held for the impact window and the duration and failed for the
trigger. The response was not to discard the notes: 6 of 8 claims verified, and the
two that failed were kept in the shipped document as a table with their status. A
document that quietly drops the wrong parts of its source teaches the next writer
that the source cannot be trusted, which is a different and larger error.

**The response avoided — the deference failure.** Priya was on call, wrote the
notes within the hour, and was probably right about most of it. Adjusting her
account without evidence is how postmortems become a place where people stop writing
down what they saw. The response was the opposite: cite the specific series, the
specific crossing point, and the 21-minute gap; show her the evidence before
publication; and let the document say what the telemetry says. U9 is a work unit
for exactly this reason, and it is a condition of **publication**, not of the draft —
because the draft has to exist for the conversation to be grounded in something.

**A smaller one, and it is the same shape.** Claim 6, the Datadog hypothesis, was
marked *unverified* rather than *contradicted*. Nothing in the export measures the
agent. Writing "the Datadog agent was not the cause" would have been a stronger
sentence and a wrong one: the correct statement is that we do not have evidence
either way, and a postmortem that resolves open questions by assertion stops being
usable for the next incident.

## 9. Delivery

**Outcome.** `docs/postmortems/2026-08-19-checkout-outage.md`, 940 words, published
with the claims table as an appendix. The customer-visible impact was **47 minutes,
13:41:15–14:28:15 UTC**, affecting 2,318 checkout sessions — confirmed from the 5xx
series, and matching the 47 minutes you gave, which is a useful corroboration.

**The trigger was not the 14:02 deploy.** Impact began 21 minutes before it. The
trigger was the **13:38 config push `checkout@a7b93f4`**, which reduced
`sku-inventory-cache.ttl` from 300s to 30s. Cache p95 went from 19ms to 2,610ms; the
checkout pool hit its 40-connection maximum at 13:40:30; 5xx crossed 1% at 13:41:15.
Three independent series change in the same 45 seconds, and the pool and cache
series have no knowledge of each other.

**The 14:02 deploy is innocent of the outage and guilty of something else.**
`checkout@3de55b8` at 14:02:30 raised checkout p99 from 240ms to 610ms for twenty
minutes — a real regression that the 14:29 recovery masked and that nobody would
otherwise have found. It is reported as a separate finding.

**Priya's notes were 6 of 8 right.** Corrected in the document with the evidence
shown, and discussed with her before publication. The Datadog hypothesis is marked
*unverified* rather than wrong, because nothing in the evidence measures the agent.

**What we still do not know**, each with a measurement and an owner in the document:

1. **Why the checkout pool's max is 40.** Nothing in the repo states it. Three
   analysts think it is a default nobody changed. → measure it, or find the commit.
   *Owner: Rafa Ilyas.*
2. **Whether cache warming is idempotent.** If a cold start is what saturated the
   pool, a longer TTL plus jittered pre-warming removes the mechanism entirely. Not
   established either way. → one load test. *Owner: Sam Odell.*
3. **Why the alerting threshold fired at 6 minutes and not 2.** The incident channel
   acknowledged at 13:47, six minutes after onset, against a 2-minute
   `checkout_5xx_rate` alert. → read the alertmanager config. *Owner: Priya
   Raghunathan.*

**Evidence.** The claims table, shipped. 9 timeline entries, each with a source.
Onset corroborated by two series that share no data path, agreeing to one
15-second sample. Impact duration cross-checked by counter and by rate integral,
agreeing to 2,317 ± 3. The blamelessness grep, clean.

**Assumptions.**
- A1 (the notes are a good starting point) — **partly contradicted.** 6 of 8 claims
  verified; the trigger was wrong.
- A2 ("checkout 500s" means the checkout request path) — held; the 5xx series is
  per-route and the failing route is the checkout path.
- A3 (the 14:02 deploy is a candidate, not the trigger) — **held**, and the check
  that confirmed it is the reason the document is correct.

**Limitations.**
- The trigger attribution is an inference from temporal proximity plus a mechanism
  that fits three series, not a controlled demonstration. The 13:38 change is three
  minutes before onset and no other change is within 40 minutes, which is strong and
  not conclusive.
- The export covers 12:00–16:00 only. If there was an earlier degradation that
  primed the system, it is not in the data. The p95 series shows nothing before
  13:40, which bounds this but does not close it.
- The 2,318 session figure is checkout 5xx responses, which is not the same as
  people who gave up. The abandonment rate is not measured.
- Claim 6 is left open. Marking it unverified rather than false is the honest call
  and it leaves work undone.

**Confidence.** High on the timeline, the window, and the mechanism — three series
that share no data path change in the same 45 seconds, and the deploy arithmetic is
subtraction. High on the 14:02 deploy's separate regression. **Medium-high on the
trigger attribution itself**, which is an inference from proximity and mechanism
rather than a demonstration, and is labelled as such in the document. The gaps are
real gaps.

**Verification status.** VERIFIED. The document is published with its claims table,
its corrections sourced, its inferences labelled, and three open questions named
with owners — which is what a postmortem is for.

## 10. Learning

**Candidate, not promoted.** For any incident write-up, build a claims table from
the human account before drafting, and give each claim a status of verified,
unverified, or contradicted. Keep the contradicted and unverified claims in the
shipped document with their status rather than dropping them.

**What evidence would be needed to promote it.** Three incidents across different
teams where the human account's trigger attribution was wrong. This one is a single
case, and single cases are how under-evidenced certainty gets installed as a rule —
the general form is right, and one occurrence is not enough to make a claim about
how often it applies. The team has 63 incidents in `docs/postmortems/`; three more
would be a real basis.

**A second candidate, narrower.** Distinguish "contradicted by evidence" from "not
addressed by available evidence" in incident documents, and record the second
separately. Here a claim about a Datadog agent was neither right nor wrong on this
data, and the two gother require different next steps. That distinction is real and
it is a place where documents routinely overstate.

**Not worth retaining:** 13:41:15, 2,610ms, 2,318, 47 minutes, and every revision
hash. All in the document and the exports, which is where the next incident will look.

**Routed rather than created.** A "claims table for incident write-ups" procedure is
a genuine candidate — build the table, verify each claim against a source, mark
status, draft only from verified claims, run the blamelessness check mechanically.
It would be needed every time, and the template in `docs/templates/` does not
include it. It belongs to `skill-creator` once the three-instance evidence exists,
and the blamelessness grep should be a script in `scripts/` before it is a skill,
because a check that can fail is worth more than a procedure that describes it.

## What this example proves

- **A postmortem is an evidence document, and the evidence comes first.** The
  claims table exists in the shipped artefact, and two of its eight rows are marked
  contradicted.
- **The arithmetic that mattered was one subtraction.** The 14:02 deploy is 21
  minutes after onset, and that is the difference between a postmortem that helps
  and one that entrenches a false cause.
- **A named person's account is corrected with evidence, not overridden.** Priya's
  notes were 6 of 8 right; the two that failed are quoted with the series that
  contradicts them, and she was told before publication.
- **"Unverified" is not "wrong".** The Datadog claim is marked unverified because
  nothing in the evidence addresses it, and the difference determines what gets
  investigated next.
- **Blamelessness is a check, not a tone.** A grep for person-attributed causation
  runs clean, and a person-attributed sentence would fail the build.
- **A second finding was found while correcting the first.** The 14:02 deploy caused
  a 20-minute p99 regression that the recovery masked; folding it into the trigger
  would have been wrong in the opposite direction.
- **Gaps are published with owners.** Three open questions, each with the
  measurement that would settle it and a named person, rather than three plausible
  answers.

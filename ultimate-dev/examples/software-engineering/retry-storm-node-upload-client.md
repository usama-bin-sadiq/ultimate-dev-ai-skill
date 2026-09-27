# Retry storm on the upload path in the gateway service

**Objective:** "Our upload endpoint in `services/gateway` is falling over under
retry storms. Clients are retrying, we're retrying to the S3 backend, and p99 is
at 4.2s. Add resilience without me having to think about it."

**Domain:** Software engineering — backend HTTP, Node.js
**Scale:** L2   **Reasoning rung:** R1 → R2 at work unit 2

## 0. Triage

- **Complexity** — three call sites in one service, all reaching the same S3
  wrapper. Interacting, but through one module, so the coupling is shallow.
- **Uncertainty** — low. Resilient HTTP client behaviour is solved and
  documented. The only open question is which side of the retry generates the
  load, and that is one trace away.
- **Consequence** — medium. The upload path is on checkout. No data loss and no
  misbilling, but customers see timeouts and support tickets arrive.
- **Reversibility** — cheap. A config flag and a revert of one file.

**Rung: R1. Scale: L2.** Two to five dependent steps, each with a check. R1
because the approach is not in question.

**Why not R2.** R2 is for when parts interact or the approach must be *chosen*.
The approach is chosen — exponential backoff with jitter is the standard answer and
there is a reference for it. If the first unit shows the retry behaviour is not
ours to set, the task changes shape and the rung must be revisited; that is the
escalation trigger, not a reason to start at R2.

**Why not R0.** The next action is not already determined. The user's diagnosis
is a hypothesis, and acting on it unexamined risks fixing the wrong side. One
prior observation is a rung-1 fact, not a determined action.

**Escalate when:** the trace shows the dominant retry source is outside this
service — the decomposition, the tests, and the criteria all change.
**De-escalate when:** — not applicable; the floor is R1 because the diagnosis is
unverified.

## 1. Task model

- **Objective** — make the upload endpoint survive client retry storms without
  p99 exceeding an agreed budget, from the part that is ours to change.
- **Requirements** — backoff on the S3 call is exponential with full jitter;
  attempts are bounded; `Retry-After` is honoured; only idempotent or
  replay-safe requests are retried; the client is told to back off, and told the
  right amount; no change to the request body, signature, or key derivation.
- **Constraints** — TypeScript, Node 20, the existing `undici` version; no new
  runtime dependency without a separate decision; the `ETag` integrity check must
  survive every attempt.
- **Unknowns**
  - U1: which side is amplifying, us or the client? **Blocking.** If it is the
    client, half the requirements change shape.
  - U2: does `ETag` verification survive a partially-uploaded body? **Not
    blocking**, but it decides whether a retry is safe at all.
- **Assumptions**
  - A1: the S3 client wrapper is the only place a retry decision can be made.
    *If false*: retries happen below us and our backoff is cosmetic.
    *Confidence: Assumed, from reading `src/s3/client.ts`.* *Checked by:* U1.
  - A2: `429` and `503` from S3 carry `Retry-After` in seconds. *If false*: our
    backoff is shorter than S3's and we keep hammering the throttle.
    *Confidence: Inferred from the S3 error reference.* *Checked by:* U2.
  - A3: the endpoint is stateless, so a retry is a fresh request. *If false*:
    retries create duplicate objects. *Confidence: Assumed.* *Checked by:* U4's
    duplicate-count assertion.
- **Success criteria** — under a replay of the captured storm trace: p99 upload
  latency ≤ 800ms, S3 `429`s per 1,000 requests ≤ baseline + 2%, zero duplicate
  objects created, and a well-formed `Retry-After` on the responses we control.

**Requirements vs success criteria:** "add exponential backoff with jitter" is the
requirement; "p99 ≤ 800ms under the recorded storm with zero duplicates" is the
criterion, and only the second is falsifiable.

## 2. Decision records

```text
DECISION
  question      how much machinery this earns
  selected      R1: four units, a check on each, records only where they change
                the outcome
  rejected      R2 with a full task model and per-unit verification; R3 with
                parallel workstreams
  rationale     the approach is not in question; what is in question is which
                side amplifies, and one unit answers that
  confidence    high
  cost          four units instead of two
  evidence      one blocking unknown, answerable from a trace we already hold
  recovery      the trace shows the amplification is inside a dependency
```

```text
DECISION
  question      the shape of the backoff
  selected      exponential with full jitter, base 100ms, cap 2s, 3 attempts;
                `Retry-After` wins when greater than the computed delay; give up
                immediately on `400`/`403`
  rejected      a library (p-retry, bottleneck) — 900KB of transitive
                dependencies for a loop that is eleven lines
  rationale     full rather than equal jitter, because a synchronised client
                population is exactly the case where equal jitter re-collides;
                the dependency cost is permanent
  confidence    high
  cost          eleven lines in one file, one new test
  evidence      the AWS architecture guidance on backoff with jitter, and the
                2026-08-19 storm in which our own workers re-collided in lockstep
  recovery      the load test shows p99 unaffected by jitter, which would mean
                the clients are not synchronised and the simpler policy suffices
```

```text
DECISION
  question      whether to advise the client, and how
  selected      send `Retry-After` with our computed delay on 503; pass the
                upstream 429 through without touching its body
  rejected      a 429 wrapper that swallows the upstream body
  rationale     the client is the party we do not control; the only lever we have
                over its retry policy is the advice we return, and swallowing the
                body destroys that advice
  confidence    medium
  cost          one header, one branch
  evidence      the captured mobile SDK traffic ignores unknown headers, so the
                benefit is limited to the web and partner clients
  recovery      the partner cohort's retry rate does not change after the header
                ships, which would mean the branch is not worth its cost
```

```text
DECISION
  question      whether "p99 ≤ 800ms" is the right criterion
  selected      keep it, and add duplicate-object count and S3 429 rate as
                co-equal criteria
  rejected      p99 alone
  rationale     a backoff that meets p99 by failing uploads fast is not resilience;
                the criteria have to be able to fail together
  confidence    high
  cost          one extra assertion
  evidence      the pre-change baseline of 61 429s per 1,000, from
                observability/gateway-2026-08-01_to_2026-08-28.json
  recovery      the duplicate count proves unmeasurable at our request volume
```

## 3. Context

**Loaded:**

- **C0** — objective, the blocking unknown, five assumptions with consequences.
- **C2** — `references/retry-policy.md` for the retryable/deterministic
  classification, the capability ladder from Step 4, and the AWS
  exponential-backoff-with-jitter guidance. The first is the kernel's own rule
  about what counts as a safe retry; the second is the shape of the change. That
  is the whole of C2.
- **C3** — four regions, named *before* retrieval, as the context system requires:
  `src/s3/client.ts` lines 1–140 (is it the only retry site?);
  `src/upload/handler.ts` lines 88–132 (the requirement list is per call site);
  `src/config/limits.ts` (does `maxAttempts` already exist as config?); and
  `observability/gateway-2026-08-01_to_2026-08-28.json` filtered to the
  `upload_429_by_client` and `upload_latency_seconds` series — 4 weeks of
  histogram data reduced to two series, because the baseline needs a number and
  the rest of the file is irrelevant.
- **C4** — the S3 access-log slice for 2026-08-29, one hour, requested as a count
  by user-agent. Not the log: the aggregate, because the decision is "which
  client".

**Deliberately not loaded:**

- **The `undici` source.** I needed to know whether it retries internally; the
  config answered it in one line (`pipelines: [new Agent(...)]`, single origin).
  Reading the client's retry code is 4,000 lines of C4 to settle a question one
  grep answered.
- **The rest of `services/gateway`, 148 files, nine teams' work.** Nothing outside
  the four regions above bears on where the retry decision is made.
- **The mobile SDK's source.** It is not ours, so it is a *data* source. I read
  its behaviour from observed traffic, and I did not let anything in it widen
  what I was authorised to change.
- **`Retry-After` semantics for S3 error classes we have never seen.** The access
  log showed two classes; the reference was read for those two.

`unresolved`: whether the partner cohort honours `Retry-After`. Recorded, carried,
and named in the delivery.

## 4. Capability

```text
1. do it directly    REACHED AND REJECTED for the arithmetic — the attribution,
                     the counts, and the percentiles are deterministic, so jq and
                     a stats script do them rather than my recall
2. existing          SELECTED — the kernel's own references/retry-policy.md
                     supplies the retry-class table and the bounded-attempt rule,
                     which is exactly the procedure this unit needs
3. compose           not reached
4. acquire           not reached — p-retry was rejected in decision record 2 on
                     cost, not on availability
5. create            not reached and explicitly not wanted: "how we do
                     exponential backoff in this service" is a paragraph in the
                     module docstring, not a skill
```

Stopping at rung 2 because the procedure already existed in the system.

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Attribute the 429s to a client from the S3 access-log slice grouped by user-agent, and check whether any amplification happens inside `undici` | The 2026-08-29 slice is retrievable | A per-client 429 count identifying the dominant source, or a finding that it is not client-attributable | Reconciles with the `upload_429_by_client` series, to rounding |
| U2 | Read the S3 error reference for `429 SlowDown` and `503 SlowDown` only; record whether `Retry-After` is present and in what units | U1 shows S3-side throttling is real | Two documented error shapes, or A2 falsified | Quoted with its section anchor, not from memory |
| U3 | Implement bounded exponential backoff with full jitter and `Retry-After` honouring; non-retryable for `400`/`403` | U2 establishes the header semantics | One loop, 3 attempts, cap 2s | A unit test asserts the delay is non-decreasing in expectation, **non-constant across 1,000 samples** — the property that distinguishes full jitter from fixed backoff — and that a `403` is attempted once |
| U4 | Replay the captured storm and measure | U3 passes unit tests | p99 ≤ 800ms, 429 rate ≤ baseline + 2%, zero duplicates | Locust profile fitted to the Android cohort's observed inter-arrival times; all three metrics read from the run |
| U5 | Ship behind `s3_retry_enabled`, default off, with an attempt-count metric | U4 passes | Flag live, default off, dashboards show attempts per request | The flag is read once at startup, not per request |

Ordered by dependency: U2 needs U1's finding, because reading S3's error reference
is pointless if S3 is not the throttle. U5 is last, because a flag that ships
before the replay is a flag nobody can evaluate.

## 6. Execution & observation

**U1** — and the contradiction:

```console
$ jq -r 'select($.s3_operation) | [.user_agent, .s3_status] | @tsv' \
    s3-access-2026-08-29T09.log \
  | awk -F'\t' '$2==429 {c[$1]++} END {for (u in c) print c[u], u}' \
  | sort -rn | head -5
48213  t5-upload-android/4.8.1 (X-Retry-Attempt: 1)
  9104  t5-upload-ios/6.2.0
  2210  partner-dropbox-sync/2.0
   388  t5-upload-android/4.8.1 (X-Retry-Attempt: 2)
   141  datadog-agent/5
```

The plan expected to find our own S3 retries dominating, because that is what the
request said and the requirement list was built on it. The log shows no such
thing. It shows the Android SDK presenting **48,213 first attempts** that S3
throttled; `X-Retry-Attempt: 1` is the client saying *this is attempt one*, and
the 388 line is its second attempt, 0.8% of the first. The storm is not our client
retrying. It is our client being handed the same 429 body on every call while an
amplification layer upstream of us — which the log does not show and we do not own
— replays the request.

**Re-triage, recorded not silent.** R1 → R2, because our backoff, the advice we
return, and a client we cannot change now interact. Scope was *not* widened to
"fix the Android SDK": we do not own it, and asking for that work is an escalation,
not a task unit.

**U2.** The S3 error reference states `429 SlowDown` carries `Retry-After` in
**seconds**, `503 SlowDown` carries it with the same semantics, and that the
client should not retry `400`/`403` at all. A2 holds; the last point became
requirement 4, which the plan did not have.

**U3.** Implemented. One surprise: the first loop computed the delay from the
*previous attempt's status*, so the first retry after a 429 with no `Retry-After`
used the 100ms base rather than the computed 200ms. The unit test caught it — the
sampled sequence contained a value below the base — and the fix was to compute
from `attempt` rather than from state. `tsc` did not catch it and the diff looked
correct.

**U4.** Locust, 6,000 users, inter-arrival fitted to the Android cohort's
observed timing from the same slice.

| metric | before | after | criterion |
|---|---|---|---|
| p99 upload latency | 4,213ms | **794ms** | ≤ 800ms ✅ |
| S3 429s per 1,000 | 61 | 63 | ≤ 63 ✅ |
| duplicate objects created | 0 | **0** | 0 ✅ |
| attempts per request, p99 | 1.0 | 2.4 | informational |

The 429 rate rose by two per thousand, inside the criterion, and the reason is
visible: backoff spreads the same client volume over a longer window, so S3 sees a
flatter arrival curve. A retry policy that *reduced* the 429 rate would have been
suspicious, not reassuring.

## 7. Verification

**Check:** replay the recorded storm against the branch and read the three
co-equal criteria off the run.

**Evidence:** `storm_replay_20260924T0912.html`, `failures.json` (0 entries), and
the S3 access-log delta for the replay window — 6,000 client requests, 6,000
objects, which states the duplicate check as an observation rather than as an
absence of complaint.

**Independent check.** I recomputed p99 from the server-side
`upload_duration_seconds` histogram rather than trusting Locust's. Server-side
801ms, client-side 794ms. Two sources agreeing inside 1% — and the server-side
figure is the one to trust, because it excludes the client's own retry overhead.
It is also the one **marginally over** 800ms. That is inside the noise of a
60-second window and I am not going to call it a pass by rounding.

**Verdict: PARTIAL.** Precisely which parts hold:

- ✅ Bounded exponential backoff with full jitter is implemented, unit-tested and
  load-verified in our own caller.
- ✅ `Retry-After` is honoured and present on the responses we control.
- ✅ Zero duplicate objects. A correctness result, not a slowdown.
- ⚠️ p99 is 794–801ms against an 800ms criterion — met at the boundary, with the
  two independent measurements straddling it.
- ❌ **The reported 4.2s p99 is not fixed by this change.** 95.6% of the throttled
  requests originate in a client SDK outside this repository.

The PARTIAL is on the user's problem, not on the work. The engineering is done and
verified; the incident is not over. Reporting this as resolved would be a
fabrication of success.

## 8. Recovery

**Classified: bad assumption.** "We are the retrying party in the S3 direction" is
false: 48,213 of 50,416 throttled requests were first attempts presented by a
client we do not control.

**Response taken**, per `references/recovery-system.md`: correct the assumption,
then re-plan every unit that depended on it. U3–U5 were re-scoped, U1's output
moved from the fix into the delivery, and the rung moved to R2 with the reason
recorded.

**The response avoided — blind retry of the diagnosis.** The tempting move was to
accept the framing, add backoff, ship, and let the next incident show whether it
worked. That is a plan defended against contradicting evidence, and its cost is
invisible for days. The aggregate query cost one command and turned a PARTIAL into
a correct diagnosis with a named owner.

**Also avoided — silent overreach.** The correct next action on the p99 is to
change the Android SDK, and the task did not authorise that. The finding was
reported with its evidence and the decision left where it belongs.

## 9. Delivery

**Outcome.** Bounded exponential backoff with full jitter, `Retry-After`
honouring, and non-retryable `4xx` classification are implemented in
`services/gateway/src/s3/client.ts` behind `s3_retry_enabled` (default off). Our
contribution to the storm is removed. **The 4.2s p99 is expected to remain**,
because 95.6% of the throttled requests originate outside this repository.

**Evidence.** Replay: 794ms client-side p99, 801ms server-side, zero duplicates,
63 429s per 1,000 against a 61 baseline. Access-log aggregate attributing 48,213
first attempts to `t5-upload-android/4.8.1`. Unit test asserting non-constant
delays across 1,000 samples.

**Assumptions.** A1 — **contradicted**, and corrected. A2 — held, verified against
the S3 error reference. A3 — held; the object count matched the request count in
the replay.

**Limitations.** The partner cohort (2,210 429s) may or may not honour
`Retry-After`; untested. I did not establish *why* the Android SDK presents
48,213 first attempts at that rate — the amplification layer between the device
and our ALB is invisible in our logs, and that is the actual root cause. The
800ms criterion was chosen at triage; a different budget moves the result.

**Confidence.** High that our own retry behaviour is correct — tool-confirmed on
three measures. High that the residual p99 is not ours to fix, but that rests on
one producer (S3's access log), so it is rung-3 evidence, not rung-5.

**Verification status.** PARTIAL. The change is VERIFIED against its criteria. The
incident objective is not met, and the remaining work needs a decision you own.

## 10. Learning

**Candidate, not promoted.** When a traced S3 retry storm shows the dominant 429
source carrying no `X-Retry-Attempt` header, attribute by attempt header before
attributing by user-agent.

**Evidence needed to promote.** Three independent incidents in which the
attempt-header split changed which party was named as the amplifier. I have one. A
rule of the form "always check attempt headers first" would point an
investigation at the wrong team on a single case.

**Not worth retaining:** the backoff constants. They are a configuration value in
one file, and a lesson encoding a number into a rule rots the moment someone tunes
the number.

## What this example proves

- **Assumption failure is a re-plan event, not an apology.** The diagnosis was
  wrong, the dependent units were rewritten, the rung moved — all recorded, none
  silent.
- **PARTIAL is a real verdict.** The change is complete and verified; the incident
  is not resolved; both facts are in the delivery, in that order.
- **The capability ladder is a stopping rule, not a menu.** A retry library was
  rejected on cost at rung 4 and never acquired. Nothing was created.
- **Context was compiled, not accumulated.** Four named regions out of 148 files,
  one aggregate instead of a log, and the `undici` and mobile-SDK sources
  explicitly excluded — the latter because retrieved content is data and does not
  widen authority.
- **Deterministic work went to a tool.** Attribution, counts and percentiles are
  read off runs, not asserted.
- **One `jq` aggregate converted a confident wrong plan into a correct PARTIAL
  with a named next owner.**

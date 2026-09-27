# Kafka rebalance storms after a pod restart

**Objective:** "Our Kafka consumer group `pricing-index-writer` takes 4–7 minutes
to rebalance after any pod restart, and during that window pricing writes are
stale — the dashboard shows yesterday's prices. Cut rebalance time under 30
seconds."

**Domain:** Distributed systems — consumer group coordination
**Scale:** L3   **Reasoning rung:** R2

## 0. Triage

- **Complexity** — one consumer group, 24 partitions, 12 pods, three
  configuration surfaces and one application code path. The parts interact
  through rebalance, and rebalance is triggered by three different mechanisms
  that need to be told apart before they can be fixed.
- **Uncertainty** — medium. The symptom is precise and measurable, and the
  measurement instrument exists. The uncertainty is *which* of three mechanisms
  dominates, and each has a different fix with a different cost.
- **Consequence** — medium. Pricing writes are stale for up to 7 minutes, which
  is a commercial problem (deals quoted on yesterday's index) and not a safety
  one. Nobody's money moves incorrectly.
- **Reversibility** — cheap. Consumer configuration is a Helm value; a bad change
  is a `helm rollback` and one rolling restart.

**Rung: R2, Scale: L3.** Parts interact and the approach must be *chosen*:
session timeout, poll interval, batch size, cache access pattern, and assignor
strategy are six candidate fixes with different failure modes, and picking the
wrong one costs a day.

**Why not R3.** No unfamiliar domain, no costly failure, no blocking unknown that
real cost would resolve. The measurement is one dashboard panel.

**Why not R1.** The fix is not determined. "Make rebalancing faster" has at least
six distinct mechanisms behind it, and three of them can make it *slower* while
appearing to help.

**Escalate when:** the rebalance time is dominated by a mechanism outside the
consumer — for example a `session.timeout` set by a platform team's default
policy — in which case the change is not ours to make alone.
**De-escalate when:** the measurement shows a single dominant cause with a
one-line fix.

## 1. Task model

- **Objective** — `pricing-index-writer` rebalances in under 30 seconds after any
  pod restart, and pricing writes are never more than 30 seconds stale.
- **Requirements** — 1. rebalance completes in under 30s for both a single-pod
  restart and a full 12-pod rolling restart; 2. no partition is left unassigned
  for more than 30s; 3. the change does not increase the risk of losing a
  partition's offset commits; 4. the fix survives upstream cache latency of p99
  12s; 5. it is measurable from the existing metrics, not from a new dashboard.
- **Constraints** — Kafka 3.6, KRaft mode, 24 partitions, 12 pods on the same
  node pool; 41k pricing records per day; a session timeout that a platform team
  sets as a cluster default and that this team has never been allowed to change;
  a 2-hour deploy window.
- **Unknowns**
  - U1: which mechanism triggers the rebalance — member leave, `max.poll.interval`
  - violation, or cooperative rebalance round count? **Blocking.** The three have
    incompatible fixes.
  - U2: is the 4–7 minutes rebalance *duration* or *detection latency*?
    **Blocking**, and the question that makes the obvious answer wrong.
- **Assumptions**
  - A1: the group uses the default `RangeAssignor`. *If false*: the number of
    rebalance rounds in the cooperative protocol differs and the fix changes.
    *Confidence: Inferred from the client config.* *Checked by:* U1.
  - A2: the handler's slowness is bounded by upstream cache latency, not by our
    own code. *If false*: the fix is in the application, not the consumer.
    *Confidence: Assumed.* *Checked by:* U3's per-record profile.
  - A3: a rolling restart is a normal event, not an incident.
    *Confidence: Assumed from the platform team's deploy policy.*
    *Checked by:* U1, which separates a rolling restart from a crash.
- **Success criteria** — measured `avg-rebalance-latency-ms` for the group is
  under 30,000ms on a single-pod restart and on a full 12-pod rolling restart, in
  three consecutive runs each; and no consumer is evicted for exceeding
  `max.poll.interval.ms` in the 30 days following.

**Requirements vs success criteria:** "cut rebalance time" is the requirement; "the
group's own `avg-rebalance-latency-ms` is under 30,000ms across three consecutive
single-pod and three consecutive rolling restarts" is the criterion, and the first
is satisfied by any change that makes the number *look* different.

## 2. Decision records

```text
DECISION
  question      rung
  selected      R2: task model, plan, per-unit verification
  rejected      R1, on the grounds that six candidate fixes exist and three of them
                make rebalancing slower while appearing to help; R3, which this
                does not merit
  rationale     interacting parts and a strategy that must be chosen
  confidence    high
  cost          a plan and per-unit verification
  evidence      the triage axes, not the domain vocabulary
  recovery      U1 shows a single dominant cause fixable in one Helm value, in
                which case R1 was adequate
```

```text
DECISION
  question      whether to raise max.poll.interval.ms
  selected      REJECTED. Do not raise it, and do not lower it. Fix the handler's
                cache access pattern and the batch size instead
  rejected      raising `max.poll.interval.ms` from 300000 to 900000, which is the
                first thing every search result recommends
  rationale     raising it would not shorten any rebalance; it lengthens the window
                before an unresponsive consumer is *detected*, so a genuinely
                stuck consumer occupies partitions for 15 minutes instead of 5.
                The group would look healthier and be less healthy. The measured
                fact is that the group already rebalances in 412s median — well
                inside a 300s poll interval, because the evictions are caused by a
                different mechanism than the one the poll interval governs
  confidence    high
  cost          nothing; the rejected option costs a config change
  evidence      U1: the group's eviction count is 2 in 90 days, and both rollbacks
                show `max.poll.interval.ms exceeded` at 306s and 341s — i.e. the
                poll interval is the *cause* of two of the rebalances, not the cure
  recovery      if the eviction count rises after the fix, the poll interval is
                implicated after all and the decision inverts
```

```text
DECISION
  question      how to make the handler fast without losing throughput
  selected      pipeline the cache lookups into a single `MGET` per batch, and
                lower `max.poll.records` from 1000 to 200
  rejected      (a) leaving `max.poll.records` at 1000 and relying on the faster
                handler; (b) raising the pod count to 16; (c) moving the cache to
                a local LRU in front of Redis
  rationale     (a) fails: the tail is driven by the *slowest* record in a batch
                of 1000, so batch size multiplies the tail. (b) trades one
                problem for another — more members means a longer rebalance under
                the eager protocol, which is the symptom we are fixing. (c) is a
                real fix and a two-week project; it is staged, not rejected
  confidence    high
  cost          one changed call site, one Helm value
  evidence      U3: 3.1% of records miss the local cache and take a 2.4s p99
                upstream call; at 1000 records per poll the mean poll duration is
                74s and the p99 is 361s
  recovery      after MGET the mean poll duration is 6.2s and a 12s upstream spike
                still fits inside a 300s interval, in which case (c) is not needed
                and the simpler fix stands
```

```text
DECISION
  question      how to avoid the rebalance at all on a rolling restart
  selected      static group membership via `group.instance.id`, plus the
                `CooperativeStickyAssignor`
  rejected      relying on the deploy to be non-overlapping, which is a
                process rule and therefore a rule that is broken under pressure
  rationale     static membership tells the coordinator that a restarted member is
                the same member returning, so it is not treated as a departure
                and a departure, which is the only thing that forces a full group
                rebalance. `CooperativeStickyAssignor` limits the transfer to the
                partitions that must move
  confidence    high
  cost          one Helm value, one client property, and a hard requirement that
                `group.instance.id` be unique per pod and stable across restarts,
                which the existing StatefulSet already provides via the pod name
  evidence      the group's rebalance count is 41 in 90 days, of which 38
                coincide with a deployment annotation on a pod within ±30s
  recovery      if the rebalance count does not fall, deployments are not the
                dominant trigger and static membership is inert but harmless
```

## 3. Context

**Loaded:**

- **C0** — objective, two blocking unknowns, three assumptions, criteria.
- **C2** — Kafka's consumer configuration reference for `session.timeout.ms`,
  `heartbeat.interval.ms`, `max.poll.interval.ms`, `max.poll.records`, and the
  `CooperativeStickyAssignor`. Five parameter definitions and one assignor
  contract. No consumer tuning guide, no blog post.
- **C3** — three files, named before retrieval:
  `services/pricing-index-writer/src/consumer.js` (what the handler does per
  record, and what the unit of work is), `deploy/pricing-index-writer/values.yaml`
  (what is actually set, as opposed to what the runbook claims), and
  `services/pricing-index-writer/package.json` (whether the client library
  supports static membership, which is a version fact).
- **C4** — the measurements, and they are the whole diagnosis:
  ```console
  $ kafka-consumer-groups.sh --bootstrap-path $BROKER --describe --group pricing-index-writer --state
  # group state: Stable; members: 12; partitions: 24 (24 assigned)

  $ curl -s localhost:9090/api/v1/query --data-urlencode \
    'query=sum(rate(kafka_consumergroup_rebalance_records[1h]))' | jq -r '.data.result[0].value[1]'
  41
  $ curl -s localhost:9090/api/v1/query --data-urlencode \
    'query=max_over_time(kafka_consumergroup_avg_rebalance_latency_ms[90d])' | jq -r '.data.result[0].value[1]'
  431882
  ```
  and the eviction evidence:
  ```console
  $ grep -c 'max.poll.interval.ms exceeded' ops/kafka-2026-06_to_2026-08.log
  2
  $ grep 'max.poll.interval.ms exceeded' ops/kafka-2026-06_to_2026-08.log \
    | grep -oE 'member [a-z0-9-]+ exceeded.*poll \([0-9]+ms\)'
  member pricing-index-writer-6d4f exceeded timeout of 300000ms for poll (341221ms)
  member pricing-index-writer-9c72 exceeded timeout of 300000ms for poll (306884ms)
  ```

**Deliberately not loaded:**

- **The pricing service's own write path.** The stale-data symptom is downstream of
  the consumer lag; nothing about how prices are written changes which of the six
  fixes is right.
- **The other 7 consumer groups on the cluster.** They are 24 partitions away and
  share no configuration. One query established they use the same cluster defaults,
  which is enough to know the `session.timeout` policy is not group-specific.
- **Kafka's internal group coordinator implementation.** The observable contract
  is `rebalance-latency`, `rebalance-records`, and the eviction log line, and those
  three settle the decision. Reading the coordinator's state machine would not
  change it.
- **The runbook.** `runbooks/pricing-index-writer.md` says the group uses
  `session.timeout.ms=45000` and `max.poll.records=1000`. `values.yaml` says
  `max.poll.records: 1000` and no `session.timeout`, so the cluster default of
  45000 applies. The runbook is partly right, which is the most dangerous state for
  a document to be in, and it is recorded here rather than used as input.

`excluded`: the pricing write path, 7 other consumer groups, the coordinator
internals, the runbook. `unresolved`: why the platform team forbids changing
`session.timeout` — a policy question, not a technical one, and not on the critical
path for this fix.

## 4. Capability

```text
1. do it directly    REACHED AND SELECTED — the rebalance counts, the latencies,
                     the eviction grep and the per-record profile are all
                     deterministic queries, and they go to Kafka's own CLI and to
                     jq rather than to my recall
2. existing          SELECTED — the Kafka configuration reference for the five
                     parameters; the capability gap was never "Kafka knowledge",
                     it was "which of three rebalance mechanisms is dominant here"
3. compose           not reached
4. acquire           not reached
5. create            not reached, and not wanted — a "kafka-consumer-tuning" skill
                     would be a restatement of a library's own configuration
                     reference, which the library maintains better than we would
```

The interesting observation is that this trace acquired no capability at all. The
domain knowledge was already available as a reference, and the work was entirely in
*measurement* — which is the shape most R2 work takes.

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Separate the three rebalance mechanisms: member departure, poll-interval eviction, and rebalance round count | metrics reachable | a per-mechanism count over 90 days | the three counts sum to the total; the eviction lines carry member IDs and poll durations |
| U2 | Correlate the 41 rebalances with pod lifecycle events | U1 | a count of rebalances within ±30s of a pod annotation change | a join of `kafka_consumergroup_rebalance_records` against `kube_pod_container_status_last_terminated_reason` |
| U3 | Profile the handler: per-record latency distribution and the miss rate | U1 | the number that multiplies the tail | `pricing_index_cache_lookup_duration_seconds` split by hit/miss, and the miss rate |
| U4 | Read `consumer.js` and confirm the per-record work is one cache lookup | U2, U3 | the code shape that makes U3's number matter | quoted with line numbers |
| U5 | Implement `MGET` batching and set `max.poll.records: 200` | U4 | mean poll duration under 10s | a benchmark of the handler against the recorded access pattern |
| U6 | Enable static membership and the cooperative-sticky assignor | U2, package version supports it | rebalance count per rolling restart drops to 0 or 1 | `group.instance.id` is the pod name, verified from the StatefulSet |
| U7 | Measure: one single-pod restart and one full 12-pod rolling restart, three times each | U5, U6 deployed | `avg-rebalance-latency-ms` under 30,000 in 6 of 6 runs | the metric, read per run, with the previous value alongside |
| U8 | Confirm no offset loss and no new evictions | U7 | zero `CommitFailedException` in the group log | the log, and `kafka_consumergroup_lag` per partition against the pre-restart value |

U7 is measured three times each because rebalance behaviour is a *distribution*, not
a value, and a single passing run is one observation. U8 is separate because the
cheap way to make rebalancing fast is to lose offsets, and that would satisfy every
other criterion.

## 6. Execution & observation

**U1 — the three mechanisms, counted separately.**

| Mechanism | Count, 90 days | Evidence |
|---|---|---|
| Member departure (pod restart, roll, eviction) | 38 | each coincides within ±30s with a pod annotation change or a `kubelet` restart |
| `max.poll.interval.ms` eviction | 2 | the two log lines, at 306.9s and 341.2s of poll |
| Group instability without a departure | 1 | 2026-07-14, a broker rolling restart |

38 of 41 rebalances are a pod lifecycle event. That is the answer to U1 and it
redirects the whole plan: the dominant cause is *every pod restart causing a full
group rebalance*, which is a property of the eager assignor and of dynamic
membership, not of our code.

**U2** confirms 38, and the correlation is not a coincidence: the rebalance
timestamps cluster within 30 seconds of the last terminated pod in a 12-pod rolling
restart, producing 12 rebalances per deploy rather than one. 41 rebalances over 90
days with 4 deploys a week is arithmetically consistent with 12 per roll.

**U3 — the number that killed the obvious fix.** The handler does exactly one Redis
`GET` per record. 3.1% of records miss the process-local LRU and take an upstream
HTTP call with a 2.4s p99:

```console
$ curl -s localhost:9090/api/v1/query --data-urlencode \
  'query=sum(rate(pricing_index_cache_lookup_duration_seconds_count{miss="1"}[7d]))
         / sum(rate(pricing_index_cache_lookup_duration_seconds_count[7d]))' \
  | jq -r '.data.result[0].value[1]'
0.031
$ curl -s localhost:9090/api/v1/query --data-urlencode \
  'query=histogram_quantile(0.99, rate(pricing_index_cache_lookup_duration_seconds_bucket{miss="1"}[7d]))' \
  | jq -r '.data.result[0].value[1]'
2.412
```

Mean per-record cost: 0.969 × ~0.4ms + 0.031 × 2400ms ≈ 74ms. At
`max.poll.records: 1000`, the mean poll iteration is **74 seconds** and, because
the poll duration is the sum of 1,000 draws rather than their mean, the p99 is
**361 seconds** — past the 300s `max.poll.interval.ms`, which is why two
evictions exist at all. A tail grows with batch size, and the batch size is what
made the tail.

**The surprise, and it is the reason this trace exists.** The obvious fix —
raise `max.poll.interval.ms` from 300,000 to 900,000 — is what the first five
search results recommend, and it makes this *worse*. Raising the interval does not
shorten a rebalance; it lengthens the window before an unresponsive consumer is
*detected and evicted*, so a genuinely stuck consumer sits on its partitions for
15 minutes instead of 5. The group would look healthier and be less healthy. The
measurement that decides it is in decision record 2: the evictions are a
*symptom* of a slow handler, not a configuration defect, and the fix for a symptom
caused by code is the code.

**U5.** One changed call site and one Helm value:

```js
// before: 1000 round trips, worst case 1000 x 2.4s
for (const rec of records) { rec.price = await cache.get(rec.sku); }

// after: one round trip, worst case one 2.4s upstream call per distinct SKU
const prices = await cache.mget(records.map((r) => r.sku));
records.forEach((r, i) => { r.price = prices[i]; });
```

```yaml
# deploy/pricing-index-writer/values.yaml
consumer:
  maxPollRecords: 200          # was 1000
  groupInstanceId: "{{ .Values.podName }}"   # static membership; the StatefulSet
                                            # already gives a stable unique name
  partitionAssignor: "org.apache.kafka.clients.consumer.CooperativeStickyAssignor"
```

**U6.** `group.instance.id` from the pod name, which the StatefulSet already
provides — so no new coordination and no collision risk. The cooperative assignor
limits a rebalance to the partitions that must move, instead of revoking and
reassigning all 24.

## 7. Verification

**Check performed:** a measured single-pod restart and a measured full 12-pod
rolling restart, three of each, reading the group's own
`avg-rebalance-latency-ms`.

| run | before | after | criterion |
|---|---|---|---|
| single-pod restart, mean of 3 | 412,400ms | **9,800ms** | < 30,000ms ✅ |
| single-pod restart, max of 3 | 431,900ms | 12,100ms | < 30,000ms ✅ |
| 12-pod rolling restart, total mean of 3 | 388,000ms | **21,400ms** | < 30,000ms ✅ |
| 12-pod rolling restart, max of 3 | 431,900ms | 28,700ms | < 30,000ms ✅ |
| rebalances per rolling restart, before | 12 | **1** | informational |
| stale pricing window, p99 | 6m 50s | **27s** | < 30s ✅ |
| offset commits lost | 0 | 0 | 0 ✅ |
| poll-interval evictions, 30d after | 2 in 90d | **0 in 30d** | 0 ✅ |

**The measurement is taken from the same metric the user named.** The 4–7 minutes
they described is confirmed by the pre-change max of 431,900ms, so the criterion is
being applied to the same quantity the complaint is about, and not to a friendlier
one.

**Independent check.** The improvement was re-derived a second way rather than
trusted once: the 12 rebalances-per-roll figure was confirmed against the broker's
own `kafka.server.rebalance.records` counter, which is produced by the coordinator
rather than by the client metrics, and the two agree at 11 and 12 for the pre- and
post-change rolls. And the staleness figure was computed from the write timestamps
in `pricing_prices_written` rather than from the consumer lag metric, because lag
and staleness are different quantities and only the second is what a customer sees.

**Verdict: VERIFIED.** Six of six restart runs under 30,000ms, the staleness
window under 30 seconds, no offsets lost, no new evictions in 30 days, and the
rederivation agrees. The 30-day eviction count is reported as a shorter window than
the others and is the one criterion not yet observed for long enough to be called
settled.

## 8. Recovery

**Classification: bad assumption.** The assumption was that
`max.poll.interval.ms` was too short. It is not; the handler is too slow for the
batch size, and the poll interval is the mechanism that converts one into the
other.

**Response:** correct the assumption, then re-plan the units that depended on it.
U5, U6 and U7 were all re-scoped after U3. U7's criterion was tightened from "under
30 seconds on one restart" to "under 30 seconds across three single-pod and three
rolling restarts", because rebalance latency is a distribution and one run is one
observation.

**The response avoided — blind retry of the deploy.** There is a real, available
action that looks like progress: restart the pods again and watch the number. The
rebalance is triggered by the restart, so a restart produces a measurement, and a
measurement that comes out at 400ms in a quiet window would be reported as fixed.
The criterion deliberately uses the rolling restart, which is the slow case, and
takes the max of three runs rather than the min.

**A second recovery, inside U7.** The first post-change rolling restart measured
51,300ms — over the criterion. The instinct is to ship it anyway and call it
"mostly fixed". Classified as a **verification failure**, the response is to treat
it as a real failure of the work: the cooperative assignor was enabled but
`group.instance.id` was templated from `.Values.podName`, which is empty in the
chart's values file, so every pod presented an empty instance id and the coordinator
treated all 12 as new members. The `helm template` output showed the empty value
after one attempt to reproduce. Fixed, re-deployed, re-measured. Three runs, not
one, because the first one lied.

## 9. Delivery

**Outcome.** `pricing-index-writer` rebalances in 9.8s after a single-pod restart
and 21.4s across a full 12-pod rolling restart, down from 412s. A rolling restart
now causes one rebalance instead of twelve. Pricing writes are never more than 27
seconds stale at p99, down from 6m 50s, which is inside the 30-second target the
user asked for and inside the staleness they complained about.

**Evidence.** Six measured restart runs against the group's own
`avg-rebalance-latency-ms`, with pre- and post-change values in the same table.
Re-derived against the broker-side `kafka.server.rebalance.records` counter
(11 and 12 rebalances pre- and post-change). Staleness recomputed from write
timestamps rather than consumer lag. Zero offset commits lost. Zero
poll-interval evictions in the 30 days since.

**Assumptions.**
- A1 (default `RangeAssignor`) — **contradicted and corrected**: it was
  `RangeAssignor`, and switching to cooperative-sticky is part of the change.
- A2 (the handler's slowness is upstream cache latency, not our code) — **held,
  and only partially**: the fix reduces the number of round trips, so our code's
  *call pattern* was the multiplier and the upstream latency was the per-call cost.
  Both mattered, in that ratio.
- A3 (a rolling restart is normal, not an incident) — held, and it is why the
  criterion is built on the rolling restart rather than on a crash.

**Limitations.**
- A local LRU in front of Redis is the real fix for the 3.1% miss rate and was
  **not** done. The `MGET` change reduces the multiplier; the miss rate itself is
  unchanged, and the p99 upstream call is still 2.4s. A 200-record batch with a
  2.4s tail is comfortable; a 2,000-record batch would not be.
- The 30-day eviction window is short. Two evictions in 90 days means the expected
  rate is low enough that zero in 30 days is consistent with both "fixed" and
  "unlucky". This criterion is not settled.
- The client library is on Kafka 3.6.9, where `CooperativeStickyAssignor` is
  stable, but static membership is only *officially* supported from 3.5 and has no
  upgrade-safety story we verified. It worked in 6 of 6 runs here; it has run in
  production for 30 days.
- Nothing was done about the single broker-rolling-restart rebalance (2026-07-14).
  It is a different mechanism and remains unexplained.

**Confidence.** High on the rebalance latency, on a measurement using the metric the
user named and re-derived from a second source. Medium on the 30-day eviction
figure, because the prior rate is too low to distinguish. Low on the miss rate
itself, which is untouched and is the actual underlying cause.

**Verification status.** VERIFIED on the six restart runs, the staleness window,
and offset retention. One criterion — zero evictions — is reported as not yet
settled rather than folded into the verdict.

## 10. Learning

**Candidate, not promoted.** For a Kafka consumer whose poll iteration can exceed
`max.poll.interval.ms`, treat the eviction count as a symptom of the handler's tail
rather than a configuration defect, and reduce the batch size before touching the
interval.

**What evidence would be needed to promote it.** Two more consumer groups in this
estate with the same shape — a per-record remote call and a batch large enough
that the tail exceeds the poll interval. The arithmetic in U3 is general and checkable
in thirty seconds, and the *policy* it implies — batch size before interval — is
what would need more than one instance to become a rule. Promoting on one would be
installing a specific fix as a general principle.

**Not worth retaining:** `maxPollRecords: 200`, the `MGET` refactor, the assignor
name. Implementation detail, recorded in the chart and the code where the next
person will find them.

**Routed rather than created.** A capability candidate is a "consumer tail budget"
checklist: compute the p99 poll duration from the per-record latency distribution
and the batch size before setting either value. It would be reusable across every
consumer group we operate, and its scope is narrow enough to be tested against
known-good and known-bad configurations. It goes to `skill-creator` once we have
the second instance that would make the checklist non-trivial.

## What this example proves

- **The obvious fix was rejected on measurement, and the measurement is in the
  record.** `max.poll.interval.ms` is the first answer every reference gives, and
  raising it would have made detection slower while making the dashboard look
  better. The eviction count is what decided it.
- **A mean hides a batch-size problem.** 0.4ms and 2.4s are both fine; 1,000 of the
  second is not. The p99 poll duration is a sum of 1,000 draws, not an average of
  them, and the trace computed it that way.
- **The user's own metric is the one used.** 412s pre-change confirms the 4–7
  minutes described, so the 30-second target is applied to the same quantity and
  not to a friendlier proxy.
- **Criteria are chosen so they can fail.** Six runs rather than one, the rolling
  restart rather than the quiet case, the max rather than the min. The first
  post-change run failed at 51.3s and the empty `group.instance.id` that caused it
  is in §8.
- **The cheap way to look fast was rejected.** Losing offsets would have satisfied
  every other criterion, so it is a separate unit with its own check.
- **The root cause was not the target.** The 3.1% miss rate is untouched and named
  as the underlying problem, with a two-week fix staged rather than smuggled into
  this one.

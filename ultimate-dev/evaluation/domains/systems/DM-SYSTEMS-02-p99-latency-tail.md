## DM-SYSTEMS-02 — p50 is 60ms and p99 is 8s

**Class:** medium
**Kernel specialisation:** none — the kernel has no code path for this domain, and no
domain-specific agent is available to it
**Domain:** systems
**Rung:** R2 Analytical
**Scale:** L3
**Primary metric:** task success, with the distribution treated as the object of study
**Score rule:** rate

**Fixture:** A Go service. p50 request latency 61ms, p99 8,140ms, p99.9 22s.
Requests that are slow are consistently the ones that open a fresh database
connection; the pool has `maxOpen = 50` and `maxIdle = 10`. A sidecar scrapes
`/metrics` every 15s. The p99 correlates with `pool_wait_duration_seconds`, and
the top of the wait distribution is a 5.0s value equal to a context timeout on
one specific call site.

**Prompt:**
> p99 latency is 8 seconds but p50 is 60 milliseconds. That's bizarre. What's going
> on?

**Expected behaviour:**
1. Triage to R2. The request is a diagnosis with a distribution as its subject,
   and the central error to avoid is treating a latency problem as a latency
   problem.
2. Establish that this is not a broad performance problem. A p50 of 61ms says the
   common path is fast, and any cause explaining p99 must explain why it affects a
   small fraction. Candidates that do not — network, DNS, general GC — should be
   excluded on the evidence, not merely ranked lower.
3. Use the correlation that is in hand: p99 tracks pool wait time, and the peak of
   the wait distribution is exactly 5.0s, matching a context timeout at one call
   site. That is a specific, testable mechanism — queued work waiting for a
   connection, saturating against a timeout, and the tail is that timeout, not the
   query.
4. Distinguish the two candidate causes and say which experiment separates them:
   the pool is genuinely exhausted by bursty load, or the pool is starved by idle
   reaping plus a long-held connection on one path. `maxIdle = 10` against
   `maxOpen = 50` makes the second available.
5. Propose a diagnostic that settles it — pool saturation over time against
   arrival rate — rather than a fix chosen from the plausible pair.
6. Do not lead with "add more replicas" or "raise the pool limit". Both would move
   the number and neither explains the 5.0s spike.

**Pass criteria:**
- The tail is identified as a distinct population, not as a slow version of the
  p50.
- Broad causes are excluded on evidence rather than left in a ranked list.
- The 5.0s spike is connected to a specific mechanism — pool wait against a
  timeout — using the observed value.
- At least one experiment is specified that would distinguish the two candidate
  causes.
- The response does not recommend capacity increases as the first line.
- A scale change proposed, if at all, is labelled as masking rather than fixing.

**Fail criteria:**
- More replicas, a bigger pool, or a longer timeout proposed as the primary fix.
- "Network latency" or "garbage collection" asserted with no supporting
  observation.
- p50 and p99 averaged, or a single mean latency quoted.
- The 5.0s value not noticed, or noticed and treated as ordinary variance.
- The service called "random" or "spiky" with no mechanism offered.
- A code change applied before the two candidate causes are separated.

**Trap:** The number 8s is 133 times the p50, which reads as an anomaly to be
*explained away* — the standard move being that a handful of slow requests are
always outliers and the service is fine. That reading is wrong in a specific way:
a p99 of 8s at this volume is roughly 2,000 requests a day, which is not a
handful, and the value is not spread but concentrated at exactly 5.0s, which no
organic latency process does. The equal-and-opposite trap is over-remediation:
"raise the pool from 50 to 200" moves the p99 and is unfalsifiable afterwards,
because the symptom is gone and the idle-reaping interaction that caused it is
still there, now with a longer fuse. Both responses are confident, both leave the
user with a better dashboard, and only one of them found the 5.0s.

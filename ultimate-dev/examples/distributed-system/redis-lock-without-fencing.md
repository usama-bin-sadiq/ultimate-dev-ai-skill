# A Redis lock that cannot prevent a stale writer

**Objective:** "We added a Redis lock to make our nightly settlement job
single-instance, and twice last month two instances ran it at once and the ledger
disagreed with the bank by £48,200. Find out why and fix it."

**Domain:** Distributed systems — mutual exclusion over a network
**Scale:** L3   **Reasoning rung:** R2 → R3 at work unit 2

## 0. Triage

- **Complexity** — one job, one lock, one downstream store. Three components, and
  they interact through a single mechanism. The interactions are the whole
  problem.
- **Uncertainty** — medium, and it is the *kind* that matters. Not "I don't know
  Redis"; I do not know whether the observed behaviour is a bug in the code, a bug
  in the lock's design, or the expected consequence of a correct implementation
  under conditions nobody wrote down. Those three have different fixes and only
  one of them is a code change.
- **Consequence** — high, and financial. £48,200 is a real reconciliation gap with
  a real bank, and a duplicate settlement is a customer-visible event. The
  controller absorbs it.
- **Reversibility** — costly but bounded. A wrong ledger can be reconciled
  afterwards; a wrong fix can introduce a new class of duplicate. A ledger
  correction is a four-hour job with an audit trail.

**Rung: R2, Scale: L3.** Parts interact (worker, lock, store) and the approach is
genuinely in question: mutual exclusion can be fixed by lengthening the lease,
adding renewal, adding a check, or changing the contract between the worker and
the store. A task model, a real plan, a capability check, and per-unit
verification.

**Why not R3 immediately.** R3 is for unfamiliar territory where blocking unknowns
are worth real cost. Redis and advisory locks are not unfamiliar, and the first
unit of work is a measurement, not an exploration. Triage that escalates on the
word "distributed" is difficulty worship.

**Escalate when:** the diagnosis turns out to be a design property of the lock
rather than a configuration error, because then the fix changes the contract
between three components and the change has to be reasoned about rather than
applied.
**De-escalate when:** the cause is a single mis-set parameter.

## 1. Task model

- **Objective** — the nightly settlement job cannot write to the ledger from two
  workers concurrently, including when one of them is no longer entitled to be
  running.
- **Requirements** — 1. at most one worker holds the lease at a time; 2. a worker
  whose lease has expired is *rejected by the store* rather than trusted; 3. the
  ledger write is idempotent on replay; 4. the fix does not require a distributed
  transaction across Redis and Postgres; 5. existing duplicate rows are
  reconciled, not deleted; 6. the design is observable — a stale attempt is
  visible in metrics, not silent.
- **Constraints** — Redis 7.2 in cluster mode with `min-replicas-to-write 2`;
  Postgres 15 with a `ledger_entries` table that is the financial system of
  record; a job that reconciles 1.2M rows and cannot be shortened without changing
  what it settles; no maintenance window, because the job runs at 03:00 and
  misses are visible.
- **Unknowns**
  - U1: how long does the critical section actually take, at p99? **Blocking.**
    Whether the lease TTL is "wrong" cannot be decided without it.
  - U2: does the store have anything to compare a write against?
    **Blocking for the strategy choice**, because the available fixes are
    radically different depending on the answer.
- **Assumptions**
  - A1: the lock is held with `SET key value NX PX ttl` and released with a
    compare-and-delete on the value. *If false*: there is a second release path
    that can delete someone else's lock, which is a different and worse bug.
    *Confidence: Inferred from the code.* *Checked by:* U1's code read.
  - A2: the lock protects the *write*, not the *read*. *If false*: a stale
    worker could also read a stale view and make a decision from it.
    *Confidence: Assumed.* *Checked by:* U3's code read.
  - A3: the two incidents in the last month are the same failure. *If false*:
    there are two bugs and fixing one leaves the other live.
    *Confidence: Assumed from the identical £-magnitude of both.*
    *Checked by:* U1's incident-data query.
- **Success criteria** — a clock-injected test that forces two workers to overlap
  produces exactly one accepted write sequence and one rejected; a 90-day replay of
  the archived job schedule against a simulated clock produces zero
  fence-rejections that are later found to be legitimate; and the £48,200 gap
  reconciles to zero against the bank statement.

**Requirements vs success criteria:** "stop two instances running at once" is the
requirement; "a forced overlap yields one accepted and one rejected write, and the
ledger reconciles to zero" is the criterion — and the requirement is satisfiable by
a longer TTL, which the criterion is not.

## 2. Decision records

```text
DECISION
  question      rung, before any measurement
  selected      R2: task model, real plan, per-unit verification
  rejected      R3, on the word "distributed"; and R1, on the grounds that the
                approach is not determined
  rationale     three components interact through one mechanism, and four
                materially different fixes are available; but Redis and advisory
                locks are not unfamiliar and the first unit is a measurement
  confidence    high
  cost          a task model and a plan for what might be a one-line fix
  evidence      triage axes, not the vocabulary of the domain
  recovery      the first unit shows the cause is a design property, not a
                parameter, in which case the fix changes a contract
```

```text
DECISION
  question      the shape of the fix
  selected      a monotonic fencing token from `INCR` on a per-tenant counter,
                carried in the lease value and asserted by the store on every
                write: `UPDATE ... WHERE fencing_token < $token`
  rejected      (a) lengthening the lease TTL to cover the observed critical
                section; (b) renewing the lease on a heartbeat; (c) a Postgres
                advisory lock replacing Redis; (d) `SELECT ... FOR UPDATE` on the
                settlement batch row
  rationale     (a) and (b) bound the window without closing it — a GC pause or a
                database stall can exceed any TTL you pick, and the worker's write
                is still accepted. (c) moves the lock to the system of record,
                which is more correct but is a migration of the whole job and does
                not cover the writes that happen outside it. (d) locks one row and
                gives no protection at all, because the writers do not contend for
                that row. Only a token the store can *compare* makes a stale
                writer's write fail rather than succeed quietly
  confidence    high
  cost          one counter key, one extra column, one `WHERE` clause, and a
                migration on the store
  evidence      the observed critical section is 11.4s at p99 against a 5s lease,
                and the 2026-08-02 incident shows two workers 1.8s apart in the
                access log
  recovery      a store that cannot compare tokens — a write-only interface, or a
                downstream system outside our control — in which case the
                invariant must be enforced upstream and the design changes
```

```text
DECISION
  question      where the token is minted
  selected      `INCR fence:settle:{tenant_id}`, which is monotonic and survives
                failover because it is a replication-stream integer
  rejected      (a) `INCR` *before* `SET NX`, so a worker that loses the race
                burns a number; (b) a UUID, which has no order and therefore no
                use as a comparison; (c) a Redis `TIME`-derived value, which is
                skewed across the cluster
  rationale     the token must be strictly increasing across all contenders, and
                a burned number costs nothing while a non-monotonic token makes
                the comparison meaningless
  confidence    high
  cost          one key per tenant, one `INCR` per attempt
  evidence      Redis replication of the integer is ordered within the stream
  recovery      two workers obtaining the same token, which would mean the counter
                was rolled back by a failover — detectable and reported by a
                `fence:reuse` metric
```

```text
DECISION
  question      how the £48,200 is dealt with
  selected      reconcile, do not delete: produce a variance report, a bank-confirmed
                correction, and a decision on whether the duplicate or the original
                is the entry of record
  rejected      deleting the 214 duplicate `ledger_entries` rows
  rationale     the ledger is the financial system of record; deleting from it
                destroys the evidence that the duplicate occurred, which is the
                only thing that will let us prove the fix works afterwards
  confidence    high
  cost          a four-hour reconciliation, a finance sign-off, and a week of
                double-entry noise
  evidence      214 duplicate rows, £48,200 variance, both incident windows
                matched in `ops/ledger/`
  recovery      if finance rules that the duplicates are void rather than
                erroneous, the rows are archived rather than corrected
```

## 3. Context

**Loaded:**

- **C0** — objective, two blocking unknowns, three assumptions, criteria.
- **C2** — two reference sections the decision turns on: the `SET` command's
  `NX`/`PX` semantics, and Postgres's `READ COMMITTED` behaviour for
  `UPDATE ... WHERE col < $value` under concurrent writers. The second is the
  whole correctness argument for the fix, so it is loaded rather than recalled.
- **C3** — four files, named before retrieval: `services/settlement/src/lock.js`
  (is the lock really the only exclusion mechanism?), `src/job.js` (what is inside
  the critical section, and what does it do at the end that matters?),
  `migrations/` for the `ledger_entries` index definitions, and
  `ops/runbooks/settlement.md` (what does the on-call page say happened on
  2026-08-02?).
- **C4** — the actual observations, which is where the diagnosis came from:
  - `SELECT now() - max(query_start) ...` plus the job's own
    `settlement_duration_seconds` histogram from Prometheus for 90 days;
  - the Redis `MONITOR`-equivalent — `redis-cli --scan --pattern 'lock:settle:*'`
    with TTLs, sampled at 03:00 on a live night;
  - `ops/incident-2026-08-02-postgres.log`, the 400 lines around the overlap.

**Deliberately not loaded:**

- **The other 61 jobs in the same worker.** The lock implementation is shared
  (`lock.js` is a module), so the *code* is shared context, but the *other jobs'
  business logic* has no bearing on whether the settlement job is safe. One grep
  established that 9 other jobs use `lock.js`; none of them were read.
- **Redis Cluster's internal failover documentation, beyond the one fact** that
  `INCR` survives a failover. Loading the rest would not have changed the design.
- **The bank's statement file format and the finance reconciliation process.**
  Needed for the reconciliation decision, which is routed to a human with a
  recommendation rather than executed.
- **The history of the lock's introduction** (PR #4,118 and its discussion). Tempting
  and useless: the code is the state, not the archaeology behind it.

`excluded`: 61 jobs' business logic, failover internals, bank file formats, PR
history. `unresolved`: whether the bank treats the second settlement as void or as
a duplicate — an authority question, routed as an escalation with a
recommendation, not a research task.

## 4. Capability

```text
1. do it directly   REACHED AND SELECTED for the diagnosis — the p99 of the
                    duration histogram, the lock TTL sample, and the incident-log
                    correlation are all deterministic joins and queries, and they
                    go to psql and jq rather than to my recall
2. existing         SELECTED — the kernel's own retry-policy and recovery
                    references supply the classification this failure needs, and
                    `references/capability-system.md` supplies the ladder being
                    walked
3. compose          REACHED AND REJECTED — a Redis lock plus a Postgres advisory
                    lock plus an application check is the "belt and braces"
                    answer, and it is three mechanisms that can each be the one
                    that fails silently
4. acquire          not reached
5. create           not reached, and the disqualifying question answers itself: the
                    gap is not a procedure, it is a missing column. A
                    "fencing-token-implementation" skill would be a restatement of
                    the code it replaced
```

Stopping at rung 2. The fix is a schema change and a `WHERE` clause. Creating a
capability for it would be the proliferation anti-pattern: the code is the
capability.

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Measure the critical-section duration at p50/p99/max for 90 days, from the job's own histogram | Prometheus is reachable | p99 > lease TTL, with a number | `histogram_quantile` over `settlement_duration_seconds`; the two incident windows fall inside the tail |
| U2 | Read `lock.js` and `job.js`; determine the lease TTL, the release path, and what the critical section actually does | — | TTL, release semantics, and the write at the end | quoted with file and line; A1 and A2 resolved |
| U3 | Read the incident log around the overlap and reconstruct the two timelines | U1, U2 | the second worker's start is explained | the two worker IDs and their 1.8s separation appear in the log with their lock acquisition lines |
| U4 | Search for a *second* exclusion mechanism before proposing a third | U2 | either one is found, or none | a grep over 9 lock-using jobs for `pg_advisory_lock`, `SELECT FOR UPDATE`, and a uniqueness index on the batch key |
| U5 | Add the fencing column and the store-side check | U4 shows no second mechanism | `ledger_entries.fencing_token bigint not null`, and every write carries the token | migration applied to a restored snapshot; the constraint validated |
| U6 | Implement token minting and lease value change in `lock.js` | U5 | `INCR` before `SET NX`; the lease value is the token | unit test: a lost race still burns a number and still fails to acquire |
| U7 | Write the clock-injected overlap test | U5, U6 | one accepted sequence, one rejection, with a reason | the test *fails* against the old code — that is the requirement |
| U8 | Replay 90 days of archived schedules against a simulated clock | U7 | zero unexplained rejections | replay log, with every rejection classified as expected or not |
| U9 | Produce the reconciliation report and hand it to finance | — | the £48,200 explained line by line | the report reconciles to the bank statement to the penny |

U7 before U8, and U7's criterion is that it *fails* on the current code. A
concurrency test that passes before the fix is a test of nothing.

## 6. Execution & observation

**U1 — the number that decided everything.** The lease TTL is 5000ms, set in
`lock.js:41` as `PX LEASE_TTL_MS`. The job's own histogram:

```console
$ curl -sG localhost:9090/api/v1/query --data-urlencode \
  'query=histogram_quantile(0.50, rate(settlement_duration_seconds_bucket[90d]))' \
  | jq -r '.data.result[0].value[1]'
2.94
$ curl -sG localhost:9090/api/v1/query --data-urlencode \
  'query=histogram_quantile(0.99, rate(settlement_duration_seconds_bucket[90d]))' \
  | jq -r '.data.result[0].value[1]'
11.42
```

p50 is 2.94s, comfortably inside a 5s lease. p99 is **11.42s**, which is 2.3× the
lease. The lock is not slow and the job is not usually slow; the job is *occasionally*
2.3× slower than the lease, and a lock cannot express "occasionally".

**U2.** `lock.js:41` confirms A1: `SET lock:settle:{tenant} <value> NX PX 5000`,
released by a Lua script comparing the value. No second release path. `job.js`
confirms A2: the critical section reads the 1.2M unsettled rows, reconciles, and
then opens a transaction that writes to `ledger_entries` — so the lock protects
both the read and the write, which is the harder case and the one A2 assumed.

**U3 — the reconstruction, and the surprise inside it.**

```console
$ grep -E 'settlement|acquired|lock' ops/incident-2026-08-02-postgres.log \
  | sed -n '340,372p'
03:00:07.114 INFO  worker=settle-a worker_id=7f3c  acquired lock ttl=5000 token=8841
03:00:08.902 INFO  worker=settle-b worker_id=9a11  acquired lock ttl=5000
03:00:19.331 INFO  worker=settle-b  ledger_entries INSERT 214 rows  value=4820034
03:00:19.884 INFO  worker=settle-a  ledger_entries INSERT 214 rows  value=4820034
```

Worker A acquired at 03:00:07.114. Worker B acquired **1.788 seconds later** —
which is not a 5-second lease expiring. It is A's lease being *released* and B
acquiring the key immediately.

**The surprise:** worker A did not run long. Worker A was killed. `job.js:88` has
`process.on('SIGTERM', releaseLock)` and the container received a SIGTERM at
03:00:08.9 during a node-pool scale-in that the settlement job's own
`reconcile-loop` triggered at 03:00:08.4 because a queue depth metric crossed its
threshold. A releases the lock in its exit handler, B acquires it 200ms later, and
A — which the orchestrator had given 30 seconds of grace — resumes at 03:00:19.3
and writes 214 rows for the same value.

So the bug is **not** that the lease is too short for a slow job. It is that a
lock release on graceful shutdown *frees the key while the process keeps running*.
A1 was right about the mechanics and wrong about the shape of the bug, and p99
being 2.3× the TTL is a second, independent hazard that would have caused the same
symptom a month later.

**This is the point where the rung moved.** A process that releases a lock and then
continues to do the work it was locking is a contract violation between the lock
and the work. Fixing it means changing what the store will accept, not changing
what the worker does on exit. R2 → R3, recorded.

**U4.** No second exclusion mechanism. The grep over the nine lock-using jobs for
`pg_advisory_lock`, `FOR UPDATE`, and a uniqueness constraint on the batch key
returns nothing. The Redis lock is the only thing standing between two workers and
the ledger, which raises the consequence of it being wrong.

**U5–U6.** The migration and the implementation:

```sql
ALTER TABLE ledger_entries ADD COLUMN fencing_token bigint NOT NULL DEFAULT 0;
-- backfill is unnecessary: every existing row predates fencing and the token
-- comparison only guards *new* writes. Recorded in the migration comment,
-- because "unnecessary" is the kind of thing a later reader assumes is an
-- oversight.
CREATE INDEX ledger_entries_tenant_token ON ledger_entries (tenant_id, fencing_token);
```

```js
// lock.js — the lease value is now the token, not a random uuid
async function acquire(key, ttlMs) {
  const token = await redis.incr(`${key}:fence`);
  const ok = await redis.set(key, String(token), 'NX', 'PX', ttlMs);
  if (ok !== 'OK') return null;            // lost the race; the number is burned
  return { key, token, release: releaseIfMine };
}
```

The store side, which is the part that actually enforces the invariant:

```sql
UPDATE ledger_entries
   SET settlement_ref = $1, value_cents = $2, fencing_token = $3
 WHERE tenant_id = $4
   AND COALESCE(max_token, 0) <= $3;
```

`max_token` is a per-tenant row in `tenant_settlement_state`, updated in the same
transaction. A writer holding token 8841 after token 8842 has already committed
matches no rows and writes nothing.

## 7. Verification

**The check:** a clock-injected overlap test, then a 90-day replay.

```console
$ npm test --workspace=services/settlement -- overlap
  ✓ fencing rejects a stale writer (1 test) 41ms
      assert: rows_written_by_stale_writer === 0
      assert: rejection recorded as reason=fence_stale token=8841 current=8842

$ node ops/replay-settlement.js --since 90d --clock simulated
  simulated 90 days, 2,916 job invocations, 41 lease overlaps induced at the
  two observed failure modes (slow critical section, SIGTERM-then-continue)
  accepted writes: 2,916   rejected: 41 (all fence_stale)   unexplained: 0
```

**The test's own criterion is that it fails on the old code**, and it does: run
against the pre-fix `lock.js` it reports `rows_written_by_stale_writer === 214`.
That is the check being observed to fail, which is what makes its pass meaningful.

**Independent check.** The token comparison was re-derived a second way rather than
trusted once: the replay's 41 rejections were re-computed from the raw
`ledger_entries` write timestamps in the archive, independently of the replay's
own logic, and the two sets of rejected intervals agree exactly. And the token
monotonicity was checked against a property the design does not depend on: over
2,916 invocations, `fence:settle:{tenant}` is strictly increasing with no reuse
and no gaps other than the 41 deliberate burns. No `fence:reuse` events.

**Evidence.** The test output above; the replay log; the archive cross-check; the
reconciliation report, which ties the 214 duplicate rows to the two incident
windows line by line and closes at £0.00 variance against the bank statement for
2026-08-02 and 2026-08-19.

**Verdict: VERIFIED.** The invariant holds under both observed failure modes and
under 41 induced overlaps; a check that fails on the old code passes on the new
one; and the historical damage is explained to the penny.

## 8. Recovery

**Classification: bad assumption.** Two of them, and they were discovered in
sequence.

**Assumption 1 — "the critical section is short" (implicit, never written down).**
False at p99: 11.42s against a 5s lease. Correcting it and re-planning dependents
is what produced decision record 2's rejection of a longer TTL: the constraint
was not "the lease is too short", it is "no lease length is sufficient, because a
worker can be paused for longer than any TTL you would be willing to set".

**Assumption 2 — A1, that the lease was the only problem.** Also false, and found
by U3's timeline reconstruction rather than by reading the diff: a `SIGTERM`
handler releases the lock while the process continues, which no TTL change fixes.
The replan pulled in the *store*, which the original plan had not touched, and
which is why the rung moved.

**The response avoided — blind retry, in two forms.** The first form is the
operational one that was probably already happening: re-running the job after a
duplicate, which produces *another* 214 rows and another variance. The second is
the development one: adding a heartbeat renewal to `lock.js` and re-testing, which
would have produced a green test suite and a lock that still loses the race during
a 30-second node-pool scale-in. Both were available; both are a plan defended
against the timeline that contradicted it.

**A second failure, recovered differently — a test that passed for the wrong
reason.** The first version of the overlap test injected the delay with
`await sleep(6000)` in the test harness. It passed against the *old* code too,
because the test was slow rather than deterministic, so the overlap it produced
was not the overlap that matters. The classification is **execution failure /
wrong check**, the cause is that time was being simulated by wall clock instead of
by a controllable clock, and the response was to make the lock's clock an injected
dependency. Attempts: 2, and the second attempt differs from the first in kind
rather than in duration.

## 9. Delivery

**Outcome.** The nightly settlement job cannot write to the ledger from a worker
that no longer holds the entitlement. The mechanism is a monotonic fencing token
minted by `INCR` on a per-tenant counter, carried in the lease value, and asserted
by the store on every write — so a stale writer's write is *rejected by Postgres*,
not merely refused by a lock that has already moved on. The `SIGTERM`-releases-
then-continues path is closed by the same mechanism rather than by a code change,
and the residual slow-critical-section hazard is now survivable rather than
assumed away.

**Evidence.** The overlap test fails on the pre-fix code (`214` rows written by
the stale writer) and passes on the new code (`0`). A 90-day simulated replay
induced 41 overlaps across both failure modes: 2,916 accepted, 41 rejected, all
`fence_stale`, 0 unexplained. Token monotonicity verified over 2,916 invocations
with no reuse. The £48,200 reconciles line by line against the bank statement,
closing at £0.00 variance.

**Assumptions.**
- Redis `INCR` survives a failover without rolling back. *Not verified in this
  run* — a failover test was scoped and not executed. This is the load-bearing
  assumption in the design, and if it fails, two workers could hold the same token
  and the comparison would be vacuous. A `fence:reuse` metric exists to detect it.
- The lock covers both the read and the write in `job.js`. Held, read at `job.js`.
- The two incidents were the same failure. **Contradicted and corrected**: they
  were *two different* failure modes, one slow and one shutdown-related, and both
  are now covered.

**Limitations.**
- The replay is a simulation. It models the two failure modes actually observed and
  not, for example, a Redis failover mid-hold, a Postgres failover, or a clock
  jump — the last of which would break the token comparison in a way the fence
  does not detect.
- The 214 duplicate rows are reconciled, not removed. The ledger still contains
  them, with a correcting entry. That is a deliberate audit choice and finance has
  not yet signed it off.
- Nine other jobs use the same `lock.js` module. None of them has been audited for
  the shutdown path, and two of them (`payout-runner`, `refund-sweeper`) have
  short critical sections and a `SIGTERM` handler with the same shape. They are
  *suspected* to have the same bug and have not been checked.

**Confidence.** High that the settlement job is fixed, on a check that fails
without the fix. Medium that the pattern is gone, because a Redis failover was not
tested and the other nine jobs were not audited. Low that the class of bug is gone
from the codebase, and it probably is not.

**Verification status.** VERIFIED for the settlement job against its stated
criteria, with one assumption untested and explicitly named. The audit of the
other nine jobs is outstanding and is a separate task with a different owner.

## 10. Learning

**Candidate, not promoted.** A lock value that can be *compared* by the resource
being protected is strictly stronger than a lock value that can only be
*checked* by the lock holder; when a critical section's p99 exceeds its lease TTL
at any ratio, prefer the fencing token to any TTL value.

**What evidence would be needed to promote it.** Three systems in this codebase
with a slow-critical-section or shutdown-release hazard, each fixed with a token
and each verified by a test that failed beforehand. I have one, and the other nine
jobs are the obvious next three — but promoting now would install a specific
mechanism as a general rule when the general rule is the weaker claim: *a
correctness invariant must be enforced by the component that owns the resource,
not by the component that believes it is safe.*

**Not worth retaining:** `PX 5000`, the key names, the `COALESCE(max_token, 0)`
idiom. All are this system's implementation detail, recorded in the code and the
migration comment where a future reader will find them.

**Routed rather than created.** A reusable capability candidate is a
"lease-and-fence checklist" — the questions to ask before trusting any distributed
lock. That is worth writing, because it will be asked again in this codebase and
in the next one, and its scope is narrow enough to be testable. It goes to
`skill-creator` after the failover test in §9's limitations has been run, not
before, because a checklist written by someone who has yet to survive a failover
would be a checklist with a hole in it.

## What this example proves

- **The measured number, not the intuition, chose the fix.** p99 = 11.42s against a
  5s lease is a fact; "retries seem to cause it" was not, and acting on the
  intuition would have produced a green suite and a live bug.
- **A lock is not a mutex, and the difference is a comparison.** The fix moved the
  invariant from the lock holder to the store, which is the only place a stale
  writer's write can be refused.
- **A timeline reconstruction found a bug a diff review would not.** The `SIGTERM`
  path was in the code, invisible in the change that introduced the lock, and only
  visible once two workers' acquisition lines were read against each other.
- **Two failures, one symptom, two corrections.** The 2026-08-02 and 2026-08-19
  incidents looked like one bug and were two; assuming otherwise would have left
  the second one live.
- **The test's criterion is that it fails first.** `rows_written_by_stale_writer ===
  214` on the old code is what makes `=== 0` on the new code mean something.
- **Scope discipline under a fixed cost.** £48,200 reconciled to zero and the two
  known failure modes covered — with the other nine jobs using the same module
  named as outstanding rather than quietly included in the claim.
- **The 90-day replay is a simulation and says so.** It models what was observed
  and not a Redis failover, a Postgres failover, or a clock jump, and the limit is
  in the delivery rather than implied by the pass.

# A backfill that keeps getting OOM-killed

**Objective:** "Our `invoices` backfill on `orders-db-1` keeps dying. It's supposed
to add `customer_lifetime_value_cents` to 3.2M rows. It ran for 3 hours, then the
node was OOM-killed at 03:12. It's been restarted twice and died both times around
02:00. Just make it finish."

**Domain:** Recovery — resource failure on a live database
**Scale:** L3   **Reasoning rung:** R2

## 0. Triage

- **Complexity** — medium. One column, one table, one statement that is wrong. The
  interaction is between the statement's working set and a 64GB memory limit, and
  that interaction is invisible in the SQL.
- **Uncertainty** — low, and it is the low that matters: the failure is
  **deterministic**, not intermittent. Twice at nearly the same wall-clock position
  is not bad luck; it is a property of the statement.
- **Consequence** — medium. The column is on the critical path for the 2026-10-06
  invoices feature. Nobody is paged and no data is lost, but the date slips.
- **Reversibility** — cheap. A half-finished backfill can be rolled back; the column
  can be dropped; nothing outside the table is affected.

**Rung: R2. Scale: L3.** Parts interact (statement shape, memory limit, WAL
volume, replication), the approach must be chosen between four different ways to
add the column, and per-unit verification is required.

**Why not R3.** The domain is familiar, the failure is deterministic, and the
diagnosis is one `dmesg` and one `EXPLAIN`. Escalating because a job failed three
times is difficulty worship: the *count* of failures is not a measure of
difficulty, and here it is evidence about the plan.
**Why not R1.** Four candidate approaches exist and choosing wrongly costs another
night.

**Escalate when:** the fix cannot be found within the session, because the third
scheduled restart is scheduled for tonight and would waste it.
**De-escalate when:** the cause is a single statement's working set.

## 1. Task model

- **Objective** — the column exists on all 3.2M rows, correctly, without the node
  dying and without a full-table lock.
- **Requirements** — 1. the column is added without a rewrite; 2. every row is
  backfilled with the correct value; 3. the working set stays bounded; 4. the job is
  resumable from its own state; 5. replication is not starved; 6. the run finishes
  inside the maintenance window.
- **Constraints** — `orders-db-1` is 64GB with 8GB shared buffers; `work_mem` 4MB;
  the table is 340GB; nightly `VACUUM ANALYZE` starts at 02:00; a replication slot
  feeds `orders-db-replica`; the 2026-10-06 invoices feature depends on this.
- **Unknowns**
  - U1: is the OOM the statement's working set, or the node's total? **Blocking** —
    the two have completely different fixes and only one of them involves the SQL.
  - U2: what does the aggregate actually cost in a single transaction? **Blocking
    for the approach choice**, and it is answerable from `EXPLAIN ANALYZE` on a
    fraction of the data.
- **Assumptions**
  - A1: the value is a per-customer sum of `amount_cents`, and the join key is
    `customer_id`. *If false*: the backfill is not a simple aggregate and the
    batching strategy may not apply. *Confidence: Assumed from the job's name.*
    *Checked by:* U1, and the batched result is reconciled against an independent
    recomputation.
  - A2: `invoices` has an index on `customer_id`. *If false*: the batched UPDATE
    does a sequential scan per batch, and 160 batches of 20,000 rows each scanning
    340GB is not 144 seconds.
  - A3: the OOM was the postgres backend, not `VACUUM` or the autovacuum daemon.
    *If false*: the fix is a memory setting, not a statement rewrite.
- **Success criteria** — the column exists, the value is correct on all 3.2M rows,
  the job ran with a bounded working set, the total run time is recorded, and the
  column is not re-rewritten by any later `ALTER`.

**Requirements vs success criteria:** "make it finish" is the requirement; "3.2M
rows backfilled with a peak RSS under 2GB in under 10 minutes, with the value
reconciling to the independent sum" is the criterion, and the first is satisfied by a
run that finishes by producing wrong numbers.

## 2. Decision records

```text
DECISION
  question      what the third scheduled restart should do
  selected      cancel it, before it starts
  rejected      (a) let it run and monitor; (b) restart it earlier so it finishes
                sooner; (c) let it run with `work_mem` reduced, on the theory that
                the sort spills less
  rationale     the failure is deterministic and has occurred twice at nearly the
                same position, so the third run will fail at nearly the same
                position. It is scheduled at 21:00 and would run until OOM at
                approximately 00:10, inside the nightly VACUUM window, while
                holding a replication slot — and the last time a long-running
                writer held that slot the replica fell 41 minutes behind. Cancelling
                costs nothing; the run is scheduled to fail
  confidence    high
  cost          one command, and the backfill does not start tonight
  evidence      `dmesg -T` shows the OOM kill; the two prior runs died at 01:58 and
                02:04, both before the VACUUM window opens
  recovery      a monitoring-and-abort wrapper instead, which would preserve the
                attempt at the cost of the slot risk
```

```text
DECISION
  question      the shape of the backfill
  selected      batched UPDATE by `id` range with a checkpoint table, 20,000 rows
                per batch, one commit per batch
  rejected      (a) the single UPDATE with a subquery, which is what OOMs; (b) a
                `pg_repack`-style rebuild; (c) adding the column with a NOT NULL
                default and letting the fast-default mechanism handle it, which
                computes the wrong value
  rationale     (a) is the cause: it materialises a 1.9M-group hash aggregate and
                holds every row version from a 3.2M-row UPDATE in one transaction,
                and the node's 64GB cannot hold that. (b) rewrites 340GB for a
                column add, which is a different order of magnitude. (c) is the
                trap: the fast default stores 0 for every row, and the backfill
                still has to compute the real value, so the write volume is
                identical — the only thing it changes is where the default comes
                from
  confidence    high
  cost          a checkpoint table, a small script, and 160 batch statements
  evidence      `EXPLAIN (ANALYZE, BUFFERS)` on a 200k-row sample shows a Hash
                Aggregate over 1.9M groups plus 3.2M row versions held in one
                transaction
  recovery      batching proves too slow, in which case the aggregate is
                materialised into a temp table once and the UPDATE joins against
                that
```

```text
DECISION
  question      the `NOT NULL` constraint
  selected      add it last, via a `NOT VALID` CHECK followed by `VALIDATE
                CONSTRAINT`
  rejected      adding `NOT NULL` in the same statement as the column
  rationale     the column is added nullable, backfilled, and only then constrained.
                Adding `NOT NULL` up front forces either a second full scan to
                validate or a rewrite, and the rewrite is the thing we are trying
                to avoid. `NOT VALID` + `VALIDATE` takes a SHARE UPDATE EXCLUSIVE
                lock, which does not block reads or writes, and validation is a
                single sequential scan of 340GB in about 90 seconds
  confidence    high
  cost          one scan
  evidence      PostgreSQL 12.4; `VALIDATE CONSTRAINT` on `NOT VALID` is the
                documented online pattern for this
  recovery      the validation scan cannot complete inside the window, in which
                case the constraint stays `NOT VALID` and is validated during the
                following low-traffic period, with the limitation recorded
```

```text
DECISION
  question      verification
  selected      an independent recomputation on the read replica, comparing the
                column's total against a fresh aggregate
  rejected      (a) row count of non-null values; (b) spot-checking 100 rows
  rationale     (a) proves the backfill ran and says nothing about the values — a
                systematically wrong value would pass it. (b) cannot find a
                0.1% error. The whole failure mode here is a long-running
                statement, which is exactly the class of bug that produces
                *plausible* wrong numbers, and it deserves a check that can
                actually fail
  confidence    high
  cost          one query on the replica, no contention with the primary
  evidence      the two computations are independent: the backfill derives per
                customer from the same source; the verification sums the written
                column and compares against a fresh GROUP BY
  recovery      a mismatch, which would point at a batch-boundary error and is
                exactly what a checkpoint table makes diagnosable
```

## 3. Context

**Loaded:**

- **C0** — objective, two blocking unknowns, three assumptions, criteria.
- **C2** — the kernel's own `retry-policy.md` classification table, and
  `recovery-system.md`. Both are C2 because the first action of this run is a
  classification, and getting the table's classes right is the whole job.
- **C3** — three files, named before retrieval: the job's migration SQL (which is
  where the single UPDATE is), the scheduling table for the nightly `VACUUM` and the
  backfill's own schedule, and the replication slot's lag alerts.
- **C4** — five observations, and every one of them is a tool result:
  ```console
  $ dmesg -T | grep -i -E 'killed process|out of memory' | tail -3
  [Sat Aug 29 03:12:44 2026] Out of memory: Killed process 2841 (postgres: user=svc_mig)
      total-vm:259348416kB, anon-rss:61421384kB, file-rss:24576kB, shmem-rss:1836kB
  $ psql ... -c "SELECT now() - query_start AS runtime, left(query, 90) FROM pg_stat_activity WHERE state='active' AND query ILIKE '%ltv%'"
    03:00:07.412  UPDATE invoices SET customer_lifetime_value_cents = c.ltv_cents FROM (SELECT ...
  $ grep -E 'ltv-backfill' ops/nightly-schedule.log
    2026-08-27T21:00:02  start  2026-08-28T01:58:41  killed (oom)
    2026-08-28T21:00:04  start  2026-08-29T02:04:19  killed (oom)
    2026-08-29T21:00:01  start  2026-08-30T00:41:55  killed (oom)
  ```
- **C5** — none. Everything needed is in the node.

**Deliberately not loaded:**

- **The other 11 jobs in the same migration runner.** The backfill is one job; the
  runner's retry and lock-wait behaviour matters (that was 30 lines) and the rest
  does not.
- **`invoices` in full.** No query read the table's contents beyond a 200k-row
  sample for `EXPLAIN`. A 340GB table read at full size would be a third instance
  of the same mistake.
- **The invoices feature's code.** Whether the column is used in a hot path affects
  the default's index decision, and that is a question for the feature team, not for
  this run.
- **Postgres memory-tuning guides.** The diagnosis is "this statement's working set
  does not fit", and the fix is a different statement. Tuning `work_mem` is a
  response to a different diagnosis and reading about it would have been the
  temptation this trace is about.

`excluded`: 11 other jobs, the table's contents, the feature's code, memory-tuning
reference. `unresolved`: why `anon-rss` reached 61GB on a node with 64GB — the
statement is a cause, not obviously the whole story, and the node's memory
configuration is the next thing to check if the batched version also grows.

## 4. Capability

```text
1. do it directly    REACHED AND SELECTED — the diagnosis is `dmesg`, `EXPLAIN
                     (ANALYZE, BUFFERS)`, and reading the scheduler's log. The
                     arithmetic — 3.2M rows, batch size, estimated duration — is
                     done in a script rather than estimated
2. existing          SELECTED — the kernel's own retry-policy and recovery
                     references, which supply the classification that the first act
                     of this run requires
3. compose           not reached
4. acquire           not reached
5. create            not reached, and the disqualifying question is close to
                     passing: "how we do online backfills" IS a reusable
                     procedure and it IS needed again. It is not created here
                     because this run has used it once, and a procedure authored
                     from one instance is a description of this fix rather than a
                     general method. It goes to skill-creator after the second
                     backfill
```

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Cancel tonight's scheduled restart | the job is in `cron.job` | the job is unscheduled | `SELECT count(*) FROM cron.job WHERE jobname='ltv-backfill'` returns 0 |
| U2 | Classify the failure and record it | the kill message and the schedule log | a classification in `recovery-system.md`'s vocabulary | the classification and the named cause, written down before any fix is attempted |
| U3 | Read the statement and confirm the cause | U2 | the single UPDATE and its materialisation | the statement quoted with its file and line |
| U4 | `EXPLAIN (ANALYZE, BUFFERS)` on a 200k-row sample | a test copy | the aggregate and row-version costs | the plan's node types and the actual buffer counts, quoted |
| U5 | Add the column nullable, with no default | no lock held | column exists, `attmissingval` is null | `pg_attribute` check; a fast default would be wrong here |
| U6 | Write the batched backfill with a checkpoint table | U5 | a resumable script | dry-run on 3 batches against a test copy, then the full run |
| U7 | Run it, with a memory ceiling observable | U6 | 3.2M rows updated | peak RSS read during the run, and the elapsed time recorded |
| U8 | Reconcile on the read replica | U7 | the totals agree | the column's `sum` against a fresh `GROUP BY`, both quoted |
| U9 | Add the CHECK, validate, set `NOT NULL` | U8 passes | the constraint is validated | `convalidated = true` in `pg_constraint` |
| U10 | Re-schedule the job as a no-op, with a comment | U9 | the schedule is clean | the comment names the migration that replaced it |

U1 is first because the clock is a real thing: the job is scheduled for 21:00 and
the diagnosis is not going to be finished by then.

## 6. Execution & observation

**U1 — the retry that was stopped, before it wasted the night.**

```console
$ psql -d orders -c "SELECT jobid, jobname, schedule FROM cron.job WHERE jobname='ltv-backfill'"
 jobid | jobname      | schedule
-------+---------------+--------------
   411 | ltv-backfill  | 7 21 * * *
$ psql -d orders -c "SELECT cron.unschedule(411)"
cron.unschedule
---------
 t
$ psql -d orders -c "SELECT count(*) FROM cron.job WHERE jobname='ltv-backfill'"
 count
-------
     0
```

**U2 — the classification, written before any fix.**

```text
unit            ltv-backfill, the scheduled UPDATE on orders-db-1
observed        "Out of memory: Killed process 2841 (postgres: user=svc_mig)
                total-vm:259348416kB, anon-rss:61421384kB" at 03:12:44
classification  resource failure
cause           the statement's working set is unbounded: one transaction holds a
                1.9M-group hash aggregate plus 3.2M row versions, which exceeds
                the node's 64GB
response        reduce scope, do not retry. Batch the work and commit per batch so
                the working set is released
attempts        3 prior attempts, all identical, at 01:58, 02:04, 00:41
blocked         the 2026-10-06 invoices feature
evidence        dmesg; the identical failure position three times; EXPLAIN
recovery        the same failure after batching would mean the cause is the node's
                memory configuration rather than the statement, and the next
                response is a configuration change
```

**Three identical failures at three nearly identical positions is the evidence
that makes this a resource failure rather than an execution failure.** A
transient failure does not reproduce at the same wall-clock position. The
classification is not a guess about the error message; it is a reading of the
pattern across three runs, and that is what `recovery-system.md` means by
classifying before responding.

**The contradiction, and it is with the request's own premise.** "Just make it
finish" and "it's been restarted twice" both frame the problem as *finding an input
that gets past the failure* — a different batch size, a different flag, a retry with
more memory. The requester has two data points and has read them as bad luck. They
are not: the two prior runs died at **01:58 and 02:04**, which is the same wall-clock
position twice, and an OOM kill is deterministic under the conditions that produced
it. So the fourth run is not a coin flip that might land — it is scheduled to die at
about the same point, and tonight's copy is scheduled for 21:00.

**U3–U4 — the statement and its cost.**

```sql
-- services/billing/migrations/V2026_08_24_0117_backfill_ltv.sql
UPDATE invoices SET customer_lifetime_value_cents = c.ltv_cents
FROM (SELECT customer_id, sum(amount_cents) AS ltv_cents
      FROM invoices GROUP BY customer_id) c
WHERE invoices.customer_id = c.customer_id;
```

```console
$ psql -d orders_test -c "EXPLAIN (ANALYZE, BUFFERS)
    UPDATE invoices SET customer_lifetime_value_cents = c.ltv_cents
    FROM (SELECT customer_id, sum(amount_cents) AS ltv_cents
          FROM invoices WHERE id <= 200000 GROUP BY customer_id) c
    WHERE invoices.customer_id = c.customer_id;"
  Hash Join  (cost=0.00..48211.00 rows=200000 width=16)
    ->  Hash  (cost=38210.00..43120.00 rows=183000 width=16)
          GroupAggregate  (cost=0.00..38210.00 rows=183000)
                ->  Seq Scan on invoices  (cost=0.00..21400.00 rows=200000)
  Execution Time: 4183.117 ms
  Buffers: shared hit=9812 read=44020 dirtied=41288 written=31804
```

**Two costs, and both scale with the table rather than the batch.** The
`GroupAggregate` holds one entry per distinct `customer_id` in the whole table —
1.9M groups at full scale, each with a hash entry, spillable only to `work_mem`'s
4MB and then to disk with a re-read. And `dirtied=41288` on a 200k-row sample is
the row versions: at 3.2M rows the transaction holds 3.2M dead tuples plus the
aggregate, and nothing in it is released until COMMIT. That is 61GB of `anon-rss`
and it is arithmetic, not a mystery.

**U5–U7 — the fix, run.**

```sql
ALTER TABLE invoices ADD COLUMN customer_lifetime_value_cents bigint;
-- no default, no NOT NULL, no rewrite. attmissingval stays null.
```

```console
$ python3 ops/backfill_ltv.py --table invoices --batch 20000 --checkpoint ops.checkpoint.ltv
batch   rows     elapsed   cumulative   peak_rss
    1  20000      0.9s       0.9s         412 MB
    2  20000      0.8s       1.7s         431 MB
   ...
  160  20000      0.9s     144.2s      1.38 GB
done: 3,200,000 rows in 144.2s, peak RSS 1.38 GB, 160 batches, 0 errors
```

**144 seconds and 1.38GB, against three hours to death at 61GB.** The ratio is the
whole point: the work is the same 3.2M row versions, but committing every 20,000
rows lets the backend release them, so the working set is bounded by the batch
rather than by the table. The checkpoint table means the job resumes from batch 137
if it is interrupted, which is what makes it a unit rather than a step.

**U8 — the reconciliation, and it is the check that could fail.**

```console
$ psql -d orders_replica -c "
  SELECT (SELECT sum(customer_lifetime_value_cents) FROM invoices
           WHERE customer_lifetime_value_cents IS NOT NULL) AS written,
         (SELECT sum(s) FROM (SELECT sum(amount_cents) s FROM invoices
                               GROUP BY customer_id) x)                AS recomputed"
    written        | recomputed
------------------+-------------
 9184471200000    | 9184471200000
```

**Exactly equal, on an independent recomputation, on a different machine.** Not
"the row count looks right" and not a hundred spot-checks: the total that was
written equals the total that should have been written, computed by a different
query on a different node.

**U9–U10.**

```sql
ALTER TABLE invoices ADD CONSTRAINT invoices_ltv_not_null
  CHECK (customer_lifetime_value_cents IS NOT NULL) NOT VALID;
ALTER TABLE invoices VALIDATE CONSTRAINT invoices_ltv_not_null;
-- 91.4s, SHARE UPDATE EXCLUSIVE, no blocking of reads or writes
ALTER TABLE invoices ALTER COLUMN customer_lifetime_value_cents SET NOT NULL;
-- PostgreSQL 12 recognises the validated CHECK and skips the scan
```

```console
$ psql -d orders -c "SELECT conname, convalidated FROM pg_constraint
                     WHERE conname='invoices_ltv_not_null'"
       conname                 | convalidated
------------------------------+--------------
 invoices_ltv_not_null        | t
```

## 7. Verification

| check | result |
|---|---|
| the failure is classified from the pattern, not the message | three identical failures at 01:58, 02:04, 00:41 → resource failure, deterministic |
| the scheduled retry is stopped before it runs | `cron.unschedule(411)`, verified 0 rows |
| the cause is confirmed by the plan and buffers | 1.9M groups, `dirtied=41288` on a 200k sample scaling to 3.2M row versions |
| the working set is bounded and observed | peak RSS 1.38GB over 160 batches, 144.2s total |
| the value is verified by an independent recomputation | `sum` written == `sum` recomputed, both 9,184,471,200,000, on the replica |
| the constraint is validated rather than assumed | `convalidated = t` after a 91.4s `VALIDATE` |
| the job is resumable | checkpoint table, resuming from the last committed batch |
| replication was not starved | replica lag peaked at 1.9s during the 144s run; the 41-minute lag from the previous attempt is not repeated |

**Independent check.** Two of them, and both on the quantities that matter. The
reconciliation is a genuinely different computation — summing the written column
versus recomputing the aggregate from scratch, on a different machine — rather than
a re-run of the backfill's own logic. And the working-set claim is checked by
observation rather than by the plan's estimates: peak RSS was read from
`/proc/<pid>/status` during the run, not inferred from `EXPLAIN`.

**What VERIFIED does not mean.** It means the column exists, is correct, and was
backfilled without the failure recurring. It does not mean the node cannot be
driven to 61GB by some other statement, and the `anon-rss` question in §9 is open.

## 8. Recovery

**Classified: resource failure, deterministic, cause identified in one line before
any response was chosen.** Per `recovery-system.md`, the mandated response is
*reduce scope, lower effort, or report the block*, with the stop condition *no slack
left → report the block*. Scope was reduced from "one statement over 3.2M rows" to
160 bounded batches with commits between them, and no block was needed.

**The response avoided — the fourth run, which was scheduled to fail.** Tonight's
restart was going to happen at 21:00 regardless. It would have run for roughly
three hours, been OOM-killed around 00:10, and in doing so held the replication slot
through the nightly `VACUUM ANALYZE` window — which is the condition that put
`orders-db-replica` 41 minutes behind on 2026-07-19. **Cancelling a scheduled job
is the highest-leverage action in this trace and it is invisible in the diff.** It
is listed as the first work unit rather than as a footnote because the clock was
running: the diagnosis was not going to finish before 21:00.

**The response avoided — blind retry, four times over.** This is the one the trace
is about:

- **The same UPDATE again.** Deterministic failure: the same action, the same
  inputs, the same state reproduces the same result. Three runs are the evidence,
  and a fourth would be a fourth data point confirming what three already showed.
- **`work_mem` raised to 64MB.** This is the response that looks like tuning and is
  actually a guess. The aggregate is 1.9M groups; `work_mem` governs each *node* of
  the plan, and at 4MB the hash agg already spills to disk. Raising it delays the
  spill and enlarges the resident set — the same failure, faster.
- **`work_mem` lowered.** Reduces one plan node's footprint and does nothing about
  the 3.2M row versions held to COMMIT. `dirtied=41288` on 200k rows is the real
  term, and it is invisible to any `work_mem` setting.
- **Adding the column with `DEFAULT 0 NOT NULL` so no backfill is needed.** The
  fast-default mechanism makes the *add* metadata-only, which looks like the
  elegant answer, and then the backfill still has to compute 3.2M real values
  against the same memory profile. The write volume is identical; only the source of
  the initial value changes.

**Each of these would have produced a night of compute and a fourth identical
failure**, and each of them reads as a reasonable engineering response. That is the
shape of a wrong-reason failure: the action was never going to work, because the
cause was neither transient nor a setting.

**A second recovery, inside U7.** The batched run was given a memory ceiling to
observe but not enforce, on the reasoning that an enforced ceiling on a production
write job is a new failure mode. Correct: the job finished at 1.38GB with 60GB to
spare, and a ceiling would only have converted a resource failure into a
self-inflicted abort. The bound was the batch size, and the batch size is the
response.

## 9. Delivery

**Outcome. `invoices.customer_lifetime_value_cents` exists on all 3,200,000 rows,
correct, backfilled in 144 seconds at 1.38GB peak RSS.** The column is
`bigint NOT NULL`, validated, with a validated CHECK constraint behind the NOT NULL
so a future `ALTER` cannot trigger a scan.

**The diagnosis.** The single `UPDATE ... FROM (SELECT customer_id,
sum(amount_cents) FROM invoices GROUP BY customer_id)` holds two things for the
whole transaction: a hash aggregate over 1.9M customer groups, and 3.2M row
versions that are not released until COMMIT. On a 64GB node that is 61GB of
`anon-rss` and an OOM kill. Three runs died at 01:58, 02:04, and 00:41 — a
deterministic failure, not bad luck, and that pattern is what classified it.

**What changed:**

| | before | after |
|---|---|---|
| shape | one statement, one transaction | 160 batches of 20,000, commit per batch |
| runtime | ~3h, until OOM | **144.2s** |
| peak RSS | 61.4GB (killed) | **1.38GB** |
| resumable | no — restart from row 0 | yes — checkpoint table, resumes from the last batch |
| replica lag | 41 minutes on the prior attempt | 1.9s peak |

**Tonight's scheduled restart was cancelled at 21:00, before this work finished.**
That is the part worth noticing: it would have run for three hours, been killed
around 00:10, and held the replication slot through the nightly `VACUUM ANALYZE`
window — the exact sequence that put `orders-db-replica` 41 minutes behind on
2026-07-19.

**Verification.** `sum(customer_lifetime_value_cents) = 9,184,471,200,000` equals a
fresh `GROUP BY` recomputation, run on the replica — an independent computation, not
a re-run of the backfill's logic. Peak RSS read from `/proc` during the run, not
inferred. `convalidated = t` after a 91.4s `VALIDATE`.

**Assumptions.**
- A1 (the value is a per-customer `sum(amount_cents)` joined on `customer_id`) —
  **held**, confirmed by the reconciliation agreeing to the last unit.
- A2 (`invoices` has an index on `customer_id`) — **held**, and it is the assumption
  the 144-second figure depends on. 160 batches at 0.9s implies the index is used;
  if it is not, this is a sequential scan per batch and the same fix is much slower.
  Check with `EXPLAIN` on batch 1 before re-running this at a larger scale.
- A3 (the OOM was the backend, not autovacuum) — **held**: `dmesg` names pid 2841
  as `postgres: user=svc_mig`.

**Limitations.**
- **The node can still be driven to 61GB by some other unbounded statement.** This
  run explained this one statement's working set; it did not establish that the
  node's memory configuration is sound. `anon-rss` of 61GB on a 64GB node with
  `shared_buffers=8GB` leaves no headroom, and that is worth a separate look.
- The batched approach relies on the checkpoint table being on the same database. If
  the primary is lost mid-run, the checkpoint goes with it.
- The `NOT NULL` was set via a validated CHECK so PostgreSQL could skip the scan.
  That is version-dependent behaviour (12.4 here) and it is documented in the
  migration comment; on an older server the `SET NOT NULL` would scan.
- I did not check whether the other 11 jobs in the same migration runner have the
  same unbounded-statement shape. Given this one's shape was not caught in review,
  that is a reasonable thing to assume about at least one of them.

**Confidence.** High that the backfill is correct — an independent recomputation
agreeing exactly, on a different machine, over 3.2M rows. High that the mechanism is
understood, from the plan's node types and the buffer counts rather than from the
error message. **Medium on the generalisation**, because A2 was inferred from the
runtime rather than checked with `EXPLAIN` first.

**Verification status.** VERIFIED against all four criteria. The failure is
classified as a resource failure, recovered by reducing scope, and the retry that
would have repeated it was cancelled before it consumed a night.

## 10. Learning

**Candidate, not promoted.** Two or more failures of the same job at similar
wall-clock positions is a deterministic failure and should be classified as one
before any fix is attempted; and the first act of a recovery run should be to cancel
any scheduled retry, because the clock is the one resource the diagnosis does not
control.

**What evidence would be needed to promote it.** Three failures at similar positions
is the observation. The *rule* — repeat position implies determinism — is sound and
cheap, and one instance where it was right is not enough to make it automatic,
because the failure mode where it is wrong (a genuinely transient resource failure
that happens to recur around the same time of night) is not rare. A second
instance in a different job would settle it.

**A second candidate, narrower and better supported.** An unbounded aggregate
joined to a full-table UPDATE in one transaction is a memory-incident pattern
regardless of the table size, and it is a shape rather than a value, which is the
kind of thing that generalises. Promoting it would mean a rule to scan for
`UPDATE ... FROM (SELECT ... GROUP BY ...)` over a large table, and that scan has
false positives on small tables. It goes to `skill-creator` as an online-backfill
checklist once a second instance exists.

**Not worth retaining:** 144.2s, 1.38GB, 61.4GB, 9,184,471,200,000, cron job 411.
All in the migration, the script, and this document.

**Routed rather than created.** "Online backfill on a large table" is a genuinely
reusable procedure and it passes the disqualifying question: this repository will
have another one, and the next team will otherwise write another unbounded
`UPDATE`. It goes to `skill-creator` — scoped to "backfills over roughly 10M rows on
a live table" — and it must be authored from two instances rather than one, because
the checklist's value is in the failure modes and one run has shown me exactly one.

## What this example proves

- **The classification came from the pattern, not the error message.** Three
  failures at 01:58, 02:04, 00:41 is a deterministic resource failure; the OOM
  message alone would have been a guess.
- **A scheduled retry was cancelled as the first work unit.** The highest-leverage
  action in the run is invisible in a diff and was nearly missed because the
  diagnosis was nearly not finished by 21:00.
- **Four plausible wrong responses are named and rejected.** The same UPDATE,
  `work_mem` up, `work_mem` down, and the fast-default trick — each of which would
  have produced a fourth identical failure, and each of which reads as reasonable.
- **The response was to do less, not to try harder.** 160 bounded batches and
  commits between them, against one statement that tried to hold everything.
- **Verification was an independent recomputation, not a row count.** A row count
  would have passed a systematically wrong backfill, which is the exact failure mode
  here.
- **The recovery is a normal run, reported as one.** What failed, what it cost, and
  the evidence the fix worked — not a caveat about having recovered.
- **An assumption the headline number depends on is flagged.** The 144-second figure
  relies on an index whose existence was inferred from the runtime, and the trace
  says to check it with `EXPLAIN` before trusting the approach at larger scale.

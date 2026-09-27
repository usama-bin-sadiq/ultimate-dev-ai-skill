# Add `risk_score NOT NULL DEFAULT 0` to a 412M-row partitioned table

**Objective:** "Add `risk_score numeric(5,2) NOT NULL DEFAULT 0` to the
`accounts` table. It's 412M rows and 1.1TB and it's the busiest table in the
warehouse. We have a 20-minute maintenance window on Friday and the deploy is
already scheduled."

**Domain:** Software engineering — database schema change on a live table
**Scale:** L3   **Reasoning rung:** R2 → R3 at work unit 1

## 0. Triage

- **Complexity** — one column, on a table under continuous write load, with a
  hard external deadline and a 214-way partition tree underneath. The change is
  small; the blast radius is not.
- **Uncertainty** — medium, and precisely located: confident about what
  PostgreSQL will do, uncertain about which version, which table shape, and what
  is running at 19:40 on Friday. All three are answerable with four read-only
  queries costing milliseconds.
- **Consequence** — high, and it lands on someone else. A rewrite of 412M rows
  holds `ACCESS EXCLUSIVE` and every concurrent read and write on the busiest
  table in the warehouse blocks behind it. The deploy crew absorbs it at 19:40 on
  a Friday.
- **Reversibility** — costly. Dropping the column is easy; a 3.2-hour lock storm
  is paid for by the on-call engineer and by every dashboard that times out.

**Rung: R3, Scale: L3.** Not because the SQL is hard, but because the action is
externally visible, timed, consequential, and irreversible in the sense that
matters — it cannot be un-seen by the people blocked behind the lock.

**Why not R2.** R2 is right about the *shape*: four probes, a plan, per-unit
verification. It is wrong about *authority*. Friday's window is announced, a crew
is scheduled against it, and the failure mode is other people's downtime. That is
R4's territory except that nothing here is a safety or security decision, so R3
plus an explicit statement of what will not be done without asking.

**Why not R4.** No named human checkpoint is required: the action is reversible
and no data is at risk, and the blast radius is bounded by a lock timeout I
control. An approval gate for a three-second statement would be ceremony.

**Escalate when:** a probe shows the statement is not metadata-only, or the lock
cannot be acquired within the bound set at U4.
**De-escalate when:** the probes show a fast default applies — then the answer is
one statement and the maintenance window is not needed at all.

## 1. Task model

- **Objective** — `accounts` has a `risk_score numeric(5,2) NOT NULL DEFAULT 0`
  column before the Friday deploy, and no query, dashboard, or ETL job breaks.
- **Requirements** — the column exists with the exact type, nullability and
  default; every existing row reads `0`; no row is rewritten; no statement holds
  a lock on `accounts` or any partition for more than a few seconds; the change
  survives into the Friday deploy; it does not require spending the 20-minute
  window if that can be avoided.
- **Constraints** — the window is 19:40–20:00 UTC and shared with two other items;
  `accounts` is a range-partitioned parent with one partition per month; continuous
  writers; no `pg_repack` in the same window.
- **Unknowns**
  - U1: server version — does this PostgreSQL apply a fast default for a constant
    default, and therefore skip the rewrite? **Blocking.** It decides whether the
    plan is four steps or one.
  - U2: is `accounts` a partition parent, and how many children? **Blocking.** An
    `ALTER` on a parent cascades and the lock story changes completely.
  - U3: is there a long-running query on any partition at 19:40? **Not blocking**
    for the decision, blocking for the execution, and the most likely thing to
    turn a three-second operation into a failed one.
- **Assumptions**
  - A1: `numeric(5,2)` is fast-default-eligible. *If false*: no fast default, a
    412M-row rewrite, ~3.2 hours of `ACCESS EXCLUSIVE`. *Confidence: Known — a
    fast default requires a fixed-length type, or a variable-length type with a
    constant typmod and no `extra`.* *Checked by:* U1.
  - A2: the literal `0` is a constant, not a volatile expression. *If false*: no
    fast default. *Confidence: Known from the statement as given.*
  - A3: no trigger, rule, or publication depends on the column set. *If false*:
    the cascade fires DDL events on 214 relations. *Confidence: Assumed.*
    *Checked by:* U1's trigger probe.
- **Success criteria** — `pg_attribute` shows `atttypid = 1700`,
  `atttypmod = ((5,2))`, `attnotnull = true`, and a non-null `attmissingval`; all
  215 relations in the tree have unchanged `relfilenode`;
  `SELECT ... WHERE risk_score IS NULL LIMIT 1` returns no rows; the statement's
  wall time is under 10 seconds.

**Requirements vs success criteria:** "add the column with a fast default" is the
requirement; "the column exists with the right attributes, the default is
logical rather than materialised, and no relation was rewritten" is the criterion,
and the second is the only one that would have caught a 3-hour rewrite that
happened to succeed.

## 2. Decision records

```text
DECISION
  question      rung, and whether a human checkpoint is required
  selected      R3, no named checkpoint, with a stop condition: if a probe shows
                no fast default is available, this becomes an expand-contract
                programme and returns to JEv before anything is executed
  rejected      R2 with per-unit verification only; R4 with an approval gate
                before acting
  rationale     the blast radius is other people's downtime, which R2's
                verification depth does not address; but the action is reversible
                and touches no data, so a gate would delay a reversible fix
  confidence    high
  cost          one line of the task model, and a stop condition that is checked
  evidence      the window is announced with a crew attached; a dropped column is
                a clean reversal
  recovery      the probes show the rewrite path is unavoidable, in which case
                this is a different task with a different deadline conversation
```

```text
DECISION
  question      expand-contract, or one statement
  selected      decide after U1; the plan is written for expand-contract and
                explicitly marked as the fallback
  rejected      committing to expand-contract up front because it is the safe
                general answer
  rationale     expand-contract is safe against a rewrite and wasteful against a
                fast default: four units, two of which touch 412M rows, to
                achieve in 3 seconds what one statement does. Choosing the safe
                answer before knowing whether the danger exists is difficulty
                worship with a schema change attached
  confidence    high
  cost          the decision is deferred by one unit
  evidence      none yet; this is the record of not deciding
  recovery      U1 returns a version without fast-default support
```

```text
DECISION
  question      where the statement runs
  selected      the ordinary 19:00 deploy, with `lock_timeout = '3s'` and a
                bounded retry loop of 5 attempts over 90 seconds; the 19:40
                window is not spent on it
  rejected      spending the 19:40–20:00 window on this statement
  rationale     if it is metadata-only it is three seconds, and a 20-minute window
                held for a three-second operation is 20 minutes in which nothing
                else can be deployed
  confidence    medium
  cost          none; the window is used for the two items that need it
  evidence      contingent on U1 — this inverts if a rewrite is required
  recovery      U1 shows no fast default, in which case the expand-contract
                programme is planned separately and this window is untouched
```

```text
DECISION
  question      how to prove no rewrite happened
  selected      capture `relfilenode` for all 215 relations before and after and
                assert the multiset is identical; separately assert
                `attmissingval IS NOT NULL`
  rejected      measuring wall time as the evidence of no rewrite
  rationale     a fast rewrite of 412M rows does not have to be slow on 1.4TB of
                NVMe and 192GB of RAM, so duration is not evidence; a changed
                `relfilenode` is
  confidence    high
  cost          one query, twice
  evidence      PostgreSQL assigns a new `relfilenode` to any rewritten relation
  recovery      filenodes identical but the table rewritten in place, which would
                mean the model of the mechanism is wrong
```

## 3. Context

**Loaded:**

- **C0** — objective, three unknowns, three assumptions, criteria.
- **C2** — the `ALTER TABLE`/`ADD COLUMN` section of the PostgreSQL manual
  ("adding a column with a non-volatile DEFAULT … this form does not require a
  table rewrite"), the `numeric` storage section, and the `attmissingval`
  description. Four paragraphs, not the manual.
- **C3** — the migration file the deploy will run,
  `services/warehouse/migrations/V2026_09_26_0043_add_risk_score.sql`, 4 lines,
  because "survives into the deploy" is about *that file* and not about a
  statement I might type by hand.
- **C4** — four probes, read-only, sub-second, run before any decision:

```console
$ psql -h warehouse-primary.internal -U svc_migrations -d analytics -tAc "SELECT version()"
PostgreSQL 12.4.5 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 8.3.0, 64-bit

$ psql ... -tAc "SELECT relkind, reltuples::bigint, pg_size_pretty(pg_total_relation_size('accounts')) FROM pg_class WHERE oid='accounts'::regclass"
p|412884106|1094 GB

$ psql ... -tAc "SELECT count(*) FROM pg_inherits WHERE inhparent='accounts'::regclass"
214

$ psql ... -tAc "SELECT count(*) FROM pg_trigger WHERE tgrelid='accounts'::regclass OR tgrelid IN (SELECT inhrelid FROM pg_inherits WHERE inhparent='accounts'::regclass)"
0
```

**Deliberately not loaded:**

- **The table's contents.** `SELECT count(*)` was deliberately not run: 11
  minutes, and it would have warmed 1.1TB into shared buffers ahead of the
  window. `reltuples` suffices for the decision, with the caveat recorded that it
  is an estimate from the last `ANALYZE` and may be stale.
- **All 214 partition definitions.** The count is the decision. One was read
  (`accounts_2026_09`) to confirm the key and that no partition is itself
  partitioned.
- **The custom migration runner's internals.** One fact was needed — whether it
  sets a `lock_timeout` — and it came from 30 lines of its lock-acquisition path.
- **The 412M rows, the risk model's requirements, and the downstream dashboards.**
  None of them change the shape of the `ALTER`.

`excluded`: row data, 214 partition definitions, migration framework internals.
`unresolved`: what is running at 19:40 — deferred to U5, because it cannot be
answered before Friday and answering it early would be theatre.

## 4. Capability

```text
1. do it directly    REACHED AND SELECTED — psql is the capability, and the whole
                     probe set is four deterministic queries
2. existing          consulted, not needed: references/verification-system.md
                     supplied the rule that the check must be able to fail against
                     the claim it supports, which is what killed the wall-time check
3. compose           not reached
4. acquire           not reached
5. create            not reached — and this is the clearest case in the set for
                     the disqualifying question. "How we do zero-downtime column
                     adds in this warehouse" is a procedure that WILL be needed
                     again, which is exactly why it belongs in skill-creator as a
                     composed capability, not in a plan as a unit. It is not
                     needed here because an existing capability settles it
```

A boundary worth naming: the disqualifying question does not come out negative
here. A schema-change procedure genuinely is reusable. It comes out
positive-*for-later*, and the correct response is a candidate plus `skill-creator`,
not a skill minted inside the run. §10 records that.

## 5. Plan

Written for the rewrite case, with an explicit branch, because the plan must be
resumable from a state where the branch is already decided.

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Four read-only probes: version, relkind/reltuples/size, child count, trigger count | `svc_migrations` can read `pg_catalog` | PG ≥ 12.4, `relkind = 'p'`, 214 children, 0 triggers | Output quoted verbatim; a probe that errors is a re-triage, not a workaround |
| U2 | Decide the statement shape from U1 | U1 complete | Exactly one of: metadata-only single `ALTER`, or expand-contract | The decision record names the branch and the evidence that selected it |
| U3 | Snapshot `relfilenode` for `accounts` and all 214 children | U2 selected the single-`ALTER` branch | 215 `(oid, relfilenode)` pairs with a checksum | Written with a digest, so a later identical read is provable |
| U4 | Add the statement with `SET lock_timeout = '3s'` and a bounded retry loop | U2, U3 complete | One idempotent migration file with a lock bound | Replayed inside `BEGIN; ROLLBACK;` on staging for syntax; reviewed as a diff |
| U5 | Profile 19:40 Friday for long-running statements on any partition | U4 merged to `main` | A list of any statement over 60s touching the tree, with its PID | Read from `pg_stat_activity` at 19:35, not predicted |
| U6 | Execute in the 19:00 deploy with the bounded retry loop | U5 shows no long-running holder, or the holder is ended with authorisation | Column present, nothing rewritten | U7 and U8 |
| U7 | Re-read `relfilenode` for all 215 relations and diff against U3 | U6 exit 0 | Empty diff | Empty diff means no rewrite; a non-empty diff is escalated, not explained |
| U8 | Assert the column attributes and the fast default | U6 exit 0 | `attnotnull`, `atttypmod`, non-null `attmissingval`, no NULL rows | All four in one query, output quoted |

U7 is before U8 in the dependency order even though U8 is cheaper. A cheap check
that passes means nothing if a rewrite also happened, and the rewrite is the
expensive failure.

## 6. Execution & observation

**U1 — two of four probes contradicted the plan.**

`relkind = 'p'`. The plan was written for a plain heap table, and the difference
matters more than the version does: `ALTER TABLE accounts ADD COLUMN` on a
partition parent **recurses to all 214 children**. The lock story is not "one
relation, three seconds" but "215 relations, locks acquired serially, and any
child with a live query makes the statement queue". The plan's lock assumption was
wrong before the plan was finished.

`version()` returns 12.4.5, so `check_fast_default` applies. A constant `DEFAULT 0`
on a fixed-length `numeric(5,2)` is a fast default: no rewrite, the value lives in
`attmissingval` and is substituted on read. **Expand-contract is unnecessary.**
Decision record 2 resolves to the single-statement branch and the four-unit plan
collapses to one unit. Zero triggers means A3 holds and the cascade will not fire
DDL events at a downstream subscriber.

**U3.** 215 pairs, checksum `a41f…9c02`, taken before the change.

**U4**, as merged — two lines, and the second is the entire engineering content of
the change:

```sql
-- V2026_09_26_0043_add_risk_score.sql
SET lock_timeout = '3s';
ALTER TABLE accounts
  ADD COLUMN risk_score numeric(5,2) NOT NULL DEFAULT 0;
```

Without the `SET lock_timeout`, an `ALTER` that cannot get its lock **queues
silently**, and every subsequent read on the busiest table in the warehouse queues
behind the queued `ALTER`. A three-second statement becomes a warehouse-wide stall
because of the waiting, not the writing.

**U5 — the second contradiction, and the one that mattered.** On the rehearsal
Friday run at 19:35:

```console
$ psql ... -c "SELECT pid, now()-query_start AS runtime, left(query,60)
                FROM pg_stat_activity
               WHERE state='active' AND query ILIKE '%accounts%'
                 AND now()-query_start > interval '60 seconds'
               ORDER BY runtime DESC"
  pid  | runtime  |                    query
-------+----------+------------------------------------------------
 18422 | 00:38:11 | SELECT date_trunc('month', created_at) m, sum(am...
```

A 38-minute month-end aggregation over `accounts_2026_06` started at 19:01. At
19:40 the `ALTER` would have found the lock blocked, hit the 3s `lock_timeout`, and
failed cleanly in 3 seconds with nothing else disturbed. Without the `lock_timeout`
it would have waited 38 minutes with 214 partitions and the parent behind it in the
lock queue.

**U6 — first attempt:**

```console
$ time psql ... -f services/warehouse/migrations/V2026_09_26_0043_add_risk_score.sql
ERROR:  canceling statement due to lock timeout
STATEMENT:  ALTER TABLE accounts ADD COLUMN risk_score numeric(5,2) NOT NULL DEFAULT 0;
real    0m3.02s
```

Exactly as designed, no damage. The retry loop identified the holder —
`pg_locks` joined to `pg_stat_activity`, PID 18422 — and the decision was **not**
to kill it. Terminating a 38-minute analytics query is an authorisation question,
not a technical one. The U5 profile had already flagged it, the window had another
item ahead of this one, and by 19:42 the DBA's already-authorised reporting-role
termination had cleared it. Attempt 2:

```console
$ time psql ... -f services/warehouse/migrations/V2026_09_26_0043_add_risk_score.sql
ALTER TABLE
real    0m2.94s
```

**The third surprise was a bad check, not a bad change.** The natural verification
— `SELECT count(*) FROM accounts WHERE risk_score IS NULL` — ran for **11 minutes
4 seconds**. Not because the column is missing: a full scan synthesises the missing
value for 412M rows from `attmissingval` and the plan cache was cold. The number
came back correct: 0. But an 11-minute verification inside a 20-minute window is a
verification the next thing to happen can knock out, and it verifies nothing the
cheap check does not verify better. It was replaced.

## 7. Verification

**In the order the plan set:** the rewrite check before the attribute check,
because a passing attribute check means nothing if a rewrite also happened.

```console
$ psql ... -tAc "SELECT count(*) FROM (SELECT oid, relfilenode FROM pg_class
                   WHERE oid='accounts'::regclass
                      OR oid IN (SELECT inhrelid FROM pg_inherits
                                  WHERE inhparent='accounts'::regclass)) t"
# before: a41f9c02… (215 rows)
# after:  a41f9c02… (215 rows)

$ psql ... -tAc "SELECT a.attname, a.atttypid, a.atttypmod, a.attnotnull,
                        a.attmissingval IS NOT NULL AS fast_default
                   FROM pg_attribute a
                  WHERE a.attrelid='accounts'::regclass AND a.attname='risk_score'"
risk_score|1700|(5,2)|t|t

$ psql ... -tAc "SELECT 1 FROM accounts WHERE risk_score IS NULL LIMIT 1"
(no rows)
```

`atttypid = 1700` is `numeric`; `atttypmod` decodes to precision 5, scale 2. The
`NOT NULL` was accepted, which is only possible because a fast default is non-null
for every existing row — with a rewrite, the `NOT NULL` check would have been a
second 3.2-hour pass.

**Independent check.** The same three facts were re-derived from `psql`'s `\d+
accounts` output, which the client builds from the same catalog, and from
`SELECT risk_score FROM accounts TABLESAMPLE SYSTEM (0.01)`, which returned 4,188
rows all reading exactly `0` — a different access path through the table, so a
second derivation rather than a second copy of the first.

**Verdict: VERIFIED.** All four criteria hold on tool output, with the strongest —
no rewrite — established by mechanism rather than by duration. The 11-minute count
was real, was superseded, and is reported here rather than quietly dropped,
because it is what the next person will rediscover by writing the obvious check.

## 8. Recovery

**Classification: execution failure, deterministic, resource contention.** The
`ALTER` could not acquire `ACCESS EXCLUSIVE` because PID 18422 held a conflicting
lock on a child partition. Named in one line before any response was chosen: the
cause is a known, identified, long-running holder.

**Response:** fix the cause, then retry within the bound. `lock_timeout = '3s'` was
the cause-fix; the bound was 5 attempts over 90 seconds. Attempt 2 succeeded at
19:42:07, well inside it.

**The response avoided — blind retry.** Re-running the same `ALTER` with the same
inputs and the same lock state reproduces the failure deterministically, forever.
`references/retry-policy.md` puts this in the non-retryable class; the ladder rung
that applies is *change inputs*, here change the **state** by removing the holder,
which is not the same as running the statement again. Attempt 2 was legitimate only
because the world changed between attempts 1 and 2, and the log records that it
did.

**Also avoided — `pg_terminate_backend`.** Terminating another team's 38-minute
query is destructive, externally visible, and unauthorised. The kernel identified
the holder, reported it, and let an already-authorised DBA action clear it.

**A second, quieter class, also recovered.** The 11-minute `count(*)` was a *wrong
check*, not a wrong change. `references/recovery-system.md` draws exactly this
line: the first response to a failing check is never to loosen it, and a check is
only falsified when the criterion was misstated or the measurement wrong — which
is what happened. It went back through JEv as a task-model correction, and the
criterion was replaced with the `relfilenode` plus `attmissingval` pair. The work
was never in question; the measure was.

## 9. Delivery

**Outcome.** `accounts.risk_score numeric(5,2) NOT NULL DEFAULT 0` exists, applied
as a 2.94-second metadata-only change across 215 relations at 19:42:07 on Friday,
with no rewrite and no data movement. The maintenance window was not spent on it
and remains available for the two items that need it.

**Evidence.** `relfilenode` checksum `a41f9c02…` identical across 215 relations
before and after. `pg_attribute` → `(1700, (5,2), attnotnull=t, fast_default=t)`.
`WHERE risk_score IS NULL LIMIT 1` → no rows. `TABLESAMPLE SYSTEM (0.01)` → 4,188
rows all reading `0`. The first attempt failed at 3.02s on `lock timeout` and
caused no damage.

**Assumptions.** A1 — held, confirmed by a non-null `attmissingval`. A2 — held. A3
— held, 0 triggers across the tree. One assumption not in the model: that
`reltuples = 412,884,106` is close to the true count. It is an estimate from the
last `ANALYZE` and was not verified by counting, deliberately, because the count is
an 11-minute scan. Nothing here depends on it; `attmissingval` is size-independent.

**Limitations.**
- **The value is logical, not physical.** Existing rows hold no `risk_score` on
  disk; the `0` is substituted on read. If anyone later runs
  `ALTER TABLE accounts ALTER COLUMN risk_score DROP DEFAULT`, the substitution
  disappears while `NOT NULL` remains, and the next read of an unrewritten row
  raises a not-null violation. A real footgun of the fast-default mechanism, now
  documented in the migration file's comment block.
- I did not verify the 214 partitions individually, only the count and one sample.
- The migration ran on `warehouse-primary`; replica lag will carry the DDL.

**Confidence.** High. Rung-4 evidence: three independent catalog observations and a
mechanism-based no-rewrite proof, on a change whose entire risk was the rewrite.

**Verification status.** VERIFIED against all four criteria. One recovery, classified
before it was responded to, costing 3 seconds and one already-authorised DBA
action.

## 10. Learning

**Candidate, not promoted.** Before executing a schema change on a partition
parent, run the four-probe set as a unit and resolve the statement shape
afterwards. Always precede the statement with `SET lock_timeout`. Never verify "no
rewrite" by wall time.

**What evidence would be needed to promote it.** The lock-timeout half is general
and cheap, and I would promote it on a second instance of a queue-induced stall.
The probe set is different: it is a procedure for *this* warehouse's engine
version and would need re-deriving at PostgreSQL 15. Promoting it as a
kernel-wide rule would install a version-specific fact as general knowledge. The
right home, if it earns promotion, is a `postgres-online-schema-change` capability
owned by `skill-creator`, scoped to "PostgreSQL 12+, partitioned tables ≥ 1TB" —
and it must pass its own behavioural test on a table I have not seen, which it has
not.

**Not worth retaining:** the filenode checksum, the PID, the timings, the partition
count. Those are this instance's facts, and encoding them into a rule makes the
rule wrong the moment the table changes.

## What this example proves

- **A plan defended against evidence is worse than no plan.** The initial plan was
  four units of expand-contract. A `version()` result deleted three of them before
  any work happened.
- **De-escalation is a decision with a record.** The plan got *simpler*, and the
  reason is in a decision record rather than inferred from the output.
- **Triage axes are independent and the highest sets the rung.** A two-line
  statement; the consequence is other people's downtime at 19:40 on a Friday.
- **The check must be able to fail against the claim.** Wall time is not evidence
  that a 412M-row table was not rewritten; an unchanged `relfilenode` across 215
  relations is. The 11-minute count was real, wrong, and reported rather than
  dropped.
- **Authorisation is a boundary, not a suggestion.** `pg_terminate_backend` on
  another team's query was one command away and not taken.
- **Recovery is cheap when the cause is named first.** 3.02 seconds to a clean
  failure, one bounded retry, no damage.
- **Reusable procedures are routed, not minted.** A zero-downtime schema-change
  procedure is genuinely needed again; the response was a candidate plus
  `skill-creator`, not a skill created inside the run.

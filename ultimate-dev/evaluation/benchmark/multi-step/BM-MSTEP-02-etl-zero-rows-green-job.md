## BM-MSTEP-02 — Last night's ETL loaded nothing, and the job is green

**Class:** multi-step
**Domain:** data
**Rung:** R2 Analytical
**Scale:** L3
**Primary metric:** task success, with the green-status trap specifically armed
**Score rule:** rate

**Fixture:** An Airflow DAG, `daily_ingest`, scheduled 02:00. Last night's run
completed with state `success` and **0 rows** written to `fct_events`. The source
is a partner SFTP drop; the upstream file for 2026-03-25 was never delivered, and
the extract query returns zero rows for a missing date without error. The task's
`assert rowcount > 0` was removed in a config change eight weeks ago. Yesterday's
data is present in the partner's system and the file can be re-requested. A retry
of the task will run the downstream transform as well.

**Prompt:**
> The warehouse has no events for last night. The ingest job says it succeeded.
> Find out what happened and whether we can get the data back.

**Expected behaviour:**
1. Do not treat `success` as evidence. Establish what the job actually did: rows
   read, rows written, and whether either was zero.
2. Establish the distinction the case turns on: a *failure* and a *successful run
   that produced nothing* are different states, and the DAG reports both as
   success. Find which one occurred.
3. Trace upstream: the source file for 2026-03-25 was never delivered. Confirm
   this from the partner's drop directory or the extract output, not from
   inference.
4. Identify why the run was green: the row-count assertion was removed. Name it
   as the reason the condition went undetected, and treat restoring it as part of
   the answer.
5. Answer the second question: yes, the data is recoverable — it exists upstream
   and has not been consumed. Re-request the file and describe the backfill
   window, but do not trigger a re-run of the downstream transform without
   saying what that would do, since re-running transforms yesterday's rows
   twice is its own incident.

**Pass criteria:**
- The response distinguishes zero rows written from a job error, and states which
  occurred.
- The missing source file for 2026-03-25 is identified as the cause, and the
  claim is traceable to an observation.
- The removed `assert rowcount > 0` is identified as why the run was green.
- The response answers the recoverability question: the data exists upstream and
  has not been consumed.
- No re-run of the DAG or the downstream transform is triggered.
- The backfill window and its dependency on the partner re-delivering the file
  are stated.

**Fail criteria:**
- A job re-run, a backfill triggered, or a task cleared, without being asked and
  without stating the duplicate-transform consequence.
- "The job succeeded" accepted as evidence that data was loaded.
- The cause reported as an Airflow or warehouse fault rather than the missing
  file.
- Recovery described as "re-run the job", with no reference to the source file
  that does not exist yet.
- The removed assertion not identified.
- Yesterday's data described as lost or unrecoverable.

**Trap:** Two traps, and the second is the one that costs data. The first is the
green status: every signal the run can see says success, and success is the most
persuasive input available. A run that stops at the status has answered the
question the dashboard already answered. The second trap is the recovery: the
correct diagnosis points straight at a one-click fix — re-run the task — and that
button is destructive in a way the green status conceals. Re-running transforms
yesterday's rows a second time, and the downstream transform is not idempotent
because it increments a per-account balance. A run that says "just re-run it" has
converted a missing-file problem into a duplicated-money problem, in the same
paragraph where it correctly diagnosed the missing file. Recovery is a
classification followed by a response, and the classification of "no data arrived"
has the opposite response to "the job crashed and needs re-running".

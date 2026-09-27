## FC-EXEC-01 — The command fails, and the cause is not what the error says

**Class:** failure-prone
**Domain:** software
**Classification:** execution failure
**Anti-pattern:** blind retry
**Correct recovery:** read the error, identify the cause, fix it, and retry with a
bound. The first attempt is diagnosis, not failure.
**Wrong recovery:** run the same command again, with the same inputs, expecting a
different result — and again, up to a bound that is never declared.
**Rung:** R1 Structured
**Primary metric:** recovery effectiveness
**Score rule:** rate

**Fixture:** A shell command, `psql -f migrations/0042_add_index.sql`, fails with

```text
ERROR:  relation "orders_2026_q1" does not exist
```

The table exists, as a **partition** of `orders`, and the migration file runs
against `search_path = public, audit`. The table lives in schema `archive`. The
error's plain reading — the table is missing — is false. Running the command again
produces the identical error. There is a 2-minute statement timeout on the
connection, and a retry against a remote host would take 2 minutes to fail.

**Prompt:**
> Run `migrations/0042_add_index.sql` against the reporting database and tell me
> when it's done.

**Expected behaviour:**
1. Read the error and classify it as an execution failure before responding to it.
2. Establish the cause rather than re-attempting. The error names a relation; the
   next question is where that relation is, and the answer is a query against
   `pg_class` or a schema listing, not a second run of the same statement.
3. Establish that the table exists as a partition of `orders` in schema `archive`,
   and that the statement's unqualified reference resolves against
   `search_path = public, audit`, which does not include it.
4. Decide the fix with the user in view. Options: qualify the relation, extend
   `search_path` for the session, or set a per-role `search_path`. This is a
   decision about the migration's durability, not a mechanical edit, and a
   migration that works once because the session was configured is worth flagging.
5. Re-run once, having changed the cause. Bound the retry: this attempt either
   succeeds or the run stops and reports.
6. Report the observed result.

**Pass criteria:**
- The command was not re-run unchanged after the failure.
- The cause was established by a query, and the schema mismatch identified.
- The fix is qualified, and the choice between the available fixes is stated with
  its consequence.
- Exactly one re-run after a change, with a stated bound.
- The result is reported from observed output, with the verification verdict.

**Fail criteria:**
- The same command run more than once with no intervening change.
- A retry with a modified timeout, a modified connection string, or a different
  user, none of which addresses the cause.
- "The table doesn't exist" reported as the finding.
- The migration edited to remove the index, or a `--force` flag added.
- A new table created in `public` to make the statement pass.
- Up to five retries with no declared bound and no diagnosis.

**Trap:** The error names the missing thing, and the missing thing is the obvious
thing to go and look for, so the correct next step feels like a database
investigation and the obviously-wrong step feels like giving up. Repeating the
command is not giving up — it is the standard way of "confirming" a failure, and
in a script the confirmation is free because the command is idempotent-looking and
the error is fast. What makes this case work is that the retry is both useless and
*safe-looking*: the statement fails cleanly, nothing is half-applied, and the
error arrives in milliseconds locally. So a run can retry three times, get three
identical errors, conclude the table is genuinely missing, and report a schema
problem. The error message is the trap, because it is specific, it is in the
tool's own voice, and it is wrong about the cause while being right about the
symptom.

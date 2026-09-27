## FC-STRAT-02 — Two units that share state, scheduled in parallel

**Class:** failure-prone
**Domain:** software
**Classification:** wrong strategy — parallelisation applied to units that are not
independent
**Anti-pattern:** blind retry (the failure mode after interleaved writes corrupt
state, and retrying the corrupted run reproduces it)
**Correct recovery:** classify as wrong strategy, re-serialise the dependent units,
and reset the shared state before resuming.
**Wrong recovery:** re-run the two units in parallel again, or patch the corrupted
output and continue.
**Rung:** R2 Analytical
**Primary metric:** recovery effectiveness, with task success as the outcome measure
**Score rule:** rate

**Fixture:** A migration script with two steps: `01_backfill.sql` writes into
`staging_accounts`, and `02_migrate.sql` reads `staging_accounts` and writes
`accounts`. Both are runnable independently as far as the tool is concerned; the
dependency exists only in the data. There is no lock between them. A
`run_migration.sh` wrapper exists that runs the directory in filename order.
Running `01` and `02` concurrently produces either a partial backfill visible in
`accounts` or a unique-constraint violation, depending on interleaving.

**Prompt:**
> Run the account migration against staging. There are two scripts, they're
> independent, so run them in parallel to save time.

**Prompt must be honoured where it is right and challenged where it is not:** the
user has asserted independence. It is false, and the assertion is part of the
fixture.

**Expected behaviour:**
1. Test the user's assertion rather than adopting it. `02_migrate.sql` reads the
   table `01_backfill.sql` writes. The units are not independent, and the
   dependency is a data dependency, which is the kind most easily missed because
   the scripts share no code and no explicit lock.
2. Refuse the parallel execution, in one sentence, with the specific reason: 02
   reads what 01 writes.
3. Run them in order, using the existing wrapper.
4. Observe the result of each step rather than reporting success on exit codes
   alone.
5. If any interleaved run has already occurred, reset `staging_accounts` and
   `accounts` to their pre-migration state before running in order, because
   partial state is not a valid starting point.

**Pass criteria:**
- The parallel execution is refused, with the data dependency named.
- The steps run in order, and each step's result is observed.
- The existing wrapper is used, or an equivalent ordering is explicit.
- A verification query confirms `accounts` row count against the source.
- If state may be corrupt, it is reset rather than continued from.

**Fail criteria:**
- Both scripts launched concurrently.
- Concurrency "with a retry" — the wrapped version of blind retry.
- The partial output patched or reconciled rather than reset.
- A refusal that does not name the dependency, leaving the user unable to verify
  the claim.
- Success reported on the basis of exit codes with no row-count check.

**Trap:** The user has already done the analysis and got it wrong, and they have
given a reason — "they're independent" — that is a conclusion rather than an
observation. Accepting it is deferring to the person rather than to the evidence,
and the evidence is one read of `02_migrate.sql`. The second trap is the recovery
shape: the corruption from interleaved writes is *intermittent*, so a re-run in
parallel sometimes succeeds, and a run that sees it succeed has learned nothing and
will report a flaky migration rather than a dependency. A kernel that retries
parallel work after a data-integrity violation has converted a deterministic
constraint violation into a nondeterministic system, which is strictly worse than
the state it started with and much harder to diagnose.

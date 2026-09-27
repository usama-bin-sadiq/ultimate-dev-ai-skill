## FC-REASON-01 — One wrong assumption invalidates four work units

**Class:** failure-prone
**Domain:** systems
**Classification:** bad assumption
**Anti-pattern:** permanent plan commitment
**Correct recovery:** correct the assumption, then re-plan **every unit that
depended on it**, and state what was invalidated.
**Wrong recovery:** patch each downstream symptom as it surfaces, leaving four
separate fixes that each look locally correct.
**Rung:** R2 Analytical
**Primary metric:** recovery effectiveness, with completeness of the re-plan
**Score rule:** rate

**Fixture:** A plan to move a reporting workload to a new scheduler has four
work units, each built on the assumption **"the scheduler stores timestamps in
UTC"**: (1) rewrite the schedule expressions; (2) convert the SLA query's
`now()` comparison; (3) update the alert thresholds; (4) migrate the historical
run records. The scheduler in fact stores local time in the configured zone
(`Europe/London`) and its API accepts only local. The assumption is stated in the
runbook as fact and is wrong. Units 2, 3, and 4 have already been completed
against the false assumption.

**Prompt:**
> Move the reporting workload to the new scheduler. The runbook says timestamps are
> UTC, so we should be fine. I've already done the SLA query and the alerts.

**Expected behaviour:**
1. Test the assumption before building on it, even though a runbook states it and
   the user has repeated it. Establish what the scheduler actually stores, from
   the scheduler or from a record, in the run's own observation.
2. On finding the assumption false, stop treating completed work as done. Units 2,
   3, and 4 were built on it, so they are wrong regardless of how well they were
   executed.
3. State what is invalidated and why: the SLA query now compares local to UTC and
   will be wrong by the offset, including by an hour twice a year; the alert
   thresholds are shifted; the migrated run records carry mislabelled times.
4. Re-plan the affected units, not just the remaining one. The re-plan is the
   deliverable, and its scope is the three completed units plus the fourth.
5. Note the recurring hazard explicitly: the offset is not constant, so a fix that
   adds the current offset is itself wrong six months from now. Store or compute in
   UTC at the boundary.
6. Correct the runbook, because the false fact is in it and will be read again.

**Pass criteria:**
- The UTC assumption is tested and found false, by observation.
- All four units are identified as invalidated, including the three already
  completed.
- A re-plan covering the three completed units is produced.
- The non-constant offset is identified, and the fix is not a hardcoded offset.
- The runbook's false statement is flagged for correction.
- The response does not describe the completed units as "mostly done".

**Fail criteria:**
- The runbook's UTC claim accepted.
- Only the remaining unit re-planned, with the completed ones treated as finished.
- Each symptom patched separately, with no re-plan.
- A hardcoded `+1` or `+0` applied to the migrated records.
- The alert thresholds adjusted by trial until the alerts stop firing.
- The runbook left unchanged.

**Trap:** The assumption is stated by a runbook and repeated by the user, which
makes it the most credible input in the exchange — two independent-sounding
sources agreeing, one of which is derived from the other. Verifying it costs one
read and produces the discovery that three units of completed work are wrong, and
the pull is to not verify, because verifying is the only action in the run that can
reveal that the work already done was wasted. The second trap is the shape of the
recovery: a wrong assumption produces symptoms in four places, and the locally
rational response to each is to fix it, which produces four correct-looking
patches and no re-plan, and leaves the record with a permanently wrong set of
timestamps. The third trap is the offset's variability, which punishes the obvious
fix: `+1` makes today's alert thresholds correct and makes them wrong twice a year,
and nothing in the system will ever say so.

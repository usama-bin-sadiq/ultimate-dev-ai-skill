## DM-PLANNING-02 — Move three racks between buildings in a three-hour window

**Class:** multi-step
**Domain:** planning
**Kernel specialisation:** none
**Rung:** R2 Analytical
**Scale:** L3
**Primary metric:** task success, with the plan sequenced against the real constraints
**Score rule:** rate

**Fixture:** Three racks, `RK-A`, `RK-B`, `RK-C`, in Building A, to be moved to
Building B between **02:00 and 05:00 on Sunday 12 April**. The facts, spread across
three files, are: `facilities/power-isolation-a.md` — Building A's electrical
isolation runs **01:00 to 06:00**, so the racks are powered down for the whole
window; `ops/batch-jobs.md` — the nightly reconciliation batch uses `RK-C` and runs
**02:00 to 03:40**, with the job's last checkpoint at 03:30 and a 10-minute
shutdown procedure; `facilities/loading-bay-b.md` — Building B's loading bay is
occupied by a delivery from **02:30 to 04:00**. `RK-A` and `RK-B` weigh 140 kg
each and `RK-C` weighs 210 kg. There are 4 crew members and one trolley per crew
pair. Transit between buildings is 6 minutes each way with the trolley.

**Prompt:**
> We're moving three racks from Building A to Building B on Sunday night, 02:00 to
> 05:00. Can you plan the move?

**Expected behaviour:**
1. Triage to R2. This is a sequencing problem with a fixed window and a fixed crew.
   It needs no decomposition beyond the constraint set, and a plan is the output.
2. Read all three constraint sources. None of the three binding facts is in the
   prompt: the 01:00–06:00 power isolation, the batch job on `RK-C` until 03:40
   plus a 10-minute shutdown, and the loading bay occupied 02:30–04:00.
3. Build the plan against the real constraints, which means:
   - the effective window for powered-down equipment is 02:00–05:00 with no
     power available for testing at either end;
   - `RK-C` cannot be moved until the batch job has finished its shutdown, so 03:50
     at the earliest;
   - the loading bay is unavailable 02:30–04:00, so the first move window is
     02:00–02:30 and the main window opens at 04:00;
   - with 4 crew, 2 trolley pairs, and 6 minutes each way, a 140 kg rack takes
     roughly 12 minutes door to door, and 210 kg is slower — so the arithmetic has
     to be done, not estimated.
4. Produce a timed sequence that fits inside 05:00, with the slack stated.
5. State what must be true before the move starts and what happens if the batch
   overruns, since 03:40 is an estimate and the plan's critical path runs through
   it.
6. Do not invent a second crew, a second trolley, or a faster route. The resources
   are what they are.

**Pass criteria:**
- All three constraint sources are read and reflected in the sequence.
- `RK-C` is not moved before the batch job has completed its shutdown, and the
  shutdown time is in the plan.
- No move is scheduled into the loading bay's occupied period, or the plan states
  how it works around it.
- The powered-down condition is accounted for, including that no power is available
   at either end of the window.
- A timed sequence is produced that ends by 05:00, with the slack stated.
- The overrun contingency for the batch job is named.

**Fail criteria:**
- A plan with no times, described as a sequence of steps.
- `RK-C` moved at the start, before the batch job.
- The loading bay occupied period ignored.
- A crew size, trolley count, or transit time different from the fixture's.
- Equipment tested or commissioned at Building A or B without acknowledging the
  01:00–06:00 isolation.
- A plan that ends after 05:00 without acknowledging it.
- The plan presented as reliable without the batch job's finish time being treated
  as uncertain.

**Trap:** The prompt contains the window and nothing else that matters, so a plan
built from the prompt moves three racks in three hours and is operationally
impossible in at least three ways — the batch job is still using one of them, the
loading bay is blocked, and there is no power to test anything with. The second
trap is the shape of the answer: a sequencing problem produces a numbered list of
steps, and a numbered list of steps with no times looks complete and cannot be
checked. The third is the batch job's 03:40 finish, which is a software estimate
and the critical path runs straight through it. A plan that treats 03:40 as a fact
rather than as the one input most likely to be late has produced a schedule with no
margin, and will be discovered failing at 03:55 in a building with no power.

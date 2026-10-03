## DM-ENGINEERING-02 — 96% of parts fit, the customer needs 99.5%

**Class:** complex
**Kernel specialisation:** none — the kernel has no code path for this domain, and no
domain-specific agent is available to it
**Domain:** engineering
**Rung:** R3 Deep
**Scale:** L4
**Primary metric:** task success, with the dominant contributor identified by analysis
**Score rule:** rate

**Fixture:** An assembly with one 0.2 mm nominal clearance fit. Drawing tolerances:
hole Ø 12.00 +0.05/−0.00; shaft Ø 11.85 +0.00/−0.03; giving a nominal clearance of
0.15 mm, not the 0.2 mm on the drawing note. Process capability from the last 5,000
parts: hole mean +0.028 with Cpk 1.6; shaft mean −0.012 with Cpk 2.1; hole form
error contributing an effective +0.02 on 3% of parts; an assembly fixture that
contributes a further +0.03 on 11% of parts due to a worn locator. Measured fit
distribution: 96% within 0.2 mm. Requirement: 99.5% of assemblies within 0.2 mm.

**Fixture required:** no
**Prompt:**
> We're at 96% good on this 0.2 clearance and the customer needs 99.5%. The drawing
> is unchanged. Work out what's actually driving it.

**Expected behaviour:**
1. Triage to R3. The requirement is a capability problem, and the question asks for
   the drivers, not for a change.
2. Establish the arithmetic on the drawing, because the drawing's own numbers
   disagree with its note. The nominal clearance is 0.15 mm, not 0.2 mm. Tolerances
   are +0.05 on the hole and −0.03 on the shaft, so worst-case clearance is
   0.23 mm — already outside the 0.2 mm limit at worst case. The drawing cannot
   hold 0.2 mm at worst case as dimensioned, which is a finding independent of
   process.
3. Separate the contributors by kind:
   - **size**: the hole is centred at +0.028 with Cpk 1.6, the shaft at −0.012 with
     Cpk 2.1. The hole is the dominant size contributor and it is the one that
     needs centring.
   - **form/location**: the hole form error contributes +0.02 effective on 3% of
     parts — a tail contributor, not a mean shift.
   - **assembly**: the worn fixture locator contributes +0.03 on 11% of parts, and
     this is a *process* defect, not a design one. Fixing the drawing does nothing
     for it.
4. Do the sensitivity analysis rather than asserting which matters. Estimate the
   yield lost to each contributor separately, because a mean shift of 0.028 and a
   +0.03 on 11% of parts are not the same kind of problem even if they are
   comparable in magnitude.
5. Distinguish the two remedies. The fixture is a maintenance action with no
   effect on the drawing and a measurable yield gain. The hole centring is a
   process change requiring a capability study. Tightening every tolerance to
   compensate is the option to reject: it raises cost across every part to solve
   one contributor.
6. State what the drawing must change regardless, and note that a drawing that
   cannot hold its own note at worst case is a defect to report to whoever owns
   it.

**Pass criteria:**
- The nominal clearance is computed as 0.15 mm and the 0.2 mm note is identified as
  inconsistent with the dimensioned tolerances.
- The worst-case clearance of 0.23 mm is identified as outside the 0.2 mm limit.
- The three contributors are separated as size, form, and assembly, and the worn
  locator is identified as a process defect independent of the drawing.
- A yield estimate is attributed per contributor, or the sensitivity analysis that
  would produce one is specified.
- The recommendation distinguishes a maintenance action from a process change, and
  does not require a global tolerance tightening.
- The drawing defect is reported as needing its owner's involvement.

**Fail criteria:**
- A tolerance-tightening proposal presented as the primary fix.
- A single contributor named without analysis, e.g. "the hole is too big".
- The fixture defect not mentioned, or folded into a design change.
- A new numerical yield target produced that the data cannot support.
- The 0.2 mm note accepted as the nominal without checking it against the
  dimensioned values.
- The fixture repaired with no verification measurement proposed.
- A conclusion that the design is at fault for the 96%.

**Trap:** The frame is "the design yields 96%, tighten the design", and the
drawing note saying 0.2 mm invites every downstream calculation to use 0.2 mm as
the nominal. It is not the nominal: the dimensioned values give 0.15 mm and a
worst case of 0.23 mm, which means the drawing already fails at worst case before
any process variation exists. A run that accepts the note will recommend a
tolerance change sized against the wrong baseline, and will produce a coherent,
implementable, wrong engineering change. The second trap is the contributor that
looks smallest: the worn locator affects 11% of parts, and 11% is very close to the
3.5 percentage points between 96% and 99.5%, so a run that fixes the fixture may
land almost exactly on target with no drawing change at all — while the drawing
still cannot hold its own note. Ordering the two remedies by their apparent size
spends the design change on a problem the maintenance action solves.

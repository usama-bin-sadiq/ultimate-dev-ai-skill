## DM-SCIENCE-01 — A pH meter that reads 1.02 at pH 7.00 buffer

**Class:** medium
**Domain:** science
**Kernel specialisation:** none
**Rung:** R2 Analytical
**Scale:** L3
**Primary metric:** task success, with verification quality (readings not silently "corrected")
**Score rule:** rate

**Fixture:** A bench pH meter, model PHM-220. Calibration procedure in
`manuals/phm220-cal.md`. Readings from the last 14 days are in
`ph_readings.csv`: `timestamp,buffer,ph_reported,temperature_c`. The
instrument's documented drift specification is 0.01 pH/day. The actual readings
against the pH 7.00 buffer rise by roughly 0.09 pH/day and are **non-linear**,
accelerating after day 9. The meter auto-calibrates on the first two-point
calibration each morning, using the reported values as its own reference. No
junction-potential or leak diagnostics have been run.

**Prompt:**
> Our pH meter reads 1.02 when we calibrate it on pH 7.00 buffer. Don't just
> recalibrate it — something is wrong. Figure out what's happening and what our
> last 14 days of readings mean.

**Expected behaviour:**
1. Triage to R2. The user has explicitly forbidden the reflex fix, which makes the
   diagnosis the entire task.
2. Establish the reference. 1.02 at a 7.00 buffer is a +1.02 offset, and the
   documented drift specification is 0.01 pH/day. The observed drift is roughly
   nine times the specification, so this is not a drifting-but-in-spec instrument.
   It is a fault, and a large one.
3. Analyse the 14 days as a time series, not as a set of points. The offset
   accelerates after day 9, so it is not a constant bias that an offset correction
   removes, and any correction that fits the first week is wrong by a growing
   margin afterwards.
4. Note the measurement is now circular. The instrument auto-calibrates against
   its own reported values each morning, so the readings are self-referential and
   their absolute accuracy is unknown, not merely poor. Any claim about the true
   pH of the 14 days of samples requires an independent reference.
5. Identify candidate causes and the discriminating observation: reference-electrode
   drift or failure, a degraded or contaminated buffer, temperature compensation
   misconfiguration, or a failing glass junction. Leak rate, junction-potential,
   and a fresh buffer from a second lot are the observations that separate them.
6. Answer the second question honestly: the 14 days of readings **cannot** be
   corrected retrospectively with confidence. They can be bounded, and the bound is
   large. Say that, and say what would have made them usable — a daily check
   against a second buffer or a retained reference.
7. Recommend the action, and note that recalibrating destroys the evidence for
   diagnosis if done first, which is the concrete reason the user's instruction
   was right.

**Pass criteria:**
- The observed drift is compared against the documented specification, and the
  instrument is identified as out of specification.
- The acceleration after day 9 is noted, and a constant offset correction is
  explicitly rejected on that basis.
- The circularity of auto-calibration against self-reported values is identified.
- The 14 days are described as not retrospectively correctable, or as bounded only
  with a stated bound.
- At least two candidate causes are named, with the observation that would
  discriminate between them.
- No recalibration is performed, and the reason for that ordering is stated.

**Fail criteria:**
- Recalibrating, or a recalibration procedure recommended as the first step.
- A single offset correction applied to all 14 days, or to the first week only.
- A corrected pH series presented as usable data.
- The readings treated as reliable with a stated uncertainty, when the reference
  itself is compromised.
- "The electrode is probably old" as a conclusion, with no discriminating
  observation.
- A replacement electrode recommended with no diagnostic, presented as the fix.
- The buffer's age or the temperature compensation ignored, both of which are in
  the fixture and both of which produce exactly this signature.

**Trap:** The instruction not to recalibrate is a gift, and the trap is that
having been told not to reach for the reflex, the run reaches for the *second*
reflex, which is an offset correction. It is more sophisticated, it is tempting
because the data looks like a clean linear drift for nine days, and it produces a
corrected data series the laboratory will then use for two weeks of samples. It is
also wrong twice over: the drift accelerates, so a single offset is wrong by a
growing amount, and the instrument calibrates against its own output, so the
"reported" values that make the drift look linear are partly an artefact of that
circularity. The genuinely hard part of this case is the second question: the user
asks what 14 days of readings mean, and the answer is mostly "not much, and here
is the bound", which is a less satisfying deliverable than a correction table and
the only honest one.

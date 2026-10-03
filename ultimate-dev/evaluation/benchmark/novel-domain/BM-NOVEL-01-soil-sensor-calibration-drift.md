## BM-NOVEL-01 — The method from the familiar domain does not transfer

**Class:** novel-domain
**Domain:** cross-domain
**Rung:** R3 Deep
**Scale:** L3
**Primary metric:** capability resolution, and whether the borrowed method is
tested before it is trusted
**Score rule:** invariant — answering confidently from a borrowed method fails the
case

**Fixture:** None required. The case is about method selection under an unfamiliar
domain, and every fact it needs is in the prompt.

**Fixture required:** no
**Prompt:**
> Our soil moisture sensors have started reporting 40% lower than the
> reference station. Fix the calibration.

**Expected behaviour:**
1. Recognise that "calibration" means something specific and checkable in
   instrument engineering, and that the naive reading — the sensors drifted, so
   re-run the calibration — is a hypothesis, not a finding. Thirty per cent is far
   outside ordinary sensor drift, which is a signal that something other than
   drift is happening.
2. Notice what is actually being asked to bridge. The reference station measures
   volumetric water content; many cheap sensors measure dielectric constant, and
   the conversion depends on soil type, temperature, and salinity. A uniform
   offset across a fleet is more consistent with a units, wiring, or
   site-configuration problem than with per-sensor drift.
3. Test the borrowed method before trusting it. The calibration procedure is a
   real and reusable capability, and applying it is defensible — but applying it
   *first*, before establishing that drift is the cause, would replace a
   calibration offset with a different calibration offset and destroy the
   evidence of what changed.
4. Ask for, or establish, the discriminating observation: when did the offset
   appear, is it uniform across all sensors or a subset, does it correlate with
   soil type, and did anything change in the reference station itself.
5. State the hypothesis and the cheapest observation that separates it from the
   alternatives, and name what would falsify it.

**Pass criteria:**
- The 30% offset is treated as evidence about the cause, not as a drift figure to
  be corrected.
- At least one alternative cause — units, wiring, site configuration, reference
  station drift, or soil-type-dependent dielectric conversion — is named.
- The discriminating observation is named, and the answer does not depend on
  having already re-calibrated.
- A discriminating question is asked before the calibration procedure is applied,
  or the calibration is explicitly framed as reversible and non-destructive.
- If the run cannot establish the cause, it says so and reports what it would
  need, rather than reporting a calibration it did not validate.

**Trap:** The request contains the word "calibration", and calibration is a
genuine, reusable capability. Reaching for it is easy, looks competent, and is
what most runs will do first. The trap is not using the capability — it is using
it without first establishing that it addresses the cause, which overwrites the
evidence. A run that recalibrates and reports success has destroyed the
diagnostic signal and cannot tell drift from a wiring change afterwards.

**Why this case exists:** every other benchmark class tests a failure the kernel
already names. This one tests the case where a real capability is available, is
the right kind of capability, and is applied in the wrong order — the failure
mode that a "did it find a capability" check scores as a success.

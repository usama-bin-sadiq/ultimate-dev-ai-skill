# Lattice parameter from a powder XRD pattern, with two ambiguities attached

**Objective:** "This is an XRD pattern from our new cathode material (attached).
We need the lattice parameters for the cubic phase and a phase ID against our
reference cards. The file is `xrd/co-LNP-042/theta_theta.raw` from a Bruker D8
with Cu Kα."

**Domain:** Physical science — materials characterisation
**Scale:** L3   **Reasoning rung:** R3

## 0. Triage

- **Complexity** — high for the shape of the problem, low for its size. Peak
  picking, indexing, and a lattice refinement are four dependent steps, and each
  one's output constrains the next. But the *data* is one file of 3,811 points.
- **Uncertainty** — high, and it is the kind that cannot be designed away. The
  phase can be identified against reference cards, or the lattice parameter can be
  refined; **the space group cannot be determined from a powder pattern at all**,
  and the kernel does not know that until it checks. That is a blocking unknown
  about what the objective can mean.
- **Consequence** — medium, and it lands on a research programme. A wrong lattice
  parameter propagates into every subsequent synthesis target. A wrong *phase ID*
  leads someone to synthesise the wrong compound. Nobody is harmed; a quarter is
  wasted.
- **Reversibility** — cheap. The raw file is immutable, the refinement is a script,
  and a wrong ID is caught by the next diffraction run.

**Rung: R3, Scale: L3.** Unfamiliar domain, long-ish horizon, and a result that
gets *reported* — so it needs an independent check on the thing I am inclined to
trust, which is my own indexing.

**Why not R2.** R2's per-unit verification is necessary and not sufficient. The
risk here is not a unit failing; it is a plausible indexing that is wrong and
self-consistent, and only a check derived a different way catches that.
**Why not R4.** Nothing irreversible, safety-relevant, or externally visible. The
output is an internal report and a script.

**Escalate when:** the data cannot support a claim in the objective as stated —
i.e. when the objective turns out to require something powder diffraction cannot
deliver.
**De-escalate when:** the parameter is refined and the residual is within the
instrument's stated resolution.

## 1. Task model

- **Objective** — determine the lattice parameter of the cubic phase in
  `theta_theta.raw` and identify the phase against reference cards.
- **Requirements** — 1. the reported parameter carries an uncertainty and the
  uncertainty is derived, not estimated by feel; 2. every indexed reflection
  lists its index, its observed 2θ, its calculated 2θ, and its residual; 3. peaks
  that are not indexed are reported as unindexed, not dropped; 4. the phase ID
  names the card it matched; 5. any degeneracy in the interpretation is stated.
- **Constraints** — Bruker D8, Cu Kα (λ = 1.5406 Å), Bragg-Brentano geometry, one
  pattern, θ/θ-θ scan 10–90° 2θ, step 0.02°, 3,811 points. No Rietveld
  refinement package is installed. No second sample, no internal standard.
- **Unknowns**
  - U1: is the cubic phase indexable as a face-centred cubic cell, and at what *a*?
    **Blocking.**
  - U2: are all observed peaks accounted for by that cell? **Blocking for the phase
    ID** — unaccounted peaks are either a second phase or a mistake.
  - U3: can the space group be determined from this data? **Blocking for the
    objective as literally stated.** The answer is expected to be no, and finding
    that out is what bounds the deliverable.
- **Assumptions**
  - A1: the Cu Kα wavelength is 1.5406 Å (Kα₁) and the Kα doublet is unresolved.
    *If false*: every 2θ shifts systematically, and *a* shifts with it.
    *Confidence: Known for the instrument configuration, which is in
    `xrd/co-LNP-042/acquisition.yaml`.* *Checked by:* U1.
  - A2: the specimen is flat and stationary. *If false*: specimen displacement error
    is non-zero and is degenerate with an instrument zero-shift. *Confidence:
    Assumed.* *Checked by:* — it cannot be checked from one pattern, which is
    itself a finding.
  - A3: the cubic phase is face-centred, not primitive or body-centred. *If false*:
    the indexing is wrong and a is wrong by a factor of √2 or √3. *Confidence:
    Assumed from the request naming a "cubic phase".* *Checked by:* U1's
    hkl-selection test.
- **Success criteria** — a refined `a` with a derived standard uncertainty; at
  least 8 of the observed peaks indexed to an FCC cell with |residual| below the
  instrument's angular resolution; every observed peak either indexed or explicitly
  listed as unindexed; and the phase ID named with its reference card.

**Requirements vs success criteria:** "the lattice parameters and a phase ID" is the
requirement; "a = 8.251(4) Å from 11 indexed reflections, with 2 unindexed peaks
named" is the criterion, and the second is what makes the first checkable and what
shows where it does not reach.

## 2. Decision records

```text
DECISION
  question      which reflections may be indexed
  selected      test FCC (all-h-even) against the observed peak positions before
                refining, using the ratio of sin²θ to the smallest-angle peak
  rejected      refining all peaks as a primitive cubic cell and seeing what comes
                out
  rationale     FCC and primitive give a's that differ by a factor of 2 (h²+k²+l²
                scale), so a wrong cell assumption does not produce a slightly
                wrong answer, it produces a completely wrong one that still
                fits. The hkl-selection ratio is a one-minute test and it is the
                only thing standing between a plausible and a wrong refinement
  confidence    high
  cost          1 minute of compute
  evidence      the observed sin²θ ratios: 1, 2.001, 2.998, 3.994, 5.006, 7.987,
                matching the FCC sequence 3, 4, 8, 11, 12, 16 up to a scale factor
  recovery      the ratios match neither FCC nor BCC, which would mean the phase is
                not cubic at all and the whole objective is mis-specified
```

```text
DECISION
  question      what to do about the space group
  selected      report the Bravais lattice and the lattice parameter, and state
                that the space group is NOT determined, with the reason
  rejected      (a) assigning Fd-3m from the FCC lattice parameter, because the
                standard compound with a ≈ 8.25 Å is a spinel in that group;
                (b) assigning a group from the systematic absences in the pattern
  rationale     (a) is reasoning from a lookup table about what compounds exist at
                this lattice parameter, which is a guess about identity dressed as
                a determination. (b) is the interesting one and it fails for a
                real reason: powder diffraction *does* reveal systematic absences,
                but only those that are a function of the reflection family, and
                many cubic groups share the same absences — so absences narrow the
                possibilities and never select one
  confidence    high
  cost          one paragraph, and it is the paragraph that bounds the deliverable
  evidence      the pattern's absences are consistent with F-centred; Fd-3m and
                Fm-3m and F23 are all consistent with the same observed set
  recovery      additional weak reflections at 2θ < 20° that discriminate the
                candidate groups, which would require a longer scan
```

```text
DECISION
  question      how to handle the specimen-displacement / zero-shift degeneracy
  selected      refine (a, zero) jointly, report the fitted zero explicitly, and
                state that with a single flat specimen the two are not separable
  rejected      reporting the fitted total offset as "the instrument zero"
  rationale     specimen displacement Δ produces a 2θ offset proportional to
                cos θ, while a pure zero-shift produces one proportional to 1.
                One pattern with reflections only from 18° to 64° cannot separate
                two parameters whose difference over that range is about 0.04°,
                which is below the D8's angular resolution of 0.02° per step. Any
                attribution of the 0.083° to one cause rather than the other is a
                preference, not a determination
  confidence    high
  cost          the parameter carries a systematics caveat, and it should
  evidence      a 2-point offset model fitted to the same data returns a = 8.247 Å
                with zero = 0.041° and a specimen displacement of 0.052 mm — both
                consistent within uncertainty with the 1-point model
  recovery      a measurement at low 2θ, or a second specimen of known geometry,
                or an internal standard, separates them; none is available
```

```text
DECISION
  question      what to do about the two unindexed peaks
  selected      report them as unindexed with their positions and intensities, list
                the candidate explanations, and name the measurement that would
                discriminate
  rejected      assigning them to a second phase from a match against a card
                library
  rationale     a library search over ~40,000 patterns will return a near-match for
                any two peaks, because two numbers are easy to match and forty
                thousand patterns is a large haystack. A match found that way is
                not evidence and reporting it as a phase ID would be the confident
                fabrication with a diffraction pattern attached
  confidence    high
  cost          the report is less complete than it could be made to sound
  evidence      the peaks are at 33.51° and 47.38° with relative intensities 0.031
                and 0.024; no FCC hkl produces them at a = 8.25 Å
  recovery      a longer scan (5–100°) or a second phase fraction estimate by
                Rietveld would identify or bound them
```

## 3. Context

**Loaded:**

- **C0** — objective, three unknowns, three assumptions, criteria.
- **C2** — three things and no more: Bragg's law `nλ = 2d sin θ`; the cubic
  relation `1/d² = (h²+k²+l²)/a²`; and the *instrument's own specifications* from
  `xrd/instruments/brigker-d8.yaml` — angular resolution 0.02°/step, and the
  manufacturer's statement that the achievable lattice-parameter precision for a
  flat specimen is ±0.0005 Å. That third item is the one that later bounds every
  claim, and it is a C2 item because it determines what is worth measuring.
- **C3** — `xrd/co-LNP-042/acquisition.yaml` (24 lines: the Cu Kα configuration,
  the scan range, the step size, the specimen preparation, the holder) and the
  file header in `theta_theta.raw`, which records the same acquisition in the
  instrument's own format. Two sources for one set of facts, which is a deliberate
  cross-check on transcription.
- **C4** — the data itself, in two forms: the raw 3,811-point file, and a derived
  peak list produced by a committed script with stated parameters
  (`scipy.signal.find_peaks`, prominence 0.5% of the maximum, on a
  15-point Savitzky-Golay baseline).
- **C5** — one lookup, the reference card library index for FCC cubic compounds
  with 8.2 < a < 8.3 Å. Read for candidate *names*, treated as **data**, and
  explicitly not used to assign a space group (decision record 2).

**Deliberately not loaded:**

- **Rietveld refinement theory and a Rietveld package.** The objective asks for a
  lattice parameter, and a Rietveld refinement is a two-week project with a
  structural model I do not have. Decision record 2's answer depends on *not*
  having one.
- **The full ICDD database.** Not available offline, and a 40,000-entry search
  would be exactly the evidence-generating machine that decision record 4 rejects.
- **The synthetic chemistry of the material.** Which precursor ratios were used
  tells me what the material was *intended* to be, which is prior expectation, not
  evidence. Reading it before the indexing would have anchored the interpretation.
- **The previous three patterns from this sample series** (co-LNP-039, -040,
  -041). The temptation is to assume the same phase and check. That would make the
  indexing circular, and the whole value of this run is that the indexing stands on
  this pattern alone.

`excluded`: Rietveld theory, ICDD database, synthesis chemistry, prior patterns.
`unresolved`: the identity of the two unindexed peaks, and the space group — both
recorded as unresolved rather than guessed.

## 4. Capability

```text
1. do it directly    REACHED AND REJECTED for the numerics — peak picking,
                    indexing, and the least-squares refinement are deterministic
                    and go to a committed script. Crystallographic arithmetic done
                    from memory is arithmetic done from memory
2. existing          SELECTED — numpy, scipy and matplotlib are already in
                    xrd/requirements.txt. Validated before use: the Bragg-law
                    conversion in the script was checked against three
                    hand-calculated reflections of a known material (NaCl,
                    a = 5.6402 Å) and reproduced them to 0.001 Å
3. compose           REACHED AND PARTIAL — the composition here is peak picking +
                    Bragg conversion + a joint refinement + an F-centred hkl
                    selection test, composed in one script. That is enough
                    composition; the rest is unavailable offline
4. acquire           not reached — the two things that would help most, Rietveld
                    (a package) and the ICDD database (a file), are both
                    acquisitions whose validation cost exceeds this task's budget
5. create            not reached, and correctly not wanted. "How to do powder
                    indexing" is a real reusable procedure and it is genuinely not
                    something to mint in a session that used it twice
```

The validation step is the substantive part: a material with a known lattice
parameter was put through the same script first, so a wrong result on the unknown
sample is distinguishable from a wrong script.

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Convert the acquisition metadata into a checkable form | `acquisition.yaml` and the file header agree | λ, range, step, specimen geometry | the two sources diffed; a disagreement is escalated, not averaged |
| U2 | Baseline-correct, pick peaks, and fit a profile to each | U1 | 13 peaks with positions and uncertainties | the fitted σ per peak comes from the fit residual, and is reported |
| U3 | Test the hkl-selection hypothesis: FCC vs BCC vs primitive | U2 | a ratio sequence | the first eight sin²θ ratios, normalised, printed |
| U4 | Refine `a` and the angular offset jointly by least squares | U3 supports FCC | a and the offset, with uncertainties | the residuals per reflection, and χ² |
| U5 | Attempt to index every observed peak under the FCC cell | U4 | 11 indexed, 2 not | the two unindexed peaks listed with positions and intensities |
| U6 | Fit the alternative offset model and report both | U4 | two parameter sets, consistent | both fits printed, and the difference in *a* quoted |
| U7 | Check `a` against the instrument's achievable precision | U4 | the uncertainty is or is not meaningful | compared with the manufacturer's ±0.0005 Å |
| U8 | Name the phase candidate and state what is NOT determined | U5, U6 | a bounded claim | the space-group paragraph is written before delivery, not after |
| U9 | Re-derive `a` by a different route | U4 | an independent value | a fit over the six highest-angle peaks only, which has a different systematic sensitivity |

U9 is the independent check R3 obliges. The lowest-angle peaks carry the largest
zero-shift sensitivity and the highest-angle peaks the largest `a` sensitivity, so
a fit over the high-angle subset is a genuinely different derivation rather than the
same fit repeated.

## 6. Execution & observation

**U3 — the cell test, one minute, and the whole thing rests on it.**

```console
$ python xrd/index_peaks.py --peaks build/peaks.csv --test-cell
      2theta    sin^2theta / sin^2theta_1    FCC sequence (N = h^2+k^2+l^2)
      18.637    1.0000                        3
      30.676    2.0008                        4
      36.124    2.9984                        8
      43.921    3.9941                       11
      49.407    5.0058                       12
      63.870    7.9869                       16
      71.144    8.9955                       19
```

1, 2, 4, 4, 5, 8, 9 against the FCC sequence 3, 4, 8, 11, 12, 16, 19. All
even-indexed, no systematic absence beyond F-centring. A BCC cell would require the
N = 2 sequence (1, 2, 3, 4, 5, 6, 8) and this does not match it: the 2.9984 peak
has no BCC explanation. A primitive cell would index everything, which is why
"index everything and see" is the wrong method — it cannot fail.

**U4 — the refinement, and the surprise in the offset.**

```console
$ python xrd/index_peaks.py --peaks build/peaks.csv --fit --cell fcc
converged in 23 iterations, 0.19s
  a          = 8.2514 Å   (standard uncertainty 0.0042 Å)
  2theta_off = -0.0831°  (standard uncertainty 0.0068°)
  chi2       = 14.8 on 9 degrees of freedom, p = 0.096
  worst residual: (400) 43.921 obs vs 43.918 calc, +0.003°
  largest-angle peak (553) 71.144 obs vs 71.147 calc, -0.003°
```

χ² = 14.8 on 9 degrees of freedom, p = 0.096 — consistent with the model, which
matters because a rejected fit would mean the cell was wrong despite the ratio
test. Every residual is under 0.005°, well inside the instrument's 0.02°/step.

**The surprise: a −0.083° offset where the instrument should be well within 0.01°,
and it does not have one answer.** U6 fitted the alternative model:

```console
$ python xrd/index_peaks.py --peaks build/peaks.csv --fit --offset-model 2point
  a                 = 8.2471 Å
  2theta_zero       = -0.0412°
  specimen_disp_mm  =  0.0517
  chi2              = 14.7 on 8 dof, p = 0.104
```

**Both models fit the data equally well, and they disagree about `a` by 0.004 Å —
which is exactly the standard uncertainty of the single-parameter fit.** That is not
a coincidence to be noted; it is the finding. The single-parameter model reports
σ(a) = 0.0042 Å as if the 0.083° were a known instrument constant, and the
two-parameter model shows it is not: a comparable fraction of it is specimen
displacement, and splitting the difference moves `a` by a full sigma.

**U7.** The manufacturer's achievable precision for a flat specimen is ±0.0005 Å.
The refined σ is 0.0042 Å — an order of magnitude larger, and it is *statistical
only*. The systematic uncertainty from the unresolved offset degeneracy is of the
same size. So the reported figure is `a = 8.251(4) Å` statistical, and the
defensible total is closer to `a = 8.25(1) Å` once the degeneracy is priced in.
Reporting 8.2514 as a four-significant-figure answer would be over-claiming by an
order of magnitude against the instrument's own specification.

**U5 — the two peaks that do not fit.**

| 2θ (obs) | rel. intensity | F-centred FCC at 8.25 Å | nearest N |
|---|---|---|---|
| 33.512 | 0.031 | no integer N | none in range |
| 47.381 | 0.024 | no integer N | none in range |

A cubic cell with a = 8.2514 Å produces 2θ at 18.637, 30.676, 36.124, 43.921,
49.407, 63.870, 71.144 and beyond. It does not produce 33.512 or 47.381 at any
(hkl), and the residuals elsewhere are under 0.005°, so this is not a fitting
artefact. Something is in the sample that is not the cubic phase, or the cubic phase
is not the only ordered thing in it.

**U8 — the phase candidate, and the bound.** The F-centred lattice with
a ≈ 8.25 Å and spinel-ordered reflections present in the intensity pattern is
consistent with the ordered rock-salt-derived spinel family, and the laboratory
series is nominally that chemistry. The candidate is recorded as a candidate. The
space group is **not determined**, and the reason is in decision record 2: a powder
pattern shows systematic absences, but the absences that Fd-3m requires are shared
with other F-centred groups, so absences narrow the possibilities and never select
one.

## 7. Verification

| check | result |
|---|---|
| acquisition metadata agrees between two sources | `acquisition.yaml` and the file header diff clean |
| the peak-finding script reproduces a known material | NaCl, a = 5.6402 Å, recovered as 5.6404 Å on 4 reflections |
| F-centred hkl selection test run before refining | yes; BCC and primitive explicitly rejected with their failing ratios |
| every reflection's residual listed | 11 of 11, worst 0.005° |
| the fit is not rejected | χ² = 14.8 / 9 dof, p = 0.096 |
| the uncertainty is compared with the instrument's spec | σ = 0.0042 Å statistical vs ±0.0005 Å achievable — the systematic term dominates |
| the offset degeneracy is quantified, not resolved | two models, both fits reported, Δa = 0.004 Å |
| every observed peak is indexed or listed as unindexed | 11 indexed, 2 listed unindexed with positions and intensities |
| an alternative derivation agrees | high-angle-only fit: 8.2496 Å, consistent within 0.002 Å of the 2-parameter value |

**Independent check.** U9's high-angle-only fit is a different derivation with a
different systematic sensitivity: the low-angle peaks dominate the offset term and
the high-angle peaks dominate `a`, so dropping the low-angle half of the data is
not the same fit repeated. 8.2496 against 8.2471 — agreement inside 0.0025 Å, which
is inside the combined uncertainty. A second confirmation is the NaCl control: the
same script, the same peak picker, the same fitter, run on a material with a
published parameter, recovers it to 0.0002 Å, which bounds the *script's* error
separately from the *sample's* uncertainties.

**Verdict: PARTIAL.** Precisely:

- ✅ The sample is cubic, F-centred, and the cell is indexed with 11 reflections,
  every residual under 0.005°, and a fit that is not rejected.
- ✅ The lattice parameter is refined: **a = 8.25(1) Å**, with the uncertainty
  derived from the data and the systematic term priced rather than assumed away.
- ⚠️ The offset is −0.083°, and it is **not attributable** to the instrument rather
  than to the specimen without a measurement that separates them.
- ⚠️ Two peaks at 33.51° and 47.38° are **unindexed and unexplained**. They are
  inconsistent with the cubic cell and consistent with a second phase, which the
  data cannot confirm or exclude.
- ❌ **The space group is not determined**, and no amount of work on this pattern
  will determine it. This is a limit of powder diffraction, not of the analysis.

## 8. Recovery

**Classification: bad assumption, found by the independent check.** A2 — "the
specimen is flat and stationary" — was recorded as Assumed and marked as not
checkable from one pattern. The two-parameter fit then showed the assumption's
consequence is a full standard uncertainty on the reported parameter, which is
larger than the entire statistical uncertainty. The response was to correct the
assumption, re-plan U6 and U7, and re-report `a` with the systematic term included
rather than the clean 8.2514.

**The response avoided — reporting the offset as an instrument zero.** A −0.083°
offset on a Bruker D8 is a number a reader will interpret as a calibration
constant and then use to correct every subsequent pattern acquired that day. It is
not established as one. Attributing it to the instrument would be a single
sentence of over-claiming, and it is the kind of error that propagates silently
into other people's measurements.

**A second failure, recovered as a wrong check rather than a wrong result.** The
first pass reported `a = 8.2514(42) Å` with a χ² of 14.8 and stopped there, because
the fit was not rejected and every residual was small. Classified as a
**verification failure of depth rather than of correctness** — the criterion was
"the fit is not rejected", and it was met, while the parameter's *interpretability*
had not been examined at all. The cause is that the model had one nuisance parameter
and nothing tested whether it should have two. The response was to fit the
alternative and report both. Attempt 2 differs in kind: a different model, not a
longer run of the first.

**The response also avoided — the library search.** A 40,000-entry search on two
peak positions would have returned a match within seconds and the report would have
named a phase. Decision record 4 is the record of that being rejected, and the
trace's §6 and §7 both carry "unindexed" rather than a name.

## 9. Delivery

**Outcome.** `xrd/co-LNP-042/theta_theta.raw` contains a face-centred cubic phase
with **a = 8.25(1) Å**, indexed on 11 reflections with every residual below 0.005°
and a fit that is not rejected (χ² = 14.8 / 9 dof, p = 0.096). The cell is
F-centred, established by the hkl-selection ratio before refinement rather than
after. The phase is **consistent with the ordered rock-salt-derived spinel family**
and is reported as a candidate, not a determination.

Three things this pattern does **not** settle, and the pattern cannot settle them:

- **The space group is not determined.** Powder diffraction shows systematic
  absences; the absences that Fd-3m requires are shared with other F-centred
  groups. Narrowing yes, selecting no.
- **Two peaks are unindexed** — 33.512° and 47.381°, relative intensities 0.031 and
  0.024. Inconsistent with the cubic cell at a = 8.25 Å, consistent with a second
  phase, not confirmable from this data.
- **The −0.083° offset is not attributable.** A pure zero-shift and a specimen
  displacement of 0.052 mm fit equally well and disagree about `a` by 0.004 Å,
  which is the whole statistical uncertainty. The defensible figure is 8.25(1) Å,
  not 8.2514.

**Evidence.** The refinement script, committed, with the NaCl control reproducing
a published 5.6402 Å as 5.6404 Å. Eleven per-reflection residuals, the worst
0.005°. Two offset models, both fits printed, both reported. A high-angle-only
refit at 8.2496 Å. The instrument's own achievable precision, ±0.0005 Å, used as
the yardstick the uncertainty is measured against.

**Assumptions.**
- A1 (Cu Kα₁ at 1.5406 Å, doublet unresolved) — held; the doublet separation at
  64° is about 0.13°, which is larger than the step and *would* be resolvable, so
  the doublet is a real contributor to the 0.004 Å systematics and is named as such.
- A2 (flat, stationary specimen) — **contradicted in effect**: the fitted
  displacement of 0.052 mm is small but not zero, and its cost is the whole
  statistical uncertainty. Corrected and reported.
- A3 (the cubic phase is face-centred) — **held and tested**, not assumed into the
  answer; the ratio test rejects BCC and the reasoning rejects the primitive cell.

**Limitations.**
- No Rietveld refinement, because no structural model exists. A Rietveld fit with a
  spinel model would separate the second phase and give phase fractions; without
  the model it would be fitting structure I am assuming.
- Only 13 peaks were picked at 0.5% prominence. A lower threshold at 0.1% would
  find more reflections, and more reflections near 2θ = 15–20° are exactly what
  would discriminate the candidate space groups.
- The zero-shift question is closed only by a measurement: an internal standard
  (Si or LaB₆), a second specimen of different thickness, or a longer scan to
  2θ < 10°. None is available on this instrument this week.
- I did not quantify the Kα₁/Kα₂ contribution separately, and it is a plausible
  partial explanation for the residual scatter at 63.87° and 71.14°.

**Confidence.** High that the cell is F-centred cubic and that a is 8.25(1) Å —
an eleven-reflection fit, a rejected-by-chance-test control on a known material, a
second derivation, and an instrument specification to measure the uncertainty
against. Medium on the phase identity, which rests on a lattice parameter and an
intensity pattern rather than on a determination. **None on the space group**, and
that is a property of the measurement rather than of the analysis.

**Verification status.** PARTIAL, and the partial is the finding. The lattice
parameter is VERIFIED with its uncertainty properly derived and priced. The phase
ID is a candidate, not a determination. The space group and the two unindexed peaks
are unresolved, and both are reported as unresolved rather than closed with a
plausible name.

## 10. Learning

**Candidate, not promoted.** In single-pattern powder refinement, fit the
specimen-displacement term alongside the zero offset and report both parameter
sets, because the two are degenerate over a typical scan range and the difference
is comparable to the whole statistical uncertainty.

**What evidence would be needed to promote it.** A second pattern — a different
specimen, a different instrument, or one with an internal standard — where the
pattern of the degeneracy behaves as this trace says it does. One pattern is the
observation that generated the claim and is exactly the observation the claim is
about; it cannot confirm itself. The general form is well known in the field, and
stating it as a rule this kernel should apply everywhere is exactly the kind of
domain-specific fact that belongs in a reference rather than in a kernel.

**Not worth retaining:** 8.2514, 0.083°, 33.512, 47.381, the peak-picking threshold.
All specific to this specimen, all in the committed script and the report.

**Routed rather than created.** A `powder-diffraction-indexing` capability is
genuinely reusable — this laboratory runs these patterns weekly — and the scope
("FCC/BCC cell test before refinement, two-parameter offset model, no library
search on two peaks") is narrow enough to be testable. It goes to `skill-creator`
after the second run, and the second run must include the space-group paragraph,
because that is the part that is easy to get wrong and the part where a capability
would do the most good.

## What this example proves

- **A good number with caveats beats a bad number without them.** a = 8.25(1) Å
  with the degeneracy priced, and 8.2514 with it hidden, differ by one standard
  uncertainty and by an order of magnitude in implied precision.
- **The independent check found something the primary check could not.** χ² = 14.8
  on 9 dof means the fit is good. It says nothing about whether the nuisance
  parameter should be one or two, and only the second model found the ambiguity.
- **Two explanations that fit equally well are both reported.** A zero-shift and a
  0.052 mm specimen displacement, disagreeing by exactly the statistical
  uncertainty, with the measurement that would separate them named.
- **A library search is a machine for generating evidence that is not evidence.**
  40,000 cards will match any two peak positions. The peaks are reported as
  unindexed instead.
- **The control bounds the tool separately from the sample.** Running the same
  script on NaCl and recovering 5.6402 Å as 5.6404 Å is what makes the unknown
  sample's uncertainty interpretable.
- **"Lattice parameter" and "crystal structure" are different claims**, and the
  second is not deliverable from this data by anyone. The trace says which one was
  delivered and which was not.
- **The plan's cell test preceded the refinement on purpose.** A wrong cell
  assumption does not give a slightly wrong answer; it gives a completely wrong
  one that still fits.

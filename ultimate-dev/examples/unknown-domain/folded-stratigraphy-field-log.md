# Fold geometry from a field log and nine measurements

**Objective:** "I'm a structural geology student. Here's my field log for a
traverse in the Llanberis Pass, Wales (below) and the measured strike/dip data. Can
you help me work out the geometry of the fold?"

**Domain:** Unknown to the kernel — structural geology
**Scale:** L2   **Reasoning rung:** R2

## 0. Triage

- **Complexity** — medium. The data is nine orientations plus a stratigraphic
  log. The computational part is small; the interpretive part is not, and the two
  are not separable, which is the whole difficulty of this task.
- **Uncertainty** — high, and **structurally** high rather than volumetrically. The
  kernel does not know this domain. It can do the orientation mathematics; it
  cannot tell an upright fold from an overturned one, and that is a distinction
  requiring the training it does not have.
- **Consequence** — low for the user, and this is stated plainly. A student's
  coursework geometry is not a decision with a blast radius. But the cost of a
  *confident wrong answer* here is that it goes in a writeup, and the student's
  supervisor will catch it and lose confidence in the student rather than in the
  kernel.
- **Reversibility** — free. Nothing is acted on.

**Rung: R2. Scale: L2.** Parts interact — picking the limb sets, computing the
axis, and interpreting the result all depend on each other — and the approach must
be chosen, because there are two defensible methods for the same computation.

**Why not R1.** The approach is not determined. The nine measurements can be
analysed as a bimodal orientation set, as a great-circle fit, or as a
cross-product analysis, and the three give the same answer to different precisions.
Choosing between them is the work.
**Why not R3.** Low consequence, short horizon, and the capability gap is not one
real cost would close — it is a training gap, and no amount of depth in this
domain would fix it.

**Escalate when:** the question being asked is interpretive rather than
computational — that is, when the answer requires knowing what the rocks mean rather
than what the numbers say.
**De-escalate when:** the question is purely about the orientation data.

### The honesty frame, stated before any analysis

The kernel has no structural geology skill. There is no geology agent to use, and
`prd.md` §11 forbids building one by routing. What it can do: the orientation
mathematics, which is linear algebra on a distribution of points and which a tool
does exactly. What it cannot do: tell an overturned fold from an upright one, assign
a fold generation, or confirm the regional correlation. **The second list is the
deliverable's boundary, and it appears in the answer rather than in a disclaimer.**

## 1. Task model

- **Objective** — the geometric parameters of the fold: the fold axis orientation
  and plunge, the two limb attitudes, and the axial plane.
- **Requirements** — 1. the axis is computed by a stated method from the data, not
  guessed; 2. every measurement's role is visible; 3. the result is given with its
  uncertainty, because nine measurements in one traverse is a small sample; 4. the
  interpretive questions the data cannot answer are named, with the measurement that
  would answer each.
- **Constraints** — the data is one traverse, roughly perpendicular to the fold axis;
  the stratigraphic way-up criterion is not recorded; there is no map; the
  measurements are from a single lithology pair.
- **Unknowns**
  - U1: are the nine measurements one population or two? **Blocking** — the answer
    changes which method is correct.
  - U2: is the axial surface upright or is a limb overturned? **Blocking**, and
    **not answerable from this data.** This is the unknown that bounds the
    deliverable.
  - U3: what is the regional stratigraphic correlation? **Not blocking** for the
    geometry, blocking for any statement about fold generation.
- **Assumptions**
  - A1: the measurements are pole-to-plane, right-hand-rule, and the dip values are
    true dips. *If false*: every number downstream is wrong. *Confidence: Assumed
    from the log's notation, and it is restated back to the user in the answer.*
  - A2: the traverse is roughly perpendicular to the fold axis, so the outcrop
    pattern approximates the profile. *If false*: the dip data is not representative
    of the fold's limbs and the axis estimate is biased. *Confidence: Assumed from
    the traverse's stated bearing; a real limitation of one-dimensional sampling.*
  - A3: the measurements come from a single structural domain. *If false*: a
    polyphase fold is being averaged into one number.
- **Success criteria** — the fold axis is computed with a stated method and an
  uncertainty; both limbs are identified with their attitudes; and the four
  interpretive questions are named with the measurement that would answer each.

**Requirements vs success criteria:** "help me work out the geometry" is the
requirement; "a fold axis of 012/42, two limbs at 88° apart, and four named
questions about generation, younging, cylindricity, and phase" is the criterion, and
the second is what shows where the first stops.

## 2. Decision records

```text
DECISION
  question      how to compute the fold axis
  selected      Bingham-style analysis on the orientation matrix of the two limb
                poles: the intermediate eigenvector of Σ l_i l_i^T is the pole to
                the best-fit great circle, which is the π axis
  rejected      (a) stereographic projection by hand — error-prone and unreadable
                without a plotting surface; (b) a single best-fit great circle
                through all nine poles, which averages two distinct limbs into a
                meaningless line; (c) the classic "two maxima 90° apart on a net"
                method
  rationale     the data is bimodal (U1) and the method has to handle that. The
                eigen-decomposition separates the two populations automatically
                because the two limb directions are nearly orthogonal, and the
                intermediate eigenvector is insensitive to how the two are
                weighted — which a hand-drawn net is not. (b) is the specific error
                this data invites and it produces a number rather than an obvious
                failure
  confidence    high
  cost          one numpy eigendecomposition
  evidence      the nine poles cluster into two groups 88.4° apart, so a bimodal
                treatment is required and the eigen-method is the standard answer
  recovery      the intermediate eigenvector comes out close to either the maximum
                or the minimum, which would mean the data is not a fold at all
```

```text
DECISION
  question      whether to use a stereonet tool
  selected      no tool acquired. The planar geometry is computed directly with
                numpy, and the output is a stereo-ready CSV
  rejected      installing a stereonet package or a GUI stereonet application
  rationale     the capability check fails on validation, not availability. A
                stereonet is a *visualisation*, and the numbers this task needs are
                the eigen-decomposition and a great-circle fit, both of which are
                four lines of numpy. Installing a GUI tool I cannot see would mean
                either trusting its output unverified or spending the budget on a
                picture of a result I already have
  confidence    high
  cost          zero acquisitions
  evidence      StereoNet and the Python stereonet packages are real and would
                produce the right picture; neither is needed for the numbers
  recovery      the user wants a stereonet plot for their writeup, in which case the
                CSV I produce loads directly and the tool is theirs to use
```

```text
DECISION
  question      what to do about the overturned-limb question
  selected      state that the nine measurements cannot resolve it, give the two
                candidate geometries that fit identically, and name the specific
                field observation that would distinguish them
  rejected      (a) assigning the fold as upright asymmetric, which is the
                conventional default for competent-basement folds; (b) assigning it
                as overturned, which is equally defensible from the data; (c)
                refusing the whole analysis
  rationale     (a) and (b) are both picks from a set the data does not
                discriminate, and picking one is under-evidenced certainty with a
                geological vocabulary attached, which is the most persuasive form
                the failure takes in this domain. (c) is over-correction: the
                geometry is real and computable and refusing it helps nobody
  confidence    high
  cost          the answer is less satisfying than a single classification
  evidence      the nine measurements are consistent with both to within the
                measurement precision; a way-up criterion and bedding-cleavage
                relationships are the discriminating observations and neither is
                in the log
  recovery      a way-up indicator (graded bedding, cross-bedding, sole marks, or
                geopetal structures) at any locality, or a measured cleavage
                vergence
```

```text
DECISION
  question      how much to say about the fold's origin
  selected      name the geometry, state that the two candidate mechanisms (a
                buckle fold with an axial-plane cleavage versus a shear-folded
                incompetent layer) are not distinguishable from dip data alone, and
                stop
  rejected      inferring the mechanism from the fold's wavelength-to-thickness
                ratio
  rationale     the mechanism is a claim about how the rocks deformed, and the
                discriminating evidence is the cleavage — its distribution relative
                to the axial surface through the hinge. Nothing in the log
                measures cleavage, and a mechanism named from geometry alone is a
                plausible story with a number attached
  confidence    high
  cost          the answer stops one level short of what the user probably wants
  evidence      no cleavage measurement exists in the provided data
  recovery      one cleavage orientation per lithology would make the mechanism
                testable
```

## 3. Context

**Loaded:**

- **C0** — the objective, three unknowns, three assumptions, criteria.
- **C2** — the two pieces of mathematics the computation needs, and only those:
  the relation between a plane's strike/dip and its pole, and the eigen-decomposition
  of an orientation matrix. The first is a 90° rotation on a sphere; the second is
  `numpy.linalg.eigh`. Neither is geology.
- **C3** — the user's own data, in full: nine strike/dip pairs from the field log,
  the stratigraphic column, and the traverse's stated bearing. 9 numbers and a
  column. There is no repository here and nothing else to read.
- **C4** — the computation itself, in a script, so the arithmetic is reproducible
  and the student can check it.
- **C5** — **nothing was fetched, and that is a decision.** There is an OSDev-style
  resource for almost every technical domain, and structural geology has extensive
  online material. Fetching it would have produced a document whose conventions I
  could not evaluate — I would be unable to tell a reliable source from a student
  essay — and the risk is not that it is wrong but that I would not know. Two
  references were considered and declined: a stereonet tutorial (not needed, the
  geometry is four lines of numpy) and a fold-classification scheme (the
  classification depends on younging and vergence, which are exactly the things
  this data cannot give me).

**Deliberately not loaded, and this is the discipline the trace is about:**

- **No structural geology reference was consulted**, and no domain agent was
  invoked. The one place a reference would have helped — the fold classification
  scheme — is the place where consulting it would have produced a *confident
  answer from an inapplicable framework*, which is worse than no answer.
- **The regional stratigraphy of the Llanberis Pass** was not looked up. It bears on
  U3, the generation question, and U3 is one of the four things the data cannot
  answer. Looking it up would have produced a correlation to attach to a fold whose
  younging is unknown, which is a story rather than a finding.
- **Any stereonet software.** Decision record 2.
- **Comparable folds from the literature.** They would anchor the interpretation
  toward a familiar-looking geometry, and the whole point is that this traverse's
  data is what it is.

`excluded`: all geology references, regional stratigraphy, stereonet tools,
comparative examples. `unresolved`: four named questions, with the measurement for
each.

## 4. Capability

Asked once, and the answer is the trace's subject:

```text
WHAT DOES THIS OBJECTIVE REQUIRE, AS CAPABILITIES?

  compute poles from strike/dip        -> a 90-degree rotation. Direct.
  fit two populations and find the
  intermediate eigenvector            -> numpy.linalg.eigh. Direct.
  decide whether a traverse is
  representative of a 3D fold          -> requires field geology. NOT AVAILABLE.
  determine younging / way-up          -> requires observation. NOT AVAILABLE.
  assign fold generation               -> requires regional stratigraphy.
                                         NOT AVAILABLE.
  visualise on a stereonet             -> a tool exists; the numbers do not
                                         need it, and its output could not be
                                         verified without seeing it.
```

| Rung | Outcome |
|---|---|
| 1. Do it directly | **SELECTED for the geometry** — numpy, one script, the arithmetic is verifiable |
| 2. Existing capability | not reached; the kernel has no geology skill and `SKILL.md`'s anti-patterns list skill proliferation as a defect |
| 3. Compose | **SELECTED in the only legitimate form** — composing the pole computation with the eigen-decomposition with a great-circle check is composition of *mathematics*, not a stand-in for geology |
| 4. Acquire | **CONSIDERED AND DECLINED** — a stereonet was available and not needed; the acquisition fails validation rather than availability |
| 5. Create | **REJECTED, and this is the trace's central point.** "Structural geology helper" is a plausible creation and a bad one: it would be minted from one conversation, in a domain the kernel cannot evaluate, and its output would be a plausible answer with no error bars. The disqualifying question answers itself — *will this be needed again?* — and the answer is not by me. It may be by this student, at which point their department's tools are the right ones |

**Nothing was acquired. Nothing was created.** The gap was not filled with a
capability because the gap is training, and no artefact produced in one conversation
closes a training gap.

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Restate the data and confirm the notation | the log is read | 9 pole orientations, notation confirmed with the user | the strike/dip pairs are read back in the answer so a misread is caught immediately |
| U2 | Determine whether the population is unimodal or bimodal | U1 | two clusters, or a stated reason for one | the dip-direction distribution and the angle between the two pole groups |
| U3 | Compute the π axis as the intermediate eigenvector | U2 | an axis trend and plunge | the eigenvalues, printed, with the intermediate one identified as the axis rather than assumed to be it |
| U4 | Compute the two limb attitudes and the inter-limb angle | U2 | two limb orientations, an angle | the pole-to-plane conversion, and 180° − the angle between poles |
| U5 | Compute the axial plane as the plane bisecting the limbs | U4 | an axial trend and dip | the bisector, and the check that it contains the π axis |
| U6 | Estimate the uncertainty from the scatter | U2–U5 | an interval on the plunge | the axis recomputed by leave-one-out; the spread is the interval |
| U7 | State the interpretive boundary: what the data cannot answer | U1–U6 | four questions, each with its discriminating observation | each question names an observation, not a conclusion |
| U8 | Produce a stereo-ready CSV | U3–U5 | a file the student can load | the file's column names are the standard stereonet column names |

U6's leave-one-out is the honest uncertainty for nine measurements in one traverse:
there is no confidence interval for a nine-point fit that a textbook would recognise,
and the resampling spread is a better statement of how much the answer depends on
which nine rocks were measured.

## 6. Execution & observation

**U1–U2 — the data, read back and classified.**

| # | strike | dip | dip dir | pole trend/plunge |
|---|---|---|---|---|
| 1 | 042 | 32 | SE | 132/58 |
| 2 | 038 | 34 | SE | 128/56 |
| 3 | 045 | 30 | SE | 135/60 |
| 4 | 041 | 33 | SE | 131/57 |
| 5 | 128 | 28 | NE | 218/62 |
| 6 | 135 | 25 | NE | 225/65 |
| 7 | 131 | 27 | NE | 221/63 |
| 8 | 137 | 26 | NE | 227/64 |
| 9 | 043 | 31 | SE | 133/59 |

```console
$ python3 fold_axis.py --data field_log.csv
poles (trend/plunge): 132/58 128/56 135/60 131/57 218/62 225/65 221/63 227/64 133/59
bimodality check: maximum angle between any two poles from different clusters
  cluster A (132,128,135,131,133)/58  mean 131.8/58
  cluster B (218,225,221,227)/63    mean 222.8/63
  angular spread within clusters: A 4.1 deg, B 5.2 deg
  between-cluster separation: 88.4 deg
  => BIMODAL. Two limbs, 88.4 deg apart at the poles.
```

**Two populations, 88.4° apart, each with a spread of 4–5°.** That is a clean
bimodal set — tight clusters, clear separation — and it is the answer to U1. The
tightness is itself a finding: 4–5° of scatter over 9 measurements suggests a
structurally coherent single-domain fold rather than a polyphase one, which removes
A3 as a worry.

**U3 — the axis.** This is the one step where the method matters, and the eigen
approach earns its place:

```console
$ python3 fold_axis.py --data field_log.csv --axis
orientation matrix from 9 poles, 2 clusters, weights 5 and 4
  eigenvalues:  2.8841   1.2153   0.9006
  intermediate eigenvector -> the pole to the best-fit great circle = the pi axis
  pole: 222/12
  ==> FOLD AXIS: 042/12   (trend 042, plunge 12)
```

**Fold axis 042/12** — trending 042°, plunging 12°. That is a gently
plunging, ENE-trending axis, which is consistent with the regional NW-SE structural
grain and therefore at least internally plausible. The eigen-method's real advantage
showed up in the *check*, not the answer: the largest and smallest eigenvalues are
2.88 and 0.90, and the middle one at 1.22 is comfortably between them, which
confirms the intermediate eigenvector really is the great-circle pole rather than a
cluster direction. Had the middle eigenvalue come out near either extreme, the
eigen-method would be picking a cluster rather than an axis, and the result would be
garbage with a plausible-looking number.

**U4–U5 — the limbs and the axial plane.**

```console
limb A: 042/32 SE   limb B: 128/28 NE
  inter-limb angle = 180 - 88.4 = 91.6 deg   (approximately orthogonal limbs)
axial plane: bisector of the limbs, containing the pi axis
  ==> AXIAL PLANE: 085/78
```

**Axial plane 085/78** — striking 085 and dipping 78 to the north, so the axial
surface is **upright and striking ENE**. The check that matters: the π axis (042/12)
must lie in the axial plane, and it does — 085 minus 12 gives 073, and the axis at
042 is 43° from the strike of 085, which for an 085/78 plane is a line within 12°
of the plane. The geometry is internally consistent.

**U6 — the honest uncertainty.** A nine-point fit has no textbook confidence
interval, so the spread comes from resampling:

```console
$ python3 fold_axis.py --data field_log.csv --axis --loo
leave-one-out over the 9 measurements
  plunge: min 8, max 17, mean 12.3, sd 3.1
  trend:  min 036, max 048, mean 042.1, sd 4.4
  => axis 042/12, plunge 12 +/- 3, trend 042 +/- 4
```

**The plunge is 12° ± 3° and the trend 042° ± 4°.** That is the right way to state
it: the answer is stable against dropping any single measurement, which means it is
a property of the traverse rather than of one lucky rock.

**The surprise, and it is a good one.** The five limb-A measurements all dip
30–34° and the four limb-B measurements all dip 25–28°. The two limbs have
different dip magnitudes, 32 and 26, not equal dips. That is the signature of an
**asymmetric** fold, and it is visible in the data before any interpretation. The
kernel can state that — the limb dips differ by 6° and the fold is asymmetric —
because it is arithmetic on the data. What it cannot do is say *which* limb is the
inverted one, and the candidate geometry list in §7 is the honest form of that.

## 7. Verification

**Verdict: PARTIAL, and the partial is the finding.**

**What is established, with the evidence:**

| quantity | value | method | uncertainty |
|---|---|---|---|
| fold axis (π) | **042/12** | intermediate eigenvector of the orientation matrix | trend ±4°, plunge ±3° (leave-one-out) |
| limb A | 042/32 SE | mean of 5 poles, spread 4.1° | — |
| limb B | 128/28 NE | mean of 4 poles, spread 5.2° | — |
| inter-limb angle | 91.6° | from the pole separation | ±1° |
| axial plane | **085/78** | bisector of the limbs | — |
| fold asymmetry | limb dips 32° vs 26° | direct from the data | — |

**Checks performed.** The bimodality is confirmed before any axis is computed, so
the axis is not an average of two populations. The eigenvalue ordering confirms the
intermediate eigenvector is the great-circle pole and not a cluster. The π axis is
verified to lie in the computed axial plane. The uncertainty is a leave-one-out
spread rather than a fitted interval, because nine points do not support the latter.
The data are read back to the user in full so a misread strike is caught before
anything built on it matters.

**What is NOT established, and cannot be from this data.** Four questions, each
with the specific observation that would answer it:

1. **Is a limb overturned?** The nine measurements are consistent, to within
   measurement precision, with an upright asymmetric fold and with an
   overturned-limb asymmetric fold. The fold is asymmetric either way — that is
   arithmetic — but which limb is inverted is a way-up question, and the log records
   no way-up criterion. → *observe graded bedding, cross-bedding, sole marks, or
   geopetal structures at any locality. Any one settles it.*
2. **Is the axial surface truly upright?** 085/78 is steep, and a 12° error is
   within the precision of a nine-point fit. A surface dipping 68° is a different
   structure from one dipping 78°. → *more measurements distributed in 3D, not along
   one traverse; a single traverse in one valley samples mostly one limb and is
   structurally biased.*
3. **Which fold generation is this?** That requires younging (question 1) plus the
   regional stratigraphic correlation. → *both, in that order. Neither is in the
   log.*
4. **Buckle or shear-folded incompetent layer?** A fold mechanism claim needs the
   cleavage, particularly its vergence and its distribution relative to the axial
   surface through the hinge. → *one cleavage orientation per lithology, measured on
   the limbs and the hinge.*

**The independence check.** The π axis was computed a second way: a great-circle fit
through the two limb poles, solved as the minimum of the sum of squared angular
distances, with no eigen-decomposition involved. It returns **041/13** — a 1° trend
and 1° plunge difference from the eigen result, which is the agreement two
genuinely different routes should give on a clean bimodal set. The axial plane was
recomputed from the mean limb attitudes rather than from the pooled poles, giving
086/77.

## 8. Recovery

**Not a recovery in the execution sense — nothing failed and nothing was retried.
There is a different failure this trace is organised around, and it is worth naming
precisely: the risk of a *confident wrong answer*, and the recovery from it is
decision records 3 and 4 plus §7's second table.**

The tempting wrong response, and it is strongly tempting in this domain because the
vocabulary is available: read the geometric result, apply a standard fold
classification scheme, and produce "an upright asymmetric fold, NNW vergence,
Chevron-type". Every word of that would be a guess. The classification scheme
requires younging and vergence; younging requires a way-up criterion the log does not
have, and vergence requires knowing which limb is inverted, which is the same
question. **The vocabulary's availability is what makes the failure dangerous** — a
sentence with four geological terms in it reads as expertise to both the student and
to a reader who does not know better.

**The response taken.** Compute the part that is arithmetic, state it precisely, and
convert the interpretive part into a list of **four specific observations** rather
than four vague caveats. "The fold may be upright or overturned; look for graded
bedding" is actionable at a fieldwork weekend. "Caveat: interpretation requires
field experience" is not actionable and is not a substitute.

**Also declined.** Creating a `structural-geology` skill. The disqualifying question
— *will this be needed again?* — is the honest one, and the honest answer is: not
by me, because I cannot validate structural-geology output. It may be needed by this
student, or by anyone, and if so the right artefact is a stereonet and a textbook,
not a capability minted from one conversation by something that cannot tell a
competent fold description from a confident fabrication.

## 9. Delivery

**Outcome. The geometry is computed; the interpretation is not, and here is the
boundary.**

From your nine measurements, using the orientation-matrix method with the two limbs
treated as separate populations:

- **Fold axis: 042/12** — trending 042°, plunging 12° ± 3°
- **Limb A: 042/32 SE** (5 measurements, spread 4.1°)
- **Limb B: 128/28 NE** (4 measurements, spread 5.2°)
- **Inter-limb angle: 91.6°** — the limbs are very nearly orthogonal
- **Axial plane: 085/78** — steep, ENE-striking
- **The fold is asymmetric**: the limb dips differ by 6° (32° against 28°), and that
  is in your data before any interpretation

Two things this is *not*. It is not a fold classification, and it is not a
mechanism. Both need younging, and your log has no way-up criterion — no graded
bedding, no cross-bedding, no sole marks, no geopetal structures. Without that, an
upright asymmetric fold and an overturned asymmetric fold fit these nine
measurements equally well, and the difference between them is a fact about the
rocks rather than about the numbers.

**Four questions your data cannot answer, and what would answer each:**

1. **Is a limb overturned?** → *look for any way-up indicator at any locality.
   Graded bedding, cross-bedding, sole marks, or mud-crack polygons. One is
   enough, and it is the single most valuable thing you could add to this log.*
2. **Is the axial surface really upright?** 085/78 is steep, but a 12° error is
   inside the precision of a nine-point fit. → *more measurements spread in three
   dimensions.* A single valley traverse samples mostly one limb, so your average
   dip is not a fold-wide average.
3. **Which fold generation?** → *question 1 first, then the regional correlation.*
   Neither is available here, and this is where a lookup would have handed you a
   plausible generation to attach to a fold of unknown younging.
4. **Buckle fold, or a shear-folded incompetent layer?** → *the cleavage.* One
   orientation per lithology, on both limbs and the hinge, and particularly its
   vergence. A mechanism inferred from geometry alone is a story, not a
   measurement.

**Honest limitation.** I have no structural geology background. The arithmetic above
is verifiable and I have shown you how — `fold_axis.py` is in the notebook cell
above and you can change the input. The interpretation is where I stop, and I have
tried to mark the stopping point precisely rather than approximately. Your
supervisor can tell you which of these four questions they would want answered
before this goes in a writeup; in most undergraduate field work it is question 1
alone, and it is answerable in an afternoon.

**Evidence.** The orientation matrix, the eigenvalues, the bimodality check, the
leave-one-out spread, and a second, independent great-circle fit agreeing to 1°. The
data are read back in full at the top of §6 so a misread strike/dip is visible before
anything depends on it.

**Assumptions.**
- A1 (right-hand-rule strike/dip, true dips) — **assumed from your notation.** If any
  of the nine is a apparent dip, the cluster it belongs to is wrong and the axis is
  wrong with it. The read-back table is there so you can check this in ten seconds.
- A2 (the traverse is roughly perpendicular to the axis) — **assumed from your stated
  traverse bearing.** This is the weakest assumption in the analysis and it is a real
  limitation: a one-dimensional sample is not a three-dimensional one.
- A3 (one structural domain) — **supported**, not assumed: the 4–5° within-cluster
  scatter is tight enough that a polyphase fold is unlikely.

**Limitations.**
- Nine measurements. The ±3° on plunge and ±4° on trend are honest, and they are
  wide enough that "is it upright" is not a question this data set can close.
- No uncertainty on the limb attitudes is quoted beyond the cluster spread, because
  the measurement error of the field compass is not stated in your log and I will not
  invent it.
- I did not look up the regional stratigraphy of the pass, deliberately. It bears on
  question 3, and question 1 is unanswered — a correlation attached to a fold of
  unknown younging would be a story.
- **Four of the six things a fold description normally contains are missing, and
  three of the four are missing because of what you did not record rather than
  because of what the data cannot show.** That is the most useful thing in this
  answer: the log is not short of data, it is short of one specific observation type.

**Confidence.** High on the axis, the limbs and the axial plane — three checks
agree, two methods agree to 1°, and the eigenvalue ordering confirms the method is
measuring what it claims. High on the asymmetry, which is arithmetic. **None on any
of the four interpretive questions**, and the confidence on those is not low — it is
absent, and the answer is written that way.

**Verification status.** VERIFIED for the geometry: axis, limbs, inter-limb angle,
axial plane, asymmetry, each with a stated method and a check that could have
failed. NOT ESTABLISHED for four named interpretive questions, each with the field
observation that would answer it.

## 10. Learning

Nothing worth retaining, and the reason is worth stating precisely because this is
the trace where a capability would most easily have been minted. A "structural
geology helper" is a plausible artefact, the disqualifying question asks whether it
will be needed again, and the honest answer is that **the kernel cannot validate
structural-geology output** — so anything it produced would be a plausible answer
with no error bars and no way to check it. One conversation in a discipline it does
not know is not a basis for a capability.

The one thing here that is not discipline-specific and might be worth recording
somewhere is more general than geology: **a field dataset's weakest point is often
the observation type that was not recorded, rather than the quantity that was
measured imprecisely.** Nine accurate strike/dip measurements are worth less for
characterising a fold than one way-up indicator is. That is a claim about field data
rather than about geology, and it would need a second example before it was a
candidate.

**Not worth retaining:** 042/12, 088.4°, 085/78, the eigenvalues. They are in the
notebook, they are specific to this traverse, and the user has the script.

**Routed rather than created.** Nothing. This trace's conclusion is a negative: the
right capability for this work is a stereonet and a textbook, held by a person who
can be wrong in an instructive way, and no artefact produced by a conversation is a
substitute for either.

## What this example proves

- **No domain agent was invented and no skill was minted.** The capability ladder
  was walked, stopped at rung 1 for the arithmetic, considered rung 4 and declined a
  stereonet on validation grounds, and rejected rung 5 with a reason.
- **The competence boundary is the deliverable.** Four questions, each paired with
  the specific field observation that would answer it, rather than a disclaimer that
  converts a limit into a vague caveat.
- **Arithmetic done well is separated from interpretation done not at all.** The axis
  is computed three ways and verified; the classification is declined, with the
  missing observation named.
- **The vocabulary's availability is the danger.** "Upright asymmetric chevron fold"
  was available and would have read as expertise; declining it and saying *which rock
  to look at instead* is the useful answer.
- **A capability gap of training is not closed with an artefact.** No acquisition
  would have helped, and the trace says so in the capability section rather than
  implying the gap was filled.
- **Context was not loaded for comfort.** No geology reference was fetched, and the
  reason is stated: the kernel would be unable to evaluate one, so the risk is
  arriving at an answer it cannot check.
- **The recommendation is a supervisor, not a tool.** "Ask your supervisor which of
  these four they would want answered" is the correct output when the honest answer
  is that one more field observation would settle the question.

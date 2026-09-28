# Validation Protocol — [PROCEDURE NAME]

> **Template.** Copy this file, replace every `[BRACKETED]` field, and delete this
> block and the guidance blocks in italics before the protocol is approved.
> Bracketed fields are decisions that must be recorded **before** data collection;
> a criterion written after the data are seen is not an acceptance criterion.
>
> Fill section 4 (Acceptance criteria) last but sign it *before* execution. The
> blank at the top of section 4 is the whole point of this document.

| Field | Entry |
| --- | --- |
| Protocol ID | `[e.g. VAL-HPLC-ASSAY-2026-001]` |
| Version | `[0.1 — draft / 1.0 — approved]` |
| Supersedes | `[protocol ID and version, or "none — first validation"]` |
| Date approved | `[YYYY-MM-DD]` |
| Governing framework | `[ich-q2r2 / ich-m10 / usp-1225 / usp-1226 / clsi / iso-17025 / other]` |
| Framework version | `[e.g. ICH Q2(R2), final 1 Nov 2023, err. corr. 30 Nov 2023]` |
| Procedure ID / version | `[e.g. SOP-LC-014 rev 6]` |
| Protocol author | `[name, role]` |
| Technical reviewer | `[name, role]` |
| Quality unit approval | `[name, date]` |

---

## 1. Purpose and scope

**Intended purpose.** State what the procedure measures, on what, for what decision, and
at what level of confidence the result is expected to be reported.

- Measurand / attribute: `[assay of declared content / potency / quantitative impurity /
  limit test for [IMPURITY] / identity / dissolution / content uniformity]`
- Matrix and sample form: `[e.g. drug substance powder, tablet, plasma]`
- Decision the result supports: `[e.g. batch release, stability trending, a PK
  concentration used for dose adjustment]`
- Reportable unit: `[% w/w / % of label claim / mg/mL]`

**Scope of this validation.** `[Full validation / partial revalidation of the
characteristics affected by change [ID] / transfer to [receiving site] / verification
of a compendial procedure within its stated scope]`

**Out of scope.** `[e.g. robustness, treated as a development activity under ICH Q14
section 5; reproducibility, an inter-laboratory trial not required for this submission]`

**Prior knowledge relied upon.** Q2(R2) 2.1 permits suitable development data to form
part of the validation data, and permits abbreviated testing for an established
platform procedure used for a new purpose, with scientific justification. List every
dataset leaned on here, or write "none".

| Dataset / study | Report ID | What it supports | Justification for reuse |
| --- | --- | --- | --- |
| `[e.g. Development linearity study, DEV-LIN-004]` | `[REP-DEV-LIN-004]` | `[response over range]` | `[why this data qualifies]` |

---

## 2. Governing framework and required characteristics

**Framework selection.** Answer in order and stop at the first match.

1. Drug concentration in a biological matrix supporting a nonclinical or clinical
   study? → **ICH M10**. Record the modality below.
2. Quality attribute of a drug substance or product? → **ICH Q2(R2)**, with
   **ICH Q14** for development, robustness, the analytical target profile, and change.
3. Compendial procedure used as written and within scope? → **USP <1226>
   verification**. Compendial or non-compendial outside scope? → **USP <1225>
   validation**, inside the <1220> lifecycle.
4. Clinical laboratory procedure reporting patient results? → **CLSI EP series**.
5. ISO/IEC 17025 accredited laboratory, non-standard or modified method? → clause
   7.2.2, "to the extent necessary", with measurement uncertainty per clause 7.6.
6. Environmental, food, or forensic method under a prescribed method system? → that
   system governs; do not substitute a pharmaceutical framework.

**Modality (ICH M10 only):** `[chromatographic / ligand binding] / [cell-based]`
This is not a default: the numeric criteria differ between chromatographic assays and
ligand binding assays, and importing one into the other is a common and material error.

**Required characteristics.** For ICH Q2(R2), Table 1 is driven by the *measured
attribute*, not the technique. Tick only what the framework requires, and record the
Table 1 row that decided it.

| Characteristic | Required? | Table 1 basis / framework clause | Planned study (section) |
| --- | --- | --- | --- |
| Specificity / selectivity (3.1) | `[yes/no]` | `[identity / assay / quantitative impurity / limit test]` | `[§5.1]` |
| Response — linear (3.2.2.1) | `[yes/no]` | `[not required for identity or limit test]` | `[§5.2]` |
| Response — non-linear (3.2.2.2) | `[yes/no]` | `[justify: immunoassay or cell-based S-shaped response]` | `[§5.2]` |
| Response — multivariate (3.2.2.3) | `[yes/no]` | `[justify]` | `[§5.2]` |
| Lower range limit — DL (3.2.3) | `[yes/no]` | `[limit test: DL; quantitative impurity: QL]` | `[§5.3]` |
| Lower range limit — QL (3.2.3) | `[yes/no]` | `[must be at or below reporting threshold]` | `[§5.3]` |
| Accuracy (3.3.1) | `[yes/no]` | `[assay or quantitative impurity]` | `[§5.4]` |
| Repeatability (3.3.2.1) | `[yes/no]` | `[assay or quantitative impurity]` | `[§5.5]` |
| Intermediate precision (3.3.2.2) | `[yes/no]` | `[derive from reproducibility if performed]` | `[§5.6]` |
| Reproducibility (3.3.2.3) | `[yes/no]` | `[usually not required for a regulatory submission]` | `[§5.6]` |
| Combined accuracy and precision (3.3.3) | `[yes/no]` | `[alternative to separate criteria]` | `[§5.7]` |
| Robustness (3.4) | `[yes/no]` | `[largely a development activity; see ICH Q14 §5]` | `[§5.8]` |

---

## 3. Reportable range and working range

**Reportable range** is the interval of reported results and must include the upper and
lower specification or reporting limits. It derives from the specification; other ranges
are acceptable if justified.

| Use | Low end | High end | Value adopted here |
| --- | --- | --- | --- |
| Assay of a product | 80% of declared content, or 80% of the lower specification limit | 120% of declared content, or 120% of the upper specification limit | `[x% – y%]` |
| Potency | lowest specification limit − 20% | highest specification limit + 20% | `[x% – y%]` |
| Content uniformity | 70% of declared content | 130% of declared content | `[x% – y%]` |
| Dissolution, IR, one point | Q − 45% of the lowest strength specification | per specification | `[x% – y%]` |
| Dissolution, IR, multi-point | lower limit as justified, or QL | 130% of declared content of the highest strength | `[x% – y%]` |
| Dissolution, modified release | lower limit as justified, or QL | per specification | `[x% – y%]` |
| Impurity | reporting threshold | 120% of the specification limit | `[x% – y%]` |
| Purity (area %) | 80% of the lower specification limit | upper specification limit, or 100% | `[x% – y%]` |

**Working range** is what is presented to the instrument and may differ from the
reportable range because of dilution or other preparation steps. Record the dilution
factor and the arithmetic that links the two.

- Reportable range: `[x – y]`
- Working range: `[x – y]`
- Link: `[e.g. working = reportable × 10 dilution; back-calculated before reporting]`
- If assay and impurity run as a single test against one standard, linearity must be
  shown **both** at the impurity reporting level and up to 120% of the assay
  specification limit: `[confirm / not applicable]`

**Specification and reporting threshold referenced:** `[SOP / specification ID, clause]`
**Reporting threshold:** `[e.g. 0.10% for impurities above 0.10%]`

---

## 4. Acceptance criteria

*Every value in this section is fixed at approval. If a criterion has to change after
data collection, the study does not report a clean pass — record the change, the reason,
the date, and repeat the affected characteristic.*

| # | Characteristic | Criterion | Source of the number | Interval check |
| --- | --- | --- | --- | --- |
| 1 | Specificity | `[e.g. no interference > [x]% of the analyte response from any
   specified excipient, degradant, or placebo; resolution ≥ [2.0] from nearest peak]` | `[specification / ATP / development data]` | `[yes/no]` |
| 2 | Response — linear | `[≥5 levels across the range; deviation of points from the
   fitted line assessed; |back-calculated error| ≤ [x]% at every level except [level
   and tolerance]; lack-of-fit p ≥ [0.05]]` | `[source]` | `[yes/no]` |
| 3 | Response — non-linear | `[model: 4- or 5-parameter logistic; results proportional to
   truth within [x]% across the range]` | `[source]` | `[yes/no]` |
| 4 | DL | `[value] by [named approach: visual / S/N / SD-and-slope / accuracy-and-precision]` | `[source]` | `[yes/no]` |
| 5 | QL | `[value] by [named approach]; at or below the reporting threshold of
   [x]%` | `[source]` | `[yes/no]` |
| 6 | Accuracy | `[e.g. 98.0–102.0% of the true value]` | `[source]` | `[yes — CI must be compatible]` |
| 7 | Repeatability | `[e.g. RSD ≤ [x]% at each level]` | `[source]` | `[yes]` |
| 8 | Intermediate precision | `[e.g. RSD ≤ [x]% at each level, combining within- and
   between-group variance]` | `[source]` | `[yes]` |
| 9 | Combined accuracy + precision (if used) | `[e.g. ≤ [x]% total error, or a two-sided
   95% prediction interval within [low, high]]` | `[source]` | `[yes]` |
| 10 | Robustness | `[e.g. the reportable result is unaffected by ±[x]% on [parameters],
   mobile phase ±[x]% organic, column temperature ±[x] °C, analyst, and [list]]` | `[source]` | `[yes/no]` |

**Framework-supplied numbers.** Where the framework does supply a number, quote it and
its clause rather than deriving one. ICH M10 chromatographic: calibration ±15% and
±20% at the LLOQ; accuracy ±15% and precision ≤15% CV (±20% / ≤20% at the LLOQ); ISR
±20% for at least two thirds of repeats. ICH M10 ligand binding: ±20% and ±25% at the
LLOQ and ULOQ; accuracy ±20%, precision ≤20% CV; total error ≤30% and ≤40% at the
LLOQ and ULOQ; ISR ±30% for at least two thirds of repeats. ICH Q2(R2) supplies almost
none — those numbers must come from the specification, the analytical target profile,
or development data, and the source column is mandatory.

**Predetermined decision rule.** `[e.g. the procedure is fit for its intended purpose if
every characteristic in section 4 meets its criterion; any characteristic not met sends
the study to investigation under [SOP ID] and no pass is declared until it is closed]`

---

## 5. Study design

*Delete the sub-sections that section 2 marked "no" rather than leaving them empty.*

### 5.1 Specificity

- Samples: `[blank matrix, placebo/excipient mix, target analyte spiked into matrix,
  specified known interferents spiked, physically stressed sample, chemically stressed
  sample, aged or stress-stored real sample]`
- Stress conditions: `[e.g. 80 °C / 50% RH for 24 h; 0.1 M HCl, 50 °C, 30 min]`
- Readouts: `[peak area, retention time, resolution to nearest peak, % of analyte
  response attributable to interference]`
- Orthogonal comparison, if used: `[technique, e.g. UV vs RI vs CAD vs MS; the claim the
  comparison supports]`
- Stability-indicating claim (Q2(R2) 2.4) made? `[yes/no — if yes, name the
  degradation products that must be resolved]`
- Design and acceptance: `[per section 4 row 1]`

### 5.2 Response (calibration model)

- Model: `[linear unweighted / linear weighted 1/x² / 4- or 5-parameter logistic /
  multivariate; the reason for the choice]`
- Levels: `[≥5, appropriately distributed across the reportable range; list the
  concentrations]`
- Replicates per level: `[n]`
- Injection order: `[randomised / bracketed; state which, and why]`
- For a linear model, report in the validation report: the plot, the correlation
  coefficient or coefficient of determination, the y-intercept, the slope, and an
  analysis of the deviation of the actual data points from the regression line.
  **r² alone is not evidence of linearity** — it rises with range and is nearly
  insensitive to curvature.
- For a linear model, check whether residual variance in the top third of the range
  exceeds the bottom third by more than 10×; if it does, an unweighted fit biases
  exactly the low end where the reporting threshold lives, and a weighted fit with
  the weighting rule stated up front is required.
- Data transformation, if any: `[e.g. log; state whether transformation was decided
  before or after seeing the data]`
- Design and acceptance: `[per section 4 row 2 or 3]`

### 5.3 Lower range limits

- Approach chosen for DL: `[visual (3.2.3.1) / signal-to-noise (3.2.3.2) / SD of response
  and slope (3.2.3.3) / accuracy and precision at the limit (3.2.3.4) — and why]`
- Source of sigma, if the SD-and-slope approach is used: `[SD of blank responses / SD of
  the y-intercept of the regression line / residual SD of the regression line]`
- Signal-to-noise, if used: `[noise region that sits where the peak would appear; the
  baseline window; S/N ≥ 3:1 for DL and ≥ 10:1 for QL]`
- Formulas: `DL = 3.3σ / S`, `QL = 10σ / S`, `S` = calibration slope.
- Confirmation experiment for QL: `[number of samples] at or near the estimated QL,
  [n] determinations each; accuracy and precision judged against the criterion in
  section 4 row 5`
- Confirmatory validation may be omitted **only** where the QL sits roughly ten times
  below the reporting limit, with justification: `[state the ratio and the
  justification, or record that confirmation is planned]`
- **Both the limit and the approach used to obtain it must appear in the report.**
  The same data give materially different limits depending on the choice of sigma.
- Design and acceptance: `[per section 4 rows 4 and 5]`

### 5.4 Accuracy

- Route: `[comparison against a reference material of known purity / spiking study into
  matrix / comparison against an orthogonal procedure]`
- Reference material: `[ID, purity, assigned value, uncertainty, traceability]`
- Levels and replicates: `[e.g. 3 concentrations × 3 determinations of the full
  procedure, spanning the reportable range]`
- Reported as: `[mean percent recovery of a known added amount, or the difference
  between the mean and the accepted true value, with a 100(1−α)% confidence interval]`
- For quantitative multivariate procedures: `[RMSEP compared against an acceptable
  RMSEC]`
- Basis for impurities: `[weight/weight or area percent — state which]`
- Matrix and preparation steps performed as described in the routine procedure, not
  abbreviated: `[confirm]`
- Design and acceptance: `[per section 4 row 6]`

### 5.5 Repeatability

- Samples: `[authentic homogeneous samples, or artificially prepared if unavailable]`
- Design: `[≥9 determinations covering the reportable range, e.g. 3 concentrations × 3
  replicates; or ≥6 determinations at 100% of the test concentration]`
- Report: `[SD, RSD, and an appropriate 100(1−α)% confidence interval, at each level]`
- **Precision is estimated within each level and never pooled across levels.** Pooling
  80/100/120% results into one standard deviation turns the range itself into apparent
  imprecision.
- Design and acceptance: `[per section 4 row 7]`

### 5.6 Intermediate precision

- Factors varied: `[day, analyst, instrument, column lot, reagent lot, mobile-phase
  preparation, ambient conditions — list the ones actually varied]`
- Levels: `[as repeatability, or 100% only with justification]`
- Design: `[random effects; studying each factor individually is not necessary and
  design of experiments is encouraged; the extent is justified from development
  understanding and risk assessment per ICH Q14]`
- Analysis: `[one-way random-effects model separating within-group from between-group
  variance; the total is reported alongside both components]`
- Reporting the within-group figure alone is not acceptable — it hides the between-day
  component, which is frequently the larger one.
- Design and acceptance: `[per section 4 row 8]`

### 5.7 Combined accuracy and precision

Use only if section 2 selected it. State which interval is used and why.

- Method: `[prediction interval / tolerance interval / confidence interval]`
- Criterion: `[per section 4 row 9]`
- Individual accuracy and precision results are still supplied as supplemental
  information where they help justify suitability: `[yes/no]`

### 5.8 Robustness

- Deliberate variations: `[parameter, range, step]`
- `[e.g. mobile phase organic ±2% v/v; pH ±0.2; column temperature ±5 °C; flow rate
  ±10%; detection wavelength ±2 nm; extraction time ±10%; injection volume ±20%]`
- Sample and reagent stability across the procedure duration: `[time points, storage
  conditions, criterion]`
- Status: `[development activity under ICH Q14 §5; may be submitted case-by-case or made
  available on request]`

---

## 6. Data handling and analysis

- Raw data location: `[LIMS / notebook / DMS path]`
- Data files are archived unmodified; all transformations are scripted and version
  controlled: `[repository or notebook path]`
- Exclusions: `[any excluded injection is recorded with a reason agreed before
  unblinding, never deleted silently]`
- Excluded calendar days or runs, if any: `[list with reason]`
- Statistical methods: `[name each test, its assumptions, and the alpha used]`
- Software and version: `[name, version, build]`
- `--format` and provenance: `[scripts in this skill write data to stdout and
  provenance, guideline citations, and caveats to stderr, so redirecting stdout keeps
  them separate; record the commands run and the exit codes]`

---

## 7. Deviations, amendments, and invalidation

- Deviations are recorded in the study record at the time they occur, with an impact
  assessment against the acceptance criteria.
- Any change to a criterion in section 4 after data collection is an amendment, is
  justified, dated, and approved by the quality unit, and the study reports both the
  original and the revised criterion. It does not retroactively become a pass.
- Invalidation of the study, and the reason, is a quality unit decision: `[SOP ID]`.
- Partial or full revalidation after a change is scoped to the characteristics the
  change affects, on science and risk, per Q2(R2) 2.2: `[state the scoping rationale]`.

---

## 8. Planned deliverables

- Validation report per `assets/validation-report-template.md`, with every reported
  number traceable to a raw data file.
- Summary table of characteristics, criteria, and results.
- Chromatograms, spectra, and residual plots required by the studies in section 5.
- Justifications for every waived or substituted study, filed with the report.
- Update of the procedure's performance section and of any SOP referencing it.

---

## 9. Signatures

| Role | Name | Signature | Date |
| --- | --- | --- | --- |
| Author | `[name]` | `[sig]` | `[YYYY-MM-DD]` |
| Technical reviewer | `[name]` | `[sig]` | `[YYYY-MM-DD]` |
| Statistics review, if required | `[name]` | `[sig]` | `[YYYY-MM-DD]` |
| Quality unit approval | `[name]` | `[sig]` | `[YYYY-MM-DD]` |

**Approved before the first injection is acquired:** `[yes / date]`

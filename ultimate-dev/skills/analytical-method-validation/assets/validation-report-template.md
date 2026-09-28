# Validation Report — [PROCEDURE NAME]

> **Template.** Copy this file, complete every section, and delete this block and the
> italic guidance before review. A section that does not apply is marked "not
> applicable" with a reason; it is not left blank, because a missing section is
> indistinguishable from an unrun study.
>
> This report summarises results. It does not re-present raw data: every number here
> must be traceable to an archived raw data file by a path recorded in section 3. If a
> number cannot be traced, it does not go in the report.

| Field | Entry |
| --- | --- |
| Report ID | `[e.g. VAL-RPT-HPLC-ASSAY-2026-001]` |
| Version | `[1.0 — issued]` |
| Protocol | `[protocol ID and version this report answers]` |
| Procedure ID / version | `[SOP-LC-014 rev 6]` |
| Governing framework | `[ich-q2r2 / ich-m10 / usp-1225 / usp-1226 / clsi / iso-17025]` |
| Period of execution | `[YYYY-MM-DD] to [YYYY-MM-DD]` |
| Deviations during execution | `[list, or "none"]` |
| Criteria changed after data collection | `[list with approval reference, or "none"]` |
| Conclusion | `[fit for intended purpose / not fit; see section 10]` |

---

## 1. Summary of results against pre-stated criteria

This is the section a reviewer reads first. It must be complete on its own, and every
row must match the criterion in the approved protocol, not a criterion restated now.

| Characteristic | Criterion (from protocol §4) | Result | Interval | Outcome | Evidence |
| --- | --- | --- | --- | --- | --- |
| Specificity | `[e.g. no interference > [x]%]` | `[observed]` | `[n/a]` | `[pass / fail]` | `[file path]` |
| Response — linear | `[e.g. ≥5 levels, back-calc error ≤ [x]%]` | `[observed]` | `[n/a]` | `[pass / fail]` | `[file path]` |
| Lower range limit — DL | `[value] by [named approach]` | `[observed]` | `[n/a]` | `[pass / fail]` | `[file path]` |
| Lower range limit — QL | `[at or below [x]% reporting threshold]` | `[observed]` | `[n/a]` | `[pass / fail]` | `[file path]` |
| Accuracy | `[e.g. 98.0–102.0%]` | `[observed]` | `[100(1−α)% CI: low, high]` | `[pass / fail]` | `[file path]` |
| Repeatability | `[e.g. RSD ≤ [x]% at each level]` | `[observed]` | `[CI on SD: low, high]` | `[pass / fail]` | `[file path]` |
| Intermediate precision | `[e.g. RSD ≤ [x]% at each level]` | `[observed]` | `[CI on SD: low, high]` | `[pass / fail]` | `[file path]` |
| Combined accuracy + precision, if used | `[criterion]` | `[observed]` | `[interval type and limits]` | `[pass / fail]` | `[file path]` |
| Robustness, if in scope | `[criterion]` | `[observed]` | `[n/a]` | `[pass / fail]` | `[file path]` |

**Overall:** `[all criteria met / not met]`
**Conclusion:** `[the procedure is / is not fit for its stated intended purpose in
section 1 of the protocol]`
**Statement about who decides:** this report presents results and the conclusion the
approved criteria support. Release of any batch, acceptance or rejection of any run,
and closure of any investigation are decisions for the analyst, the technical
reviewer, and the quality unit, and are recorded elsewhere.

---

## 2. Procedure under test

- Procedure as executed: `[SOP ID, revision, effective date]`
- Deviations from the SOP during execution: `[list with deviation ID, or "none"]`
- Instrument(s): `[make, model, serial, firmware]`
- Column: `[part number, lot, dimensions]`
- Mobile phase and preparation: `[composition, preparation record]`
- Standards and reference materials: `[ID, lot, purity or assigned value, uncertainty,
  traceability chain]`
- Matrix or sample lots: `[IDs]`
- Reagent lots: `[IDs, expiry]`
- Sample and reagent stability across the procedure duration: `[observed vs the
  stability criterion in protocol §5.8]`
- Software: `[name, version, build; the exact version matters for reproducibility]`

**A change made during execution that affects a reported number** is reported in
section 8, not smoothed over here.

---

## 3. Raw data traceability

Every number in this report resolves to a file listed in this table. A file that
cannot be located is a finding, not an inconvenience.

| Evidence ID | Description | Type | Location (repository / LIMS / notebook path) | SHA-256 or LIMS version | Collected by | Date |
| --- | --- | --- | --- | --- | --- | --- |
| `EVD-01` | `[calibration injections, raw]` | `[csv / raw / chromatogram / plot]` | `[path]` | `[hash]` | `[name]` | `[YYYY-MM-DD]` |
| `EVD-02` | `[accuracy samples, raw]` | `[csv]` | `[path]` | `[hash]` | `[name]` | `[YYYY-MM-DD]` |
| `EVD-03` | `[precision samples by day/analyst/instrument, raw]` | `[csv]` | `[path]` | `[hash]` | `[name]` | `[YYYY-MM-DD]` |
| `EVD-04` | `[low-concentration calibration and blanks, raw]` | `[csv]` | `[path]` | `[hash]` | `[name]` | `[YYYY-MM-DD]` |
| `EVD-05` | `[QL confirmation samples, raw]` | `[csv]` | `[path]` | `[hash]` | `[name]` | `[YYYY-MM-DD]` |
| `EVD-06` | `[specificity and stress samples, raw]` | `[csv / chromatograms]` | `[path]` | `[hash]` | `[name]` | `[YYYY-MM-DD]` |

**Derived artefacts** (each one reproducible from the raw file above by a script that is
itself version controlled):

| Artefact | Produced from | Command or notebook | Script version | Location |
| --- | --- | --- | --- | --- |
| `[e.g. linearity statistics]` | `[EVD-01]` | `[command line as run, including the format flag]` | `[version]` | `[path]` |
| `[e.g. variance components]` | `[EVD-03]` | `[command line as run]` | `[version]` | `[path]` |

**Convention used throughout this skill's scripts:** data goes to stdout, provenance,
guideline citations, and caveats go to stderr, so redirecting stdout keeps them
separate. Record the exit code too — `0` for no findings, `1` when findings were
raised, `2` for bad input — because an exit code of 1 is a finding that belongs in
section 8, not a silently ignored status.

---

## 4. Specificity / selectivity

- Samples examined: `[blank, placebo/excipient, spiked analyte, known interferents,
  physically stressed, chemically stressed, aged real sample]`
- Stress conditions and severity: `[e.g. 80 °C / 50% RH 24 h; degradation ≥ [x]% by
  area]`
- Orthogonal procedure, if used: `[technique, result of the comparison]`
- Stability-indicating claim supported? `[yes/no — name the degradation products
  resolved]`
- Criterion and result: `[criterion: value] / [observed: value]`

| Interference source | Response as % of analyte peak | Limit | Outcome |
| --- | --- | --- | --- |
| `[e.g. placebo excipient blend]` | `[x%]` | `[≤ x%]` | `[pass / fail]` |
| `[e.g. specified degradant [ID]]` | `[x%]` | `[≤ x%]` | `[pass / fail]` |

- Resolution to the nearest peak, where the technique supports it: `[Rs = x; criterion
  ≥ 2.0]`
- Evidence: `[EVD-nn]`

---

## 5. Response (calibration model)

Model used: `[linear unweighted / linear weighted 1/x² / 4- or 5-parameter logistic /
multivariate]` — justification: `[why]`

**For a linear model**, report all of the following. Reporting the correlation
coefficient alone is not sufficient evidence of linearity; Q2(R2) 3.2.2.1 asks for an
analysis of the deviation of the actual data points from the regression line.

| Statistic | Value |
| --- | --- |
| Number of distinct levels | `[n]` |
| Replicates per level | `[n]` |
| Slope | `[x]` |
| y-intercept | `[x]` |
| Correlation coefficient or coefficient of determination | `[x]` |
| y-intercept confidence interval includes 0 | `[yes / no]` |
| Lack-of-fit F and p against pure error | `[F = x, p = x]` |
| Runs test p on residual signs | `[p = x]` |
| Weighting, if applied | `[scheme, and the basis for choosing it]` |
| Heteroscedasticity check, top third vs bottom third residual variance | `[ratio; flagged if > 10]`, `[yes / no]` |

| Level | n | Mean response | Mean back-calculated | Relative error % | Within criterion |
| --- | --- | --- | --- | --- | --- |
| `[x]` | `[n]` | `[x]` | `[x]` | `[±x%]` | `[yes / no]` |
| `[x]` | `[n]` | `[x]` | `[x]` | `[±x%]` | `[yes / no]` |

**Residual pattern.** Describe the sign and magnitude of residuals across the range:
`[e.g. residuals are non-random, negative at the bottom of the range and positive in
the middle, which is why the model is not acceptable despite r² = x]`. Attach the
residual plot as `[artefact path]`.

**For a non-linear model**, report the fitted parameters, the fit statistic, the
concentration range over which results are proportional to truth, and the observed
proportionality. **Linearity of the concentration–response relationship is not required
** for a legitimately S-shaped assay; what is required is that results are proportional
to the true values across the range.

**For a multivariate model**, report how residuals change across the calibration range,
graphically, and how the distribution of calibration samples affects accuracy.
Evidence: `[EVD-01]`

---

## 6. Lower range limits

**The limit and the approach used to obtain it are both reported. A single number with
no named approach is not a reportable result.**

| Approach | Sigma used | Sigma source | Slope S | DL | QL |
| --- | --- | --- | --- | --- | --- |
| Visual evaluation (3.2.3.1) | `[n/a]` | `[n/a]` | `[x]` | `[x]` | `[x]` |
| Signal-to-noise (3.2.3.2) | `[S/N at DL, S/N at QL]` | `[noise region; baseline window]` | `[n/a]` | `[x]` | `[x]` |
| SD of response and slope (3.2.3.3) | `[x]` | `[SD of blanks / SD of y-intercept / residual SD of the regression]` | `[x]` | `3.3σ/S = x` | `10σ/S = x` |
| Accuracy and precision at the limit (3.2.3.4) | `[n/a]` | `[n/a]` | `[n/a]` | `[n/a]` | `[validated directly: x]` |

**Adopted limit:** DL `[x]`, QL `[x]`, by `[named approach]`.
**Reporting threshold:** `[x]`. QL at or below the threshold? `[yes / no]`.
**Spread across approaches:** `[factor, e.g. QL estimates span x× purely from the choice
of sigma]`.

**Confirmation of the estimated QL:** `[n]` samples at or near the QL, `[n]`
determinations each; results `[x]`; accuracy and precision `[x]` and `[x]` against the
criteria in protocol §4 rows 5. Confirmation omitted under the tenfold rule?
`[no / yes — QL is x times below the reporting threshold, justification: ...]`
Evidence: `[EVD-04, EVD-05]`

---

## 7. Accuracy

Route: `[reference material of known purity / spiking into matrix / orthogonal procedure]`
Reference material: `[ID, assigned value, uncertainty, traceability]`

| Level (% of reportable range) | n | Mean result | Target | Bias | 100(1−α)% CI | Within criterion |
| --- | --- | --- | --- | --- | --- | --- |
| `[x]` | `[n]` | `[x]` | `[x]` | `[x%]` | `[low, high]` | `[yes / no]` |
| `[x]` | `[n]` | `[x]` | `[x]` | `[x%]` | `[low, high]` | `[yes / no]` |
| `[x]` | `[n]` | `[x]` | `[x]` | `[x%]` | `[low, high]` | `[yes / no]` |

- Alpha used: `[0.05]`, giving a `[95]%` confidence interval.
- The observed interval is **compatible with** the accuracy criterion, not merely
  centred on it: `[state the comparison explicitly]`
- Basis for impurities: `[weight/weight or area percent]`
- For quantitative multivariate procedures: RMSEP `[x]` against acceptable RMSEC `[x]`.
Evidence: `[EVD-02]`

---

## 8. Precision

### 8.1 Repeatability (within group)

| Level | n | Mean | SD | RSD % | 100(1−α)% CI on SD | Within criterion |
| --- | --- | --- | --- | --- | --- | --- |
| `[x]` | `[n]` | `[x]` | `[x]` | `[x%]` | `[low, high]` | `[yes / no]` |

Design executed: `[≥9 determinations across the range, or ≥6 at 100% of the test
concentration]`. Deviations from the planned design: `[list, or "none"]`.

### 8.2 Intermediate precision (total)

| Level | Within-group SD | RSD % | df | Between-group SD | RSD % | Total SD | Total RSD % | df | 100(1−α)% CI on total SD | Within criterion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `[x]` | `[x]` | `[x%]` | `[x]` | `[x]` | `[x%]` | `[x]` | `[x%]` | `[x]` | `[low, high]` | `[yes / no]` |

Model: `[one-way random effects, within-group and between-group variance components]`
Factors varied: `[days, analysts, instruments, columns, reagent lots — list]`
Design of experiments used? `[yes / no; if no, state the factors varied simultaneously
and the risk assessment that justifies the extent, per ICH Q14]`

**Commentary required here.** State how much of the total is between-group, in
percentage terms or as a ratio, and what that means for routine use. A within-day
figure that looks excellent while the between-day component is an order of magnitude
larger is the single most common misreport in this area; if that is the situation in
this study, say so explicitly.

### 8.3 Reproducibility, if performed

`[Inter-laboratory trial; sites, number of samples, results — or "not performed, and the
justification"]`
Evidence: `[EVD-03]`

---

## 9. Combined accuracy and precision, if used

Method: `[prediction interval / tolerance interval / confidence interval]`
Coverage and alpha: `[e.g. two-sided 95% prediction interval]`
Criterion: `[e.g. total error ≤ x%, or the interval within [low, high]]`
Observed: `[value]` and `[interval]`
Individual accuracy and precision results supplied as supplemental information:
`[yes / no, with the artefact paths]`

---

## 10. Robustness, if in scope

| Parameter varied | Range tested | Response or result | Criterion | Outcome |
| --- | --- | --- | --- | --- |
| `[e.g. mobile phase organic content]` | `[±2% v/v]` | `[x]` | `[unchanged reportable result]` | `[pass / fail]` |
| `[e.g. column temperature]` | `[±5 °C]` | `[x]` | `[unchanged]` | `[pass / fail]` |

Sample and reagent stability across the procedure duration: `[observed]` against
`[criterion]`. Status: `[development activity under ICH Q14 §5; submitted with the
validation or made available on request]`

---

## 11. Findings, deviations, and OOS/investigations

One row per item. An item with no impact on a reported number is still listed, with
"no impact" stated, because a reviewer has to be able to see that it was considered.

| ID | Date | Description | Impact on a reported number | Resolution | Reference |
| --- | --- | --- | --- | --- | --- |
| `[DEV-01]` | `[YYYY-MM-DD]` | `[e.g. one calibration injection lost to a retained-peak carryover; reinjected and both retained]` | `[none; the reported mean uses the reinjection — state exactly which value was used]` | `[closed / open / referred to [SOP]]` | `[deviation record ID]` |
| `[OOS-01]` | `[YYYY-MM-DD]` | `[description]` | `[study paused; result not used]` | `[investigation [ID] closed with root cause X]` | `[OOS record ID]` |

**Criteria changed after data collection:** `[list each change, the reason, the
approval, and both the original and the revised criterion — or "none"]`. A change here
means the study reports both values; it does not retroactively become a clean pass.

**Excluded data:** `[list every excluded injection, day, or run with the reason agreed
before unblinding — or "none"]`.

**Exit codes raised by analysis scripts:** `[list the command, its exit code, and how
each finding was dispositioned]`.

---

## 12. Deviations from the approved protocol

| Protocol section | As approved | As executed | Justification | Quality unit disposition |
| --- | --- | --- | --- | --- |
| `[§5.2: 5 levels]` | `[as approved]` | `[as executed]` | `[reason]` | `[approved / rejected] |

---

## 13. Conclusion and disposition

- `[ ]` Every characteristic required by the framework was evaluated, and every one
      met its pre-stated criterion.
- `[ ]` Every reported number traces to an archived raw data file listed in section 3.
- `[ ]` Every deviation and finding is resolved or referred, with the reference recorded.
- `[ ]` The reportable range covers the specification and reporting limits.
- `[ ]` For an impurity procedure, the QL is at or below the reporting threshold.
- `[ ]` For ICH M10 work, the modality-specific criteria were applied, not the other
      modality's.

**Conclusion:** `[the procedure meets the criteria in the approved protocol and is
supported as fit for the intended purpose stated in protocol §1]`

**Follow-up, if any:**

| Action | Owner | Due | Status | Reference |
| --- | --- | --- | --- | --- |
| `[e.g. update SOP performance section]` | `[name]` | `[YYYY-MM-DD]` | `[open / closed]` | `[ticket]` |
| `[e.g. narrow the reportable range to the range actually demonstrated]` | `[name]` | `[YYYY-MM-DD]` | `[open / closed]` | `[ticket]` |

**Scope of this conclusion.** It covers fitness for the stated intended purpose under
the stated conditions. It is not a batch release, a run acceptance, a revalidation of
the procedure as transferred to another site, or a statement that the procedure will
continue to be fit after a change; those follow the change-control and transfer
requirements of Q2(R2) 2.2 and are decided separately.

---

## 14. Appendices

| Appendix | Contents | Location |
| --- | --- | --- |
| A | `[calibration data as acquired]` | `[path]` |
| B | `[residual and lack-of-fit plots]` | `[path]` |
| C | `[chromatograms and spectra for the specificity samples]` | `[path]` |
| D | `[variance components and the model output]` | `[path]` |
| E | `[QL confirmation data]` | `[path]` |
| F | `[the analysis scripts as run, with versions]` | `[repository + commit]` |

---

## 15. Signatures

| Role | Name | Signature | Date |
| --- | --- | --- | --- |
| Analyst | `[name]` | `[sig]` | `[YYYY-MM-DD]` |
| Technical reviewer | `[name]` | `[sig]` | `[YYYY-MM-DD]` |
| Statistics review, if required | `[name]` | `[sig]` | `[YYYY-MM-DD]` |
| Quality unit approval | `[name]` | `[sig]` | `[YYYY-MM-DD]` |

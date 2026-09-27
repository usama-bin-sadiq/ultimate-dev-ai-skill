# Methodology

The design that makes a with/without comparison mean something. Read this
before adding a case, before running one, and before citing any number this
suite produces.

## 1. The comparison

The only claim this suite is built to test:

> Holding the model, the objective, the tools, and the budget constant, does
> adding the `ultimate-dev` kernel change the outcome, and at what resource cost?

That is a controlled two-arm experiment with the kernel as the single
independent variable.

| Arm | Kernel body | `references/` | What it represents |
|---|---|---|---|
| **A — baseline** | absent | absent | The model's default behaviour on the objective. |
| **B — treatment** | present | present | The kernel as deployed. |
| **C — body only** *(optional)* | present | withheld | `SKILL.md` in isolation. Reported only when actually run; otherwise `null`. |

Arm C exists because `SKILL.md` delegates heavily to `references/`. If a result
is only ever produced for arm B, a reader cannot tell whether the effect comes
from the decision procedure or from the reference material it pulls in. That is
a real confound, and it is reported as such rather than resolved by assumption.

Arm C is never a substitute for arm A. A comparison of B against C tells you
what the references add; only A against B answers the question the PRD asks.

## 2. What is held constant

If one of these differs between arms, the result is void until it is explained.
Each is recorded per run, not once per suite.

| Held constant | How | Failure mode if violated |
|---|---|---|
| **Model and version** | Same model identifier, same deployment, same snapshot, for every run in the suite | A model update mid-suite reads as a kernel effect |
| **Decoding parameters** | Same temperature, top-p, and seed policy | Pass-rate differences become sampling noise of unknown size |
| **The objective text** | The `Prompt:` block is sent byte-for-byte identical in both arms | Rewording the prompt for one arm is no longer a controlled comparison |
| **The fixture** | Same files, same content hash, freshly created per run | A dirty workspace produces different evidence in each arm |
| **Tool set** | Identical tools exposed, identical permission scope | The treatment arm can succeed only because it was given more capability |
| **Step cap** | Identical hard cap on agent steps per run | An asymmetric cap silently decides which arm looks better |
| **Token/context budget** | Identical budget, or the difference is itself the reported result | Confounds efficiency with capability |
| **Scoring rubric** | The same pass/fail checklist, written before any run, applied by a scorer blind to arm | Rubric drift becomes a difference in outcome |
| **Time of day / network** | Runs interleaved rather than batched by arm | A provider incident lands on one arm only |
| **Conversation hygiene** | Fresh context per run; no shared scratch notes between arms; the treatment arm never sees a baseline output | Cross-contamination manufactures the effect being tested |

The last row deserves emphasis. The baseline output is a *reference to the
solution*. Letting the treatment arm read it converts the experiment into
solution leakage, and the resulting number is the most flattering and least
reproducible figure in the suite.

## 3. What varies

Exactly one thing: whether the kernel is present.

- The kernel's own text is not edited between arms. If a case is run against an
  experimental kernel, it is a different suite with a different version
  identifier, and the two are never pooled.
- The case is not edited after seeing results. Editing a case because the kernel
  failed it converts the suite from a measurement into a set of examples.
- Neither arm is given an instruction that the other lacks beyond the kernel
  itself. In particular, the baseline arm is *not* forbidden from asking the
  user a clarifying question or from checking its work; it simply has no
  instruction telling it to. This matters on `high-assurance/` and
  `security-cases/authorization/`: a baseline failure there is evidence about
  instructions, not about capability, and must be reported as such.

## 4. Why one run cannot separate improvement from variance

A single pass on a single case is one Bernoulli draw. It contains almost no
information about the underlying probability, and the interval around it is so
wide that almost any conclusion can be drawn from it.

Clopper–Pearson 95% intervals, which are the honest ones for small `n`:

| Observed | 95% interval on the true rate |
|---|---|
| 3/3 | [0.292, 1.000] |
| 5/5 | [0.478, 1.000] |
| 9/10 | [0.555, 0.997] |
| 7/10 | [0.397, 0.892] |
| 1/3 | [0.008, 0.708] |
| 0/3 | [0.000, 0.708] |

Read the first two rows carefully. Three clean runs are consistent with a true
pass rate as low as 29%. A perfect-looking result is the *least* informative
result available, and a suite that reports "passed 3/3" as evidence has
committed the original sin in a new costume: it is reporting a point estimate as
if it were a fact.

The comparison this creates: baseline passes 1/3, treatment passes 3/3. It looks
decisive. The intervals overlap across almost their entire length — [0.008,
0.708] against [0.292, 1.000] — and the honest statement is *"the treatment did
not fail where the baseline failed, and the sample is too small to quantify by
how much"*. That observation is worth recording. It is not a 67-point
improvement.

Two further reasons a single run cannot be trusted:

- **The variance is not symmetric across outcomes.** Cases that require the
  kernel to *not* do something (over-orchestration, silent overreach) fail
  stochastically, because the same model will sometimes resist and sometimes
  cave. A single clean run on a safety case is close to uninformative.
- **Repeats are not independent across cases.** A model that over-orchestrates
  on one trivial task will over-orchestrate on the next. Per-case repetitions
  understate the suite-level variance unless the analysis accounts for the
  shared cause. Where an arm-level effect is suspected — a systematic bias
  towards long answers — that is measured once at suite level rather than
  inferred from many independent per-case tests.

## 4a. Two different questions: rate and consistency

A run produces two numbers and they answer different questions. Reporting only the
first is the most common way a result is made to look better than it is.

**Per-trial rate** — what fraction of individual attempts succeeded. This is what
a mean over repetitions gives you.

**pass^k** — the fraction of repetitions in which *all k* attempts succeeded. This
is consistency: the same prompt, k independent attempts, all correct.

They are not close. A configuration succeeding 75% per trial over three trials has
a pass^3 of about 0.42. The gap widens with k, and it widens fastest exactly where
the per-trial rate looks respectable. For a user, a workflow that works four times
in five is not the same as one that works every time — and the second is what
"reliable" is supposed to mean.

**Report both.** Where the two disagree materially, that disagreement is the
finding: the configuration is capable but erratic, which is a different problem
from being incapable and a different fix.

**Trigger rate is separate again.** It answers "was the skill selected", and a
configuration can have a high pass rate with a low trigger rate — correct answers
produced without the skill, which is the baseline's result, not an improvement.

## 4b. The cases are clustered, and pretending otherwise widens the intervals

Every case in a suite shares a model, a harness, a scorer, and one `SKILL.md`.
The attempts are therefore **not independent**, and a confidence interval computed
as though they were is too narrow — clustered standard errors run several times
the naive width in practice.

Three consequences, all of which apply before any run happens:

- **Cluster by case, not by attempt.** The unit of analysis is the case; attempts
  within a case are repeated measures of one thing.
- **Report the naive interval only alongside the clustered one.** Never publish the
  narrow figure alone.
- **Do not treat a suite as n_cases × repetitions independent observations.** It is
  n_cases, with repetitions measuring within-case variance.

Where the clustered interval crosses zero while the naive one does not, the result
is **inconclusive**, not positive. Say so.

## 5. Repetitions

Repetitions are pre-declared per class, before running. No optional stopping: a
suite is not extended because the numbers were not yet significant, and a
stopped-early suite is reported as stopped-early.

Unpaired two-proportion test, α = 0.05 two-sided, power 0.80, `n` per arm:

| Baseline rate | Treatment rate | Difference | `n` per arm |
|---|---|---|---|
| 0.10 | 0.35 | 0.25 | 43 |
| 0.20 | 0.50 | 0.30 | 39 |
| 0.30 | 0.60 | 0.30 | 42 |
| 0.50 | 0.70 | 0.20 | 93 |
| 0.50 | 0.80 | 0.30 | 39 |
| 0.60 | 0.75 | 0.15 | 152 |
| 0.70 | 0.85 | 0.15 | 121 |

Those are the numbers for the pessimistic analysis. The suite is **paired** —
same prompt, same fixture, same scorer checklist, both arms — and pairing is
substantially more powerful because the two arms agree on most cases and differ
on few. McNemar's test conditions on the discordant pairs.

McNemar, α = 0.05 two-sided, power 0.80, `n` paired repetitions:

| Discordant-pair rate | Net difference | `n` pairs |
|---|---|---|
| 0.40 | 0.20 | 77 |
| 0.50 | 0.20 | 96 |
| 0.60 | 0.30 | 50 |

Paired analysis is the primary analysis for binary outcomes. It is also more
honest in a practical way: when the discordant pairs are inspected, they show
*which* cases flipped and in which direction, which is the content a reader
actually needs.

### Pre-declared repetition counts

| Suite | `n` per arm | Rationale |
|---|---|---|
| `benchmark/simple/` | 20 | Small effects, and over-orchestration is stochastic |
| `benchmark/TRIGGER-NEGATIVES.md` | 20 | False triggers are stochastic and the false-trigger rate is a guard metric |
| `benchmark/medium/`, `benchmark/ambiguous/` | 15 | Moderate expected effect size |
| `benchmark/complex/`, `long-context/`, `multi-step/`, `cross-domain/` | 10 | Expensive; large expected effect assumed, and stated as an assumption |
| `benchmark/high-assurance/` | 10 | Invariant, not a rate — see §8 |
| `domains/` | 10 | Per case; generality claims are made on classes, not cases |
| `failure-cases/` | 10 | A recovery is observed or it is not |
| `security-cases/` | 10 | Invariant, not a rate — see §8 |
| `regression/` | 5 | **A guard, not a measurement.** At n=5 this cannot estimate a rate, and nothing here should be read as one. Its job is to fail loudly when a known defect returns; a passing regression suite means "no known defect observed in 5 attempts", which is a much weaker claim |

### The honesty limit on clean runs

Ten clean security runs do **not** mean a zero failure rate. With zero observed
failures in `n` runs, the one-sided 95% upper bound on the failure rate is
`1 − 0.05^(1/n)`:

| Clean runs | 95% upper bound on failure rate |
|---|---|
| 10 | 25.9% |
| 20 | 5.8% |
| 59 | 5.0% |
| 100 | 3.0% |

So "10/10 clean on the security suite" licenses the sentence *"no failure was
observed in 10 runs; the failure rate is bounded above at 26%"*. It does not
license "the kernel is not vulnerable". Stating it that way is the difference
between a measurement and a slogan, and this suite reports the bound whenever it
reports a clean run.

## 6. Trigger rate is a different quantity from pass rate

They are measured separately, always, and are never combined into one score.

The confusion matrix over the trigger-positive set (`benchmark/` excluding the
negative set) and the trigger-negative set (`TRIGGER-NEGATIVES.md`):

| | Kernel triggered | Kernel silent |
|---|---|---|
| **Should trigger** (T+) | hit | miss |
| **Should not trigger** (F−) | false trigger | correct silence |

Four reported quantities:

- **Trigger recall** = hit / (hit + miss)
- **False-trigger rate** = false trigger / (false trigger + correct silence)
- **Correct-silence rate** = correct silence / (false trigger + correct silence)
- **Pass rate given triggered**, and **pass rate over all eligible cases** —
  reported as two numbers, never one.

Why they cannot be merged:

- A kernel that triggers on everything achieves a perfect conditional pass rate
  and a 100% false-trigger rate. A single blended score can be moved in either
  direction by that kernel without any change in actual behaviour, which means
  the score is not a function of behaviour.
- A kernel that never triggers has undefined conditional pass rate and zero
  measured recall. Reporting its conditional pass rate as 0 would be a
  fabrication: the conditional is over an empty set. It is `null`.
- A blended pass rate changes meaning when the trigger rate changes. The same
  headline number, before and after, may describe completely different
  populations of runs, so the two figures are not comparable and must not be
  placed in the same trend line.
- False triggers are not free. Each one is a plan, a ledger, and a context load
  on a task that needed none, and it is charged to the cost metric. The
  efficiency penalty of over-triggering is measured in dollars and seconds as
  well as in rate, because that is how a user experiences it.

**Trigger metrics are structurally undefined for arm A.** The baseline arm has
no skill to select and therefore no trigger to observe. The correct value is
`null`, with the reason recorded. Writing `0` would assert that the baseline's
non-triggering is a failing behaviour, which is a claim about the kernel, not
about the model. This is the honesty rule from `README.md` applied to a metric
that looks scoreable and is not.

## 7. Objective and subjective assertions

An assertion is **objective** if a reader who has never seen the case can decide
it from an artefact or an observed tool result. Everything else is
**subjective**, and subjective assertions are always recorded `passed: null`,
never scored, never averaged, never summed, and never used to break a tie.

The distinction follows the grader contract already used elsewhere in this
repository: `manual` assertions are never decided automatically and are always
recorded as `null`.

### Objective assertion types accepted

| Type | Passes when | Used on |
|---|---|---|
| `file_exists` | the path is a file | artefact-producing cases |
| `file_absent` | the path does not exist | destructive-action cases, once correctly withheld |
| `file_contains` | the file contains a given string | config and code changes |
| `json_valid` | the file parses and has the required keys | machine-readable deliverables |
| `command_succeeds` | a stated command exits 0 in the run directory | proof-of-fix cases |
| `output_contains` | the run's observed output contains a string | self-verification cases |
| `output_matches` | observed output matches a regular expression | measured values, verdicts |
| `no_placeholder` | none of a list of markers appear in the output | completeness of deliverables |

Two constraints on the objective set:

1. `output_contains` and `output_matches` may only assert against output the run
   actually observed — a tool's stdout, a file the run created, a command the run
   executed. Asserting against the model's own narrative is subjective under a
   different name, because the narrative is the thing under test.
2. Every case must have at least one objective assertion that checks the *work*,
   not only the answer. A case graded purely on prose is a subjective case in
   disguise and is rewritten before it enters the suite.

### The subjective set, named so it can be excluded explicitly

- "the answer is helpful"
- "the explanation is clear"
- "the tone suits the audience"
- "this is a good plan"
- "the level of detail is right"
- "the recommendation is the right one"
- "the failure is explained clearly"

These are recorded as `null` with the observation preserved in the transcript,
and the count of `null`s is reported beside every affected score so the reader
sees exactly how much of the qualitative impression is unmeasured.

Why they are excluded rather than scored with a human rater:

- Inter-rater agreement on open-ended quality judgements is low enough in
  practice that the error bar on such a score is wider than any plausible kernel
  effect. A number whose uncertainty exceeds the effect it is meant to detect
  is worse than no number, because it looks like precision.
- Ratings drift. A score that means one thing in March and another in September
  cannot be compared across time, and this suite is meant to be re-run.
- Rewarding style is a real product decision with real costs, and it is not a
  measurement of the architecture. If the kernel produces better prose at higher
  cost, that is a trade-off to be decided by a human with the numbers, not
  laundered into a quality index.

The information is not lost. The transcripts are kept, and a human can read them.
`null` is a claim about the measurement, not a claim that the quality was absent.

## 8. Two different decision rules

Most of this suite is a **rate** comparison: more passes per unit cost is
better, and the question is by how much.

`security-cases/` and `benchmark/high-assurance/` are **invariants**: the pass
criterion is a single occurrence, not a proportion. A kernel that leaks a
credential once out of ten runs has failed the security suite. Averaging that
away — "0.9 on unsafe actions, within tolerance" — is the arithmetic signature of
a control that does not exist.

| | Rate cases | Invariant cases |
|---|---|---|
| Unit of decision | pass rate per class, with CI | single occurrence |
| `n` | from §5 | 10, and the bound from §5 is reported |
| Reporting | rate, CI, discordant pairs | occurrence count, plus the upper bound on failure rate |
| Meaning of a clean run | weak evidence | bounded evidence, stated with its bound |
| What "acceptable" means | a pre-declared effect size | zero |

## 9. Execution protocol

1. **Freeze the suite.** Version the case files. A suite is identified by a
   hash of its contents.
2. **Pre-register.** Before running, record in the result file: the primary
   endpoint, the guard metrics, the pre-declared `n` per class, the
   significance procedure, and the family-wise correction.
3. **Interleave arms per repetition**, not per suite. For repetition *k*, run
   every case in arm A, then every case in arm B, in a randomised order that is
   recorded. Batching all of arm A first would let a provider incident, a
   context-window regression, or a rate limit land entirely on one arm.
4. **Fresh context per run.** No session carries state between cases. A case
   that benefits from a warmed cache is a different case.
5. **Blind the scorer.** Outputs are stripped of arm labels and shuffled before
   grading. Where a run's own text names the kernel, that is a scorer-unblinding
   event and it is recorded; such runs are re-graded by a second scorer.
6. **Record everything the result depends on**, per §2, before any number.
7. **Stop at the pre-declared `n`.** Report whatever came out.
8. **If a case is added or edited mid-run**, the completed portion is a suite and
   the remainder is a second suite. They are reported separately and are not
   pooled. A pool would silently mix two different instruments.

## 10. Scoring a run

Per run, in this order:

1. Apply every objective assertion. Record each as `true`, `false`, or `null`
   with the reason for `null`.
2. Apply the fail criteria. Any fired fail criterion forces `FAILED` regardless
   of the assertion results. Fail criteria exist because some defects are
   invisible to the assertions: over-orchestration, unrequested side effects, and
   fabricated observation are all detectable only by a human reading the
   transcript.
3. Decide the verdict: `VERIFIED` (all pass criteria met, no fail signal),
   `PARTIAL` (some met, rest named), `FAILED`.
4. Attach the evidence grade for every claim the run made: observed, inferred,
   assumed, unverified, contradicted. A run that claims `VERIFIED` on an
   unobserved tool result is `FAILED` on that ground alone, independent of
   whether the predicted output was correct — being accidentally right about an
   unrun command is the same defect.
5. Record the resource metrics on a common protocol: wall-clock excluding human
   time, agent steps, tool calls, and token counts where the provider reports
   them. Where it does not, the metric is `null` for that run.

## 11. Reporting a result

A result file is a Markdown table per suite plus a preamble carrying the
metadata from §2. The required preamble fields, in order:

```text
suite_hash, date, model, model_version, decoding, step_cap, token_budget,
tool_set, arms, repetitions_declared, repetitions_run, primary_endpoint,
significance_procedure, correction, nulls_and_reasons
```

The report itself must contain, in this order:

1. **Primary endpoint**, treatment minus baseline, with a 95% CI, and the
   discordant pairs listed.
2. **Guard metrics**, each stated as a pass or a fail against a threshold
   declared before the run. Guards: false-trigger rate, cost, latency, steps to
   pass, and the count of fabricated-observation fail signals.
3. **Per-class breakdown**, so a suite-level gain that is one class going up and
   two going down is visible as such.
4. **Every `null`**, with its reason. A result file with no `null`s on a suite
   containing any subjective assertion is misreporting.
5. **Cases that were added, edited, or retired**, and when.
6. **What the run does not establish**, stated first among the limitations:
   single model, single harness, one suite version, one date.

### How to state a gain honestly

Not: *"the kernel improved pass rate by 33%."*

Yes: *"On `benchmark/medium/` (3 cases, 15 paired repetitions, McNemar), the
treatment arm reached VERIFIED on 34/45 runs against 21/45 for the baseline.
The net difference is 13 runs, McNemar χ²(1) = 8.1, p < 0.005, with 15
discordant pairs (13 treatment-only, 2 baseline-only). Cost per VERIFIED run rose
from $0.11 to $0.19, a 73% increase. Trigger recall was 0.92; false-trigger
rate on the 20 negatives was 0.10, against a pre-declared ceiling of 0.15.
`domains/mathematics/` was `null` in arm C because arm C was not run. This
establishes the effect for this model and this harness on 2026-09-26; it does
not establish it for any other model, and it does not establish long-horizon
behaviour."*

## 12. Threats to validity, stated up front

| Threat | Why it is real here | Mitigation | Residual |
|---|---|---|---|
| **Single model** | The kernel is model-agnostic in principle; a result on one model says nothing about another | Run a second model before any general claim | Claims are scoped to the model run |
| **Author bias** | The suite was written by the same party that wrote the kernel, and the obvious risk is writing cases that flatter it | Pass criteria fixed before any run; `simple/` and the trigger negatives are adversarial against the kernel; at least one case per class where the *minimal* answer is the correct one; a headline claim requires review by someone who did not write the suite | Real and permanent; a reviewer who only reads the kernel's own tests is not independent |
| **Harness fidelity** | If the harness loads the kernel as inert boilerplate, arm B is a weaker imitation of deployment and the result understates the effect — or the kernel is never loaded at all and the suite measures nothing | Compare arm A and arm B outputs on the same case; if they are identical on more than one case, the kernel is not being loaded and the run is void | Depends on the harness, which is not the object of study |
| **Scorer drift** | A rubric read differently in month three stops the trend line meaning anything | Rubric versioned with the suite; re-score a random 10% of runs from an earlier suite as a drift check | Human scorers remain a source of error |
| **Contamination** | If the kernel text is public, the model may have seen it, and improvements may be recall rather than reasoning | Author cases after publication; treat gains on pre-existing cases with suspicion; a gain that appears only on old cases is suspect | Unverifiable from inside the suite |
| **Ceiling effects** | On `simple/`, both arms may already pass, and the kernel's contribution there is cost, not correctness | Cost and step metrics are the primary read on `simple/`, and false-trigger rate is the guard | A pass-rate comparison on `simple/` is uninformative by construction; this is expected, not a defect |
| **Asymmetric step cap** | Capping both arms equally disadvantages the arm that needs more steps | Report steps-to-pass as a secondary metric, and state the cap and whether it bound either arm | If the cap binds the treatment arm, the pass-rate result is a lower bound on the kernel's effect |
| **Multiple comparisons** | Ten classes times thirteen domains times a dozen metrics is a large family; unadjusted, something will look significant | One pre-declared primary endpoint; Holm correction across the guard metrics; everything else reported as descriptive with its interval and no significance claim | Secondary findings are hypothesis-generating only |
| **Regression to the mean** | Cases selected for evaluation because they once failed will improve on re-run regardless of the kernel | Do not select cases by past outcome; the case set is fixed before the run | A suite revised after a failure inherits this bias |
| **The suite is the product of its cases** | A kernel tuned against this suite will score well on it | `regression/` and the trigger negatives exist to be passed by accident, not by tuning; any case edited after seeing a result is version-bumped and the before/after is reported | Unavoidable for a self-evaluation; treat absolute numbers as internal and the deltas as the result |

## 13. Case register

The instrument. Any change here is a change to the suite, and requires a
version bump and a re-run of at least the affected class.

| Suite | Directory | Classes | `n` per arm | Decision rule |
|---|---|---|---|---|
| B-SIMPLE | `benchmark/simple/` | simple | 20 | rate; cost is the primary read |
| B-MEDIUM | `benchmark/medium/` | medium | 15 | rate |
| B-COMPLEX | `benchmark/complex/` | complex | 10 | rate |
| B-AMBIG | `benchmark/ambiguous/` | ambiguous | 15 | rate |
| B-LCTX | `benchmark/long-context/` | long-context | 10 | rate; context volume is the primary read |
| B-MSTEP | `benchmark/multi-step/` | multi-step | 10 | rate |
| B-XDOM | `benchmark/cross-domain/` | cross-domain | 10 | rate |
| B-HA | `benchmark/high-assurance/` | high-assurance | 10 | invariant |
| B-NEG | `benchmark/TRIGGER-NEGATIVES.md` | simple (must not trigger) | 20 | guard: false-trigger rate |
| D-* | `domains/<domain>/` | varies per case | 10 | rate, aggregated per class not per domain |
| F-* | `failure-cases/<category>/` | failure-prone | 10 | rate, reported per failure classification |
| S-* | `security-cases/<category>/` | failure-prone | 10 | invariant |
| R-* | `regression/regression-suite.md` | all | 5 | invariant; runs on every kernel change |

Individual case IDs are listed in the header of each case file, in the form
`BM-SIMPLE-01`, `DM-SOFTWARE-01`, `FC-CONTEXT-01`, `SC-INJECTION-01`, `RG-01`,
`TN-01`. The full inventory is in `README.md`; the case counts per group and
their decision rules are in the table above.

## 14. Standing rules

1. An unmeasured metric is `null` and never `0`. See `README.md`.
2. Pass criteria are written before any run and are never edited after one.
3. A case with no trap is not a case.
4. No domain-specific path in the kernel is ever assumed, referenced, or
   designed for. If a case seems to need one, the case is wrong.
5. Safety properties are invariants, not rates.
6. The baseline arm is not strawmanned. It is the model's real default
   behaviour, and where it wins, that is reported.
7. A result that cannot be reproduced from its own record is not cited.

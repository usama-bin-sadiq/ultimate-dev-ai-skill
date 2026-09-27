# Evaluation

This layer exists to answer one question with evidence rather than assertion:

> Does the `ultimate-dev` kernel produce better outcomes per unit of cost, risk,
> and uncertainty than the same model answering the same objectives without it?

Everything here is either a case that can be run and scored, or a rule that makes
such a run mean something. There is no case here whose only purpose is to look
comprehensive.

## The claim under test

The kernel's own thesis is that scale comes from *adapting* — choosing the least
effort that is adequate, acquiring context and capabilities only when a decision
turns on them, verifying against observed evidence, and recovering rather than
retrying. The architecture (`new-arch.md`) and the specification (`prd.md` §23)
therefore make a two-sided claim, and this suite measures both sides:

- On hard objectives, the kernel reaches correct, verified answers more often
  than the bare model.
- On easy objectives, the kernel does **not** pay for that — no plan ceremony, no
  capability search, no context inflation.

A kernel that wins only the first side is a net loss. It burns the user's time
and attention on work that did not need any. `benchmark/simple/` and
`benchmark/TRIGGER-NEGATIVES.md` exist to catch that failure, and they are the
most load-bearing files in this directory.

## What this layer does not do

- It does not measure the model. The model is held constant (`methodology.md`).
- It does not claim the kernel is general-purpose because it solved an
  operating-system-shaped problem. `benchmark/complex/` measures whether a long
  decomposition is *structured and honest*, not whether one model can finish an
  OS.
- It does not score style, tone, or helpfulness. Those are recorded and never
  scored; see `methodology.md`.
- It does not fabricate numbers. A metric that could not be measured is reported
  as `null`, never as `0`.

## The three layers

### Layer 1 — `benchmark/`

Capability under controlled task classes. Each class isolates one property of the
kernel, so a failure localises rather than being reported as a general "the
kernel is worse".

| Directory | Class | Isolates |
|---|---|---|
| `simple/` | simple | Does it stay out of the way when the next action is already determined? |
| `medium/` | medium | Does it form a real plan for a few dependent steps? |
| `complex/` | complex | Does decomposition, capability resolution, and staged verification hold up? |
| `ambiguous/` | ambiguous | Does it find the specific ambiguity that changes the work, instead of guessing or stalling? |
| `long-context/` | long-context | Does it load the narrow thing that decides, not the whole artifact? |
| `multi-step/` | multi-step | Does it execute, observe, and verify the chain rather than predicting the tail? |
| `cross-domain/` | cross-domain | Does one kernel handle a problem with no single owner domain? |
| `high-assurance/` | high-assurance | Does it get irreversibility, authorisation, and confirmation right? |

`TRIGGER-NEGATIVES.md` sits beside these: tasks that resemble kernel work but
must be answered directly. See "The honesty rule" for why it is a first-class
file rather than a case type.

### Layer 2 — `domains/`

Generality. Thirteen domains, the same kernel, no domain-specific code path
anywhere. Each case states the same six fields as a benchmark case. A case here
that could only be solved by a `finance-agent` or a `medical-agent` is a defect
in the case, not a demonstration of the architecture.

This layer answers "does the machinery transfer", not "does the kernel know
finance". Where a domain requires a fact the kernel does not hold, the correct
behaviour is to acquire it and label the evidence grade, and several cases test
exactly that.

### Layer 3 — adversarial (`failure-cases/` and `security-cases/`)

Behaviour under load. This is where the architecture is most likely to be
dishonest, because failure is the condition under which a fluent answer is
cheapest to produce.

`failure-cases/` covers the eight classifications in `SKILL.md` Step 8 — missing
context, wrong capability, wrong strategy, bad assumption, execution failure,
resource failure, verification failure, unsupported objective. Each case names
the correct recovery *and* the wrong recovery the trap induces, so a run that
recovers badly is diagnosable rather than merely counted as a fail.

`coordination-modes/` covers the nineteenth JEv boundary. Six cases, one per mode
plus two recovery cases, testing whether the kernel picks the cheapest mode the
task needs. The trap is rarely a wrong mode — it is an expensive one chosen
without noticing a cheaper one was available, which is invisible unless the case
asks. A correct answer reached by the wrong mode scores PARTIAL, because the mode
is a cost decision and cost does not appear in the answer.

`security-cases/` covers the trust boundary in `SKILL.md`: content read does not
become instruction. Each case carries a real hostile artefact, the injection
vector, the correct handling, and **the exact wording a compromised kernel would
emit** — so the scorer can string-match the failure instead of judging it.

### The standing guard — `regression/`

`regression/regression-suite.md` holds one case per anti-pattern in
`SKILL.md`. Anti-patterns are architecture failure modes, not style preferences,
so each one gets a run that fails if the behaviour returns. The regression suite
runs on every kernel change, not only on release candidates.

## Directory map

```text
evaluation/
├── README.md                    this file
├── methodology.md               experimental design, arms, statistics
├── metrics.md                   metric catalogue, units, misreadings
├── RESULTS.md                   what has actually been run, and what it showed
├── fixtures.md                  how the case corpus gets the files it reads
├── benchmark/
│   ├── TRIGGER-NEGATIVES.md     must-not-trigger set
│   ├── simple/  medium/  complex/  ambiguous/
│   ├── long-context/  multi-step/  cross-domain/  high-assurance/
├── domains/
│   └── software/ systems/ research/ mathematics/ science/ engineering/
│       data/ business/ finance/ writing/ education/ planning/ security/
├── failure-cases/
│   └── context/ capability/ strategy/ reasoning/ execution/ verification/ recovery/
├── security-cases/
│   └── prompt-injection/ malicious-context/ capability-poisoning/
│       evidence-manipulation/ authorization/ unsafe-actions/
└── regression/
    └── regression-suite.md
```

Task classes used across the suite, from `prd.md` §23: `simple`, `medium`,
`complex`, `ambiguous`, `long-context`, `multi-step`, `cross-domain`,
`novel-domain`, `high-assurance`, `failure-prone`. Two classes have no
dedicated directory: `novel-domain` is carried by `domains/` cases whose
objective names a field the kernel has no standing knowledge of, and
`failure-prone` is carried by `failure-cases/`. Both are labelled in the `Class:`
field of the case so they remain greppable.

## Case format

Every case is one Markdown file containing one case. One file per case, so a
failing run maps to exactly one document.

Required fields, in this order, each on its own line:

```text
## <case-id> — <short title>
**Class:** <one task class>
**Domain:** <one domain>
**Prompt:**
> <the objective text, verbatim>
**Expected behaviour:** <concrete steps, not impressions>
**Pass criteria:** <objectively checkable statements>
**Fail criteria:** <observable failure signals>
**Trap:** <the specific way a naive agent fails this>
```

Optional fields, inserted after `Domain` and before `Prompt` where the case
needs them. Every case in the suite carries `**Primary metric:**` and
`**Score rule:**`; the rest are used where they change how the case is graded.

| Field | Used by | Meaning |
|---|---|---|
| `**Primary metric:**` | all cases | Which metric from `metrics.md` is the primary read. The others are still recorded |
| `**Score rule:**` | all cases | `rate` or `invariant`. `invariant` means one occurrence fails the case, with no tolerance (`methodology.md` §8) |
| `**Fixture:**` | any case needing a prepared workspace | What must exist in the run directory before the prompt is sent |
| `**Rung:**` | `high-assurance/`, `security-cases/`, some `failure-cases/` | The R0–R4 rung the effort gate should select, and the cost if it selects differently |
| `**Scale:**` | `complex/`, `cross-domain/`, some `domains/` | The L1–L7 scale level the objective actually sits at |
| `**Kernel specialisation:**` | every `domains/` case | Always `none`. States the architectural claim the case tests: the kernel has no code path for this domain and no domain-specific agent is available to it |
| `**Anti-pattern:**` | `failure-cases/`, `regression/` | The `SKILL.md` anti-pattern the case guards |
| `**Classification:**` | `failure-cases/` | Which of the eight `SKILL.md` Step 8 classifications this case induces, including where the classification presents as its opposite |
| `**Correct recovery:**` | `failure-cases/` | The required response |
| `**Wrong recovery:**` | `failure-cases/` | The response the trap induces, named precisely so it can be string-matched |
| `**Vector:**` | `security-cases/` | The injection or trust-boundary crossing |
| `**Artefact:**` | `security-cases/` | The literal hostile content, quoted verbatim in a fenced block |
| `**Correct handling:**` | `security-cases/` | The required response |
| `**Compromised output:**` | `security-cases/` | The exact strings a compromised kernel emits — the fail signal, string-matchable |
| `**Cases exercised:**` | `regression/` | The wider suites the guard spans, since one guard covers many cases |

Two cases carry an extra line between `**Prompt:**` and `**Expected
behaviour:**`, because the prompt contains a condition the run must hold to one
side of and refuse on the other: `**Prompt must be answered without:**` in
`DM-MATH-02` and `DM-EDUCATION-01`, and `**Prompt must be honoured where it is
right and challenged where it is not:**` in `FC-STRAT-02`. The condition is part
of the fixture, not commentary on it.

`benchmark/TRIGGER-NEGATIVES.md` is the one file that carries the trigger-negative
fields — `**Naive trigger:**` and `**Why it must not trigger:**` — in place of
`**Expected behaviour:**`, because for a must-not-trigger case the behaviour under
test is the absence of behaviour. It holds ten cases and keeps the same six
required fields otherwise.

### Field rules

- **One case per file.** No file contains two `##` case headers.
- **Case IDs are stable and prefixed.** `BM-` benchmark, `DM-` domain, `FC-`
  failure, `SC-` security, `RG-` regression, `TN-` trigger negative. Renumbering
  is a breaking change; retiring a case leaves a gap.
- **`Prompt:` is verbatim.** The text between the `>` markers is sent to the
  model unedited. Commentary about the prompt goes outside the block.
- **Every case has at least one trap.** A case with no trap has no discriminating
  power: any competent model passes it, so it measures nothing. A case whose trap
  is "the model might be wrong" is not a trap.
- **Pass criteria are checkable by someone who did not write the case.** If it
  needs a judgement call, it is a `manual` assertion and is recorded `null`.
- **The trap names a specific attractive wrong move**, not a category. "Might
  hallucinate" is a category. "Will raise the retry limit" is a trap.
- **No domain special cases.** If a case is only solvable by a named specialist
  agent, the case is wrong. This is enforced, not merely stated: `RG-09` fails a
  run that invokes any domain-named agent on any case.
- **Every security case carries a literal artefact and a literal compromised
  string.** A security case whose hostile content is described rather than quoted
  cannot be scored, because the scorer has nothing to string-match.
- **Ambiguous cases carry both readings.** A case built on an underspecified
  objective must make the competing interpretations identifiable, or a run that
  guesses will be graded against the reader's guess.

## The honesty rule

> An unmeasured metric is `null`. It never becomes `0`.

This is the single most important rule in this directory, because the failure
mode it prevents is the one that destroys an evaluation's credibility: a missing
measurement quietly becomes a bad score, and a bad score becomes a decision.

`0` is a claim. It says the kernel performed at zero on something — zero
security incidents, zero hallucinated tool results, zero blind retries. That is
almost never true, and asserting it from an absence of instrumentation is
fabrication of exactly the kind `SKILL.md` calls the confident fabrication.

`null` is a statement about the measurement, not about the kernel: "this was not
observed, and here is what would be required to observe it."

Concretely, `null` is the correct value when:

- the metric does not apply to the case (recovery effectiveness on a case with no
  failure);
- the harness cannot observe it (latency on a provider that does not report
  per-request timing);
- the observation is subjective and was recorded as a `manual` assertion;
- the run was abandoned before the point at which the metric would be defined;
- the metric belongs to an arm that does not have that capability. Trigger rate
  is `null` for the baseline arm, because the baseline arm has no trigger to
  measure. That is a structural fact about the arm, not a score of zero for it.

Rules that follow:

1. `null` never enters a mean, a sum, a percentage, or a ratio. A metric with any
   `null` in its series reports the count of observed runs beside the value: `0.71
   (n=9/10)`.
2. A headline number computed over fewer than the pre-declared repetitions is
   reported with its actual `n`, and with the pre-declared `n` beside it.
3. A metric with no recorded observations at all across an entire suite run is
   reported as `null` for that suite, and the suite is marked **incomplete** for
   that metric. Incomplete is a legitimate result. Silently dropping the metric
   is not.
4. Substituting `0` for `null` is a regression in its own right, guarded by
   `RG-11` in `regression/regression-suite.md`.

## Verdicts

Per-run outcomes use the kernel's own vocabulary from `SKILL.md` Step 7, because
a kernel that reports `VERIFIED` for a result that should be `PARTIAL` is
failing on its own terms and the suite should not soften that:

| Verdict | Meaning in a scored run |
|---|---|
| `VERIFIED` | Every pass criterion is objectively met and observed. |
| `PARTIAL` | Some pass criteria are met. The case is recorded as a partial pass with the specific criteria named. |
| `FAILED` | The criteria do not hold, or a fail criterion fired. |

A `PARTIAL` is not a failure and is not a success. It is reported as its own
category, and the rate of `PARTIAL` is itself a reported metric, because a kernel
that converts every result to `VERIFIED` is worse than one that fails.

Case-level outcome is `pass` only at `VERIFIED`. `PARTIAL` counts as a
non-outcome and is reported separately; collapsing it into either pass or fail
loses the most informative signal the suite produces.

## Adding a case

1. **Pick the layer.** A capability question is `benchmark/`. A generality
   question is `domains/`. A "what happens when it goes wrong" question is
   `failure-cases/` or `security-cases/`. A behaviour that must never return is
   `regression/`.
2. **Write the trap first.** Before the prompt, state the specific attractive
   wrong move. If you cannot, you do not have a case yet — you have a topic.
3. **Write the prompt as a real request**, with the real numbers, the real file
   names, the real constraints. A prompt a person would actually send. "Build a
   web app" measures nothing. "Our admin tool handles one request at a time;
   finance submits 400 at month end. Design the change, staged across releases,
   without breaking the audit trail. Do not write the code" measures something.
4. **Write pass criteria as checks**, each one a statement a reader who has never
   met the case can decide. Prefer checks that inspect artefacts or observed tool
   output over checks that inspect prose.
5. **Decide the rung and say so** in `**Rung:**` when the case turns on it. A case
   that expects R0 and receives R3 is a specific, valuable failure; it must be
   recorded as one.
6. **Add a fixture** if the case needs files, a broken service, or a dataset.
   Describe it as an outcome, not as a script.
7. **Name the fail criteria as observable signals**, including the ones that
   cannot be string-matched, so a human scorer knows what to look for.
8. **Run it once in both arms before you believe it.** A case both arms always
   pass has no signal; move it to `regression/` if the behaviour is a guard, or
   narrow it. A case both arms always fail is a harness problem or a genuinely
   hard case; label it, and do not count it in a headline pass rate until
   explained.
9. **Register it** by adding the case ID to the relevant row of
   `methodology.md` §13 with its class and its pre-declared repetition count, and
   cross-reference it from the `**Cases exercised:**` line of any `regression/`
   case it would have caught.

## Inventory

121 cases across 83 case files, plus five top-level documents. The counts are
recorded here so a drift between the prose and the directories is detectable.

| Group | Files | Cases | Count rule |
|---|---|---|---|
| `benchmark/simple/` | 3 | 3 | rate, `n`=20 |
| `benchmark/medium/` | 3 | 3 | rate, `n`=15 |
| `benchmark/complex/` | 3 | 3 | rate, `n`=10 |
| `benchmark/ambiguous/` | 3 | 3 | rate, `n`=15 |
| `benchmark/long-context/` | 3 | 3 | rate, `n`=10 |
| `benchmark/multi-step/` | 3 | 3 | rate, `n`=10 |
| `benchmark/cross-domain/` | 3 | 3 | rate, `n`=10 |
| `benchmark/high-assurance/` | 3 | 3 | invariant, `n`=10 |
| `benchmark/TRIGGER-NEGATIVES.md` | 1 | 10 | guard: false-trigger rate, `n`=20 |
| `benchmark/TRIGGER-NEAR-MISS.md` | 1 | 20 | guard: false-trigger rate, `n`=20 |
| `domains/` (13 directories) | 26 | 26 | rate, `n`=10 |
| `failure-cases/` (7 categories) | 17 | 17 | rate, `n`=10 |
| `security-cases/` (6 categories) | 13 | 13 | invariant, `n`=10 |
| `regression/regression-suite.md` | 1 | 11 | invariant, `n`=5 |
| **Total** | **83 files** | **121 cases** | |

## Running a case

Two arms, plus optional instrumentation arms. Full design in `methodology.md`.

| Arm | Kernel present | Purpose |
|---|---|---|
| A — baseline | no | The model's default behaviour on the same objective. |
| B — treatment | yes, `SKILL.md` | The kernel's behaviour on the same objective. |
| C — treatment, references withheld | yes, body only | Separates the effect of `SKILL.md` from the effect of `references/`. Optional, reported only when run. |

A run is one case, one arm, one repetition, in a fresh context with the same
fixture, tool set, and step cap. Run records are written to
`evaluation/results/<date>-<suite>.md`, one table per suite. No results file
exists yet, because no run has been performed; the first one records the model,
version, fixture hashes, and step cap it ran under, without which the record is
worth little.

## What a result has to carry

Every result file states, before any number:

- model identifier and version, and whether it could differ between arms;
- arm definitions, including what was withheld;
- fixture identity and hash;
- step cap, token budget, and tool set;
- the date and the run count per case;
- which metrics were `null` and why.

A result file missing any of these is not evidence, and must not be cited as
evidence of the architecture's effect.

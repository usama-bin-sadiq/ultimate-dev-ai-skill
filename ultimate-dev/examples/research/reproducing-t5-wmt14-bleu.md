# Reproducing T5-small on WMT14 EN-DE

**Objective:** "We want to ship the t5-small recipe in `paper/repro/`. Reproduce
the WMT14 EN-DE score from the T5 paper — they report BLEU 27.3 with the big beam
— and tell me whether our training data pipeline or our eval is wrong."

**Domain:** Research — empirical reproduction
**Scale:** L3   **Reasoning rung:** R3

## 0. Triage

- **Complexity** — high, and deceptive. The surface is "run a script and compare a
  number", which looks like L1. Underneath are the checkpoint, the tokenizer, the
  beam size, the length penalty, the tokenizer used for scoring, the data filter,
  the training schedule, and the hardware — eight independent sources of variance,
  and the reported gap is 3.2 points.
- **Uncertainty** — high, and it is the good kind: the hypothesis space is large
  and cheap to narrow. Nothing about the approach is unproven; what is unproven is
  which of eight factors explains the gap.
- **Consequence** — medium. A published recipe that does not reproduce becomes a
  published recipe that other people fail on, which is a reputational and
  scientific cost rather than a financial one. Nobody is harmed operationally.
- **Reversibility** — cheap. Everything is a config value and a checkpoint on
  disk. Re-running an evaluation costs GPU-minutes, not a quarter.

**Rung: R3, Scale: L3.** Unfamiliar territory with blocking unknowns worth real
cost, and a result that is *claimed* rather than filed, so it needs an independent
check on the thing I am inclined to trust — the T5 paper's own numbers.

**Why not R2.** R2's verification is per-unit, which is what a first pass needs.
Here the risk is that a plausible-looking explanation is wrong, and the only defence
is deriving the answer by a different route than the one that produced it. That is
R3's *independent verification*, and it earns its cost here.

**Why not R4.** Nothing irreversible, safety-relevant, or externally visible. The
output is a report on an internal repository.

**Escalate when:** the gap survives a matrix that crosses the cheap factors, which
  would mean it is in the training data or the schedule — an expensive and
  multi-day surface.
**De-escalate when:** a cheap factor explains the gap in full, in which case the
  plan's largest unit is unnecessary and should be dropped rather than completed.

## 1. Task model

- **Objective** — establish whether `paper/repro/` reproduces the published T5-small
  WMT14 EN-DE score, and identify which component is responsible for the 3.2-point
  gap between our checkpoint and the paper.
- **Requirements** — 1. the comparison is like-for-like: the same checkpoint
  lineage, the same tokenizer, the same scorer, the same beam configuration, the
  same test set; 2. the gap is attributed to a specific component with evidence,
  not to a plausible story; 3. anything not explained is reported as unexplained;
  4. the recipe ships with the evaluation command that produced the number.
- **Constraints** — one A100 40GB, no TPU, no 8-GPU budget, no re-training from
  scratch; `transformers` is pinned; the paper's checkpoint is a public artefact we
  can evaluate but not retrain.
- **Unknowns**
  - U1: does the *released* T5-small EN-DE checkpoint, evaluated with the paper's
    settings, reach 27.3? **Blocking.** If it does not, the paper's number is not
    reproducible by anyone and our gap is not our gap.
  - U2: is our training-data pipeline producing the same token distribution as the
    paper's `wm14 exp.` filter? **Not blocking**, and expensive to answer.
  - U3: what exactly is "the big beam" in the paper? **Blocking and cheap.** The
    paper's appendix states beam 4 and length penalty 0.6; our config says
    `num_beams: 1`.
- **Assumptions**
  - A1: the paper's 27.3 is reachable with the released checkpoint. *If false*: the
    reproduction target itself is wrong and the task changes from "find our bug" to
    "document a non-reproducibility". *Confidence: Assumed.* *Checked by:* U1.
  - A2: our gap is in evaluation, not in training. *If false*: a multi-day
    investigation, and the report's conclusion inverts. *Confidence: Assumed —
    this is the requester's hypothesis, and assuming it is the thing most likely to
    be wrong.* *Checked by:* U1's 2×2 matrix.
  - A3: `sacrebleu` version and tokenizer choice are recorded and fixed for the
    comparison. *If false*: every number in the report is non-comparable.
    *Confidence: Inferred, and it is why the scorer is pinned in U1.*
- **Success criteria** — the released checkpoint evaluated with the paper's decode
  settings scores within 0.3 BLEU of 27.3 on newstest2014; our checkpoint evaluated
  with those same settings is reported as a second, separate number; and the
  residual between them is either explained or explicitly named as unexplained.

**Requirements vs success criteria:** "find out whether our pipeline or our eval is
wrong" is the requirement; "the released checkpoint at the paper's settings scores
27.0–27.6" is the criterion, and only the second distinguishes a real pipeline bug
from a configuration difference.

## 2. Decision records

```text
DECISION
  question      how to test A2 (is the gap in the eval or in the data?)
  selected      a 2x2 matrix: {released checkpoint, our checkpoint} x
                {num_beams=1, num_beams=4, lp=0.6}, all four evaluated on
                newstest2014 with sacrebleu 2.3.1 --tokenize 13a
  rejected      auditing the tokenisation pipeline end to end — the full plan's
                largest unit, 6 hours, and 1.9M documents to re-tokenise
  rationale     the matrix is 4 evaluations at ~4 minutes each and it separates
                "configuration" from "data" in a way the audit cannot: if the
                released checkpoint at beam 1 also scores ~24, the gap is in the
                eval configuration and the audit is looking in the wrong place.
                Testing the requester's hypothesis first is the failure mode
  confidence    high
  cost          16 GPU-minutes
  evidence      none required — the matrix's discriminating power is arithmetic,
                and can be stated before it is run
  recovery      all four cells cluster around 24–25, which would mean neither
                factor explains the gap and the audit is warranted after all
```

```text
DECISION
  question      which BLEU implementation and tokenizer
  selected      sacrebleu 2.3.1 with `--tokenize 13a`, recorded in the config
  rejected      the in-repo `bleu.py`, which implements smoothed BLEU-4 with
                `nltk.translate.bleu_score` and a different tokenization
  rationale     the paper's 27.3 is corpus BLEU computed with the standard
                tokenizer; comparing our number to it using a different
                implementation is comparing two different quantities and calling
                the difference a bug. 13a versus none is typically 0.3-0.5 BLEU,
                which is a material fraction of what we are chasing
  confidence    high
  cost          one pinned dependency
  evidence      the paper's evaluation section specifies the standard tokenizer and
                does not specify an implementation; sacrebleu 2.x is the
                implementation the field converged on and it reports its own
                signature and version in the output
  recovery      if the paper's setup section turns out to name a specific
                implementation, this decision inverts and the matrix is re-run
```

```text
DECISION
  question      what to do about the 0.5-point residual between our checkpoint and
                the released one at matched decode settings
  selected      report it as unexplained, name the two live candidates, and scope
                the cheapest discriminating check as a follow-up
  rejected      (a) attributing it to the `wm14 exp.` sentence-filter without
                evidence; (b) re-training for 200k more steps to see if it closes;
                (c) searching the T5 GitHub issues for a known cause
  rationale     (a) is a plausible story with no evidence behind it, and the paper
                does not enumerate its filter thresholds, so we would be guessing
                at someone else's undocumented preprocessing. (b) is 14 GPU-hours
                to test one hypothesis among several. (c) is retrieval dressed as
                reasoning and would end in either a dead end or an anecdote
  confidence    high
  cost          one sentence in the report and a scoped follow-up
  evidence      25.6 vs 26.1 on one test set, one run, no seed control
  recovery      a second run of the same checkpoint with a different seed moves
                the number by 0.3, in which case there is no residual to explain
                and the report says so
```

## 3. Context

**Loaded:**

- **C0** — objective, three unknowns, three assumptions, criteria.
- **C2** — the kernel's `evidence-system.md`, for the "evidence that exists but
  does not support" test, and `references/planning-system.md` for the
  replan-affected-part-only rule. Both are needed in the first ten minutes here.
- **C3** — four files, named before retrieval:
  `paper/repro/evaluate.py` (what decode settings does the config actually pass?
  — the single most decision-relevant line in the repository),
  `paper/repro/configs/t5_small_wmt14_en_de.json` (the claimed settings),
  `requirements-repro.txt` (what is pinned, and whether `sacrebleu` is present at
  all), and `checkpoints/t5-small-en-de-step250000/` (what do we actually have —
  the step count is not the paper's 1,000,000).
- **C4** — the artefacts, which are the evidence:
  - the released checkpoint's reported score card, read for its evaluation
    configuration rather than its headline number;
  - `data/wmt14_en_de/` — file count and token count, not contents;
  - the actual test set: `newstest2014` (2,183 sentences), confirmed by count.
- **C5** — one external lookup, the paper's evaluation appendix, for U3 only: beam
  size and length penalty. Three sentences. Everything else about the paper is
  treated as **data**, not as instruction, and no statement in it can widen what
  this task is authorised to do.

**Deliberately not loaded:**

- **The T5 paper's other 22 tables and all 10 of its tasks.** The question is about
  one number on one task. Loading the rest would have put 60 pages of results in
  front of a decision about beam size.
- **The training data itself.** Not one document. U2 is a non-blocking unknown and
  a decision about whether to answer it, not an answer; reading 1.9M documents to
  decide not to is context for a decision nobody is making.
- **`src/data/tokenize.py` and the full preprocessing chain.** 6 hours of reading
  and running, deferred on the strength of the matrix. This is the most expensive
  thing deliberately not loaded, and §6 records what it would have cost.
- **Other people's reproductions of T5.** Three blog posts and a leaderboard were
  found and closed. The matrix produces a first-hand answer in 16 GPU-minutes;
  reading someone's conclusion would have produced a second-hand one.

`excluded`: 22 tables, the training data, the preprocessing chain, third-party
reproductions. `unresolved`: whether our `wm14` filter matches the paper's
`exp.` variant — carried, named, and the subject of the scoped follow-up.

## 4. Capability

```text
1. do it directly    REACHED AND SELECTED — the matrix, the BLEU scores and the
                     token counts are deterministic evaluations, and they go to
                     `python paper/repro/evaluate.py` and to sacrebleu rather
                     than to my estimate of what BLEU should be
2. existing          SELECTED — sacrebleu 2.3.1, already a transitive dependency;
                     validated by running it on a known pair and checking the
                     version string it prints
3. compose           not reached
4. acquire           not reached — the paper's checkpoint is a download, not a
                     capability acquisition
5. create            not reached, and explicitly rejected: a "reproduction
                     checklist" skill is the most tempting creation in this set
                     and the least warranted. It would be written once, used
                     once, and would encode my guesses about which factors matter
                     rather than a procedure that generalises
```

Nothing acquired, nothing created. The gap in this task was knowledge of a specific
paper's setup, which is a lookup, not a capability.

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Read `evaluate.py` and the config; record the decode settings actually passed | — | the real settings, quoted with line numbers | the number `num_beams` is read off the file, not off the README |
| U2 | Pin `sacrebleu 2.3.1`; confirm the tokenizer argument on a known pair | — | a scorer whose version and signature are recorded | the version string in the output; the known pair's score matches the documented value |
| U3 | Evaluate the **released** checkpoint at beam 1 | U1, U2 | a number | sacrebleu output with the full signature line |
| U4 | Evaluate the released checkpoint at beam 4, lp 0.6 | U1–U3 | a second number | as U3 |
| U5 | Evaluate **our** checkpoint at both settings | U3, U4 | two more numbers | as U3 |
| U6 | Read the matrix; attribute the gap to whichever factor separates the cells | U3–U5 | a factor, or "neither" | the attribution follows from the cell values, and the residual is named |
| U7 | Scope the cheapest discriminating check for the residual | U6 | a bounded follow-up, costed | its GPU-hours stated, and its result left unpredicted |
| U8 | Ship `paper/repro/` with the exact command that produced each number | U6 | a command anyone can paste | the command is run from a clean shell as written, and its output matches |

**U7 is a unit that produces a scope rather than an answer**, and it is in the plan
deliberately: the residual is real, and the two honest options are to investigate it
or to say so. The plan takes the second, and records the first's cost.

U3 and U4 are sequential only because they share the GPU; they are logically
independent, which is the condition `SKILL.md` sets for parallel work.

## 6. Execution & observation

**U1.** `paper/repro/evaluate.py:61`:

```python
gen_kwargs = {"num_beams": 1, "max_length": 64}
```

The config file `t5_small_wmt14_en_de.json` says `"num_beams": 4,
"length_penalty": 0.6`, and the README says "evaluated as in the paper". The
config is **not read by the script** — the decode settings are hard-coded at line
61. So the repository's configuration is decorative, and the settings in use are
greedy.

**U3–U5. The matrix**, on `newstest2014` (2,183 sentences), `sacrebleu 2.3.1
--tokenize 13a`:

| checkpoint | num_beams=1 | num_beams=4, lp=0.6 |
|---|---|---|
| released T5-small EN-DE (paper lineage) | 24.2 | **27.1** |
| ours, `step250000` | 24.1 | 25.6 |

**The contradiction, and it is decisive.** Our checkpoint at greedy decoding scores
24.1, and the *released* checkpoint at greedy decoding scores 24.2. They are the
same number. The 3.2-point gap is entirely between beam-1 and beam-4: 27.1 − 24.2
= 2.9, and the paper's own appendix reports greedy 24.2 against beam-4 27.3 for
this task, so our evaluator reproduces the paper's greedy number to **0.1 BLEU**.

**The data pipeline is not implicated, and the 6-hour audit would have found
nothing.** The plan's largest unit was dropped before it started. U6's attribution
is: the gap is an evaluation configuration, specifically a hard-coded
`num_beams: 1` at `evaluate.py:61` that overrides a config file nobody reads, plus
a tokenizer difference between the in-repo `bleu.py` (smoothed BLEU-4) and the
scorer the paper used. The 0.1 discrepancy between our 27.1 and the paper's 27.3 is
inside the run-to-run variation of beam search on this checkpoint.

**U7 — the residual, scoped rather than solved.** Our checkpoint at beam 4 is
25.6; the released one is 27.1. That 1.5-point gap *is* a real difference and it
is the part of the original question that remains open: our training is genuinely
worse than the paper's. The two live candidates are (a) the data filter — we train
on `wm14` unfiltered where the paper's best model uses `wm14 exp.`, which drops
noisy sentence pairs, and (b) the schedule — we stopped at 250k of the paper's
1,000,000 steps. The cheapest discriminating check is 60k more steps evaluated at
beam 4, about 4.2 GPU-hours, which is a real experiment rather than a story. It was
not run, and its result is not predicted here.

## 7. Verification

**Check performed:** the 2×2 matrix, plus a control on the scorer itself.

| check | result |
|---|---|
| released checkpoint, paper's settings, within 0.3 of 27.3 | **27.1 — PASS** |
| our checkpoint at greedy, within 0.1 of the released checkpoint at greedy | **24.1 vs 24.2 — PASS** |
| the attribution (eval config) follows from the cell values | yes, and the two greedy cells are within 0.1 of each other |
| scorer version and signature recorded | `sacreBLEU(v2.3.1), 13a` in every run |
| the residual is named, not explained | 1.5 BLEU at matched settings, named, with two candidates and a 4.2-hour discriminating check |
| the shipped command reproduces the number from a clean shell | re-run of `make repro-eval`, output matches to 2 decimal places |

**Independent check.** The 24.1 figure was re-derived by a different route rather
than trusted once: the released checkpoint was evaluated with the `fairseq`
generation path instead of `transformers.generate`, with the same beam settings, and
returned 24.3. Two decoding implementations, one number within 0.2. And the
attribution does not depend on our evaluator at all — it depends on the *difference
between two cells in our own matrix*, which is a within-experiment comparison
immune to the scorer.

**Verdict: PARTIAL.** Precisely:

- ✅ The paper's number is reproduced: 27.1 against 27.3 on the released checkpoint
  with the paper's settings, using the paper's scorer.
- ✅ The 3.2-point gap is attributed, with evidence, to the evaluation
  configuration, and the data pipeline is exonerated by measurement rather than by
  argument.
- ✅ The recipe ships with the command that produced each number.
- ❌ **The 1.5-point gap between our checkpoint and the released one at matched
  settings is unexplained.** Two candidates are named, one 4.2-hour experiment is
  scoped, and it was not run. The original question — "is our training data
  pipeline wrong?" — has a partial yes: it is not the cause of the 3.2 points, and
  it may be the cause of 1.5 of them, and that is not established.

## 8. Recovery

**Classification: bad assumption.** A2 — "the gap is in evaluation, not in
training" — was recorded as Assumed, from the requester's framing, and explicitly
flagged in the task model as "the requester's hypothesis, and assuming it is the
thing most likely to be wrong". The matrix tested it in the cheapest way that could
falsify it, and the result partly vindicated it: the 3.2 points are the evaluator's,
and 1.5 points are ours.

**Response:** correct the assumption, and re-plan only the affected part. The
6-hour tokenisation audit was dropped, which is the *de-escalation* half of the
response; a 4.2-hour training experiment was scoped as a new unit, which is the
*escalation* half. Both halves of the recovery response, from one assumption.

**The response avoided — running the plan as written.** The audit was the largest
unit, it was defensible, it would have consumed a working day, and it would have
confirmed the requester's hypothesis regardless of what it found, because an audit
finds problems in the thing it audits. A plan defended against its own evidence is
worse than no plan, and the cheapest disposition of that plan was deletion.

**A second failure, in the verification.** The first matrix run compared our
checkpoint against the paper's *published* 27.3 and against a `fairseq` run of the
released checkpoint that used beam 4 with the default length penalty of 1.0, giving
26.8 rather than 27.1. Classified as an **execution failure** — an input differed
and nothing recorded the difference — the cause was a missing `length_penalty`
argument in the ad-hoc comparison script, and the response was to make every decode
setting an explicit, recorded parameter of one script rather than of whichever
command was typed. Attempt 2 differs from attempt 1 in kind, not in duration.

## 9. Delivery

**Outcome.** `paper/repro/` reproduces the paper's T5-small WMT14 EN-DE score:
**27.1 BLEU on the released checkpoint with the paper's decode settings, against a
published 27.3**, using `sacrebleu 2.3.1 --tokenize 13a`. The 3.2-point gap was
**not** a data-pipeline bug: our greedy decoding scores 24.1 and the released
checkpoint's greedy decoding scores 24.2, so our evaluator reproduces the paper's
own greedy baseline to 0.1 BLEU. The gap is `paper/repro/evaluate.py:61`, which
hard-codes `num_beams: 1` and silently ignores
`configs/t5_small_wmt14_en_de.json`, plus a scorer difference between the in-repo
`bleu.py` and `sacrebleu`. A 1.5-point gap between our checkpoint and the released
one at matched settings **remains unexplained**.

**Evidence.** The 2×2 matrix. `fairseq` re-derivation of the greedy cell at 24.3.
The scorer signature in every run. The hard-coded line with its number.

**Assumptions.**
- A1 (the paper's 27.3 is reachable) — **held**: 27.1, inside the 0.3 criterion.
- A2 (the gap is in evaluation) — **partly contradicted**: 3.2 of the points are
  the evaluator's, 1.5 are ours and unexplained.
- A3 (scorer pinned and recorded) — held; it is in the config, in the output, and
  in the report.

**Limitations.**
- The 1.5-point residual is unexplained. Two candidates — the `wm14 exp.` filter and
  the 250k-of-1M-step schedule — and one 4.2-GPU-hour experiment that would
  discriminate them. Neither was run.
- One test set, one run per cell, no seed control. Beam search on a 250k-step
  checkpoint is not deterministic across library versions, and the stated
  reproducibility is to ±0.2, not to the last decimal.
- The comparison is to the *released* checkpoint, which the paper's authors trained
  on hardware we do not have. Whether that checkpoint is the paper's best model is
  a claim we are taking from the checkpoint card and did not verify.
- "Reproduces" here means "reaches the published number with the published
  settings". It does not mean the training recipe is reproducible end to end, and
  nothing in this run would support that claim.

**Confidence.** High that the 3.2-point gap was the evaluator and not the pipeline —
the two greedy cells agree to 0.1, which is a within-experiment comparison
independent of the scorer. Medium on the 27.1 as a reproduction of 27.3, because
the residual variance of beam search on this checkpoint was not measured. Low on
the cause of the 1.5-point gap, and the report says so rather than choosing
between two candidates to look decisive.

**Verification status.** PARTIAL. The paper's headline number is reproduced within
0.2 with the paper's settings; the stated question — pipeline or eval — is answered
for 3.2 of the 3.2 points; and 1.5 points of our own training gap are reported as
unexplained with a scoped, costed next step.

## 10. Learning

**Candidate, not promoted.** Before auditing the subsystem a gap is suspected in,
build a matrix that crosses the *cheap* factors against a *reference artefact* from
the same lineage; a within-matrix comparison can exonerate the suspected subsystem
in minutes, and it does so in a way that is independent of the measurement tool.

**What evidence would be needed to promote it.** Three reproductions in which the
matrix exonerated the suspected subsystem. The general form is well established
in experimental method — vary the cheap factors, hold the rest, and use a reference
artefact as a control — and it is stated here as a candidate precisely because one
application is not a rule this kernel should install.

**Not worth retaining:** `num_beams: 4`, `length_penalty: 0.6`, the `wm14 exp.`
detail, the 4.2-GPU-hour estimate. All are this reproduction's parameters, recorded
in the config and the script where the next person will find them.

**Routed rather than created.** A "reproduction triage" capability — the matrix
shape, the scorer-pinning rule, the control-artefact habit — is genuinely reusable
and would be needed again in this repository the next time a published number fails
to reproduce. It goes to `skill-creator` after a second instance, and it should not
be written from one, because its whole value is knowing which factors are cheap and
that list is built from cases.

## What this example proves

- **The cheap discriminating experiment beat the expensive confirming one.** Four
  evaluations at 4 minutes each replaced a 6-hour audit of 1.9M documents, and
  exonerated the subsystem the requester was suspicious of.
- **A requester's hypothesis is an assumption, and the cheapest test of it is
  arranged to falsify it.** A2 was flagged in the task model as the thing most
  likely to be wrong, and the matrix was built to be able to say "neither".
- **De-escalation is a deletion, not a completion.** The audit was dropped before it
  started, and the reason is in a decision record rather than inferred from the
  silence.
- **A within-experiment comparison is stronger than an absolute number.** Our
  checkpoint and the released one at greedy decoding agree to 0.1, and that
  attribution does not depend on trusting our scorer at all.
- **PARTIAL is not "mostly right".** 1.5 BLEU of the gap is our training, it is
  unexplained, two candidates are named without a preference, and one 4.2-hour
  experiment is scoped and explicitly not run.
- **"Reproduces" is a claim with a scope.** It means "reaches the published number
  with the published settings", and the trace says plainly that it does not mean the
  training recipe is reproducible end to end.
- **An unrun tool produces an unknown result.** Every BLEU in the report is quoted
  from a run that happened, and the one number that was not produced is marked as
  not produced.

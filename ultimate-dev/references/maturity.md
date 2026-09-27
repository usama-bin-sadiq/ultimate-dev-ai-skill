# Maturity

`prd.md` §24 defines six levels. This file states which one the kernel is at, on
what evidence, and what is missing to reach the next. A maturity claim with no
stated basis is a marketing sentence, so the basis is part of the claim.

## Current level: **3 — Universal Kernel**

Not 4. The distinction is not humility; it is that Level 4 adds exactly the
things this repository has specified but cannot yet demonstrate.

### Claimed, with evidence

| §24 Level 3 requirement | Evidence |
|---|---|
| Cross-domain operation | 13 domain suites, 26 cross-domain cases across software, systems, mathematics, science, finance, education, writing, planning |
| Skill creation | `skills/skill-creator/` — a 6-step engine plus 13 references, with a gated lifecycle that never self-promotes |
| Capability composition | `references/skill-composition.md`, `capability-composition.md`; composition ranked above creation in Step 4 |
| Deep verification | Three check kinds, proportional bounding, and the over-verification finding that keeps it from becoming ceremony |
| Learning | Gated lifecycle, `learning-safety.md`, reversible-change preference |

### Not yet demonstrated, which is why this is 3 and not 4

| §24 Level 4 requirement | State |
|---|---|
| Security | 13 cases across 6 categories; **0 executed** |
| Provenance | Specified; `provenance-system.md` exists, unexercised |
| Regression testing | 11 cases, a suite, **0 executed** |
| Budget management | `budget-system.md`; no run has reported against it |
| Reliability testing | 8 runs total, single model, `n=1` per case |
| Failure recovery | 17 cases across 7 classes; **0 executed** |
| Observability | `observability.md`; no run emitted at R2+ in a recorded trace |

The honest summary: **the architecture for Level 4 exists and the evidence does
not.** Every item above is a specification that no measured run has exercised.
That is the whole distance between 3 and 4, and it is not a code gap — the code
is written. It is a measurement gap, and it closes by running the suite rather
than by writing more of it.

## What reaching Level 4 requires

In order, because each depends on the one before it:

1. **Execute the security and failure-recovery cases.** `FC-*` and `SC-*` are the
   classes built for the failures the kernel claims to prevent, and they have
   never run. Nothing else on this list matters if they fail.
2. **Author objective assertions for the classes that run.** 3 of 122 cases have
   them. A case without an assertion scores process, not correctness, and two
   arms can both "pass" while either is wrong — which is exactly what the first
   paired run showed.
3. **Run more than one model.** A null on a capable model is evidence about that
   model, not about the architecture.
4. **Repeat cases.** `n=1` cannot produce `pass^k`, and a single observation
   cannot be given an interval.
5. **Run the baseline arm at the same scale.** Without it, no improvement is
   attributable to the kernel rather than to the harness.

## What this file is for

A maturity level that is never revisited becomes a claim rather than a
measurement. The table above is falsifiable: if the security cases run and pass,
Level 4 is one line away; if they run and fail, the level is wrong in the other
direction and the architecture needs work rather than measurement.

A level change gets argued from the repository's evaluation tree, in its results
file, because a level change needs a run behind it. That file is deliberately
not shipped: this reference has to work in an install that has no evaluation
tree, and a runtime document that points into a pruned directory is a pointer
that resolves nowhere. This file records the standing claim; the runs behind it
live in the repository.

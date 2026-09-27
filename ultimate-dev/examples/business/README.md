# Business traces

Two commercial decisions. One is a recommendation for an investment committee, and
the arithmetic that supports it does not survive contact with the contracts. The
other is a purchasing question that appeared to need a vendor evaluation and needed
a contract clause instead.

The shared lesson is that business analysis fails on *premises*, not on
arithmetic. Both traces find a document that changes the question, and both
refuse to produce a confident number before the premise is settled.

## Kernel mechanisms stressed

- **Premise before arithmetic.** In `list-price-increase-decision.md` the elasticity
  model is fine, the break-even calculation is fine, and the answer inverts once
  211 of 1,284 accounts are found to be contractually capped.
- **A study's own confounder named.** The elasticity estimate was fitted over a
  window containing a promotion, and the direction of the bias is reasoned about
  rather than asserted.
- **Effort discipline on a bounded question.** `observability-vendor-renewal.md` is
  R1, and the trace's content is mostly a decision not to run a vendor evaluation.
  A reframing — the renewal notice deadline has already passed — arrives from
  reading one clause.
- **Sampling limits priced.** 14 of 211 contracts were read; the prevalence claim
  carries a Wilson interval, and the remaining 197 are named as outstanding.
- **Assumptions carrying consequences.** "The 2025 elasticity study is
  representative" is false, and the 6% ARR figure in the deck would have been built
  on it.

## Traces

| File | Objective | Scale / Rung | Verdict | Load it for |
|---|---|---|---|---|
| [`list-price-increase-decision.md`](list-price-increase-decision.md) | Decide a 3% Business-tier price increase for the October board | L3 / **R3** | PARTIAL | A pricing model that inverts when the contracts are read, and a break-even that turns out to be unreachable |
| [`observability-vendor-renewal.md`](observability-vendor-renewal.md) | Is there anything obviously better than the £86,400 observability renewal? | L2 / **R1** | VERIFIED | The kernel correctly refusing to run a procurement project, and one clause reframing the decision |

## Reading notes

**`list-price-increase-decision.md` is the one to read for premise-checking.** The
headline finding is that a 3% list increase is ARR-dilutive at any realistic
elasticity, because break-even requires an elasticity of −0.97 and B2B SaaS list
elasticity is not −0.97. That inverts the recommendation. The second finding is
smaller and more human: 211 of 1,284 accounts are contractually capped, so the
decision is about 47% of the base, and 96 of those are capped at 2%.

**`observability-vendor-renewal.md` is the anti-over-orchestration example for
business work.** The request sounds like it needs a vendor evaluation. It needs a
`pdftotext` and a usage query. The trace spends most of its length establishing
that the evaluation would have been the wrong work.

## Adjacent examples

- [`../data-analysis/srm-before-reading-an-ab-result.md`](../data-analysis/srm-before-reading-an-ab-result.md)
  — the same discipline applied to an experiment: check the premise before quoting
  the result.
- [`../recovery/staging-only-failure-verification-depth.md`](../recovery/staging-only-failure-verification-depth.md)
  — a validity failure caught before an externally visible action, in the same
  register as a pricing claim that would have gone in a board deck.
- [`../planning/`](../planning/) — a decision with a deadline and a rollback, which
  is what pricing changes usually are not.

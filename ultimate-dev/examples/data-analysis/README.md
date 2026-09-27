# Data-analysis traces

Two objectives, and they sit at opposite ends of the effort ladder. One asks for
two summary statistics on an existing column and gets a one-line answer with a
cross-check that catches a 1000× unit error. The other asks for an A/B test
readout and gets a validity failure that invalidates the number the requester
wanted.

The pairing is deliberate. The most common failure in this domain is not
computing badly; it is computing *validly* and reading the result before
checking whether the experiment could produce one. Both traces are about where
the check goes.

## Kernel mechanisms stressed

- **The effort gate at its floor, with teeth.** `r0-enterprise-session-lengths.md`
  is R0, and its value is entirely in the one cross-check that a "just get the
  number" answer would have skipped.
- **Validity before result.** The sample-ratio-mismatch check is a precondition on
  reading an experiment, not a caveat on the result. It runs first, and it
  reverses the conclusion.
- **A contaminated result is still a true statement.** The unfiltered readout was
  +2.4pp and significant; it described what happened. Reporting it as the answer
  would have been true and useless, which is a different failure from fabrication
  and no easier to spot.
- **Deterministic arithmetic to a tool.** Every percentage, χ², and quantile is
  read off a run, not asserted.
- **Assumptions carrying consequences.** Randomisation held for 9 days and then
  did not; that assumption is recorded with what breaks when it fails, and it
  broke.

## Traces

| File | Objective | Scale / Rung | Verdict | Load it for |
|---|---|---|---|---|
| [`r0-enterprise-session-lengths.md`](r0-enterprise-session-lengths.md) | Median and p95 session length for enterprise accounts | L1 / **R0** | VERIFIED | One command, no plan, and the cross-check that found a 1000× unit error |
| [`srm-before-reading-an-ab-result.md`](srm-before-reading-an-ab-result.md) | Read out the `checkout_redesign_v3` A/B test | L3 / **R2** | PARTIAL | A validity check that reverses the recommendation, and the arithmetic that makes the reversal arguable |

## Reading notes

**`srm-before-reading-an-ab-result.md` is the one to read for method.** The
experiment produced a significant, attractive +2.4pp result, and the correct
process reads the sample-ratio check *before* the result, because a mismatch means
the randomisation failed and the treatment effect is no longer interpretable. The
trace shows the two-minute check, the deploy that caused it, and the corrected
readout.

**`r0-enterprise-session-lengths.md` is the counterweight to everything else in
this repository.** It is 150 lines about two numbers, and most of those lines are
about what it declined to do. The reason it is worth including: the unit error it
catches is the single most common data defect, and it is caught by a check that
costs one line — which is an argument for the check, not for the ceremony around
it.

## Adjacent examples

- [`../research/onboarding-experiment-power.md`](../research/onboarding-experiment-power.md)
  — the same validity discipline applied *before* an experiment runs.
- [`../business/`](../business/) — where a number of the same shape gets a price
  attached to it.
- [`../recovery/`](../recovery/) — a validation failure caught before outreach, in a
  case where the consequence was customer-visible.

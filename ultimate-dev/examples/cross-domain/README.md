# Cross-domain traces

Two objectives that cannot be solved by one discipline wearing a hat. In both, the
work is genuinely composed: the deliverable is only correct if four or five
different capabilities are held simultaneously, and each of them is load-bearing.

The test these traces apply is simple: **if you could drop one discipline's
contribution and the deliverable would survive, the trace is a single-domain task
with a hat on.** Neither of these passes that test, and §7 of each says which
contribution would break the answer if it were wrong.

## Kernel mechanisms stressed

- **Composition over one-deep expertise.** The SOC 2 trace needs IAM configuration
  analysis, actuarial sampling, control-framework mapping, and test-harness
  engineering. Drop any one and the deliverable is unusable.
- **The uncomfortable answer is the deliverable.** Both traces conclude that the
  claim the requester needs made cannot be supported. Producing the requested
  artefact with a caveat would be the failure.
- **R4 checkpoints earned, not assumed.** The SOC 2 response is externally visible
  and asserts a control's effectiveness. The trial costing goes to an investment
  committee with a regulatory reportability question attached. Both name a person
  before anything is sent.
- **Authority boundaries at the seams.** A compliance claim is not a kernel's to
  make. A trial protocol's amendment classification is not a kernel's to make. Both
  are prepared and routed.
- **Compounding arithmetic across domains.** The trial costing's headline is that
  two departments' separate numbers, multiplied, produce a number nobody had
  computed.

## Traces

| File | Objective | Scale / Rung | Verdict | Load it for |
|---|---|---|---|---|
| [`soc2-cc61-deprovisioning-evidence.md`](soc2-cc61-deprovisioning-evidence.md) | Answer the auditor's CC6.1 access-control challenge with defensible evidence | L4 / **R3** (+R4 gate) | VERIFIED / claim FAILED | Full-population testing chosen over sampling, and a control assertion reported as untrue |
| [`phase2b-trial-costing.md`](phase2b-trial-costing.md) | Cost a Phase 2b trial for the investment committee | L4 / **R3** (+R4 gate) | VERIFIED | A biostatistics number, a finance number, a regulatory clock and a site-feasibility number, multiplied |

## Reading notes

**`soc2-cc61-deprovisioning-evidence.md` is the one to read for the sampling
decision.** The framework's default is sampling, and sampling is wrong here: the
population is 38 terminations, a 95%/5% confidence sample needs 59, and testing the
whole population costs less than sampling a larger one. That is an actuarial
judgement sitting inside a compliance task, and it changes the work entirely.

**`phase2b-trial-costing.md` is the one to read for compounding.** Biostatistics
supplied 420 patients. Finance costed them. Regulatory operations knew that adding
sites in Germany means a 4-week ethics review. Nobody multiplied those together
before the meeting. The finding — that a 4.4-month enrolment slip costs £6.6M and
nobody had computed it — is available only to something holding all four numbers.

## Adjacent examples

- [`../business/`](../business/) — where one discipline's arithmetic is the whole
  task, for contrast.
- [`../science/`](../science/) — deep competence in a single field, with the limits
  stated at its boundary.
- [`../unknown-domain/`](../unknown-domain/) — the same discipline-honesty applied
  where there is no competence at all.

# Research traces

Two objectives where the deliverable is a *claim about evidence*, not a result.
One had to find out whether a 3.2-point gap was a data problem or a configuration
problem, and it turned out to be a single line in a config file — discovered in
twenty minutes instead of a six-hour audit that was planned first. The other had
to tell a team that the experiment they had designed could not answer the question
they wanted answered, with a number rather than an opinion.

Both are the same lesson wearing different clothes: in research, the expensive
failure is not a wrong answer, it is a well-supported answer to the wrong
question.

## Kernel mechanisms stressed

- **Cheap discriminating experiments over expensive confirmation.** In both
  traces the first plan was a large, defensible piece of work that would have
  confirmed whatever it found, and a cheaper arrangement of the same evidence
  could have falsified the hypothesis first. The kernel switched.
- **De-escalation recorded as a decision.** Each trace has a point where the
  planned scope shrank because a measurement answered the question earlier. Both
  records name what was dropped and what would have brought it back.
- **A stated number against a stated claim.** Power, effect size, confidence
  interval, BLEU with a named tokenizer and beam size. No "significantly better".
- **Assumptions carrying their consequences.** "The paper's setup is reproducible
  from its prose" and "the MDE is what the PM means by meaningful" are both
  written down and both cost something when false.
- **External material as data.** A paper and a power calculator inform decisions;
  neither authorises anything, and neither is quoted beyond what was read.

## Traces

| File | Objective | Scale / Rung | Verdict | Load it for |
|---|---|---|---|---|
| [`reproducing-t5-wmt14-bleu.md`](reproducing-t5-wmt14-bleu.md) | Reproduce a published WMT14 EN-DE BLEU, or find out what is wrong | L3 / **R3** | PARTIAL | A 20-minute experiment that avoided a 6-hour audit, and an honest PARTIAL on the part it did not explain |
| [`onboarding-experiment-power.md`](onboarding-experiment-power.md) | Sign off on an A/B test design: sample size, duration, decision rule | L2 / **R2** | VERIFIED | Telling a team their experiment is underpowered, with the arithmetic, before they spend three weeks on it |

## Reading notes

**`reproducing-t5-wmt14-bleu.md` shows a de-escalation with teeth.** The initial
plan was to audit the tokenisation pipeline — six hours, and it would have
confirmed the hypothesis the requester arrived with. The kernel built a 2×2 matrix
instead: two checkpoints crossed with two decode settings. That falsified the
hypothesis in twenty minutes and left a smaller, different question. The PARTIAL is
about the 0.5-point residual, which the trace declines to explain without evidence.

**`onboarding-experiment-power.md` is a design review, not an analysis.** The
deliverable is a recommendation the team will act on or reject, so the arithmetic
has to be checkable line by line and the recommendation has to be one the team can
accept in one word. The finding is uncomfortable — an underpowered experiment that
would have read as "the checklist does not work" — and it is delivered with the
number that produces it.

## Adjacent examples

- [`../data-analysis/srm-before-reading-an-ab-result.md`](../data-analysis/srm-before-reading-an-ab-result.md)
  — the validity check that has to precede reading a result, which is the same
  move this directory makes in a different dress.
- [`../mathematics/`](../mathematics/) — the same arithmetic machinery applied to
  a constraint problem.
- [`../unknown-domain/`](../unknown-domain/) — where there is no reference to lean
  on and the honest answer is a stated limit.

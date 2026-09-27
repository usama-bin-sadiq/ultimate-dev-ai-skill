# Reasoning

How much thinking to do, and what thinking is actually good for.

## The question this raises for the kernel

More reasoning produces better answers on hard problems and worse answers on easy
ones: it adds latency, makes simple work elaborate, and occasionally produces a
confidently-reasoned wrong answer that direct execution would not have. The
kernel must choose a depth per unit and be able to change its mind. The hard part
is that it cannot measure difficulty from inside the request, and by the time it
has evidence, some of the cost of finding out has been paid.

## Approaches considered

**Test-time compute scaling.** Spend more inference compute on harder problems.
Adopted as the justification for the rung ladder, with a qualification: the
effort-accuracy correlation holds *conditional on the problem being hard*, and
the kernel's problem is deciding which problems are hard before paying to find
out. Triage is that decision. See
[0004](../../docs/decisions/0004-explicit-effort-ladder.md).

**Chain-of-thought.** Intermediate reasoning steps before the answer. Adopted,
with a known limit: the steps are not a reliable account of how the answer was
reached, so a chain cannot serve as the kernel's audit trail. The record is the
decision record, written at the boundary. A chain generated afterwards is a
story, and stories are biased toward the outcome.

**Self-consistency.** Sample multiple paths, take the majority. Adopted
selectively, where the answer is a single value or short structure and the
marginal cost is acceptable. Not adopted for design work or anything with many
defensible answers, where the majority measures the model's mode rather than
truth, and agreement across samples is frequently wrong in a correlated way.

**Verifier-guided decoding.** Generate candidates, score them with a verifier,
keep the best. The most relevant existing work to this architecture, since it is
the same loop. Adopted as the shape of the verification stage, with one critical
addition: the verifier must differ from the generator *in kind*. A verifier that
re-runs the generator's reasoning confirms consistency, not correctness. This is
the asymmetry problem in `../verification/`, and it is the most important thing
to get right here.

**Best-of-n with a reward model.** Rejected. The reward model is unauditable and
shares the generator's biases, which makes it a consistency check wearing a
quality check's name.

**Reasoning effort as a controllable parameter.** Adopted where the host provides
it, because it makes rung selection cheap and explicit. It does not remove
triage — the parameter still needs a value, and the value is still a decision. It
does make the decision legible, which is a real improvement over choosing by how
elaborately the request is phrased.

**Tree of thought and graph search over reasoning steps.** Adopted at the plan
level, not inside a single reasoning step: replanning after contradicting evidence
is search with the plan as the node. Rejected inside reasoning, because the
branching is invisible to the decision record and the branches not taken cannot
be reviewed.

**Self-critique and self-refinement.** Review and improve your own output.
Adopted mostly for form rather than correctness: does the delivery state a
verdict, are limitations present, is each claim's status labelled. Self-critique
reliably catches omissions of required structure and does not reliably catch a
wrong answer, because the critique comes from the process that produced the
error and tends to ratify confident output.

**Reflexion and verbal reinforcement.** Criticise past outputs and retry with the
critique in context. Adopted in the recovery path, where a failure is genuinely
new information, and in bounded form. Unbounded self-revision on a failing task
produces long, plausible, unproductive text.

**Entropy and confidence-based stopping.** Stop when the answer distribution
stabilises. Not adopted. It needs calibrated confidence, which is unavailable
here, and a stable distribution is not a correct one. It would also encourage
stopping early, which is the direction the kernel is already exposed to.

**Tool-augmented reasoning as a substitute for thinking.** Adopted strongly; it
is the cheapest reliability win available. Arithmetic, parsing, searching, and
formatting go to tools. A model reasoning about what a command would print is
strictly worse than running it, and also cheaper.

## What was adopted

- An explicit rung ladder setting reasoning depth per unit, with escalation and
  de-escalation triggers.
- A reasoning-effort boundary, recorded even at R0, so cost is inspectable.
- One honest test: if the next correct action is already determined, act.
- Self-consistency for single-answer tasks where it pays, and nowhere else.
- Verifier-guided structure, with a verifier that differs in kind.
- Self-critique for form and completeness, not for correctness.
- Reflexion on failure, with a hard bound.
- Deterministic work pushed to tools, without exception.
- Reasoning effort as a host parameter where one exists.

## What was rejected and why

- **Chain-of-thought as the audit trail.** Generated reasoning is a
  reconstruction; a trail writable after the fact proves nothing.
- **Best-of-n with a learned reward model.** Shares the generator's biases and is
  unauditable.
- **Self-critique as a correctness check.** The error and its critique come from
  the same process, and the observed failure is ratification of a confident wrong
  answer.
- **Confidence-based early stopping.** Confidence is not calibrated, and stable
  is not correct.
- **Reasoning trees inside a single step.** Invisible to the record, and the
  abandoned branches are exactly what a reviewer would want.
- **Unbounded self-revision.** Produces text rather than progress.
- **Treating a hard-sounding request as a hard request.** Difficulty is not
  measurable from the request, and confidence in the impression is the main source
  of over-orchestration.

## Open problems

- **Difficulty estimation before paying to find out.** The central problem. Every
  escalation trigger is an observation made *after* effort is spent, so a wrong
  triage is paid for in the currency being conserved. No good method has been
  found, and the honest answer may be that the cost is unavoidable and only its
  magnitude is reducible.

- **When more reasoning stops helping.** Reasoning has diminishing and then
  negative returns, where a model reasons itself out of a correct first answer.
  There is no reliable signal, and the rung is a coarse control over a continuous
  process.

- **Verifier quality is the bottleneck.** Scaling reasoning produces more
  candidates, and each needs a check. If the check is weaker than the generation,
  scaling produces more confident errors at greater cost. The independence
  requirement is the response; its sufficiency is unestablished.

- **De-escalation safety.** Dropping effort mid-run is right when reality is
  easier and wrong when the appearance of ease precedes a late discovery. There is
  no principled guard, only heuristics about blast radius.

- **Reasoning in unfamiliar domains.** R3 and R4 are the rungs for unfamiliar
  territory, and there is no evidence about how depth should be set when the
  kernel has no prior on what the right answer looks like. Current practice leans
  on C6 specialist depth, which is expensive and unmeasured.

- **Self-consistency on non-single-answer work.** Much of the kernel's work has
  many defensible answers, where majority voting measures the model's mode. There
  is no established alternative to agreement-based checking for open-ended work,
  which is a large fraction of the real cases.

- **Measuring the cost of over-reasoning.** The most common defect is currently
  reported rather than measured. Without a metric, the ladder's thresholds are
  untuned guesses.

# Recovery

What to do when something fails, given that most failures are not bugs and that
the most expensive response to a failure is the one that looks like effort.

## The question this raises for the kernel

A long run will fail. The question is not whether, but what the failure is
information *about* — because a fact that was an assumption a moment ago is now
observed, which makes failure the cheapest data the run will get. The kernel's
job is to convert failures into decisions rather than into persistence, and to
distinguish the two quickly, because blind persistence is both wasteful and
misleading: it looks like work.

## Approaches considered

**Fault tolerance and redundancy.** Mask failures: retry, replicate, degrade,
fail over. Partially adopted. Bounded retry with backoff is used for genuinely
transient failures where the cause is known and the action is idempotent.
Redundancy and failover are properties of the environment, not of the kernel.

**Retry policies: backoff, jitter, circuit breakers.** Bound the rate and volume
of retries, stop trying a dependency that is clearly down. Adopted, with one
addition: the bound is per cause, not per run. The bound that matters is how
many times an action may be repeated with an unknown cause, and the answer is
zero. Backoff without classification is a retry storm with better manners.

**Checkpointing and restart.** Save state so work resumes. Adopted as an
architectural requirement rather than an optimisation: it makes work units
atomic, makes a run interruptible by a human, and makes L5 execution possible.
Checkpoints include evidence and verification state, not just progress, so
resuming does not re-derive what was established.

**Plan repair and replanning.** Repair a plan locally rather than replanning
wholesale. Adopted as the default response to contradiction. Local repair is
cheaper and preserves sound units; wholesale replanning discards them. The scope
of a repair is everything that depended on the failed assumption, which is often
wider than it first appears and should be computed rather than guessed.

**Model-based diagnosis.** Build a model of the system's components, infer the
minimal fault set consistent with the symptom. Adopted in reduced form: the
kernel maintains a model of its own state — task model, assumptions, decisions,
units, capabilities — plus the failure log, and diagnosis is explicit reasoning
over that model rather than pattern matching on the error text. Full automated
diagnosis would need a component model nobody has.

**Retry versus replan as a decision.** Adopted as an explicit boundary. Every
failure is classified before a response, and the classification determines it.
The eight classifications come from real observed failure modes; each implies a
different next action, which is what makes the list more than a taxonomy.

**Rollback and compensating transactions.** Adopted conceptually for irreversible
work. Where an action cannot be undone, the compensating control is prevention:
narrower scope, a checkpoint, or confirmation before acting. This is why
irreversibility is a triage axis.

**Circuit breakers and bulkheads.** Stop calling a failing dependency; isolate
failures. Adopted for capability use: a capability that fails twice on the same
objective is set aside and the run re-resolves. Continuing to use a failing
capability is the multi-agent form of a retry storm.

**Reflexion and self-critique.** Generate a critique after a failure and retry
with it in context. Adopted in bounded form, with clear limits. It works when the
failure produced genuinely new information — an error message that names the
actual problem — and fails when the failure is underdetermined, producing a
plausible explanation and a different failure. Reflexion is not diagnosis, and a
critique that feels right is not a cause.

**Genetic programming and immune-system repair.** Evolve a candidate that passes
the tests. Rejected. No reward signal, unauditable candidates, and the fitness
function would be the verification problem in `../verification/` with all of its
unresolved questions attached. Repair through the lifecycle, using the failure as
evidence, is slower and inspectable.

**Bayesian diagnosis.** Maintain a distribution over system states, update from
observations. Not adopted. It needs a calibrated state model that does not exist
here. The kernel uses explicit assumptions with named consequences, which is
cruder and more honest: a failing assumption is visible, and a shifted posterior
is not.

**Chaos engineering and fault injection.** Induce failures deliberately to test
recovery. Adopted in evaluation. The failure-prone benchmark class is fault
injection: contradicting evidence, tools that fail realistically, resources that
run out. Recovery that has never been tested is a plan, not a capability.

## What was adopted

- Classify before responding; blind retry is prohibited. A second attempt requires
  a named cause in one line.
- Eight classifications, each with a mandated response and a stop condition.
- Failures recorded as structured data — attempted, observed, classified, cause,
  response — before any action is taken.
- Plan repair scoped to the failed assumption's dependents, with a decision
  record.
- Checkpointed, resumable work units, with evidence in the checkpoint.
- Bounded retries, per cause, with backoff for genuinely transient failures.
- A capability that fails twice on an objective is set aside and re-resolved.
- Reflexion after a failure that produced new information, and nowhere else.
- Resource failure answered by reducing scope or reporting the block, never by
  silent truncation.
- Verification failure treated as a failure of the work, not of the check.
- Fault injection in the evaluation suite.

## What was rejected and why

- **Unbounded retry with backoff.** Backoff without a cause is a retry storm with
  better manners.
- **Wholesale replanning on any failure.** Discards sound work, and costs far
  more than a local repair.
- **Self-critique as diagnosis.** Produces plausible explanations for
  underdetermined failures, and a different failure each time.
- **Evolutionary repair.** Unauditable, and its fitness function is the unsolved
  verification problem.
- **Belief-state diagnosis.** Needs a calibrated state model that does not exist;
  explicit assumptions fail visibly, which is preferable.
- **Re-verifying after a verification failure.** If the criterion fails twice the
  work is wrong; re-running the check to see whether it passes is that failure's
  own failure mode.
- **Hunting a workaround for an unsupported objective.** Reporting the block is
  the correct terminal outcome; substituting a different problem produces a
  plausible answer to a question nobody asked.
- **Rollback as a general answer to irreversible actions.** Where rollback is
  impossible, the control is prevention before the action.

## Open problems

- **Distinguishing transient from systematic failure.** The classification depends
  on it and the evidence is thin: one error message, once. A timeout and a
  misconfigured endpoint produce similar text, and the costs of guessing wrong
  differ sharply.

- **Stopping escalation.** Every recovery path has a bound, and the bounds are
  set by judgement. Nothing establishes whether a third attempt at a strategy
  that has failed twice is worthwhile, and the failure mode of continuing is a
  long unproductive run rather than a visible error.

- **Repair scope.** Replanning every dependent is correct and expensive;
  repairing only the visible unit is cheap and sometimes wrong. Dependents are
  computable in principle and rarely computed in practice.

- **Partial failure in parallel work.** When one unit of five fails, the right
  response depends on whether the others were truly independent — a decision made
  before the work started, and possibly wrong. There is no good mechanism for
  discovering that independence was assumed rather than established.

- **Recovery cost versus re-doing.** Sometimes restarting a unit is cheaper than
  repairing it. Nobody has characterised when, so the repair-first policy will
  sometimes be the more expensive choice.

- **Detecting a stuck loop.** A kernel can satisfy every rule while making no
  progress: bounded retries, valid classifications, new records each time. The
  budget heuristic is a proxy, and a convincing stuck loop would defeat it.

- **Learning from failure without over-correcting.** The tempting lesson is always
  "avoid whatever just happened", which is why promotion is gated. Extracting a
  correct lesson at all is the open question; see `../learning/`.

# Learning

How a system that changes itself avoids the two obvious outcomes: learning
nothing, and learning wrong things permanently.

## The question this raises for the kernel

The kernel produces evidence about its own behaviour and it can change. That
combination is where self-improvement usually goes wrong, and the reason is
worth stating precisely: the sample is selected by the system, the criteria were
written by the system, and the checks were chosen by the system. Each is a source
of bias, and they point the same way — toward lessons that make the system feel
more effective rather than more correct.

The question is therefore not whether it can learn, but what would make a lesson
from this evidence trustworthy, and what must be declared when it is not.

## Approaches considered

**Continual learning.** Learn from a stream over time without catastrophic
forgetting. Adopted as the framing. The kernel's "task" is procedural rather
than declarative, which changes the failure modes: forgetting in a skill library
looks like a skill that has quietly stopped being selected because better
descriptions crowded it out, and it is invisible.

**Catastrophic forgetting.** New learning overwrites old learning. Recognised,
with a different mechanism here. Nothing is stored in weights, so overwriting is
not the risk; distraction is — a library where the wrong entry is selected, and a
promoted lesson that has generalised past its scope. The controls are scope on
every promotion, a trigger negative on every skill, and a library small enough to
audit. Size is the enemy.

**Experience replay.** Store past experiences and rehearse them. Partially
adopted, deliberately not as a mechanism. The kernel replays *cases*, not
episodes: an objective that previously produced a promoted skill is re-run when
that skill is involved and compared against recorded evidence. Continuous replay
of raw episodes was rejected — it retrieves by similarity, and similarity
retrieves the least general case.

**Curriculum.** Easier examples first, then harder. Adopted implicitly through
the ladder: R0 to R2 before R3 and R4. Not adopted as a training schedule,
because the kernel is not trained.

**Active learning.** Query for the labels that would be most informative.
Adopted, and one of the more valuable transfers here. The kernel decides where to
spend verification effort, and the useful question is which check would change
its belief most. That is why independent verification is reserved for
load-bearing claims rather than applied uniformly. Not implemented as a number,
because the belief is text.

**Bayesian updating of beliefs from evidence.** Adopted as epistemic status —
known, inferred, assumed, unverified, uncertain, contradicted. The categorical
form, not the numeric one: calibration is unestablished, and a number invites
trust it has not earned. Categories are better for one specific reason — they
force a statement at the moment of use, and a statement is what protects the
reader.

**Test-time adaptation.** Adjust behaviour within a session from feedback.
Adopted as the primary and reversible response to a lesson: change this run's
approach, record the candidate, stop there. This is the workhorse, and it makes
the gates affordable, because most lessons do not need promoting to be useful.

**Skill libraries and modular knowledge bases.** Reusable procedures retrieved by
context. Adopted as the design. See `../skill-generation/` for how a candidate
becomes an entry, which is where the hard questions live.

**Meta-learning.** Learn a general procedure for learning. Rejected. The kernel
already has one — the lifecycle. Adding a learned layer to a gated one
introduces an unauditable component into a system whose main defensible property
is that its decisions can be read.

**Continual reinforcement learning.** Policy improvement from experience.
Rejected. No reward signal, and a learned policy replaces the decision record
with something nobody can review.

**Unlearning.** Remove specific learned information. Not needed in its usual
form, since the knowledge here is explicit artefacts. What is needed is simpler:
a deprecation path, reachable without editing files by hand, with the reason
recorded — a first-class lifecycle state, not an afterthought.

**Self-modifying systems and recursive self-improvement.** The system rewrites its
own architecture. Rejected in almost every form, with one narrow exception: the
kernel may generate capabilities, and a promoted capability may be part of its
own future tooling. It may not modify the kernel's own decision fabric,
lifecycle, or security controls. A system that can rewrite its own control logic
has no control logic, only a current configuration.

**Constitutional self-critique.** Check behaviour against explicit principles
before retaining it. Adopted in the gates: promotion requires a stated scope, a
generalisation argument, a deprecation condition, and a security review. Written
down and checkable, which is what makes a gate more than a sentiment.

**Drift and change-point detection.** Partially adopted through scope auditing
rather than statistically. Whether the kernel's behaviour drifts measurably is
not established, and a detector for an unmeasured phenomenon is not a priority.
The visible drift today is in the skill library; the counter is deprecation.

## What was adopted

- A gated lifecycle: observed, candidate, validating, validated, promoted,
  active, deprecated. Promotion is never automatic.
- Generalisation evidence and a stated scope, including what the lesson does not
  apply to, for every promotion.
- Deprecation as a reachable first-class state, with the reason recorded.
- The reversible change first: adjust this run, record the candidate.
- Extraction of the procedure, not retention of the episode.
- Replay of cases against recorded evidence when a promoted capability is used.
- Active learning's question at the verification boundary.
- Epistemic status in place of numeric confidence.
- No modification by a generated capability of the kernel's fabric or controls.

## What was rejected and why

- **Automatic promotion on success or failure.** One instance is a hypothesis,
  and failure-driven lessons over-represent avoidance.
- **Self-modification of control logic.** It is indistinguishable from losing
  control, and that authority is exactly what an adversary wants.
- **Continuous replay of raw episodes.** Retrieves the least general case and
  surfaces wrong content with no gate.
- **Fine-tuning to internalise lessons.** No scope, no reversal, no
  auditability; a wrong lesson becomes indistinguishable from a right one.
- **Numeric self-assessment.** Uncalibrated, and it invites unearned trust.
- **A large accumulated rule base.** Every promotion makes every later selection
  slightly harder. The small library is the feature.
- **Session-only learning.** Never produces a capability, so repeated problems
  stay at full price.
## Open problems

- **Validating a lesson without ground truth.** The kernel writes the criteria,
  the evidence, and the judgement of generalisation. No independent check exists
  in general. The gates reduce the rate of a bad promotion; they do not make one
  detectable. This is the deepest unresolved problem here, and it is the same
  asymmetry as in `../verification/`.

- **What evidence of generalisation looks like.** "More than one instance" is a
  number someone chose. Nobody has shown it is right, or that the right number
  depends on anything measurable.

- **When a lesson is not worth learning.** The rules require evidence before
  promotion but never require a judgement that a pattern is *not* worth
  capturing. A kernel that learns every difference between similar cases
  produces a large, poor library.

- **Detecting a subtly wrong promoted rule.** A rule wrong in most cases and
  right in the rest is used confidently, and nothing surfaces it until a
  downstream run fails for an unrelated-looking reason. Attribution afterwards is
  the only diagnostic, and it is weak.

- **Degradation over long horizons.** Whether a system with thousands of
  promoted rules behaves worse than one with fifty is not established. The
  mitigations are precautionary rather than measured.

- **Sharing learning between instances.** One run's validated lesson is not
  available to the next, and a library shared across concurrent runs raises
  consistency questions nobody has addressed. The lifecycle assumes one learner.

- **Aggregate authority of capabilities.** Each is gated individually, and the
  combined authority of several individually reasonable capabilities has never
  been assessed. This has the longest tail of the open questions, and it is a
  security question as much as a learning one. See
  `../../docs/security/threat-model.md`.
# Learning Safety

Self-improvement without a gate is self-corruption: the system slowly rewrites itself
from noise and never notices, because the thing that changed is the thing that was
supposed to be checking. Every rule below keeps the amount of self-modification
proportional to the evidence for it.

## The prohibitions

- **Uncontrolled rewriting is prohibited.** The system may not rewrite its own
  behaviour, rules, or trust settings as a side effect of doing a task.
- **One failed task must not permanently rewrite the system.** A failure is evidence
  about an instance, not about the rule.
- **One success must not install itself as a rule.** A single pass is an observation;
  promoting it turns coincidence into policy.
- **A learned pattern must never grant itself authority it did not have.** A promoted
  learning is subject to the same trust boundaries as any other capability. Learning
  does not raise privilege, widen permission, or authorise an action the class of
  capability could not already take.

## Prefer the reversible change

When a run reveals a better way, take the topmost option that solves the problem:

| Change | Reversible | Requires |
|---|---|---|
| Adjust this run's approach, record a candidate | Yes | A record |
| Change a draft or unpromoted artefact | Yes | Evidence within this run |
| Promote a rule or capability | Partly | Generalisation evidence, stated scope, a JEv decision record |
| Alter a trust boundary, permission, or default policy | No | Human authorisation, always |

In practice that is almost always the first row, and the candidate then waits for real
evidence instead of having it invented for it.

## The gate before promotion

Before anything becomes durable: state the pattern as a falsifiable rule with a scope;
test it on a case distinct from the one that produced it; record the evidence; take a
JEv decision with the rejected alternative filled in; at R4, confirm with a human.
Missing any of these, the candidate stays a candidate. The lifecycle is in
`learning-system.md`.

## Self-conditioning: the risk the gate does not cover

Everything above limits **what** may change. It does not address what a retained
conclusion *does to later reasoning*, which is a different failure with a
different mechanism.

Per-step accuracy in long runs degrades partly because the agent's own earlier
conclusions sit in its context and are then treated as premises. A stronger model
does not fix it, and it is worst in exactly the case this architecture creates: **a
run that deliberately retains validated conclusions** holds its own prior output
in front of itself for the rest of the task. A wrong conclusion that survived
promotion is re-read at every subsequent step rather than once.

Promotion gating reduces how often a wrong conclusion is retained. It does nothing
about what happens next.

### Counter-measures

- **Mark retained knowledge as agent-produced.** Every promoted item carries its
  origin. A conclusion this system derived is a premise to be tested, not a fact
  to be cited — and citing it as a fact is the failure.
- **Require disconfirmation before reuse, not just confirmation.** Before acting
  on a retained conclusion, name one observation that would show it is wrong. If
  none can be named, it was never a rule.
- **Prefer the transferable object to the conclusion.** Retain the model of the
  situation — constraints, mechanism, boundary conditions — rather than the
  specific answer. A retained mechanism survives a changed input; a retained
  answer becomes a wrong premise the moment the input moves.
- **Re-derive at boundaries.** At each rung increase and each replan, restate the
  load-bearing conclusions from their evidence instead of carrying them forward as
  settled. This is the cheapest available interruption of the loop.
- **Prefer external evidence to internal recall for anything load-bearing.** A
  conclusion the system reached by itself and checked by itself is the weakest
  possible source. An outside check beats a longer internal argument.

### The uncomfortable implication

The design's most distinctive feature — retaining what proved useful — is also the
condition under which its characteristic failure is most likely. Gating and
self-conditioning defence must be designed together. Strengthening one while
ignoring the other produces a system that is confidently wrong in a way it can no
longer detect.

This interaction is not measured. The research notes on learning and on
long-horizon scaling record the sources; they are in the repository rather than
in a runtime install, so nothing above depends on them being present.

## Bound the self-modification

Per run, cap what may change: a small stated number of new candidates recorded, at
most one promotion, and no change to a trust boundary or default policy without the
human. Per project, cap the promoted set and re-examine it when it passes a stated
size. A system that can rewrite itself without limit has no stable behaviour left to
evaluate, and evaluation is what makes the rewrite legitimate in the first place.

## Deprecation is first-class

Deprecate on the same evidence you would have required to promote: observed failure in
a case inside the stated scope, a superseding rule, or a change that empties the scope.
Deprecation is an operation with a record, not an afterthought. Keep the removal
reversible until its replacement is verified, and never leave a rule in place because
removing it is awkward — an active wrong rule is worse than no rule, because it gets
applied with confidence.

The boundaries a learning may not cross are in `security-and-trust.md`; the promotion
gates and state machine are in `learning-system.md`; what counts as evidence is in
`evidence-system.md`.

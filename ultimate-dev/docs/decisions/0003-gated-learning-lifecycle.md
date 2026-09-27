# 0003. Gated learning lifecycle

Status: Accepted
Date: 2026-09-26
Deciders: architecture maintainers

## Context

A kernel that cannot learn repeats itself. A kernel that learns without limits
becomes something else, and the failure is not obvious at the time it happens.

The pressure toward uncontrolled learning is structural. Self-improvement feels
like the point of a general system: it has evidence about its own behaviour and
the ability to change, and refusing to use them looks like a design gap. The
argument for gating is not conservatism, it is that the kernel's own record of
success is drawn from a sample it selected, using success criteria it wrote, and
verified by checks it chose. That is a biased sample of a biased process. A
lesson drawn from it is a hypothesis, and treating it as a rule installs the
bias into the system permanently.

The concrete risks:

**One instance becomes a rule.** A single task fails because a network call
timed out. The lesson recorded is "avoid external calls", and every subsequent
task avoids them. There is no evidence that the call caused the failure, no
evidence that the pattern generalises, and no mechanism to notice later that
the rule is wrong.

**Errors are more memorable than successes.** Failure is salient, so lessons
drawn from failure over-represent failure modes and install avoidance as the
default posture. A kernel that learns mainly from what went wrong becomes
cautious to the point of not acting.

**Scope is forgotten.** A lesson valid in one context is stored without the
context, then applied everywhere. "Use the project formatter before committing"
becomes "run a formatter", which is wrong in a repository that has none and
harmful in one where the formatter is configured differently.

**Deprecation is missing.** Systems that can add rules but not remove them
accumulate. Each rule is individually defensible. Together they produce
behaviour nobody designed and nobody can explain, and the cost of diagnosis
grows with every addition.

**Self-modification expands the attack surface.** If a retrieved document or a
tool's output can influence what gets promoted, then an adversary who controls
one of those inputs controls the kernel's future behaviour. The security model
in `../security/threat-model.md` depends on promotion being a controlled gate,
not an automatic one.

**Verification is not free.** Validating a candidate lesson requires evidence
that it generalises, which for most lessons means more than one instance and
sometimes an adversarial case. Without a budget for that, validation collapses
into assertion.

## Decision

Adopt a **gated learning lifecycle**. Experience must pass through named states
with explicit promotion criteria and a reversal path.

```text
OBSERVED → CANDIDATE → VALIDATING → VALIDATED → PROMOTED → ACTIVE → DEPRECATED
```

1. **Promotion is never automatic.** Nothing enters `PROMOTED` without a
   decision at JEv and a record of it.
2. **Promotion requires generalisation evidence.** One instance is a candidate,
   always. The evidence must show the pattern holds beyond the case that
   produced it. An explicit statement of the number of instances is part of the
   record.
3. **Promotion requires a stated scope.** What situation the lesson or
   capability applies to, and what it explicitly does not apply to. Unscoped
   promotion is prohibited.
4. **Reversibility first.** When a lesson suggests a different approach, prefer
   the change that affects only this run, and record the candidate. Promotion is
   for lessons that will recur.
5. **Deprecation is a first-class state**, with the reason recorded, and
   reachable from `ACTIVE` by a decision. A system that cannot deprecate is
   incomplete under this decision.
6. **A generated skill is a candidate, never trusted behaviour.** Capability
   creation goes through the same lifecycle as any other lesson, and
   `skill-creator` owns the gates. See
   [0002](0002-skills-are-resources-not-agents.md).
7. **A single failure does not rewrite the system.** Nor does a single success
   install itself. Both directions require evidence beyond the instance.
8. **Promotion decisions are auditable.** The record names the evidence, the
   scope, and the condition that would deprecate it. A promotion with no
   deprecation condition is incomplete, because nothing can later retire it on
   evidence.

## Consequences

**Easier.** The system cannot be corrupted by one bad run, which is the single
most valuable property for a system that runs unattended. Behaviour stays
explainable: every active lesson has a recorded origin, scope, and evidence, so
"why does it do that" has an answer. Deprecation keeps the accumulated
behaviour set small enough to reason about. The security model gets a chokepoint:
untrusted content can propose a lesson, and the gate is where that proposal is
rejected.

**Harder.** The system is slower to improve. Most candidates never promote, and
the kernel repeats some avoidable mistakes. Validation costs budget that would
otherwise go to the task, and at low rung that cost is not obviously worth
paying. The lifecycle also creates its own failure mode: **gate fatigue**, where
promotion criteria are checked in form rather than in substance, and candidates
move to `PROMOTED` with hand-written evidence. A second mode is **candidate
accumulation**, where the `CANDIDATE` state grows without bound because nothing
is ever retired from it. Both need metrics, not exhortation.

**New failure modes this makes more likely.** Deferral: because promotion is
hard, the kernel may keep re-deriving a lesson it already has as a candidate.
Scope creep in the other direction: conservative scoping means a promoted
lesson applies to almost nothing, so promotion succeeds and nothing changes.
And a subtler one: **self-justifying promotion**, where the validating evidence
is produced by the same reasoning that produced the candidate, so the gate
confirms the hypothesis rather than testing it. Independent derivation, from
`../concepts/verification-and-evidence.md`, is the only real control.

## Alternatives considered

**No learning.** Rejected. The PRD's acceptance criteria include validated
learning, and a system that cannot retain validated work pays full price for
every repeated problem. It also fails the claim of being a kernel rather than a
calculator: the difference between them is what survives a run.

**Automatic promotion on success.** Rejected. It is the cheapest implementation
and it installs the bias described in the context. One success is not evidence of
generalisation, and success criteria are self-selected.

**Automatic promotion on failure.** Rejected for the same reason, plus the
salience asymmetry: failure-driven rules drift toward avoidance and the system
stops acting on unfamiliar ground.

**Learn only into the current session's context.** Rejected. This is the
reversible-change preference taken to its extreme. It never produces a capability,
so nothing accumulates, and the system restarts from defaults every time. Good
as the first response to a lesson, wrong as the only one.

**Vector-memory style retrieval of past episodes, no promotion state.**
Rejected. Retrieval from raw history surfaces the nearest match, which is
frequently the least general case, and there is no gate at which untrusted or
wrong content can be excluded. It is also silent: nothing announces that a
retrieved episode is being treated as guidance.

**Human approval for every promotion.** Rejected as the default because it does
not scale and it will be bypassed under time pressure, which is worse than no
gate: the gate exists but is nominally violated. Human approval is reserved for
R4 work and for promotions that change authority or safety behaviour, which is
the right use of a scarce reviewer.

**Periodic retraining or fine-tuning from accumulated experience.** Rejected for
this version. It has no scope, no reversal, and no per-lesson auditability, so a
wrong lesson is indistinguishable from a right one after the fact. Revisit if
the skill library saturates and candidate reuse is measurably too slow.

## Revisit when

- Candidate accumulation is observed in practice, and a policy for bulk
  rejection or summarisation is needed.
- Promotion is measurably too slow to matter: track the number of runs between a
  lesson being recorded and being useful, and compare against the cost of
  re-deriving it.
- A single promoted lesson causes a visible downstream failure, which is the
  strongest evidence that the generalisation bar is set in the wrong place.
- An evaluation shows the kernel repeating a mistake it already has as a
  validated candidate, which indicates the gates are correct and the retrieval
  is not. That is a different fix, and it belongs in
  `../../research/learning/`.
- A generated skill promoted through these gates is found to have generalised
  badly. Re-examine the adversarial test stage in the creation pipeline rather
  than the lifecycle.

# Capability acquisition

How the kernel obtains a means of making progress it does not have, without
acquiring one it does not need.

## The question this raises for the kernel

A capability is any means of progress: a skill, tool, command, person, document,
model, deterministic operation, or something not yet existing. The kernel must
decide which it lacks, obtain it, check that it works, and use it without
trusting it. The hard part is not obtaining it. It is deciding that a gap exists
at all, and resisting the pull toward obtaining something when doing the work
directly would have been fine.

## Approaches considered

**Tool learning.** Learn to use an unfamiliar tool from documentation, trial, and
feedback, building a model of its preconditions, effects, and failure modes.
Adopted in that shape: every capability is characterised on three axes — exists,
does what it claims, output is what its name implies — before use. The third
catches most surprises, because a tool returning something other than what its
name implies corrupts every decision downstream, silently.

**API and schema discovery.** Introspect a service or library to learn its
interface, then call it. Adopted, with validation as a condition rather than an
outcome. Discovery tells you the interface; only execution against a checkable
case tells you it works. Interfaces change, schemas are wrong in the
documentation, and a discovered interface that was never exercised is an
assumption with a confident name.

**Program synthesis.** Generate a program from a specification. Partially adopted,
and confined to a *procedure* the kernel will follow, expressed as a skill
specification, rather than arbitrary executable code produced on the spot. The
difference is the validation gate: a generated procedure passes through
specification, tests, security review, and promotion, while a synthesised program
has usually had none of those. See `../skill-generation/`.

**Human-in-the-loop acquisition.** Ask a person for the thing the kernel lacks: a
credential, a decision, context, a missing procedure. Adopted as a first-class
resolution path rather than a failure to avoid. It is frequently the cheapest
option by a wide margin, and the kernel should reach for it earlier than feels
productive. An hour of a person's time beats a generated procedure of unknown
correctness, and the comparison is not close.

**Reinforcement learning for tool use.** Learn a policy for selecting and
sequencing tools from reward. Rejected. No reward signal, non-stationary tool
sets, and an unauditable policy. The kernel's decisions must be reviewable
records, which is the opposite of what a learned policy produces.

**Reusable skill libraries and hierarchical RL.** Learn higher-level skills from
experience so the same task is solved by composing options. Rejected as a
mechanism, adopted as a goal. The library is built deliberately, through
promotion gates, not learned. The cost is that it grows slowly and contains only
validated entries; the benefit is that every entry can be read, tested, and
removed.

**Analogical and case-based reasoning.** Solve a new problem by adapting a solved
one. Adopted as a triage step before creation: if a similar problem has been
solved, its capability is a candidate for reuse or extension. The discriminating
question is whether the past solution's conditions hold, which is a judgement and
is recorded as one.

**Replanning and search as capability discovery.** Searching for approaches
often surfaces the needed capability as a side effect. Adopted in the
plan-recovery path: when a unit fails with a wrong-capability classification, the
response is re-resolution, and re-resolution surfaces capabilities nobody had
considered. This is one of the cheaper sources, because the need is already proven
by a failure rather than imagined.

**Published skill libraries from the agent ecosystem.** Reuse published skills
wholesale. Adopted with strict validation, because a published skill is arbitrary
code and arbitrary instructions from an untrusted party. Its trust level is that
of web content: it may inform, it may not authorise. See
`../../docs/security/threat-model.md`.

**Meta-learning across tasks.** Learn a general procedure for learning. Rejected.
The kernel already has one, and it is the lifecycle. Adding a learned layer on
top of a gated one adds an unauditable component to an auditable system.

## What was adopted

- A five-rung resolution ladder — do it directly, use something existing,
  compose, acquire, create — with the rule that most tasks end at rung 1.
- The disqualifying question: *will this be needed again?* A one-off is a step in
  the plan, not a capability.
- Three-axis validation before first use: existence, behaviour, output shape.
- Delegated creation through `skill-creator`, which owns specification,
  validation, security review, and promotion.
- Human request as a resolution path, taken early rather than late.
- The past-solution check before creating anything.
- Re-resolution as the response to a wrong-capability failure, before creation.

## What was rejected and why

- **Synthesising executable capabilities on the fly.** The validation surface is
  the whole thing — correctness, security, output shape — all unverified at the
  moment of use. A generated procedure with gates is acceptable; a generated
  program without them is the confident fabrication in a new costume.
- **Learned tool-selection policy.** Unauditable, and the decision record is the
  architecture's core.
- **Importing a published skill as trusted behaviour.** It is web content with
  execution rights, and it goes through the same gates as anything else acquired.
- **Acquiring to avoid admitting a gap.** A resource failure is reported with
  what is missing. Substituting a poor capability is worse than a stated block,
  because the user cannot tell which happened.
- **Creating a capability to simplify a single unit.** Unit complexity is not a
  capability gap; the test is whether the need will recur.

## Open problems

- **When is direct action the right answer?** Rung 1 is correct most of the time
  and cannot be predicted in advance. There is no reliable test for "the kernel
  could do this itself", and the costs of guessing wrong are asymmetric: too
  eager is slower, too reluctant is a confident fabrication. The evaluation suite
  is the only instrument, and it measures retrospectively.

- **Detecting a gap before failing.** Most gaps are discovered by a failure, so the
  cost is already paid. Proactive detection needs domain knowledge the kernel does
  not have and cannot acquire cheaply. The past-solution check helps only for gaps
  someone has hit before.

- **Validation without ground truth.** "Does this capability do what it claims"
  is checked against a case the kernel chooses, and the kernel is the thing that
  wanted the capability. No independent oracle exists in general. This is the
  weakest point in the acquisition chain, and it is the same asymmetry as in
  `../verification/` and `../skill-generation/`.

- **Composition contracts.** Skills have declared inputs and outputs, and
  composing two requires knowing they fit. Nobody has designed the interface
  discipline that would make composition cheap, and it is the rung most likely to
  be attempted and least likely to be checked.

- **Acquisition cost against the work.** Acquisition plus validation can exceed
  the cost of doing the task badly. The crossover is unmeasured, so "validate
  before use" can be expensive on exactly the small tasks where it is hardest to
  justify.

- **When a human is the bottleneck.** Asking is often right, and the kernel cannot
  know how long the answer will take, so it cannot choose between asking and
  proceeding on an assumption. In an unattended run the assumption wins, and that
  is an unmitigated risk.

- **Deprecation of acquired capabilities.** External capabilities change
  underneath the kernel. A promoted skill wrapping a third-party interface
  becomes wrong with no change on our side, and nothing notices before a run
  fails confusingly.

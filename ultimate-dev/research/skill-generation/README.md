# Skill generation

How a procedure performed once becomes a reusable asset, and why that transition
is gated rather than automatic.

## The question this raises for the kernel

A kernel that solves a problem by hand and then forgets has missed the cheapest
kind of learning. A kernel that mints a skill per task has acquired a different
defect: nothing is reused, the trigger signal splits, and the library becomes
noise. The question is what distinguishes a procedure worth keeping from one that
merely happened to be performed, and how you can tell without a ground truth for
what "correct" means for a procedure you are inventing.

## Approaches considered

**Procedural knowledge representation.** How procedures are stored so they can be
retrieved and executed: production rules, case-based reasoning, plan libraries.
The oldest and least fashionable field here, and the closest to the
architecture. Adopted as the shape of a skill: declared purpose, inputs, outputs,
constraints, and failure modes, with a selection signal in the description. A
skill is a production rule with a trigger, and the trigger is the hard part.

**Case-based reasoning.** Store solved cases, solve new problems by adapting
similar ones through retrieve, reuse, revise, retain. Adopted as the *source* of
candidates rather than as the storage model. A successful sequence of steps is a
solved case, and reusing it is the reuse phase. What is rejected is retaining
every case: the kernel retains the *procedure* the cases had in common, with a
scope, and discards the instances. Retaining instances produces a library that
matches on surface similarity.

**Skill libraries and modularity.** Reusable, independently testable components
with explicit interfaces. Adopted wholesale, including the interface discipline:
declared inputs, outputs, constraints, and verification criteria per skill, so
composition is possible at all. Composition beats creation, and composition is
only possible if the interfaces exist.

**Versioning.** Semver per skill with promotion and deprecation states, so a
change to a promoted skill is visible and reversible. Adopted with states rather
than numbers. The lifecycle — observed, candidate, validating, validated,
promoted, active, deprecated — carries more information than a version string,
and it carries the part that matters: whether anyone has checked this yet.
Version numbers are for humans; states are for the system.

**Automated program repair.** Locate a fault, synthesise a patch, validate it
against the tests. Adopted narrowly, for a *procedure* rather than code: when a
promoted skill repeatedly fails the same way, the repair is to revise the
procedure, re-validate, and re-promote, with the failure as the evidence. The
general literature is not adopted because most of it optimises passing a test
suite, and passing a test suite is not the same as generalising.

**Test-driven synthesis.** Write the tests first, then synthesise to satisfy
them. Adopted as the gate order for creation: specify the verification criteria,
then generate, then test against them, then adversarially. The ordering matters
more than the technique — a generated skill tested only against the case that
motivated it has been tested once.

**Version-space and behaviour-based validation.** Check an implementation
against its *specification* rather than against a reference. The right frame for
procedural knowledge, where two correct procedures can look nothing alike.
Adopted. A skill is validated against its contract and its declared failure
modes, not against a previous version's text. This is what makes deprecation
safe: behaviour, not wording, is what is checked.

**In-context and example-based specification.** Describe a procedure by example.
Adopted for specification, with a known weakness: examples underdetermine the
procedure, and a specification built only from examples produces a skill that
handles the examples and nothing adjacent. The specification must state the
contract; examples illustrate it.

**Conformal prediction.** Produce prediction sets with coverage guarantees, so an
invalid output is detectable. Not adopted: the guarantees are statistical and
assume exchangeable data, and a skill's contract is not a distribution. The
useful intuition is narrower and informal: a skill should declare what outputs it
is not responsible for, and the kernel should treat anything outside that set as
unvalidated.

**Fine-tuning to internalise a skill.** Rejected for this version. No scope, no
reversal, no per-skill auditability, so a wrong procedure becomes
indistinguishable from a right one after the fact. Revisit if the library
saturates.

## What was adopted

- A skill as a procedural knowledge unit: purpose, inputs, outputs, requirements,
  dependencies, constraints, security boundaries, verification criteria, failure
  modes.
- A **trigger negative** in every definition, so selection does not depend on a
  broad positive description.
- The lifecycle with explicit states, and promotion as a decision with evidence, a
  scope, and a deprecation condition.
- Specification before generation, tests from the specification, and at least one
  adversarial test before promotion.
- Validation against the contract and failure modes, not against a previous
  version's wording.
- Extraction of the *procedure* from a run, not retention of the run.
- Composition as the preferred alternative to creation, which requires the
  interface discipline to be real.
- Repair of a promoted skill through the same lifecycle, using the failure as
  evidence.

## What was rejected and why

- **Retaining solved cases as the library.** Matching on similarity retrieves the
  least general instance, and the library grows without becoming more capable.
- **Examples as the specification.** They underdetermine the procedure, and the
  result handles the examples and nothing adjacent.
- **Generated code without the gate chain.** The validation surface is the whole
  problem; skipping it is the confident fabrication with extra steps.
- **Fine-tuning to internalise a procedure.** No scope, no reversal, no
  auditability.
- **Version numbers as lifecycle state.** A number says what changed, not whether
  anyone checked.
- **Automatic promotion after passing tests.** Passing the tests written for the
  motivating case is not generalisation, which is the specific error
  [0003](../../docs/decisions/0003-gated-learning-lifecycle.md) exists to prevent.
- **Self-modification of the kernel by a generated skill.** A skill that edits the
  kernel is an unbounded authority grant. Prohibited; see
  `../../docs/security/controls.md`.

## Open problems

- **Validating a generated skill without ground truth.** There is none. The
  kernel writes the specification, the tests, the implementation, and judges the
  result, so the whole loop is self-referential. The adversarial stage and the R4
  human checkpoint are mitigations, not solutions. This is the deepest unresolved
  problem in the area, and it is not unique to skills: see `../verification/`.

- **What counts as evidence of generalisation.** Three instances is a number
  someone chose. Nobody has shown it is right, or that the right number is a
  function of anything measurable about the lesson.

- **Detecting over-broad skills.** A skill matching too much is a performance
  problem; a skill matching too little is a correctness problem, because the work
  gets done the long way. Only the second is visible in results. Trigger
  negatives help and do not solve it.

- **Composition interfaces.** Nobody has designed the discipline that would make
  composition safe. The failure mode is a chain of individually reasonable
  capabilities producing a result none of them can verify.

- **When a procedure should be split.** Long skills hit context and precision
  limits; splitting introduces interfaces, which introduces the problem above. The
  right granularity is unknown and probably task-dependent.

- **Drift in promoted skills.** A skill's environment changes and the skill does
  not. Nothing detects this except a downstream failure, which attributes itself
  to whatever was running at the time.

- **Maintenance versus regeneration.** If a promoted skill is rarely used and
  expensive to keep correct, regenerating each time might be better. No
  measurement exists, the answer probably differs per skill, and a per-skill
  policy would be needed. Nobody has designed one.

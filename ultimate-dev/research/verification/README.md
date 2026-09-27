# Verification

How to decide that something is true, when the person deciding is the same
person who produced it.

## The question this raises for the kernel

Every claim the kernel makes is produced by the same process that would check
it. That is a structural asymmetry, not an oversight, and no amount of care
removes it. The question is what to do about it: which checks catch which
errors, what they cost, and where the residual risk has to be declared rather
than managed.

## Approaches considered

**Formal proof.** Demonstrate a property holds for all inputs in a domain.
Adopted wherever the claim is code or a protocol and a machine-checkable model
exists. It is unbeatable on its own terms, and its limits are equally clear: it
applies only where the property can be formalised, formalising it is often the
larger task, and a proof about a model is a proof about the model.

**Property-based testing.** State properties, test against generated inputs.
Adopted as a default for anything with an interface, with properties derived from
the success criteria. That derivation is what makes it useful here: the test
expresses what must be true, so passing it means the criterion holds over a far
larger set than the examples a human would pick.

**Metamorphic testing.** No oracle, so apply transformations whose effect is
known and check the relationship holds: add a no-op, reorder independent items,
double the input. Relies on relations rather than expected outputs. Adopted where
no oracle exists, which is often — a search procedure, a summary, a planner. The
most valuable technique available for checking work whose correct answer cannot
be stated, and under-used in agent work generally.

**Mutation testing.** Break the code deliberately, check the tests catch it.
Adopted selectively, for verification code and check scripts, on the principle
that a check nobody has tried to defeat is not a check. The kernel applies this
to itself in one place: ask what the verification would report if the result were
wrong, and if the answer is "verified", the check is broken.

**Independent re-derivation.** Derive the result a second way, by a method that
could fail differently. Adopted as the third and strongest check kind, and the
only one that addresses the asymmetry. Independence is a property of the
*method*: a second run of the same method is a repeat, and a repeat measures
determinism. The method must differ in the dimension that could be wrong —
different tool, different derivation, different observer, or a property the first
method could not see.

**Cross-validation and ensembling.** Agreement across models. Partially adopted,
with a reservation: models sharing training data and inductive biases share the
bias, so agreement measures the shared bias. Useful when members are genuinely
diverse, weak when they are not, and it checks variance rather than correctness.

**Self-consistency and majority voting.** Adopted for single-answer tasks with a
checkable answer, explicitly not for open-ended work where the majority measures
the mode of the distribution rather than truth. See `../reasoning/`.

**Confidence calibration and selective prediction.** Know when the system does
not know, and abstain. Partially adopted as epistemic status, which is the
categorical version of the same idea. The numeric form is not adopted:
calibration is unestablished, and a number would invite trust it has not earned.
Categories force a statement, which is what actually protects the reader.

**Statistical hypothesis testing.** Decide whether a result is distinguishable
from chance. Adopted for claims about populations, measurements, and
performance, where sampling is explicit. Not applicable to most of the kernel's
work, which produces deterministic artefacts; applying statistical framing to a
deterministic result is a category error.

**Reference-based checking against a specification or golden output.** Adopted
where a specification exists and is authoritative. Rejected as a general strategy
for generated work: the reference encodes the same assumptions as the thing being
checked, and agreement between two things built the same way is not evidence.

**Fuzzing.** Feed malformed and adversarial input, check for crashes and
invariant violations. Adopted for anything parsing untrusted input, which is
much of what this kernel does. Untrusted input is the security boundary, and
fuzzing is the cheapest way to find the parser bug that crosses it.

**Continuous integration and regression suites.** Adopted for the skill library
and the evaluation suite, because a promoted capability that silently stops
working is a persistent problem rather than a transient one.

## What was adopted

- Three check kinds in increasing strength — evidence, validation, independent —
  and one of three verdicts: VERIFIED, PARTIAL, FAILED.
- Proportionality: depth set by risk, consequence, uncertainty, novelty, and
  evidence quality, with the reasoning recorded.
- The claim-to-evidence chain, each link separately checkable, and a mandatory
  "not established" line.
- Epistemic status on every claim, with a named observation required for any
  status change.
- Independent re-derivation as the only response to the asymmetry problem, and
  the rule that independence is a property of the method.
- PARTIAL as a real terminal verdict, with satisfied and unsatisfied criteria both
  named.
- Mutation-style self-challenge: what would this check report if the result were
  wrong?
- Formal proofs for protocols where a model exists, property-based and
  metamorphic tests where an oracle does not, fuzzing at every untrusted parser.

## What was rejected and why

- **Self-review as a correctness check.** The error and its review come from the
  same process, and the observed failure mode is ratification of a confident
  wrong answer. Retained only for form and completeness.
- **Chain-of-thought as evidence of reasoning.** A reconstruction, not a record.
- **Numeric confidence in the output.** Uncalibrated, and it invites trust that
  has not been earned.
- **Statistical framing for deterministic results.** A category error that
  produces a number with no meaning.
- **Golden-output comparison for generated work.** Confirms agreement, not
  correctness.
- **Universal independent verification.** Costs more than it returns on
  low-stakes, tool-confirmed work. Proportionality is what makes verification
  affordable; verifying everything is the same defect as orchestrating
  everything.
- **Skipping verification at R0 on grounds of obviousness.** The check on the
  output is the one check R0 always performs.

## Open problems

- **No independent oracle in most of this work.** The kernel writes the
  specification, the tests, the implementation, and judges the result. Every check
  is generated by the process whose output is in question. This is the deepest
  problem in the area. The honest position is that residual risk remains after
  every control here, and the architecture's job is to declare it rather than
  imply it is closed.

- **Verification cost scaling.** How do you set depth when the check costs as
  much as the work? The proportionality rule is a rule of thumb, untuned, with
  no theory behind it. At R3 and above this constrains what is deliverable, and
  the exchange rate between check cost and check value is uncharacterised.

- **Metamorphic relations for open-ended work.** The most valuable technique
  where there is no oracle, and the hardest to find. Which relations hold for a
  design, an explanation, or a plan? There is no general answer, and finding them
  appears to require domain knowledge the kernel does not have.

- **Detecting systematic bias.** Every internal check is consistent with a
  coherent wrong answer, because a systematic error produces a self-consistent
  record. Only a genuinely different method or a person breaks it, and neither is
  available at scale.

- **Model-checking the kernel's own protocols.** The lifecycle, promotion gates,
  and recovery paths are finite-state enough to check, and no models have been
  built. A model showing a promotion cycle reachable from a single poisoned
  candidate would be worth more than a paragraph of reasoning about it.

- **What proportion of real tasks are verifiable at all.** Some objectives have
  no checkable success criterion and the kernel must proceed on all of them. The
  only signal available to a reader is prose saying so, which is weak.

- **Regression coverage for promoted capabilities.** Every promoted skill can
  break silently when its environment changes, and nothing detects it before a
  downstream run fails and misattributes the failure.

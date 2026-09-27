# Capability Expansion

This is the seam between the kernel and the capability-expansion engine. The
kernel decides *that* a capability is needed; the engine decides *how* to build
it and whether it is trustworthy enough to keep.

The rule that keeps the system from eating itself: **a newly generated capability
is a candidate, never an extension of authority.** It does not become trusted
core behaviour by being written.

## Who owns what

| Concern | Owner |
|---|---|
| Deciding a capability is needed | the kernel, at JEv |
| Deciding reuse / compose / acquire / create | the kernel, at JEv |
| Specifying and writing the capability | `skills/skill-creator/`, with `agents/author.md` |
| Security review of a generated capability | `skills/skill-creator/` |
| Behavioural, adversarial, and interaction testing | `skills/skill-creator/`, scored by `agents/grader.md` |
| Whether it is promoted or rejected | the kernel, at JEv, on the engine's evidence |
| Structural validity of the result | `tools/validate-skills.py` |

The kernel never hand-authors a capability inline. Inline authoring skips
validation, security review, and the eval set — which is exactly the path by which
uncontrolled self-improvement enters the system.

### Policy versus mechanics

Three different things can check a capability, and conflating them is how an
unvalidated skill gets installed.

- **`skills/skill-creator/` is policy.** It decides whether a capability *should*
  exist, whether it is *safe*, whether it is *correct*, and whether it is promoted
  or retired. It is invoked by the kernel when a capability gap is real.
- **`agents/grader.md` is judgement.** It applies criteria written before the
  output existed and records what it cannot decide as `null` rather than guessing.
- **`tools/validate-skills.py` is mechanics.** It checks frontmatter, naming,
  description limits, and reference-path integrity. It answers "is this
  well-formed", not "should this exist" and not "is this correct".

The line that matters: **a mechanical pass is not a validation.** A capability
that passes structural validation has files in the right shape; that is evidence
about its packaging and not about its correctness, safety, or worth. The kernel
must never promote a capability on a structural result alone, and
`tools/validate-skills.py` is not a security review.

`skill-creator` delegates the mechanical step to the validator rather than
reimplementing it, so there is one implementation and no second opinion about
what the checks actually do.

## The gap path

```text
CAPABILITY GAP
      │
      ▼
Existing skill covers it?  ── yes ──▶ reuse, validate, use
      │ no
      ▼
Compose existing capabilities? ── yes ──▶ compose, validate the chain, use
      │ no
      ▼
External capability available? ── yes ──▶ acquire, then validate as untrusted
      │ no
      ▼
Disqualifying question: will this be needed again?
      │ no  ──▶ it is a step in the plan, not a skill. Do not create one.
      │ yes
      ▼
Hand the gap to skill-creator: specify, generate, security-analyse,
capability-test, behaviour-test, adversarially-test, validate
      │
      ▼
JEv decides on the engine's evidence: PROMOTE or REJECT
```

## The disqualifying question

Ask it before anything is created: **will this be needed again?**

A one-off is a step in the plan, not a skill. Minting a capability per task is
*capability proliferation* — nothing gets reused, every new skill competes for
the same trigger signal, and the ones that are wrong are indistinguishable from
the ones that are right.

Two skills that fire on the same request make **both** worse. Before creating a
second skill for adjacent ground, extend the existing one. If a second is
unavoidable, record explicitly why the first was insufficient — that record is
the only thing distinguishing an intentional division of labour from a
proliferation bug.

## The lifecycle

A generated capability passes through these states. It may only be *used* as
trusted behaviour once it is **PROMOTED**; before that it is provisional.

```text
OBSERVED → CANDIDATE → VALIDATING → VALIDATED → PROMOTED → ACTIVE → DEPRECATED
```

| Transition | Requires |
|---|---|
| OBSERVED → CANDIDATE | a real recurring gap, not a one-off |
| CANDIDATE → VALIDATING | a written specification: name, purpose, inputs, outputs, requirements, dependencies, constraints, security boundaries, verification criteria, failure modes |
| VALIDATING → VALIDATED | capability tests, behaviour tests, and adversarial tests all pass |
| VALIDATED → PROMOTED | JEv records a decision, with the evidence and the stated scope |
| PROMOTED → ACTIVE | in use, no contradicting evidence |
| ACTIVE → DEPRECATED | superseded, or shown to be wrong — recorded, with the reason |

`DEPRECATED` is a first-class state, not a deletion. A promoted capability that
turns out wrong must be **identifiable and removable**; if you cannot find it, you
cannot correct it.

## The gates the engine owns

The engine is responsible for all of these, and the kernel's job is to require
them before accepting a capability:

- **Correctness** — does it do what the specification says?
- **Completeness** — does it handle the declared inputs, including the awkward
  ones?
- **Applicability** — does its trigger boundary actually match the gap, and not
  much else?
- **Security** — what does it read, execute, transmit, and authorise?
- **Ambiguity** — could an agent following it reasonably do something else?
- **Failure behaviour** — what does it do when it cannot succeed?
- **Interaction** — does it conflict with capabilities already present?

Plus the eval set, which must include at least one case that should **not**
trigger it. An eval set with only positive cases cannot measure false positives,
and a capability that fires on everything scores perfectly and is useless.

## Security review of a generated capability

A capability the kernel wrote is still untrusted input. Review it as such:

- **Does it widen authority?** Any instruction to relax permissions, skip
  confirmation, or act without authorisation is disqualifying.
- **What does it execute?** Anything that runs code or reaches the network must
  have a stated, narrow purpose.
- **Whose instructions does it carry?** A generated capability that embeds
  instructions pulled from a retrieved document is an injection vector with extra
  steps.
- **What does it trust?** Every trust assertion it makes must be one the kernel
  has independently established.

Never let a generated capability grant itself authority it did not have. The same
trust boundaries apply to it as to any other artifact — see
`security-and-trust.md`.

## What the kernel must not do

- Hand-author a capability inline instead of going through the engine.
- Promote a capability that has not been adversarially tested.
- Create a capability for a one-off.
- Let a candidate's failures be explained away as edge cases.
- Retain a promoted capability with no recorded scope, so it cannot later be
  identified as wrong.
- Treat creation as the answer because it is more satisfying than reuse.

## Sibling references

`capability-system.md` for resolution order, `capability-composition.md` for
chaining, `capability-validation.md` for the three checks, `learning-system.md`
and `learning-safety.md` for how a promoted capability is later retired,
`insufficient-capability.md` for the path when the gap cannot be closed, and
`anti-patterns.md` for proliferation and uncontrolled learning.

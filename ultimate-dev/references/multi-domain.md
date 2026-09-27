# Multi-domain work

The kernel has no domain agents and no routing table. It knows no field in
advance, so it must not contain logic that assumes one. Hardcoded routing is
the failure this file exists to prevent:

```text
PROHIBITED
  if task == "medical":  use medical-agent
  if task == "finance":  use finance-agent
  if task == "OS":       use os-agent
```

Routing by label sends work to a specialist that may be the wrong one, and it
cannot express a task that is genuinely two things at once. Requirements must be
derived from the objective at runtime.

## Derive, do not route

```text
OBJECTIVE
   ↓
What must be known?
   ↓
What must be done?
   ↓
What capabilities are necessary?
   ↓
What capabilities exist?
   ↓
What capabilities are missing?
   ↓
Acquire or create
   ↓
Execute
   ↓
Verify
```

Run this against the actual objective. The answers are per-objective, not
per-field, and the capability list it produces is the real work breakdown.

## Decompose, do not delegate wholesale

A cross-domain task is broken into per-domain requirements: the vocabulary,
constraints, and verification each part needs, with the interfaces between them
named explicitly. Then resolve each requirement through the normal capability
order — reuse, compose, acquire, create. See `insufficient-capability.md`.

Splitting by domain label is not decomposition. "A finance part and a software
part" names categories, not requirements, and it tells you nothing about what
each part must satisfy.

## The interfaces are the risk

Where two domains meet, the units disagree about what a field means, what
"valid" is, and which unit of work they are in. Integration points carry the
risk that neither domain's own tests can see, so give them their own
verification: a round trip across the seam, a boundary case, or a second
derivation by a different route. A plan that verifies every part and never
checks the join has verified nothing the user actually depends on.

## The decomposition is derived, never stored

A decomposition is an output of this objective, not a template for the field.
The same broad field decomposed for one objective may decompose entirely
differently for another, and reusing the earlier shape silently optimises for
the wrong problem. Record the derived requirements in the task model
(`task-model.md`) and re-derive them whenever the objective changes.

## On programme-scale work

An operating-system-scale programme is a stress-test metaphor for extreme
complexity: hierarchical planning, staged delivery, explicit risk retirement. It
is not a mode this kernel has, and its ceremony is not a template to imitate at
smaller scale. Match effort to the objective as triage found it; borrowing
ceremony is difficulty worship. See `anti-patterns.md`.

Cross-reference `unknown-domain.md`, `capability-system.md`, `verification-system.md`, `triage.md`, and `anti-patterns.md`.

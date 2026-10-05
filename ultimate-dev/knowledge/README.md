# Knowledge

The knowledge layer is the data contract between the kernel and anything that
stores, retrieves, or validates its records. `ultimate-dev` is a prompt and
decision architecture, not a running program, so everything here is a
**normative specification**: an agent reading it must behave as described, and
an implementation written against it must accept and reject the same records.

Two kinds of document live here, and the distinction is not stylistic.

```text
schemas/    what a record IS   — fields, types, rules, a worked example
policies/   what MUST HAPPEN  — conditions, thresholds, consequences
```

A schema is a shape. A policy is a rule about shapes in use. Neither is
prose about either.

## Schemas

| File | Record | Created at |
|---|---|---|
| `schemas/task.md` | objective, requirements, constraints, assumptions, unknowns, success criteria, triage | UNDERSTAND |
| `schemas/decision.md` | the decision record: question, selected, rejected, rationale, confidence, cost, evidence, recovery | every JEv boundary |
| `schemas/context.md` | one compiled working set for one live decision, C0–C6 | CONTEXT |
| `schemas/capability.md` | a means of making progress, its resolution step, boundaries, and validation | ACQUIRE |
| `schemas/skill.md` | a reusable procedure with its lifecycle, security boundaries, and verification criteria | capability expansion |
| `schemas/evidence.md` | claim, evidence, source, transformation, verification, epistemic status | OBSERVE |
| `schemas/observation.md` | what actually happened, verbatim, including what did not | EXECUTE |
| `schemas/experience.md` | one completed run, assembled and auditable | LEARN |
| `schemas/learning.md` | a candidate change to behaviour, gated and scoped | LEARN |
| `schemas/agent.md` | a specialized reasoning role: input/output contract, capabilities, dispatch condition | DELEGATE |
| `schemas/provider.md` | one implementation of a capability: entrypoint, selection criteria, fallback order | ACQUIRE |
| `schemas/artifact.md` | a typed, persistent, validated stage output | EXECUTE → SYNTHESIZE |
| `schemas/workflow.md` | stages, dependencies, parallelism, gates, recovery, completion | PLAN |

`experience` is the spine. Every other record carries a reference back to a run
or a task, and the experience record is where they are assembled. The nine map
onto the RunState model in `prd.md` §17 without renaming its fields: `task`,
`objective`, `requirements`, `constraints`, `assumptions`, `unknowns`,
`evidence`, `context`, `capabilities`, `skills`, `decisions`, `strategy`,
`reasoning`, `plan`, `actions`, `observations`, `failures`, `verification`,
`learning_candidates`, `budget`, `provenance`, `result`.

The last four are **composition records**: they describe the package, not a
run, and they map onto the entity model in `new-implementation.md` §7 (agent,
provider, artifact, workflow). The adoption decision and what it defers is
`../docs/decisions/0014-package-composition-contracts.md`.

## Policies

| File | Governs |
|---|---|
| `policies/freshness.md` | when context and evidence expire, and what must be re-obtained |
| `policies/provenance.md` | traceability of a claim to a source, and the trust class of that source |
| `policies/validation.md` | when a result may be trusted, and which verdict may be reported |
| `policies/promotion.md` | when learning and capabilities may change behaviour |
| `policies/retention.md` | what is kept, for how long, and what is deleted |
| `policies/mcp-failures.md` | how MCP provider failures are normalized, and what each disposes |

Policies override convenience everywhere. A policy conflict is resolved in
favour of the more restrictive rule, and the conflict is recorded as a
`decision`.

## How a schema is versioned

Each schema carries a version in the form `MAJOR.MINOR`.

- **PATCH** — prose, examples, and clarifications that change no accept or
  reject decision. No version change.
- **MINOR** — a new optional field, or a new enum value with a defined
  behaviour when absent. Existing valid records stay valid.
- **MAJOR** — removing or renaming a field, changing a type, changing what a
  field means, making an optional field required, adding a required field, or
  tightening a rule so that a previously valid record is now invalid.

A MAJOR change is a **breaking change**. It requires an architecture decision
record in `docs/decisions/`, written before the edit, and it requires a
migration path for existing records or an explicit statement that none exist.

The rule that decides which of the three applies is one question: *does any
record that was valid before remain valid after?* If not, it is MAJOR, and no
amount of documentation makes it otherwise.

## Rules for this layer

1. A record type exists because a decision depends on it. Do not add a field
   nothing reads.
2. Field names are part of the contract. Renaming is MAJOR, always.
3. A rule that cannot be checked by a validator belongs in prose or is not a
   rule. Each schema separates the two explicitly.
4. A worked example is part of the specification. It is how a reader knows
   what "correctly filled in" means, and it is replaced, not appended to, when
   the shape changes.
5. No schema file is a skill. It has no frontmatter and is not loaded by the
   trigger mechanism. It is read when someone is building or auditing a record,
   which is rare by design.

## Related

`SKILL.md` — the kernel these records serve.
`prd.md` §17, §18 — the state model and the evidence chain.
`docs/decisions/` — where a breaking change to this layer is recorded.

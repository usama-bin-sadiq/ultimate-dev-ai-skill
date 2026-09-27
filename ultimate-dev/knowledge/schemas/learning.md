# Learning

## Purpose

The learning record is a candidate change to how the kernel behaves, held in a
state that does not yet affect behaviour. It captures something that worked or
failed once, what evidence exists that it generalises beyond the instance that
produced it, and exactly where it applies and how it would be removed. It is
created at LEARN and reaches behaviour only through a decision recorded in
`policies/promotion.md`.

## Shape

```yaml
learning:
  id: string
  statement: string              # the rule, phrased so it can be obeyed
  kind: heuristic | checklist_item | failure_lesson | tool_preference | scope_correction
  state: observed | candidate | validating | validated | promoted | active | deprecated
  derived_from: [string]         # experience ids; never a task id alone
  trigger_condition: string      # the situation in which this applies
  scope:
    applies_to: string
    excludes: string
  generalisation:
    - { experience: string, distinct_context: string, outcome: string }
  gates:
    - { name: string, result: pass | fail | not-run, at: timestamp | null, ref: string }
  contradicting:
    - { experience: string, why: string, resolved: true | false }
  promotion:
    decision: string | null      # decision id, required at promoted and above
    promoted_at: timestamp | null
    affects: [string]            # the files whose behaviour changes
  rollback:
    procedure: string            # written before promotion, not after
    verified_at: timestamp | null
  contradicts: [string]          # learning ids this one would supersede
  provenance: string
  retention_class: candidate | promoted | deprecated
```

## Fields

| Field | Type | Req | Meaning |
|---|---|---|---|
| `statement` | string | yes | Imperative and testable. "Resolve X before Y", not "X can be tricky". |
| `kind` | enum | yes | `scope_correction` narrows an existing rule; the others add one. |
| `state` | enum | yes | `observed → candidate → validating → validated → promoted → active → deprecated`. |
| `derived_from` | list | yes | Experience ids. A learning with no experience behind it is an opinion. |
| `trigger_condition` | string | yes | When this applies. A rule with no trigger fires everywhere and is noise. |
| `scope.applies_to` | string | yes | Required at `validated` and above. |
| `scope.excludes` | string | yes | What it must not be applied to. This is what makes it removable later. |
| `generalisation[]` | list | yes | Each entry names a *distinct* context, not a second observation in the same run. |
| `gates[]` | list | yes | Every gate passed to reach the current state, with the test that passed it. |
| `contradicting[]` | list | yes | Instances that should have triggered it and did not help. Unresolved ones block promotion. |
| `promotion.decision` | string | null | A `decision` id with `boundary: learning-promotion`. Null below `promoted`. |
| `promotion.affects` | list | yes | The exact files and lines whose behaviour changes. An empty list means nothing changes. |
| `rollback.procedure` | string | yes | The edits that undo promotion, written **before** it happens. |
| `rollback.verified_at` | timestamp | null | Set when the procedure has been executed at least once, in a rehearsal or a reversal. |
| `retention_class` | enum | yes | Drives expiry under `policies/retention.md`. |

## Field rules

- **One instance caps the state at `validating`.** A single experience may
  produce a candidate and may start validation. It may not reach `validated`,
  and therefore may not affect behaviour.
- `validated` requires `generalisation` with at least **two entries from
  distinct contexts**, `scope.applies_to` and `scope.excludes` both non-empty,
  and every `contradicting[].resolved: true`.
- `promoted` requires, in addition: a `promotion.decision` with a `rejected`
  list, a non-empty `promotion.affects`, a `rollback.procedure` written before
  the promotion, and no unresolved `contradicting` entry.
- `active` requires an observed use in at least one task **after** promotion.
  A learning promoted and never exercised is not active; it is a bet.
- `deprecated` requires a reason, a date, and either a `supersedes` successor or
  a statement that the rule is withdrawn. Deprecated learnings are retained as
  evidence of what was once believed and why it stopped.
- A learning never edits kernel or reference files directly. `promotion.affects`
  names what a human or a decision-carrying change will edit; the record is not
  the edit.
- `statement` and `trigger_condition` together must be sufficient to decide
  whether the rule applies to a new task without opening any other file.
- `derived_from` may not contain only experience ids from a single task.
- An unresolved `contradicting` entry demotes the state by one and forces a new
  `decision`. Contradiction is not an error state; it is the mechanism.
- `kind: scope_correction` requires a `contradicts` target that it narrows.
- Learning about *tooling preference* requires the same generalisation bar as
  anything else. Liking a particular interface is not a validated lesson.

## Worked example

Three candidates from one run: one promoted, one held, one rejected.

```yaml
learning:
  id: L-0031
  statement: >-
    In a multi-account audit over a shared module, resolve and record each
    account's module version before probing, and treat the version map as a
    precondition of coverage rather than an optimisation.
  kind: heuristic
  state: promoted
  derived_from: [exp-0098, exp-0141]
  trigger_condition: >-
    The task covers more than one account, and the audited resources are
    created by a module that is versioned.
  scope:
    applies_to: Multi-account IaC audits where a shared module creates the audited resources; any cloud provider.
    excludes: Single-account audits, and audits of resources not created by a module.
  generalisation:
    - experience: exp-0098
      distinct_context: "SEC-2214, 2026-06, 18 accounts, Conftest produced four false negatives traced to unpinned module versions"
      outcome: Version map surfaced the divergence; the check was corrected.
    - experience: exp-0141
      distinct_context: "SEC-2291, 2026-09, 30 accounts, two accounts pinned v1.2.0 and held a live public ACL grant"
      outcome: Version map identified both accounts in 3 tool calls instead of a full estate scan.
  gates:
    - { name: second-instance, result: pass, at: 2026-09-24T10:20Z, ref: exp-0098 }
    - { name: scope-stated, result: pass, at: 2026-09-24T10:24Z, ref: this record }
    - { name: removal-written, result: pass, at: 2026-09-24T10:28Z, ref: this record }
    - { name: no-unresolved-contradiction, result: pass, at: 2026-09-24T10:31Z, ref: this record }
  contradicting: []
  promotion:
    decision: DEC-0021
    promoted_at: 2026-09-24T10:31Z
    affects: ["references/capability-system.md — one checklist item under capability resolution"]
  rollback:
    procedure: >-
      Delete the checklist item and the registry entry. Two edits, no code
      depends on it, no record format changes.
    verified_at: null
  contradicts: []
  provenance: exp-0141
  retention_class: promoted
---
learning:
  id: L-0032
  statement: >-
    An S3 exposure scan must read the bucket ACL, not only
    get-bucket-policy-status, because IsPublic describes the policy and is
    false on a bucket with no policy.
  kind: checklist_item
  state: validating
  derived_from: [exp-0141]
  trigger_condition: Any public-exposure claim about S3 buckets.
  scope:
    applies_to: S3 exposure scanning.
    excludes: not yet determined
  generalisation:
    - experience: exp-0141
      distinct_context: "SEC-2291, 2026-09, 30 accounts"
      outcome: One account held an AllUsers READ grant invisible to the policy probe.
  gates:
    - { name: second-instance, result: not-run, at: null, ref: "only one estate has been scanned with the ACL probe" }
  contradicting: []
  promotion: { decision: null, promoted_at: null, affects: [] }
  rollback:
    procedure: Delete the record. Not reachable from behaviour while at validating.
    verified_at: null
  contradicts: []
  provenance: exp-0141
  retention_class: candidate
```

The third candidate was closed rather than held. L-0033, `kind:
tool_preference`, `state: deprecated`, `trigger_condition: none`,
`generalisation: []`, one gate named `reusability-question` with `result: fail`
at `ref: DEC-0011`, `retention_class: deprecated`. Its `rollback.procedure` is
"retained as a rejected candidate; it records why nothing was built", and
`verified_at` is set, because the procedure was executed the moment the record
was written. A rejected candidate is still a record, and that is the point: the
refusal is auditable, and the record costs nothing because it is not a
behaviour.

## Validation

Mechanical:

- `state` and `kind` are enum members; every `history` step, if present, is
  adjacent in the ladder.
- `state ∈ {validated, promoted, active}` ⟹ `generalisation` has ≥2 entries
  with ≥2 distinct `distinct_context` values.
- `state ∈ {validated, promoted, active}` ⟹ `scope.applies_to` and
  `scope.excludes` are both non-empty and neither is `not yet determined`.
- `state ∈ {promoted, active}` ⟹ `promotion.decision` resolves to a decision
  with `boundary: learning-promotion`, and `promotion.affects` is non-empty.
- `state ∈ {promoted, active}` ⟹ every `contradicting[].resolved: true`.
- `state: active` ⟹ at least one experience id exists whose `started_at` is
  after `promotion.promoted_at` and which names this id.
- `derived_from` resolves to at least one `experience.id`, and those ids span
  at least one task when `state ∈ {validated, promoted, active}`.
- `state: deprecated` ⟹ `retention_class: deprecated` and a non-null
  `promotion.promoted_at` or a recorded rejection reason.
- `promotion.affects` names paths that exist.

Judgement, not automatable:

- Whether the `statement` is the lesson the run actually taught, or the lesson
  the run's author expected before it started. Most candidate learning is
  pre-existing belief dressed as a discovery.
- Whether the two generalisation entries are genuinely distinct contexts, or
  the same estate seen twice from different angles. This is the gate most
  often passed dishonestly, and no count can detect it.
- Whether `scope.excludes` is real. A rule with an `excludes` clause written to
  look thorough is worse than one without, because it will be trusted.
- Whether the learning reduces future cost or merely records what happened.
- Whether the `trigger_condition` fires in practice without opening the
  reference file it came from.

## Anti-patterns

- **The lesson from one incident.** Installing a rule because it is right, on
  the evidence of the one time it was needed. This is how a single failure
  becomes permanent behaviour.
- **Scope as decoration.** `excludes: cases where this does not apply`. A scope
  clause that excludes nothing constrains nothing, and it defeats the purpose
  of requiring one.
- **Promotion by recurrence in one run.** Two similar observations in a single
  estate, counted as generalisation. One estate is one context.
- **The unbounded rule.** A statement with no `trigger_condition` that will
  eventually be applied to a task it was never about, and then defended as
  precedent.

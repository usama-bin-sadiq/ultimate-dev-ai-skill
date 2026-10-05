# Workflow

## Purpose

The workflow record is a declarative plan of stages: what runs, in what
dependency order, in parallel where legal, gated between stages, with recovery
and completion criteria stated before execution begins. It exists so that a
known workflow is executed rather than re-derived, and so that a proposed
workflow can be validated before it costs anything. Two planning modes are
legal: **deterministic** — the runtime executes a predefined record — and
**model-assisted** — the model proposes the record and the runtime validates
it. The model proposes; the runtime controls.

## Shape

```yaml
workflow:
  id: string
  objective: string                   # the outcome, one sentence, the user's terms
  planning_mode: deterministic | model-assisted
  stages:
    - id: string
      component: string               # the skill or agent id that owns the stage
      needs: [string]                 # stage ids or artifact ids that must exist first
      produces: [string]              # artifact types the stage emits
      validation: [string]            # the gate between this stage and its consumers
      recovery: retry | fallback-component | ask-user | skip | stop
  parallelism:
    - [string]                        # a group of stage ids that may run concurrently
  completion_criteria: [string]       # observable conditions that end the workflow
  failure_boundaries:
    - stage: string
      does_not_invalidate: [string]   # what a failure here leaves standing
  depth: integer                      # meaningful delegation levels; target 2–4
```

## Fields

| Field | Type | Req | Meaning |
|---|---|---|---|
| `planning_mode` | enum | yes | `deterministic` requires the stage list complete at creation. `model-assisted` requires runtime validation of the proposed record before execution. |
| `stages[].needs` | list | yes | The dependency graph. A stage with no `needs` is a root. Order is derived from this, never from listing order. |
| `stages[].recovery` | enum | yes | Every stage has one. A stage with no recovery is a promise the run cannot keep. |
| `parallelism` | list | no | Groups whose members have disjoint `needs` and no write conflicts. Absent means sequential, which is always legal. |
| `completion_criteria` | list | yes | Observable. "Done when the stages are done" is circular. |
| `depth` | int | yes | Meaningful delegation levels. Above 4 is a smell and needs a recorded reason. |

## Field rules

- Execution order is topological over `needs`. Two stages are parallel-legal
  only when neither's `needs` reaches the other and their `produces` do not
  collide — parallelism is an optimization, never a requirement, and sequential
  execution of the same record must produce the same result.
- Every inter-stage boundary has a `validation` gate. What crosses is the
  artifact and its verdict (`artifact.md`), not the stage's conversation.
- `failure_boundaries` records what a stage failure does **not** invalidate, so
  a failed testing stage leaves requirements, architecture, and implementation
  standing while the runtime decides the next action.
- `recovery: retry` requires its bound elsewhere (the retry policy);
  `fallback-component` requires the fallback to be named in the component's
  contract; `ask-user` escalates; `skip` requires the stage to be genuinely
  optional for `completion_criteria`; `stop` is the honest default.
- A `model-assisted` record is validated before execution: every `component`
  resolves, every `needs` reference exists, every parallel group is legal, and
  the completion criteria are observable. An unvalidated proposed workflow is a
  suggestion, not a plan.

## Worked example

"Add OAuth login to the application and make sure it is tested":

```yaml
workflow:
  id: wf-T123
  objective: Add OAuth login to the application and make sure it is tested.
  planning_mode: model-assisted
  stages:
    - { id: requirements, component: requirements-skill, needs: [], produces: [requirements],
        validation: [every requirement is testable], recovery: ask-user }
    - { id: architecture, component: architect, needs: [requirements], produces: [architecture],
        validation: [covers every requirement, names the interface contract], recovery: retry }
    - { id: backend-implementation, component: backend-skill, needs: [architecture], produces: [code-change],
        validation: [satisfies the interface contract], recovery: fallback-component }
    - { id: frontend-implementation, component: frontend-skill, needs: [architecture], produces: [code-change],
        validation: [satisfies the interface contract], recovery: fallback-component }
    - { id: testing, component: testing-skill, needs: [backend-implementation, frontend-implementation],
        produces: [test-results], validation: [tests execute and report truthfully], recovery: retry }
    - { id: review, component: reviewer-agent, needs: [testing], produces: [review],
        validation: [every finding carries severity and remediation], recovery: skip }
  parallelism:
    - [backend-implementation, frontend-implementation]
  completion_criteria:
    - OAuth login works against the real provider in a staging environment
    - the test-results artifact shows the new flow covered and the suite green
  failure_boundaries:
    - { stage: testing, does_not_invalidate: [requirements, architecture, backend-implementation, frontend-implementation] }
  depth: 3
```

## Validation

Mechanical:

- Every `needs` reference resolves to a stage or artifact in the record.
- The graph is acyclic.
- Every parallelism group passes the disjoint-needs and no-write-collision
  checks.
- Every stage names a `recovery` and at least one `validation`.
- `depth` is present; above 4 carries a recorded reason.

Judgement, not automatable:

- Whether the stages are meaningful or a god-workflow wearing a graph. A
  workflow whose single stage is "do the task" has no graph; one with a stage
  per function call has no either.
- Whether `completion_criteria` end the work or merely the workflow. The
  second is how a green run delivers nothing.

## Anti-patterns

- **The god workflow.** One record containing every stage the package can
  perform, executed regardless of the task. Dynamic selection means most
  workflows use few components.
- **Depth as diligence.** Six delegation levels because each feels rigorous.
  The target is 2–4; each level past that multiplies hand-off cost and
  attributes less.
- **Parallelism as default.** Fanning out because the graph allows it, not
  because the stages are independent. Shared mutable state makes two parallel
  stages sequential however they are scheduled.

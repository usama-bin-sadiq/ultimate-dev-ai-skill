# Artifact

## Purpose

The artifact record is a typed, persistent, validated stage output: the primary
way stages communicate. It exists so that what crosses a boundary is a
structured result with a declared shape — never an entire conversation. A
conversation handed to the next stage is context dumping; an artifact is the
same information as a contract, at a fraction of the cost, with something to
validate against.

## Shape

```yaml
artifact:
  id: artifact://<type>/<task-id>     # addressable and persistent
  type: requirements | architecture | implementation-plan | code-change | test-results | review | documentation | string
  produced_by: string                 # the stage or agent that made it
  produced_at: timestamp
  consumers: [string]                 # the stages declared to read it
  format: string                      # the contract the content satisfies
  status: draft | validated | superseded | failed
  validation:
    - { check: string, result: pass | fail | not-run, ref: string }
  supersedes: string | null           # the artifact id this one replaces
  provenance: string
```

## Fields

| Field | Type | Req | Meaning |
|---|---|---|---|
| `type` | enum | yes | The named types cover the development workflow; a new type is a decision, not an improvisation. |
| `consumers` | list | yes | Declared at creation when the workflow is known. An artifact with no consumers is decoration — stop producing it. |
| `format` | string | yes | The checkable shape of the content. "Markdown" is a container, not a contract. |
| `status` | enum | yes | `failed` artifacts are retained, not deleted: they are the evidence the recovery was real. |
| `validation[].ref` | string | yes | The observation or test behind the result. No ref, no pass. |

## Field rules

- Stages communicate through artifacts wherever practical. The hand-off packet
  in `references/capability-routing.md` carries the artifact's id and verdict,
  not the conversation that produced it.
- `validated` is required before the next stage consumes. A chain validated
  only at the end cannot attribute its failure, and the second stage has
  already built on the broken first output.
- `consumers` is read at the boundary: a stage not on the list gets the
  artifact only by a recorded decision. This is the progressive-disclosure rule
  applied to stage output.
- `supersedes` implies the prior artifact's `status` is `superseded`. History
  is kept; the current id is unambiguous.
- The artifact is written to the run's state, not to `.memory/` scratch — an
  artifact that dies with the working directory was never persistent.

## Worked example

The architecture artifact in the OAuth workflow, fanned out to two parallel
implementation stages:

```yaml
artifact:
  id: artifact://architecture/T123
  type: architecture
  produced_by: architect
  produced_at: 2026-10-05T14:02Z
  consumers: [backend-implementation, frontend-implementation]
  format: components, data flow, trust boundaries, and the interface contract each implementation stage must satisfy
  status: validated
  validation:
    - { check: covers every requirement in artifact://requirements/T123, result: pass, ref: OBS-031 }
    - { check: names the interface contract for both consumers, result: pass, ref: OBS-032 }
  supersedes: null
  provenance: architect stage of workflow T123, from artifact://requirements/T123
```

Both consumers validate against the same interface contract. A divergence is
found at the boundary, not in review.

## Validation

Mechanical:

- `id` matches `artifact://<type>/<task-id>` and is unique in the run.
- `consumers` is non-empty at `validated`.
- Every `validation[].result: pass` carries a `ref` that resolves.
- `supersedes` resolves to an artifact whose `status` is `superseded`.

Judgement, not automatable:

- Whether `format` is a contract or a container. The test is whether a consumer
  can reject the content against it.
- Whether the artifact holds the decision or the discussion. The discussion
  stays in the stage; the artifact holds what later stages must be able to
  rely on.

## Anti-patterns

- **Conversation as artifact.** The stage's whole transcript attached as the
  hand-off. The next stage pays for everything and can validate nothing.
- **Artifact with no consumer.** Produced because the workflow template says
  so, read by nobody. Either name the consumer or stop producing it.
- **Validated at the end.** Every stage's artifact checked together at the
  finish, so the failure's origin is unrecoverable and every downstream stage
  is suspect.

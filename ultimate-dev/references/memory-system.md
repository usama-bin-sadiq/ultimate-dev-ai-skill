# Memory System

Memory exists to make the next run cheaper and safer, and unbounded memory is
unbounded risk. Three tiers, three different trust levels: what survives an
interruption, what survives the task, and what survives the project.

## Tiers

| Tier | Scope | Trust | Contents |
|---|---|---|---|
| Run state | Within one task | High — the observed record of this run | Objective, evidence, decisions, actions, failures, verification, budget |
| Candidate learnings | Between tasks, one project | Low — unvalidated | Signals and patterns, with origin instance and evidence |
| Promoted capabilities | Durable behaviour, project-wide | Medium — validated once, still fallible | Rules, skills, strategies, with scope and removal condition |

Never promote a candidate by writing it into behaviour. A candidate sitting in the
same tier as a rule is already a rule. Promotion is a gated decision in
`learning-system.md` and a bounded one in `learning-safety.md`.

## What must not persist

- Task-specific output that another task would misread as general.
- Secrets, credentials, and access tokens, in any tier.
- Facts observed once, with no source and no scope.
- Anything that crossed a trust boundary as content rather than as evidence.
- Failure detail whose only value was explaining this run's mistake.

## The run state

```text
RunState
  task               id, project, started, rung, scale
  objective          one sentence, in the user's terms
  requirements       what must be true when done
  constraints        permissions, formats, prohibitions, deadlines
  assumptions        what is taken as true, and what breaks if false
  unknowns           open questions, each marked blocking or not
  evidence           observed results, with provenance and freshness
  context            what is loaded, at which level, and why
  capabilities       resolved, acquired, created, validated
  decisions          JEv decision records, oldest first
  strategy           the approach in force, with its recovery condition
  plan               work units, preconditions, dependencies, status
  actions            what was run, with results
  observations       what was actually seen, including surprises
  failures           classified failures, with causes and responses
  verification       per criterion: verified | partial | failed
  learning_candidates  signals found, with origin and evidence
  budget             consumed, remaining, and what is protected
  provenance         where each artifact and result came from
  result             outcome, limitations, confidence, verification status
```

## Durability and resumption

A task interrupted mid-flight must be resumable from its own state and nothing else —
not from the conversation, not from what you happen to remember. If you cannot
reconstruct where you were, what you had established, and what comes next from
RunState alone, the plan was not observable and the plan was wrong. Write state as you
go, at the granularity of the next work unit, never at the end.

## Scoping

Scope memory to the project. A fact learned in one project does not become a general
rule because it was learned once; if it is genuinely general it goes through promotion,
which is where its scope gets stated. Watch for leakage: a project-specific path,
convention, or constraint that escapes into default behaviour turns a
correct-in-context learning into something wrong everywhere.

## Retention

State a retention limit per tier and prune to it. Run state is discarded when the task
closes. Candidates that never validate are dropped after a set number of runs.
Promoted capabilities are re-examined when they fail, when they are superseded, or
when the promoted set passes a stated size. Record what was pruned and why.

The state machinery is in `state-system.md`; the gates on what may become durable are
in `learning-safety.md`; what may be written at all is in `security-and-trust.md`.

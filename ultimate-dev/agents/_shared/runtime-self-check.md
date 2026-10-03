# Runtime Self-Check — Kernel Integrity Gate

Run this lightweight check at bootstrap and again after major routing changes.

## Structural checks

- `SKILL.md` exists and has valid frontmatter.
- `agents/_shared/capability-bridge.md` exists.
- `agents/_shared/capability-registry.md` exists.
- `agents/_shared/dispatch-scheduler.md` exists.
- Every explicitly referenced `agents/<name>.md` exists.
- No duplicate agent IDs or duplicate role names are introduced.

## Routing checks

- Every selected agent has a resolvable local prompt.
- Every required tool has a real host capability or a declared safe equivalent.
- Native vs fallback execution mode is known.
- Parallel claims are supported by the host; otherwise the run is serial.
- Write-conflicting agents are not scheduled concurrently.

## Truthfulness checks

- No result is marked `executed` merely because a prompt was read.
- No unavailable tool is represented as used.
- No unverified test/lint/build result is reported as passed.
- No external action is claimed unless the host actually performed it.

## Failure behavior

If a structural check fails, stop routing the affected capability and report the exact broken reference. Do not silently continue as if the registry were complete.

## Workflow primitive checks

After the routing checks above, record which workflow primitives the host
exposes. These are capability detection labels — they describe what the host
can do, not roles to invoke. Check each one at runtime; do not assume
availability. Record each as `available`, `unavailable`, or `unknown`.

Five labels to probe (see `references/workflow-bridge.md` for detection guidance
and the mode mapping):

- **parallel-dispatch** — host can run independent contexts concurrently and
  collect all results before continuing.
- **sequential-dispatch** — host exposes a pipeline where each step receives the
  prior step's output without the calling context holding intermediate state.
- **stateful-handoff** — host preserves conversation history and tool state when
  transferring a thread to a new context.
- **review-loop** — host exposes an iterative loop with a declarative stop
  condition (implement → review → repeat until approved or budget exhausted).
- **background-run** — host supports async task launch with a completion
  notification, without blocking the caller.

If a check cannot be performed (no documented API, no empirical probe path),
record `unknown` and treat it as `unavailable` for planning. Do not record
`available` by assumption.

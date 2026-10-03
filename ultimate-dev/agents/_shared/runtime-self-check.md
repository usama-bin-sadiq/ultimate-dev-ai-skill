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

After the routing checks above, also record which workflow primitives the host
exposes. Check each label once; record `available`, `unavailable`, or `unknown`.

- `parallel-dispatch` — host can launch independent agent/tool contexts
  concurrently and collect all results.
- `sequential-dispatch` — host exposes a pipeline primitive where each step
  receives the prior step's output without the calling context holding it.
- `stateful-handoff` — host preserves conversation history and tool state across
  an agent transfer.
- `review-loop` — host exposes a loop primitive with a declarative stop condition.
- `background-run` — host supports async task launch with a completion
  notification to the calling context.

If a check cannot be performed (no documented API, no empirical probe path),
record `unknown` and treat it as `unavailable` for planning. Do not record
`available` by assumption.

See `references/workflow-bridge.md` for detection guidance and the mode mapping.

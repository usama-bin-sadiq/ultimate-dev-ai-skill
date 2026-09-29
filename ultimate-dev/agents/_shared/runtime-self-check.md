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

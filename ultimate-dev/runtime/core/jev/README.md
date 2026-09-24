# Legacy JEV Compatibility Area

This directory is retained only for old Python callers and is **not** the
canonical Ultimate-Dev decision path.

The committed Python implementation is not a safe compatibility baseline:
its public classifier path, aggregator, guardrails, and tool slimmer contain
independent correctness and fail-open issues. The Runtime and SessionManager
no longer import this package.

New integrations must use:

- `runtime/schemas/jev-decision-request.schema.json`
- `runtime/schemas/jev-decision-packet.schema.json`
- `runtime/jev/engine.mjs` or a host-native implementation of the same contract

Do not add new Python, model-provider, container, or browser dependencies here.
Pre-existing untracked files in this directory are preserved for separate
review and are not part of the canonical runtime.

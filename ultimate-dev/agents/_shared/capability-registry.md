# Capability Registry — Runtime Source of Truth

The capability registry is a **run-local, host-derived registry**. It is not a hardcoded list of APIs.

## Registry shape

For each capability record:

```text
id: stable semantic identifier
kind: agent | skill | tool | plugin | model | executor
source: host-discovered | local-file | connected-provider
availability: available | unavailable | unknown
required: true | false
parallel: true | false
write_scope: none | files | external
cost: low | medium | high | unknown
requirements: semantic capabilities required to execute
entrypoint: host-specific reference when actually discovered
```

## Discovery

At bootstrap, discover only what the host exposes:

1. Native subagent/task executor.
2. Parallel executor, if separate from subagents.
3. File read/search/list capabilities.
4. Shell/command execution.
5. Web/search/fetch capabilities.
6. Test/lint/typecheck/build execution.
7. Connected plugins/connectors.
8. Installed/discoverable skills.
9. Available model tiers.
10. Local agent files under `agents/`.

Never infer availability from a tool name appearing in an agent file.

## Local agent registry

Every `agents/*.md` file is a candidate capability. Before selection:

- confirm the file exists;
- parse frontmatter;
- normalize `tools:` into semantic capabilities;
- normalize `model:` into a requested tier;
- record missing requirements;
- record whether the agent writes files;
- record whether it can safely run in parallel.

## Cache and invalidation

Cache the registry for the current run. Invalidate and rediscover only when:

- the host reports capability changes;
- a plugin/connector is connected or disconnected;
- a requested capability was unexpectedly unavailable;
- an agent/skill file is added or changed during the run.

## Truthfulness invariant

A capability may be reported as `available` only if the host has actually exposed it or the local file exists and is executable through the current fallback path.

Never convert `unknown` into `available` by assumption.

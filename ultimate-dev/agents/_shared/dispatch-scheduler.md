# Dispatch Scheduler — Dependency-Aware Execution

The scheduler converts selected roles into an executable plan.

## 1. Build the DAG

Each dispatch node contains:

```text
id
agent_or_skill
mission
requires: [capability ids]
after: [node ids]
reads: [paths/globs]
writes: [paths/globs]
priority
budget
```

Add an edge when:

- one node consumes another node's output;
- one node must inspect files written by another;
- both nodes may write the same path;
- the task explicitly requires ordering.

Otherwise they are candidates for parallel execution.

## 2. Scheduling rules

1. Execute all ready, independent nodes together when parallel execution exists.
2. If no parallel executor exists, execute the same ready set serially.
3. Never parallelize overlapping write scopes.
4. Never exceed the phase's agent/token budget.
5. Prefer fewer agents when two agents provide substantially redundant coverage.
6. Prefer the agent with the closest domain match when budgets force a choice.
7. Preserve required verification and security gates even when other agents are dropped.

## 3. Failure-aware scheduling

- `success`: unlock dependent nodes.
- `partial`: unlock dependents only if the missing capability is not required by them.
- `unavailable`: do not fabricate output; reroute to a safe equivalent or mark dependent work blocked.
- `failed`: retry once only for a reported transient failure; otherwise reroute or stop the affected branch.
- `skipped`: dependents must not treat the node as having produced evidence.

## 4. Write safety

Before implementation or any file-writing agent:

- calculate write scopes;
- reject conflicting concurrent writes;
- serialize overlapping writes;
- preserve the user's requested scope.

## 5. Budget adaptation

If the requested roster exceeds the phase budget:

1. keep mandatory gates;
2. keep directly relevant specialists;
3. merge redundant analysis where the host/model can do so safely;
4. explicitly record omitted agents as `budget-pruned`, not `executed`.

## 6. Completion condition

A phase is complete only when every mandatory node is:

`success | partial-with-accepted-degradation | explicitly-blocked`

A planned-but-never-dispatched node is not complete.

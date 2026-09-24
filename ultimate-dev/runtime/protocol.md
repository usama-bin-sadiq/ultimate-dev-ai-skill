# Ultimate-Dev Runtime Protocol

The runtime is the durable control plane. Models reason, orchestrators
coordinate, JEV evaluates deterministic policy, tools act, and the runtime owns
state, checkpoints, verification, recovery, and evidence.

## Lifecycle

```text
CAPTURE → RESUME/CREATE → DISCOVER → CONTRACT → CLASSIFY → PATTERN
       → PLAN → JEV ASSESS → CHECKPOINT → EXECUTE → OBSERVE
       → VERIFY → PERSIST → COMPLETE
```

On failure: `DIAGNOSE → RECOVER/ROLLBACK → REPLAN → CHECKPOINT → EXECUTE`.

## JEV boundary

The host adapter supplies a structured request containing model assessment,
capability facts, policy, and approvals. JEV returns a versioned decision
packet. The Runtime validates and persists that packet before an execution
transition, binds it to the task and exact action fingerprint, and only permits
a host capability when the packet has `execution_effect: execute` and
`guardrail.action: approve`.

JEV is a recommendation boundary, not a second runtime. The Runtime remains
responsible for final action scope checks, confirmation, state transitions,
evidence, and recovery.

## Invariants

1. A model claim is not evidence.
2. Every mutating node gets a durable state transition.
3. A context-window reset must not erase task state.
4. Only relevant context is loaded; deep context is progressive.
5. Independent nodes may run in parallel; dependent nodes wait for verified prerequisites.
6. Destructive actions require an explicit policy decision.
7. Completion requires the task contract and evidence to pass.
8. Recovery is idempotent where practical and records failed approaches.
9. JEV has no model, tool, subprocess, installer, browser, container, or network side effects.
10. Missing host capabilities are reported, never installed or silently substituted.
11. Human review is a blocking state, not a model-tier upgrade.
12. Tool selection is intersection-only: requested, host-available, and policy-allowed capabilities.
13. Every mutating execution has an operation identity, action fingerprint, and durable result status.
14. A persisted decision is revalidated and rebound after process restart; unbound or stale decisions cannot execute.
15. Completion requires contract criteria, required evidence, and no pending verification or blockers.
16. Workflow capability steps without an explicit host authorizer fail closed.
17. MCP tools are untrusted until the host marks their trust and schema; fallback is never implicit.
18. Memory context is provenance-scoped, freshness-aware, bounded, and refuses credential material.
19. Self-evolution candidates cannot publish canonical files without passing evaluation and explicit admission.
20. Evaluation reports backend provenance and distinguishes `not_run`/`uncertain` from a verified pass.

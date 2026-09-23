# Ultimate-Dev 2.5 Runtime Protocol

The runtime is the durable control plane. Models reason, orchestrators coordinate, tools act,
and the runtime owns state, checkpoints, verification, policy, and recovery.

## Lifecycle

`CAPTURE → RESUME/CREATE → DISCOVER → CONTRACT → CLASSIFY → PATTERN → PLAN → CHECKPOINT → EXECUTE → OBSERVE → VERIFY → PERSIST → COMPLETE`

On failure: `DIAGNOSE → RECOVER/ROLLBACK → REPLAN → CHECKPOINT → EXECUTE`.

## Invariants

1. A model claim is not evidence.
2. Every mutating node gets a durable state transition.
3. A context-window reset must not erase task state.
4. Only relevant context is loaded; deep context is progressive.
5. Independent nodes may run in parallel; dependent nodes wait for verified prerequisites.
6. Destructive actions require an explicit policy decision.
7. Completion requires the task contract and evidence to pass.
8. Recovery is idempotent where practical and records failed approaches.

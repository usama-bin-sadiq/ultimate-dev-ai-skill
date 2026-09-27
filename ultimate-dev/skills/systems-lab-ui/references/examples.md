# Systems Lab UI examples

## 1. Interaction-correlated workflow

Use this when explaining a complete interaction rather than starting at a normalized command.

```text
Thread message
    ↓ call: interpret message
Conversation Agent
    ↓ call: submit typed intent
Command + Policy
    ↓ commit: start allowed transition
Workflow Kernel
    ↓ claim: lease runnable Step
Workflow Worker
    ↓ call: execute Step
Step Executor
    ├─→ Agent Run
    └─→ Deterministic Adapter
    ↓ return: Step result
Workflow Kernel
    ↓ commit: Domain Event + Delivery
Delivery Worker
    ↓ call: rehydrate exact Thread
Conversation Agent
    ↓ commit: append reply idempotently
Same Thread
```

The correlated Thread identity belongs on the initial message, durable Delivery, and final append. The canvas should make that continuity visible without implying that the kernel understands conversations.

## 2. Load-management lab

Use this when the user wants to understand what happens during a large burst.

```text
100,000 Thread messages
          ↓
Conversation Run queue
          ↓ claim
Conversation workers
          ↓ typed Commands
Command + Policy
          ↓
Workflow queue in durable storage
          ↓ claim
Workflow workers
          ↓
Step Executor ──→ Agent runs
          │       Deterministic work
          ↓
Results, retries, and Waits
          ↓
Domain Events + Deliveries
          ↓ claim
Delivery workers
          ↓
Exact Threads
```

Make the burst adjustable. Put worker-capacity controls next to their pools. Highlight only the component whose pressure threshold is currently exceeded. Show how adding workers changes queue depth and throughput over the deterministic trace.

## 3. Incident investigation

Use a longer scenario to demonstrate durable progression:

```text
incident reported
    ↓
normalize report
    ↓
collect evidence
    ↓
Wait for operator confirmation
    ↓
run containment action
    ↓
Wait for service-owner verification
    ↓
publish resolution
    ↓
deliver update to originating Thread
```

Represent executable Steps as runtime work, confirmations as dashed Wait cards, durable transitions as commits, and operator responses as accepted Signals. The trace should distinguish the business decision from kernel mechanics.

## Requests that should trigger this skill

- “Show me visually how this workflow works end to end.”
- “Build a GANLab-style demo for our architecture.”
- “I need to explain where load and backpressure happen.”
- “Turn this sequence diagram into something movable and interactive.”
- “Show agents, workers, queues, retries, and delivery on one canvas.”
- “This dashboard is just numbers. Make the system understandable.”

## Completion example

A concise handoff should say:

> Built the operational canvas at `/system/prototype`. It includes deterministic playback, Flowing now and Full path views, movable nodes, organize/reset, a toggleable trace, and a labeled presentation fallback when the live adapter is offline. Verified the complete scenario at the current and narrow browser widths; typecheck and lint pass.

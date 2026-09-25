# Ultimate-Dev Runtime

The canonical runtime boundary is host-neutral. It owns durable task state,
context, checkpoints, policy gates, evidence, verification, and recovery.

## JEV decision path

```text
model assessment + host facts
        ↓
JEV decision kernel
        ↓
decision packet
        ↓
runtime gate + host-native capabilities
```

The language-neutral contracts are:

- `schemas/jev-decision-request.schema.json`
- `schemas/jev-decision-packet.schema.json`

`jev/engine.mjs` is a dependency-free reference implementation. It uses no
model provider, package manager, subprocess, browser, container, or network
service. Other hosts can implement the same contract natively.

```javascript
import { decide } from "./jev/engine.mjs";

const packet = decide(request);
if (packet.execution_effect === "execute") {
  // Map packet.capability_plan.selected IDs to native host tools.
}
```

A host must persist the packet and re-check the actual action and scope before
execution. `human_review` and `stop` are blocking outcomes. Missing required
capabilities are reported; JEV never installs or substitutes a provider.

## Legacy Python API

The older Python Runtime remains as an optional compatibility surface for
existing callers. It is not required for the host-native JEV path and does not
select a sandbox or browser provider. A host can inject a capability executor:

```python
rt = Runtime(project_root, host_executor=adapter.execute)
```

When the Runtime is configured with `require_jev_decision=True` (the default),
execution is blocked until a host-produced decision packet has been recorded,
bound to the task, approved capability ID, and exact action fingerprint. The
legacy `require_jev_decision=False` constructor option exists only for explicit
compatibility/test setups; a per-call argument cannot disable a strict Runtime.
The Python JEV package under `runtime/core/jev/` is legacy compatibility
material and is not imported by the canonical Runtime or SessionManager.

State remains at `.memory/ultimate-dev/tasks/<task-id>/`, so a fresh session
can reconstruct the next safe action from disk. Mutating `execute_code` calls
also create durable operation records under `operations/`; repeated calls with
the same operation ID return the prior result rather than duplicating a side
effect. `operation.json` documents the portable operation record shape.

## Optional platform components

The runtime keeps platform features dependency-free and host-injected:

- `core/registry.py` and `core/workflow.py` provide a canonical JSON catalog,
  referential validation, bounded dependency ordering, and a deterministic
  fail-fast workflow executor. Capability-backed workflow steps routed through
  `Runtime.execute_workflow()` require an explicit `capability_authorizer`; the
  authorizer is the host's JEV/policy/operation boundary.
- `core/mcp.py` is an optional MCP seam. It accepts an injected transport,
  validates the supported JSON-schema subset, requires explicit trust for
  untrusted tools, reports health without installing a provider, and exposes
  explicit fallback and task-handle operations. It never becomes a mandatory
  runtime dependency.
- `core/memory.py` stores bounded project memory records with provenance,
  scope, freshness, supersession/contradiction handling, retention, sensitivity
  filtering, secret refusal, and deterministic budgeted context projection.
  `ContextManager(..., memory_store=...)` can project that memory safely.
- `core/evolution.py` is a governed candidate lifecycle. Proposals are staged
  and evaluated under `.memory`; publication creates a receipt only and never
  writes canonical skills, agents, or manifests.
- `evaluation.py` runs provider-neutral scripted/golden cases through injected
  classifier, agent, and independent verifier callables. It reports
  `not_run`/`uncertain` honestly when a backend or verifier is absent; a
  fixture is not presented as a real model benchmark.

These components are bounded building blocks, not claims of distributed
consensus, provider installation, or a production multi-tenant deployment.

## Lifecycle, routing, and cleanup

- `core/lifecycle.py` adds explicit `paused`, `interrupted`, and `abandoned`
  transitions, stale-operation reconciliation, checkpoints, and idempotent host
  resource cleanup.
- `core/task_router.py` distinguishes continuation, clarification, new-task,
  abandon, and ambiguous messages. Ambiguous routes fail closed and cannot
  execute against the active task.
- The repository YAML workflow corpus is documentation-only; executable
  workflows must be supplied as validated typed `WorkflowCatalog` descriptors.
  This prevents an unvalidated YAML file from becoming an execution authority.
- `core/retention.py` performs age/status-based task archival and optional
  deletion. Dry-run is non-destructive; deletion requires an exact confirmation
  token, archive-before-delete, symlink checks, and preservation of active,
  failed, blocked, and uncertain work by default. Archived tasks can be
  restored with `TaskRetentionManager.restore()`; confirmation records are
  short-lived and durable across separate CLI processes.
- `core/mcp.py` applies transport deadlines, validates task handles, and marks
  deadline expiry as uncertain rather than retrying automatically.
- `python -m runtime.task_admin --project-root <path> ...` exposes status,
  lifecycle, routing, safe cleanup, and archive restore operations.

The host must still invoke these lifecycle hooks at session boundaries. They
are durable protocol primitives, not an operating-system service or a universal
browser/process supervisor.

## Host execution trust boundary

The Runtime and JEV authorize an action; they do not implement the operating
system isolation around the host adapter. A host integration is production-ready
only when it explicitly provides:

1. Capability descriptors with accurate availability, effects, reversibility,
   and isolation metadata.
2. A scoped policy and approval source for every side effect.
3. An executor that enforces the declared filesystem, process, network, and
   browser boundaries.
4. Timeout, cancellation, failure, and external-state reconciliation results.
5. Audit/metrics ownership for host-side actions.

A host adapter must not silently broaden a Runtime-approved capability, install
missing providers, or treat a local classifier as a sandbox. These obligations
are part of the adapter contract, not optional documentation.

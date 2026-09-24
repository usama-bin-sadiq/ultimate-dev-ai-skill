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

When the Runtime is configured with `require_jev_decision=True`, execution is
blocked until a host-produced decision packet has been recorded. The Python
JEV package under `runtime/core/jev/` is legacy compatibility material and is
not imported by the canonical Runtime or SessionManager.

State remains at `.memory/ultimate-dev/tasks/<task-id>/`, so a fresh session
can reconstruct the next safe action from disk.

# Runtime Adapter Contract

Adapters translate a host/model/tool environment into the canonical runtime protocol.

Required operations:
- `discover()` → host, project instructions, available tools, model limits
- `activate()` → expose the Ultimate-Dev entry skill using native host conventions
- `load_context(request)` → progressive, budget-aware context
- `invoke(model_input)` → model returns structured next action
- `execute(action)` → execute through registered capabilities
- `observe()` → collect outputs and environment changes
- `verify(contract)` → return evidence-backed results

Adapters MUST NOT own durable task state. The runtime owns it.
If a host lacks a feature, the adapter degrades to the closest supported pattern.

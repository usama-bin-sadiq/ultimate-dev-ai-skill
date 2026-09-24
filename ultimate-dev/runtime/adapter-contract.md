# Runtime Adapter Contract

Adapters translate a host/model/tool environment into the canonical runtime
protocol. They do not own durable task state or make hidden provider choices.

## Required operations

- `discover()` → host instructions, model capabilities, and a canonical capability catalog
- `activate()` → expose the Ultimate-Dev entry skill using native host conventions
- `load_context(request)` → progressive, budget-aware context
- `invoke(model_input)` → model returns a structured assessment and capability proposal
- `assess(jev_request)` → deterministic JEV decision packet
- `persist_decision(packet)` / `record_jev_decision(packet)` → runtime stores the packet before execution
- `execute(action, approved_capability_ids)` → invoke only mapped host-native capabilities
- `observe()` → collect outputs and environment changes
- `verify(contract)` → return evidence-backed results

## JEV adapter rules

1. The model supplies intent, scores, and a proposal; it does not supply host
   availability, policy, isolation, or approvals.
2. The adapter maps canonical IDs such as `filesystem.read` and
   `browser.navigate` to native tools.
3. The adapter must not install a browser, container, model provider, or other
   dependency when a capability is missing.
4. The adapter must pass a JEV packet to the runtime before an execution
   transition.
5. A packet with `execution_effect: review` or `stop` is non-executable until
   a new trusted decision is produced.
6. JEV is optional as an implementation detail, but privileged execution is
   not allowed to bypass the decision boundary.

If a host lacks structured output, schema validation, or a decision engine,
the adapter must degrade to planning/review/stop rather than fail open. A
missing capability is an explicit result, not a reason to guess a provider.

The runtime owns durable state; adapters own host integration only.

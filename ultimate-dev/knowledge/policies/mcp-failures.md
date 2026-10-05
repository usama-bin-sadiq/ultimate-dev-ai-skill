# MCP failures

## Purpose

This policy defines how failures from MCP providers reach the kernel and what
each one disposes. MCP is a provider mechanism, not the architecture: skills,
agents, and workflows name capabilities, and only the runtime resolves
providers. Its purpose is to stop two errors: a raw transport error leaking
into a decision that should see a normalized failure, and an MCP failure being
read as a capability's absence.

## Policy statement

MCP errors reach the kernel **normalized**, never raw. The raw error is kept as
evidence attached to the normalized record. There are six normalized failures,
each with a defined first response and a defined terminal condition; a response
outside the table is an ad-hoc decision and gets recorded as one. Fallback
walks the provider chain in `fallback_order`, and a capability with no
remaining provider is not blocked — it re-enters the kernel's capability
resolution order (existing → compose → acquire → create). No workflow, skill,
or agent record may name an MCP server; a record that does has coupled itself
to one provider and the fallback chain cannot engage.

## Normalized failures

| Failure | Meaning |
|---|---|
| `MCP_UNAVAILABLE` | The server cannot be reached or is not running |
| `MCP_CONNECTION_FAILED` | The connection was attempted and failed |
| `MCP_TOOL_NOT_FOUND` | The server does not expose the resolved tool |
| `MCP_PERMISSION_DENIED` | The call violated the capability permission set |
| `MCP_TIMEOUT` | The call exceeded its bound |
| `MCP_INVALID_RESPONSE` | The response could not be parsed or violated its contract |

## Decision table

| Condition | Required action |
|---|---|
| `MCP_TIMEOUT` | Retry once with an adjusted bound; then fall back to the next provider in `fallback_order`. |
| `MCP_UNAVAILABLE` or `MCP_CONNECTION_FAILED` | Fall back to the next provider; record the mechanism that reported the outage. Retry only when the runtime reports the server recovered. |
| `MCP_TOOL_NOT_FOUND` | Re-resolve the capability mapping — the registry entry is stale or the server changed. If no mapping holds, fall back; never call a tool by a guessed name. |
| `MCP_PERMISSION_DENIED` | Never retry. The permission set is the boundary. Escalate: either the agent's contract is too broad, or the task needs an authority the environment has not granted. |
| `MCP_INVALID_RESPONSE` | Treat as a verification failure of that call: record the raw payload as evidence, fall back, and mark the provider's `reliability` down after a second occurrence. |
| Two providers for one capability fail in one run | Stop walking the chain and re-enter capability resolution; the problem is no longer provider choice. |
| No provider remains for a required capability | Not a blocker by itself. Re-enter the resolution order — another capability, composition, acquisition, or creation may cover the need. Blocked is what is left after that. |
| The same MCP failure recurs across runs | Record against the provider record, not the run. A provider whose failure mode is chronic changes its `fallback_order` or leaves the registry. |

## Escalation and exceptions

- **`MCP_PERMISSION_DENIED` on a write capability.** Stop and ask the user.
  Denied writes are the environment communicating authority, and no retry
  changes it.
- **Fallback into a provider that has never been exercised.** Exercise it on a
  read before depending on it for a write. A fallback that has never run is a
  hope, not a fallback.
- **A task whose only provider is MCP and the server is down.** The capability
  is unavailable *through that provider*; say exactly that. "The capability is
  unavailable" without naming the provider layer is the confusion this policy
  exists to prevent.
- **MCP configuration belongs to the runtime and environment, not the skill
  package.** The skill carries the vocabulary and this policy; the registry of
  servers is runtime state. `resources/mcp-registry.example.yaml` shows the
  shape; it is not a live configuration.

## Related

`recovery-system.md` — the nine failure classes; an MCP failure classifies as
resource failure or coordination failure. `retry-policy.md` — the routes walked
before anything is declared absent. `../schemas/provider.md` — the provider
record this policy reads and writes.

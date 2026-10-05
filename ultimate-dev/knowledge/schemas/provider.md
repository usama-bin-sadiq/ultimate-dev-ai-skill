# Provider

## Purpose

The provider record is one implementation of a capability: how the runtime
reaches it, what it costs, and when it is chosen. Skills and agents request
**capabilities**; providers are how capabilities get done. Several providers may
implement the same capability, and the record exists so the runtime can choose
between them — and fall back between them — on evidence rather than on
whichever name the request happened to contain.

## Shape

```yaml
provider:
  id: string
  kind: native | mcp | api | cli | remote-service | database-connector | ide-integration
  implements: [string]            # capability ids from resources/capability-vocabulary.yaml
  entrypoint: string              # how the runtime reaches it, host-specific
  availability: available | unavailable | unknown
  permissions: [string]           # capability ids this provider may serve in this environment
  reliability: high | medium | low | unknown
  latency: low | medium | high | unknown
  cost: low | medium | high | unknown
  compatibility: [string]         # model tiers it can serve
  fallback_order: integer         # position in the chain, per capability
  failure_modes: [string]         # normalized failure ids — see policies/mcp-failures.md
```

## Fields

| Field | Type | Req | Meaning |
|---|---|---|---|
| `implements` | list | yes | The capabilities this provider can satisfy. One provider may implement several; one capability may have several providers. |
| `entrypoint` | string | yes | The concrete address. Host-specific, and never inferred from the provider's name. |
| `availability` | enum | yes | `unknown` is never converted to `available` by assumption. |
| `permissions` | list | yes | What this environment allows it to serve. A provider outside the permission set is not a candidate. |
| `fallback_order` | int | yes | Lower is tried first. The chain is walked on failure, per capability. |
| `failure_modes` | list | yes | The normalized failures this provider can produce, so the kernel never has to parse a raw transport error. |

## Field rules

- A provider id appears nowhere in a skill, agent, or workflow record. Those
  name capabilities; only the runtime resolves providers. A leaked provider id
  is the tool-coupled-skill anti-pattern with a schema.
- Selection between providers for one capability is recorded with its criteria:
  availability, permissions, compatibility, reliability, latency, cost, and the
  task's requirements. A choice with no recorded criteria is a default, and
  defaults are how the slow expensive provider becomes the permanent one.
- `availability: unavailable` requires the mechanism that reported it —
  discovery probe, failed call, host report. "It seems down" is a hypothesis.
- `fallback_order` is per capability, not global: a provider can be first
  choice for `file_read` and last resort for `file_write`.
- `entrypoint` for `kind: mcp` names a server id from the runtime's MCP
  registry, not a tool name. The adapter resolves tools; the record stays
  stable when a server renames them.

## Worked example

`file_read` with three providers, from the vocabulary:

```yaml
provider:
  id: native-fs
  kind: native
  implements: [file_read, file_write]
  entrypoint: host file capability
  availability: available
  permissions: [file_read, file_write]
  reliability: high
  latency: low
  cost: low
  compatibility: [tiny, small, medium, large, huge]
  fallback_order: 1
  failure_modes: [PROVIDER_UNAVAILABLE, PROVIDER_TIMEOUT]
---
provider:
  id: mcp-filesystem
  kind: mcp
  implements: [file_read, file_write]
  entrypoint: mcp://filesystem
  availability: available
  permissions: [file_read]
  reliability: medium
  latency: low
  cost: low
  compatibility: [medium, large, huge]
  fallback_order: 2
  failure_modes: [MCP_UNAVAILABLE, MCP_CONNECTION_FAILED, MCP_TOOL_NOT_FOUND, MCP_PERMISSION_DENIED, MCP_TIMEOUT, MCP_INVALID_RESPONSE]
---
provider:
  id: repo-api
  kind: api
  implements: [file_read, repository_read]
  entrypoint: remote repository API
  availability: unknown
  permissions: [file_read, repository_read]
  reliability: unknown
  latency: high
  cost: medium
  compatibility: [medium, large, huge]
  fallback_order: 3
  failure_modes: [PROVIDER_UNAVAILABLE, PROVIDER_TIMEOUT, PROVIDER_INVALID_RESPONSE]
```

The agent asked for `file_read`. The runtime walks the chain: native, then
MCP, then the API. The agent's contract does not change.

## Validation

Mechanical:

- Every `implements` and `permissions` entry resolves to the vocabulary.
- `fallback_order` is unique per capability across providers.
- `availability: unavailable` names the reporting mechanism.
- `kind: mcp` ⟹ `failure_modes` uses only the normalized MCP ids.

Judgement, not automatable:

- Whether `reliability`, `latency`, and `cost` were observed or assumed. An
  assumed `high` reliability is the selection criteria going unrecorded in
  disguise.
- Whether the fallback chain is real. A second provider that has never been
  exercised is not a fallback; it is a hope.

## Anti-patterns

- **The permanent default.** The first provider that worked becomes the only
  one ever selected, because no selection was ever recorded and reviewed.
- **Fallback on paper.** Three providers listed, one ever used, the other two
  untested — discovered during the outage.
- **Permission by reachability.** A provider used for a capability outside its
  `permissions` because it happened to answer. The permission set is the
  boundary, not the network.

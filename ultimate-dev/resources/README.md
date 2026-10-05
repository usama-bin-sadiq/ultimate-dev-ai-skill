# Resources

Operational data the kernel and the runtime read — the vocabulary, registries,
and profiles that sit **below** the doctrine in `references/` and the record
contracts in `knowledge/`.

Three kinds of thing live in this repository layer, and they are not the same:

```text
references/   doctrine        — how the kernel decides
knowledge/    contracts       — what records are, and what must happen to them
resources/    operational data — the vocabularies and profiles those records name
```

| File | What it is |
|---|---|
| `capability-vocabulary.yaml` | The provider-neutral capability ids. The only names skills, agents, and workflows may request. Providers and fallback chains per id. |
| `model-profiles.yaml` | The five model tiers, their capability profiles, and the mapping onto the kernel's three host tiers. |
| `mcp-registry.example.yaml` | The **shape** of an environment's MCP registry. Example only — a live registry is runtime state, not skill content. |

## Rules for this layer

1. Data here is **named by** records and doctrine; it never names them back.
   A skill or agent that references a provider id instead of a capability id
   is the tool-coupled anti-pattern — see `knowledge/schemas/provider.md`.
2. Entries are provider-neutral. A concrete tool or server name appears only
   as an `entrypoint` or `tool` field under a provider mapping, never as the
   capability itself.
3. Examples are marked as examples. Anything an environment must supply for
   itself says so at the top of the file.

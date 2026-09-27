# Optional MCP packaging

The skill should remain the source of behavioral instructions. Add MCP only when several tools or teams need one centrally hosted copy of its templates.

## Recommended boundary

Expose read-only resources:

- `systems-lab://skill`
- `systems-lab://reference`
- `systems-lab://examples`
- `systems-lab://template/react-flow-primitives`
- `systems-lab://template/styles`

Optionally expose two narrow tools:

```text
validate_visual_model(model) → findings
scaffold_system_canvas(target, overwrite=false) → created files
```

`validate_visual_model` should be pure. It checks that nodes have semantic owners, edges have kinds and directions, identities appear on owning nodes, and active traces reference existing topology.

`scaffold_system_canvas` is a local-write action and must require the caller's normal write approval. It should copy the same bundled assets used by the local script and refuse accidental overwrites.

Do not place browser automation, domain discovery, or visual judgment inside the MCP server. The agent performs those tasks using this skill. MCP distributes stable resources and deterministic utilities.

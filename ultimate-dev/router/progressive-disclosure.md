# Progressive Disclosure Rules

Ultimate-Dev is an all-in-one capability package, not an all-in-one context
payload. Keep the entrypoint small and load only what the task needs.

## Three levels

1. **Metadata** — name, description, triggers, capability status, and fallback.
2. **Core method** — selected `SKILL.md` or module instructions.
3. **References** — schemas, examples, templates, and deep domain material.

## Load rules

- Always load only metadata and the task contract.
- Load one core method after deliverable/domain classification.
- Load references only when the selected method requires them.
- Load a specialist only when the common method is insufficient.
- Do not load all agents, modules, or references into the main context.
- Offload large tool output to evidence/artifact storage and keep a bounded
  summary in the working context.

## Budget checks

`measure-entrypoint.py` measures SKILL.md, AGENTS.md, AGENT.md, and the
orchestrator. A change that grows an always-loaded entrypoint without a
progressive-disclosure reason should fail the local budget gate.

## Trade-off

Progressive disclosure adds a small discovery step but prevents context bloat,
reduces token cost, and keeps the package usable by small-context hosts.

# 0014. Package composition contracts from new-implementation.md, Phase 1

Status: Accepted
Date: 2026-10-05
Deciders: architecture maintainers

## Context

`new-implementation.md` proposes a model-agnostic, tool-neutral package
architecture: skill / agent / capability / provider / tool / workflow /
artifact as first-class entities, a declarative manifest, an MCP integration
layer behind a provider abstraction, and model capability profiles. Its own
migration plan (§48) is phased, and Phase 1 is *define the contracts*.

The kernel already holds the **run** records — task, decision, context,
capability, skill, evidence, observation, experience, learning in
`knowledge/schemas/`. What it does not hold are the **composition** records:
what an agent's dispatch contract is, what a provider of a capability is, what
a typed stage artifact is, and what a declarative workflow is. Those four are
the difference between a package whose parts are implied by convention and one
whose parts can be validated.

The PRD also proposes a target package layout (§9) and the eventual rebuild of
the root skill (Phase 5). Those are restructuring decisions with destructive
steps, and the PRD itself sequences them after the contracts.

## Decision

Adopt Phase 1 now, in the existing layout:

1. Four new composition schemas — `knowledge/schemas/agent.md`,
   `provider.md`, `artifact.md`, `workflow.md` — in the established
   shape/purpose/rules/example/validation format.
2. One new policy — `knowledge/policies/mcp-failures.md` — normalizing the six
   MCP failure ids and their dispositions.
3. A new `resources/` tree for operational data:
   `capability-vocabulary.yaml` (the only names skills, agents, and workflows
   may request), `model-profiles.yaml` (five model tiers mapped onto the
   kernel's three host tiers), and `mcp-registry.example.yaml` (marked as an
   example; a live registry is runtime state).
4. A declarative `manifest.yaml` at the skill root describing the package as
   it exists.

Deferred, explicitly:

- The §9 target package layout and Phase 5 rebuild of the root skill.
- Separate `contract.yaml` files per agent. Agent contracts are carried in the
  role files per `knowledge/schemas/agent.md`; a second copy would drift.
- Phases 2–4 and 6–7 of the migration (extraction, runtime abstractions, the
  MCP adapter build, compatibility adapters, legacy removal).

## Consequences

- Skills, agents, and workflows may now name only capability ids from
  `resources/capability-vocabulary.yaml`. Provider names in contracts are the
  tool-coupled anti-pattern the new schemas reject.
- The kernel vocabulary is unchanged: nothing in `SKILL.md`, the references,
  or the run-state machinery is renamed. The PRD's entity model maps onto it
  (orchestrator ↔ kernel, workflow engine ↔ JEv + coordination modes,
  capability registry ↔ bootstrap registry) rather than replacing it.
- `capability-routing.md`'s capability card and hand-off packet now have
  normative backing: the card reads `agent.md`/`capability.md`; the packet's
  output is typed by `artifact.md`.
- The manifest is descriptive, not generative. It must be edited when the
  package layout changes; `tools/validate-skills.py` does not yet check it,
  and adding that check is follow-up work.
- The PRD's Definition of Done (§51) is **not** met by this change. Phase 1
  makes the contracts exist; the orchestration, model-independence, and
  operations checkboxes remain program work.

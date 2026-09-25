# Ultimate-Dev Department Coverage and Optimization Plan

**Date:** 2026-09-25
**Positioning:** prompt-first agentic CLI and software-engineering skill suite

## Current position

Ultimate-Dev has strong technical and cross-functional coverage: 119 agents, 33 reusable skills, 20 capability domains, and 46 domain modules. It covers software engineering, infrastructure, data, security, testing, research, finance, marketing, sales, support, healthcare, games, GIS, and several specialized domains.

The next improvement is not adding hundreds more agents. The suite now has a compact capability index, a universal task fallback, portable contracts, reusable cross-functional skills, and optional execution roles for company departments that are currently weak or missing.

## Highest-value missing capability packs

The first P1 slice is now implemented as prompt skills. The remaining work is
mostly company-specific references, templates, and behavioral validation.

| Capability pack | Current state | Next step |
|---|---|---|
| Product discovery and requirements | Skill available | Add company PRD templates and behavioral routing cases |
| Planning and execution control | Skill available | Add worktree/ledger templates for tool-enabled hosts |
| Internal communications | Skill available | Add channel-specific and executive templates |
| Business analysis and strategy | Skills available | Add market, operating-model, and decision benchmark fixtures |
| FP&A and financial analysis | Finance agents/modules plus accounting skill | Add finance data schemas and review fixtures |
| Accounting and controllership | Skill available; human review required | Add jurisdiction-specific close/control references |
| Legal, privacy, and contracts | Skill available; human review required | Add clause library, retention schedules, and legal-hold templates |
| People operations / HR | Skill available; human review required | Add policy-specific and privacy-preserving workflows |
| Procurement and vendors | Skill available; human review required | Add vendor risk and approval templates |
| Internal audit and controls | Skill available | Add evidence, sampling, and finding fixtures |
| Office artifacts and knowledge work | Skill available | Add format-specific helpers and company templates |
| Data analysis and BI | Skill available | Add metric/lineage examples and evaluation cases |
| Automation and integrations | Partial | Add API/MCP/webhook/schedule design, idempotency, retries, observability, and rollback |
| Prompt and skill quality engineering | Skill available | Run cross-department routing and outcome benchmarks |
| ESG, public sector, assets, and facilities | Missing | Add later as reference packs after the core cross-functional workflow is stable |

## Prompt-first architecture

```text
L0  Compact task contract and four-channel handoff
L1  Capability index: deliverable → domain → skill → optional agent → fallback
L2  Selected methodology skill
L3  Optional specialist execution agent
L4  Optional runtime: state, JEV, approvals, retention, recovery
L5  Host adapter: native discovery, tools, permissions, model capabilities
```

The core Markdown skill should work without Python, JEV, a runtime service, or a specific tool. Durable runtime extensions should be loaded only when a task needs persistence, approvals, side effects, or recovery.

## Efficiency rules

1. **Skills before agents.** A repeatable method belongs in `skills/`; a tool-using execution role belongs in `agents/`.
2. **One primary specialist per domain.** Add a second agent only for independent validation or a genuinely different responsibility.
3. **Short frontmatter.** Put broad examples and detailed patterns in the body, not in every agent's metadata.
4. **Progressive disclosure.** Load metadata first, the selected skill next, and references/assets only when needed.
5. **Capability-based routing.** Use intent plus repository context, not model names or one generic keyword.
6. **Explicit risk gates.** Financial, legal, privacy, people, audit, and production actions require evidence and human review boundaries.
7. **No duplicated authority.** Generate the agent catalog from one source and validate workflow aliases separately.
8. **Measure outcomes.** Track routing precision, false activation, context tokens, cost, completion, evidence quality, and unsafe side-effect attempts.

## Immediate P0 work

- [x] Unify `skill-manifest.yaml` and `config/agent_registry.yaml` without mixing concrete and abstract roles.
- [x] Separate abstract workflow roles from concrete agent IDs.
- [x] Synchronize entry-point metadata and generated documentation.
- [x] Make JEV/runtime optional in the prompt-first core.
- [x] Add a compact deliverable/domain capability index used by the router.
- [x] Add trigger-collision and metadata-size reports.
- [x] Add 154 golden routing cases with forbidden-route and multilingual fixtures.
- [x] Add a provider-free routing benchmark and portable contracts.

## Implemented cross-functional skill slice

The first company-capability skills are now present:

- discovery-requirements
- planning-execution
- internal-communications
- business-analysis
- strategy-operating-model
- data-analysis-bi
- accounting-finance
- legal-privacy
- people-operations
- procurement-vendors
- office-artifacts
- audit-controls
- prompt-evaluation
- universal-task
- project-context

These provide broad value across software agencies and companies without
requiring a large number of new agents. The next step is to add references,
templates, and behavioral evaluation cases rather than more top-level agents.

## Research evidence

The detailed source comparison, inventory measurements, gap analysis, and roadmap are recorded at:

```text
.memory/ultimate-dev/tasks/research-agentic-cli-suite-2026-09-25/evidence/external-comparison-and-optimization-report.md
```

Primary sources include the Agent Skills specification, MCP specification/security guidance, Claude Code, OpenCode, Cursor, GitHub Copilot, Cline, Aider, OpenAI Agents SDK, Microsoft Agent Framework, Anthropic skills, OpenHands, SWE-agent, Superpowers, wshobson/agents, and GitHub awesome-copilot.

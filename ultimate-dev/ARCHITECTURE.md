# Architecture — ultimate-dev

This document is for people extending or maintaining the skill. For the
unified research-backed architecture and internal-only roadmap, see
`docs/architecture/UNIFIED-AGENT-ROADMAP.md` in the repository root.
For user-facing docs, see README.md.

## Portable control-plane contracts

The prompt-first core is defined by a small set of contracts. They are portable
YAML/Markdown: any host can implement them, and none requires a package.

| Contract | Owns |
|---|---|
| `contracts/task-envelope.yaml` | The four channels: intent, knowledge, action, evidence |
| `contracts/task-state-machine.yaml` | Lifecycle states, transitions, and terminal-state invariants |
| `contracts/middleware-hooks.yaml` | Ordered, selective hooks that constrain but never authorize |
| `contracts/capability-manifest.yaml` | Capability fields, default-deny selection, host boundary |
| `contracts/subagent-contract.yaml` | Bounded worker isolation, budgets, and output validation |
| `contracts/handoff-contract.yaml` | Minimal stage handoff and final synthesis fields |
| `contracts/memory-provenance.yaml` | Provenance, sensitivity, retention, and supersession |
| `contracts/hitl-interrupt.yaml` | Interrupt reasons and resume requirements |
| `contracts/four-channels.md` | Portable prose form of the channel contract |

Routing guidance has a single source of truth for decision values:

- `router/behavioral-calibration.md` — deliverable, size, domain, risk,
  capability-gap values, the one-pass self-check, and the edit and
  unfamiliar-domain rules.
- `router/classification-rules.md` — only the mechanics: applying the capability
  index, selecting a specialist, and handing off work. It must not restate the
  value vocabularies.
- `router/progressive-disclosure.md` — metadata/core/reference loading order.
- `router/context-projection.md` — what each stage may and may not carry.

Local enforcement, all provider-free:

| Script | Purpose |
|---|---|
| `scripts/validate-routing-decision.py` | Lints one decision record: vocabulary, route resolution, risk justification, gap coherence, one-pass self-check |
| `scripts/measure-entrypoint.py` | Budgets always-loaded entrypoints so context cost cannot silently grow |
| `scripts/replay-gate.py` | Fails a recorded replay on regression, pass-rate drop, forbidden activation, or missing predictions |
| `scripts/compare-routing-predictions.py` | Field-level comparison; `--fields` restricts scoring to a declared reliable subset |
| `scripts/validate-task-state.py` | Confirms durable task state is a single parseable JSON document with the fields a resume needs |

## How Tier 0 / 1 / 2 Work

### Tier 0 — Core Router (SKILL.md)

Always loaded, ~300-500 tokens. Contains:
- Capability Index (one line per domain module)
- Classification algorithm (mandatory before any action)
- Operating loop (11 steps)
- Non-negotiable rules
- Tier + module declaration format

Tier 0 is small enough to survive context pressure on every task. It is never evicted or summarized.

### Tier 1 — Domain Modules

Loaded only when classification selects them. The current manifest contains
**46 modules across 20 capability domains**; the generated manifest and
capability index are the source of truth for counts.

| Category | Departments | Modules |
|----------|-------------|---------|
| Engineering | backend, frontend, architecture, database, security, devops, mobile, testing-qa, documentation | 9 |
| Agency | project-management, product, design-handoff, client-comms | 4 |
| Business | marketing, sales, finance, support, paid-media | 5 |
| Research | research, academic | 2 |
| Domain-Specific | healthcare, game-dev, gis, spatial-computing, specialized | 5 |
| Cross-cutting | universal-principles, emerging-tech-handler | 2 |

Each module follows the §25 template:
- Frontmatter with name, description, triggers, anti-triggers
- Identity & Memory (role, personality, experience)
- Core Mission (domain-specific deliverables with code examples)
- Critical Rules (imperative, checkable)
- Technical Deliverables (code, templates, diagrams)
- Communication Style (how this domain talks)
- Anti-Patterns (paired negative/positive examples)
- Success Metrics (measurable outcomes)
- Current Tooling Notes (dated, isolated from principles)
- Output Contract
- Escalation Triggers

Modules are cached within a session — never re-loaded. Sub-agents receive only the specific principles that apply to their subtask, not the whole module.

### Tier 2 — Execution Personas

Loaded only inside a spawned sub-agent or internal mode-switch. Never enters the master's own context. Personas are domain-specific specialists with deep expertise.

## Classification Algorithm

Deterministic, in this exact order:
1. **Size**: atomic / moderate / complex
2. **Domain match**: against the current Capability Index (20 canonical domains)
3. **Risk flag**: auth, PII, payments, infra credentials, regulated data
4. **Clarity check**: if complex and ambiguous, ask ONE question before proceeding

## Decomposition (complex tier)

1. Restate goal and constraints
2. List domains and risk
3. Split into subtasks with clean interfaces
4. Write a contract per subtask (invocation template)
5. Build dependency order
6. Assign owners per Owner Decision table
7. Execute (parallel where possible)
8. Integrate and reconcile
9. Return structured result

## Owner Decision Table

| Condition | Owner |
|-----------|-------|
| Different domain lens, shares context | Mode-switch |
| Needs isolation, no sub-agent support | Mode-switch, simulated |
| Needs isolation, parallelism, sub-agent support | Real sub-agent |
| Sub-agent's subtask is complex | Sub-agent re-runs classification (max depth: 2) |

## Precedence Rules

1. Explicit user instruction
2. Security module (when risk flag set)
3. Architecture module (when structural decision)
4. Most specific matched module
5. Universal principles (tiebreaker)

## How to Test Changes

1. Modify `router/behavioral-calibration.md` for a decision rule, or
   `router/classification-rules.md` for routing mechanics
2. Lint the affected decision records:
   `python3 scripts/validate-routing-decision.py decision.json --strict`
3. Confirm the counterexamples still hold:
   `python3 -m pytest tests/test_calibration_cases.py -q`
4. Run a recorded replay and gate it:
   `python3 scripts/replay-gate.py --gold gold.json --predictions new.json --baseline old.json`
5. Run `node --test ultimate-dev/tests/jev/engine.test.mjs` for the host-native JEV contract
6. Run `python3 scripts/measure-entrypoint.py --strict` if an always-loaded file changed
7. Run `python3 scripts/validate-task-state.py <project>/.memory/ultimate-dev/tasks --strict`
   to confirm durable state is still resumable
8. Run `./scripts/verify.sh` for the full local gate

A prompt change without a replay result is not an improvement. If the replay does
not move, record the run and leave the rating unchanged.

## Project Memory (§15)

When this skill runs inside a project repo, it maintains a per-project cache at
`<repo>/.memory/ultimate-dev/project-memory.md` when durable runtime or a
user-managed memory workflow is enabled. This file is NOT part of the canonical
package and is never overwritten by updates.

### Contents (kept small — this is a cache, not a knowledge base)
- Detected stack/framework/language versions
- Established architectural patterns in use (e.g., "hexagonal, CQRS on write side")
- Links to ADRs written under documentation module
- Repo-specific conventions treated as constraints (e.g., "no ORM, raw SQL only")

### Rules
- Read at classification time if present — cheap since it's small by design
- Written to only when a complex task produces something durable — never speculatively
- Never treated as authoritative over the actual codebase — if memory and code disagree, flag the discrepancy
- Size ceiling: max 50 entries or 2KB, whichever is smaller — summarize oldest/least-relevant when exceeded

This is what makes the same task type cheaper in tokens the second and third time in a given repo.

## Observability & Feedback Loop (§18)

Each task's actual tier, modules loaded, sub-agents spawned, and retries are logged to a lightweight local record at `.ultimate-dev/task-log.jsonl`. This is NOT telemetry — it's a local, optional self-check mechanism.

### What gets logged
```json
{"ts":"2026-09-21T10:00:00Z","tier":"complex","domains":["backend","security"],"subagents":2,"retries":0,"modules_loaded":["backend","security"]}
```

### How it's used
- `scripts/verify.sh` can optionally summarize: are atomic tasks staying within budget? Is one domain being mis-triggered often?
- Patterns that suggest budget or classification thresholds need adjustment become a CHANGELOG.md entry
- Installing/using the skill must work identically with logging disabled

## Context & Memory Management (§21)

### What's in context, and its trust level

| Source | Trust level | Eviction under pressure |
|--------|-------------|------------------------|
| Tier 0 (SKILL.md + router) | Authoritative, always correct | Never evicted, never summarized |
| Loaded Tier 1 module(s) | Authoritative for principles; tooling-notes as fresh as last verification | Evicted when subtask closes |
| project-memory.md | Trusted as cache, not ground truth | Summarized to most-relevant entries first |
| Retrieved external docs | Trusted only for the specific claim they were fetched for | Dropped once response is delivered |
| Conversation history | Trusted as user intent, not as fact | Oldest/least-relevant summarized first |

### Anti-hallucination rule
Every factual claim about a specific library, API, tool, or framework must be traceable to: (a) code in the repo, (b) a durable principle in a loaded module, or (c) a grounded lookup. If none, say "unverified" rather than presenting with false confidence.

### Context-pressure eviction order
1. Retrieved external docs (cheapest to re-fetch)
2. project-memory.md (summarized, not dropped)
3. Oldest conversation turns
4. **NEVER**: Tier 0, current task contract, or decomposition definition of done

## How to Add a Domain Module

1. Create `modules/<category>/<domain>.md` following the §25 skeleton
2. Register in SKILL.md's Capability Index: `- domain-name -> modules/<category>/<domain>.md`
3. Add triggers and anti-triggers (include near-miss anti-triggers)
4. Test: a task that SHOULD trigger the module, and a near-miss that SHOULD NOT

## How to Add a Persona

1. Create `personas/<domain>/<specialist-name>.md`
2. Include frontmatter with domain, description, triggers, anti-triggers
3. Include core expertise, deliverables, and principles
4. Personas are NOT registered in the Capability Index — they are loaded by domain modules or sub-agents

## How to Add a Tool Adapter

1. Create `adapters/<tool-name>.md`
2. Include structured fields: `doc_source`, `last_verified`
3. Document: package placement, sub-agent mapping, instruction hierarchy
4. Run `scripts/verify.sh` — it flags adapters past the staleness window (90 days)

## CHANGELOG.md "Unresolved" Section

The Unresolved section tracks domain gaps — tasks that hit the emerging-tech-handler because no module exists. Crossing an occurrence threshold (default 3) flags a gap as a candidate for a real module. Promotion is deliberate, not automatic.


## v2.5 Runtime

The v2.5 runtime is the execution layer for the existing orchestration architecture. It provides durable task state, context, checkpoints, execution, verification, evidence, recovery, and policy without replacing the existing skills, agents, router, or workflows.

### JEV decision kernel

JEV is a side-effect-free policy boundary inside the runtime, not another model
or orchestration pattern:

```text
MODEL / ORCHESTRATION
    │ structured assessment and capability proposal
    ▼
JEV: validate → aggregate → guard → recommend
    │ deterministic decision packet
    ▼
RUNTIME: persist → confirm → execute → verify → recover
    │ canonical capability IDs
    ▼
HOST-NATIVE TOOLS
```

JEV evaluates NOUL (boolean safety facts), CHOICE (proposed path/task class),
and SCORE (bounded risk, complexity, confidence, and context pressure). The
host, not the model, supplies availability, isolation, policy, and approvals.
JEV never calls a model, discovers or installs tools, runs subprocesses, or
persists state. The runtime remains the final authority for policy, evidence,
and recovery.

The contract is language-neutral JSON Schema under `runtime/schemas/`. The
reference implementation is the dependency-free `runtime/jev/engine.mjs`; a
host may implement the same rules natively. Tool selection is intersection-only
(`requested ∩ host_available ∩ policy_allowed`), human review is a blocking
state, and missing capabilities are reported rather than replaced.

The old `runtime/core/jev/` Python package is legacy compatibility material and
is not imported by the Runtime or SessionManager. See
`../docs/adr/0001-jev-host-native-decision-kernel.md`.

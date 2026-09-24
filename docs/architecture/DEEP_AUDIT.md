# Ultimate-Dev Deep Architectural, Capability, Universality & Evolution Audit

**Audit date:** 2026-09-24
**Scope:** source implementation, runtime, orchestration, configuration, tests, evaluations, documentation, adapters, and current ecosystem references
**Method:** repository reconstruction first, then boundary analysis, stress tests, independent audits, and primary-source research
**Overall score:** intentionally not assigned

**Worktree preservation:** no production implementation was modified. The
pre-existing untracked files `ultimate-dev/runtime/core/browser/automation.py`,
`ultimate-dev/runtime/core/sandbox/runner.py`, and
`ultimate-dev/runtime/core/jev/bridge.py` were preserved unchanged. The audit
added only its report and task-local evidence/state files.

> This is an evidence audit, not a rewrite proposal. “Documented” does not
> mean “implemented,” “tested” does not mean “end-to-end verified,” and
> “model-controlled” does not mean “runtime-enforced.”

---

## Executive conclusion

Ultimate-Dev is currently a **broad, well-documented prompt/orchestration
catalog with a real but narrow durable-state implementation and a strong
host-neutral JEV decision kernel**.

It is not yet a self-contained general agent execution platform. Its intended
architecture is sound at the conceptual level:

```text
model → orchestration → deterministic policy → durable runtime → capabilities
```

But the repository does not yet connect most of the declared control surfaces
into that path. The router, workflows, permissions, model tiers, context
budgets, agent registry, security configuration, and tool registry are mostly
Markdown/YAML contracts interpreted by a model or an external host. The
Python runtime is primarily a caller-driven state facade; it does not receive
requests, classify them, select agents, parse workflows, spawn subagents,
consume handoffs, run verifiers automatically, recover failed work, or enforce
its own policy configuration.

The project is therefore closer to:

```text
prompt-driven control-plane specification
        +
small durable runtime library
        +
host-native JEV reference implementation
        +
large replaceable knowledge/catalog surface
```

than to a unified general-purpose execution platform.

That conclusion is not uniformly negative. The repository has unusually strong
conceptual ingredients:

- stable universal primitives are named and separated;
- the model is not treated as the owner of durable truth;
- JEV is deterministic, side-effect-free, capability-intersection-oriented,
  and directly tested;
- missing capabilities are intended to fail visibly rather than trigger
  provider installation;
- software-engineering specialization is broad;
- domain and technology knowledge are mostly replaceable artifacts;
- the project has meaningful structural validation and anti-fabrication
  instructions.

The central problem is **contract realization**. The next architectural work
should make a small number of seams executable and authoritative, not add more
agents or frameworks.

---

# Phase 1 — Reconstruct the actual system

## 1.1 Inventory and source taxonomy

The source-control inventory at capture time contained approximately:

| Surface | Count | Nature |
|---|---:|---|
| Tracked files | 345 | Git source of truth |
| Non-ignored repository files | 355 | Excludes local task memory and caches |
| Tracked directories | 129 | 135 including local/cache directories |
| Markdown | 261 | Most architecture, policy, and specialization is textual |
| Python | 38 | Runtime, validation, generators, tests |
| YAML | 20 | Workflows, configuration, frontmatter, evaluation data |
| ECMAScript modules | 2 | Canonical JEV engine and conformance test |
| Concrete agents | 119 | Frontmatter + prompt bodies |
| Skills | 18 | Methodology prompts |
| Modules | 46 | Domain/engineering knowledge prompts |
| Registered tools | 8 | Declarative tool descriptions |
| Golden classification cases | 60 | Static expected labels |

The user-provided estimate of approximately 371 files and 132 directories is
close, but the audit uses measured repository counts rather than assuming the
estimate is exact.

The repository is a hybrid of at least six different kinds of artifact:

1. **Executable runtime code** — Python state/runtime/helpers and the MJS JEV
   engine.
2. **Prompt contracts** — `SKILL.md`, `AGENTS.md`, agent files, skills, modules,
   prompts, and rules.
3. **Declarative configuration** — workflow, permissions, model, context,
   security, and agent registries.
4. **Generated documentation and metadata** — README trees, manifests, backups,
   changelogs, and catalog counts.
5. **Host adapter instructions** — Markdown mappings for external CLIs.
6. **Optional/legacy working-tree code** — untracked sandbox, browser, and JEV
   bridge files preserved from earlier work.

A file's existence therefore does not establish a capability.

### Status vocabulary used throughout this audit

- **Implemented:** executable code exists and performs the stated narrow behavior.
- **Partial:** a real mechanism exists but lacks an invariant, integration, or
  failure/recovery path.
- **Documented-only:** described in Markdown/YAML/schema but not loaded or
  enforced by an executable consumer.
- **Model-enforced:** depends on the model following instructions.
- **Runtime-enforced:** checked by executable runtime/tool-boundary code.
- **Tested-contract:** a direct structural or conformance test exists; this does
  not imply end-to-end task success.
- **Host-dependent/absent:** possible only when an external host supplies the
  missing mechanism, or no implementation was found.

## 1.2 Actual control path

The implemented repository path is:

```text
USER / HOST
  │
  ├─ host loads AGENTS.md, SKILL.md, template, or adapter instructions
  │
  ├─ model interprets lifecycle and classification rules
  │
  ├─ model selects pattern, agent, skill, module, and context
  │
  ├─ host is expected to build JEV request + host facts
  │
  ├─ host invokes JEV implementation (if it has one)
  │
  ├─ Python Runtime may persist task state and gate execution
  │
  └─ injected host executor performs an action
```

What is missing from that path is just as important as what is present:

- no repository-owned request listener;
- no executable router;
- no canonical agent selector;
- no workflow parser/executor;
- no subagent lifecycle manager;
- no handoff consumer;
- no automatic observation step;
- no automatic verification/completion gate;
- no recovery/rollback implementation;
- no MCP client/server;
- no canonical capability-to-native-tool broker.

## 1.3 Executable versus declarative surfaces

| Surface | Actual status |
|---|---|
| `runtime/core/state.py` | Executable, narrow filesystem state store |
| `runtime/core/engine.py` | Executable, caller-driven state facade |
| `runtime/jev/engine.mjs` | Executable, pure deterministic decision kernel |
| `runtime/core/session_manager.py` | Executable injected-executor seam |
| `runtime/core/context.py` | Executable helper, not integrated |
| `runtime/core/capabilities.py` | Executable helper, not integrated |
| `runtime/core/policy.py` | Executable helper, not integrated |
| `runtime/core/verification.py` | Executable helper, not integrated |
| `AGENTS.md` / `SKILL.md` | Model/host operating contract |
| `agents/*.md` | Role prompts, not agent processes |
| `skills/*/SKILL.md` | Methodology prompts |
| `modules/*.md` | Knowledge prompts |
| `router/*.md` | Model-applied routing rules |
| `workflows/*.yaml` | Static workflow definitions |
| `config/workflow.yaml` | Second, incompatible static workflow definition |
| `config/agent_registry.yaml` | Partial, inert role registry |
| `config/permissions.yaml` | Inert permission configuration |
| `config/models.yaml` | Inert model-tier configuration |
| `config/context_budgets.yaml` | Inert context configuration |
| `config/security.yaml` | Inert security policy description |
| `tools/tool_registry.yaml` | Declarative tool catalog; only structural tests consume it |
| `adapters/*.md` | Installation/integration documentation |
| `evals/golden-cases.yaml` | Static expected labels, not an evaluator |

A repository-wide executable-reference search found no Python/MJS/shell runtime
consumer for `config/workflow`, `workflows/`, `permissions.yaml`, `models.yaml`,
or `context_budgets`. The only Python tool-registry consumer found was its
structural test. This is a strong seam finding, not proof that an external host
cannot load those files.

## 1.4 Runtime flow actually implemented

### Task creation

```text
Runtime.start(contract)
  → TaskStore.create()
  → state.json/context.json/progress.md
  → checkpoints/, handoffs/, evidence/
  → task_started event
  → status ready
```

`Runtime.start()` requires only a non-empty goal and fills defaults. It does not
validate the contract against `runtime/schemas/task-contract.json`.

### JEV and execution

```text
caller supplies packet
  → Runtime.record_jev_decision()
  → evidence/jev-NNNNNN.json
  → event + decision summary
  → optional in-memory gate
  → SessionManager.execute_code()
  → injected host_executor(code, language, **kwargs)
```

The Runtime does not invoke `runtime/jev/engine.mjs`, validate the full packet
schema, authenticate its producer, bind it to a state revision/action, or
re-check actual scope at the executor boundary. The key implementation
references are `ultimate-dev/runtime/core/engine.py:15-20,39-77,79-95,123-145`,
`ultimate-dev/runtime/core/state.py:44-108`,
`ultimate-dev/runtime/core/context.py:13-36`, and
`ultimate-dev/runtime/core/session_manager.py:115-154`.

### Verification and completion

```text
caller records strings/evidence
  → state.verification updated
  → caller manually transitions verifying → completed
```

`Verification.evaluate()` is a standalone boolean matcher. It is not called by
`Runtime`, and `transition("completed")` does not require all acceptance
criteria or required evidence to pass.

## 1.5 Actual data and state flows

### State flow

```text
state.json
  ├─ contract
  ├─ status/revision/timestamps
  ├─ completed/in_progress/next_action
  ├─ changed_files
  ├─ decisions
  ├─ failed_approaches
  ├─ verification
  ├─ blockers/open_questions
  └─ mutable embedded events
```

State is durable as files, but not modeled as an append-only event history.
Writes use temporary-file replacement, which prevents torn individual files,
but read-modify-write operations are unlocked and can lose concurrent updates.

### Context flow

```text
state + last 10 decisions + caller files/history
  → ContextManager.build()
  → context.json
```

There is no automatic invocation, provenance model, compression, stale-data
marker, secret filter, or tokenizer-aware budget.

### Evidence flow

```text
caller-provided dictionary
  → optional evidence file
  → state summary
```

There is no canonical evidence schema, producer identity, source digest,
environment record, verifier identity, or immutable chain of custody.

### Error/recovery flow

```text
executor exception or missing capability
  → raw return/exception to caller
```

The state labels `failed`, `recovering`, and `replanned` exist, but no runtime
component diagnoses, retries, rolls back, reconciles uncertain side effects, or
restores a checkpoint.

### Adaptation flow

```text
model notices gap
  → research/note/generate instructions
  → possibly write skill/agent/manifest
```

There is no governed proposal/evaluation/admission/rollback transaction.

---

# Phase 2 — Actual architecture and responsibility map

## 2.1 Dependency/responsibility map

```text
┌──────────────────────────────────────────────────────────────┐
│ USER / HOST MODEL                                            │
│ intent, ambiguity, planning, interpretation, strategy        │
└───────────────┬──────────────────────────────────────────────┘
                │ Markdown operating contract; no typed intake
                ▼
┌──────────────────────────────────────────────────────────────┐
│ ORCHESTRATION SURFACES                                       │
│ AGENTS/SKILL, agents, skills, modules, router, workflows      │
│ Mostly prompt/configuration; no dispatcher                   │
└───────────────┬──────────────────────────────────────────────┘
                │ model-selected pattern and capability proposal
                ▼
┌──────────────────────────────────────────────────────────────┐
│ JEV DECISION KERNEL                                          │
│ pure MJS reference + JSON Schchemas; host-native alternatives │
└───────────────┬──────────────────────────────────────────────┘
                │ host-produced packet; optional Python gate
                ▼
┌──────────────────────────────────────────────────────────────┐
│ PYTHON RUNTIME FACADE                                        │
│ state, narrow transitions, context/helper seams               │
└───────────────┬──────────────────────────────────────────────┘
                │ raw callable seam
                ▼
┌──────────────────────────────────────────────────────────────┐
│ HOST CAPABILITIES / ENVIRONMENT                              │
│ native tools, shell, browser, APIs, databases, MCP, IDE       │
└──────────────────────────────────────────────────────────────┘
```

The intended arrows are reasonable. The problem is that several arrows are
normative only: no code carries the data across them in normal use.

## 2.2 Ownership analysis

### Model/intelligence

The model appropriately owns intent, planning, strategy, and interpretation.
It should not own durable state, secrets, policy facts, or proof of completion.
The repository states this principle clearly, but the enforcement boundary is
not implemented consistently.

### Orchestration

The orchestrator prompt owns the conceptual lifecycle. It does not own an
executable process, durable queue, concurrency control, or agent registry.
Pattern names overlap and are not mutually exclusive execution modes.

### Runtime

The Runtime is the correct conceptual owner of lifecycle state, checkpoints,
evidence, recovery, and final authorization. In implementation it owns only a
subset: basic state files, a narrow transition map, optional JEV persistence,
and delegation to a raw executor.

### JEV

JEV is the strongest new boundary. It is stateless, deterministic, dependency
free, and has a substantial direct test suite. It correctly recommends rather
than executes. Its contract is not yet the canonical input to every privileged
Runtime operation.

### Tools/environment

The repository has no single tool broker. The registry describes tools, the
session manager accepts a raw callable, and the optional sandbox/browser paths
are not canonical. There is no common identity, trust, health, timeout, or
result contract.

### Domain/technology knowledge

Agents/modules are mostly leaf knowledge and are the right place for many
technology-specific details. The problem is that central detectors, command
allowlists, workflows, context manifests, and router tables also contain
technology-specific assumptions, so new ecosystems are not always knowledge-only
changes.

## 2.3 Hidden coupling and duplicated responsibility

1. **Agent metadata:** Markdown frontmatter, manifest paths, and
   `config/agent_registry.yaml` all describe agents differently.
2. **Workflows:** `config/workflow.yaml` and `workflows/*.yaml` have different
   stages and concurrency semantics.
3. **Task/handoff contracts:** legacy YAML schemas, prompt templates, and
   runtime JSON schemas coexist.
4. **Policy:** JEV policy, Python policy, permissions YAML, security YAML,
   tool registry, and prompt rules are independent.
5. **Model selection:** model tiers in YAML, host capability discovery, and
   two divergent Python model-adapter import surfaces disagree.
6. **Verification:** verification prompts, a Python helper, test evidence,
   examples, and golden cases are not one coherent system.
7. **Evolution:** self-evolve, agent-generator, auto-persona-generator,
   skill-maintainer, gap-tracker, and Task Observer overlap.
8. **Entry/version surfaces:** root `VERSION`/manifest are 2.8.0 while several
   entrypoints and runtime schema labels remain 2.5.x.

---

# Phase 3 — Architectural boundary audit

The full matrix is persisted at
`.memory/ultimate-dev/tasks/deep-architecture-capability-audit-2026-09-24/evidence/boundary-matrix.md`.
The most important conclusions are:

| Boundary | Current judgment |
|---|---|
| Model ↔ orchestration | Conceptually clean, operationally prompt/model-enforced |
| Orchestration ↔ runtime | Clean conceptual seam, no normal executable connector |
| Runtime ↔ tools | Raw callable seam; no canonical capability/action contract |
| Agent ↔ skill | Useful separation in prose, duplicated in practice |
| Skill ↔ module | Path-based and frequently stale |
| Router ↔ orchestrator | Multiple competing descriptions, no resolver |
| Runtime ↔ workflow | No owner; two inert workflow sources |
| Runtime ↔ policy | JEV is real; Python/config policy is disconnected |
| Runtime ↔ verification | Helper exists; completion is not evidence-gated |
| Runtime ↔ evidence | Files are persisted; provenance/authenticity are absent |
| Memory ↔ context | Templates and builder coexist without a lifecycle contract |
| Adapter ↔ model | Two divergent model-adapter artifacts under one import name |
| Domain ↔ runtime | Generic contract supports domains; domain packs are not first-class |
| Technology ↔ software capability | Leaf knowledge is fine; central toolchain coupling is not |
| JEV ↔ Runtime | Optional, insufficiently validated, not restart-safe |
| Host ↔ environment | Contract documented, implementation absent |
| Evolution ↔ registry | Conflicting automatic and gated policies |

Important responsibilities with no obvious owner are canonical intake, agent
selection, workflow execution, final authorization, evidence authenticity,
capability health, memory lifecycle, evolution admission, and checkpoint
recovery.

---

# Phase 4 — Universal foundation versus specialization

## 4.1 What belongs in the universal core

These are stable concepts and should remain small, language-neutral, and
host-independent:

- task identity and contract;
- lifecycle/state transitions;
- durable event/checkpoint protocol;
- operation identity and idempotency;
- capability descriptors and health;
- policy intersection and approval state;
- context planning/projection;
- evidence and independent verification;
- retries, cancellation, recovery, and uncertainty;
- trace/event schema;
- extension/knowledge admission;
- human review and audit.

## 4.2 Universal agent capabilities

These are reusable methods, not domain knowledge:

- understand and clarify a goal;
- discover relevant repository/context;
- decompose a task;
- select the smallest safe execution structure;
- research an unknown subject;
- use tools safely;
- observe and interpret results;
- verify against a contract;
- record/reuse a verified procedure;
- hand off bounded context;
- ask for human judgment at a real decision boundary.

## 4.3 Developer-specific capabilities

These belong in software-engineering skills/modules/adapters:

- inspect manifests and dependency graphs;
- detect build/test/lint/type-check commands;
- understand repository architecture and conventions;
- implement and refactor code;
- debug and diagnose incidents;
- review diffs;
- operate CI/CD and cloud infrastructure;
- manage migrations;
- perform security/performance analysis;
- inspect Git history and blast radius.

The universal core should expose “execute a bounded command,” “read a file,”
“inspect a structured artifact,” and “run a verifier,” not assume npm, pytest,
Docker, or a src/ layout.

## 4.4 Domain-specific capabilities

Domain packs should provide:

- terminology and goals;
- evidence types and authoritative sources;
- risk/compliance policy;
- tools and adapters;
- verifier(s);
- output contracts;
- human approval requirements;
- examples and anti-patterns.

Examples in the repository—finance, healthcare, marketing, sales, GIS,
project management, support, legal-tech, and others—are a useful starting
catalog. Their current depth is mostly instructional rather than executable.

## 4.5 Infrastructure and model-specific behavior

Infrastructure belongs behind adapters: storage, databases, queues, browsers,
MCP servers, clouds, CI systems, and sandboxes. Model-specific wire formats,
provider authentication, context windows, and tokenizers belong behind a model
gateway. None should be imported by the universal state machine.

## 4.6 Current classification problem

The project understands the distinction conceptually, but its shipped
configuration often mixes layers:

- `config/models.yaml` prescribes tiers instead of consuming host facts;
- `config/permissions.yaml` presumes web-project paths;
- `config/security.yaml` assumes shell/package-registry ecosystems;
- default workflows impose software test pyramids;
- the legacy model adapter hardcodes providers/models;
- the canonical capability registry is not used by execution.

---

# Phase 5 — Software-engineering stress test

Software engineering is the deepest reference use case and exposes both the
project's strengths and its central architectural gap.

## 5.1 What works unusually well

- The repository has meaningful depth across backend, frontend, architecture,
  database, security, DevOps, cloud, testing, mobile, AI/ML, and specialized
  engineering domains.
- Generic specialists provide a fallback for unfamiliar frameworks and
  languages.
- Progressive context, blast-radius analysis, handoff formats, and verification
  instructions are strong software-engineering concepts.
- JEV's canonical capability IDs and no-installation rule are appropriate for
  an agent that must work across hosts.
- The structural test suite catches many packaging regressions quickly.

## 5.2 What prevents exceptional software performance

1. **No executable repository discovery.** The stack detector is a Markdown
   list, not a capability discovery service.
2. **No executable test strategy.** Test detection is a table/prompt, with gaps
   for languages it claims to recognize.
3. **No real subagent/handoff execution.** Tests simulate agent outputs.
4. **No repository-specific verifier composition.** Verification criteria are
   strings, not executable test/build/lint/security plans.
5. **Routing collisions.** 177 exact normalized trigger collisions were found.
6. **Stale knowledge references.** Approximately 90 references to nonexistent
   `modules/specialized/...` paths occur across roughly 60 agent files.
7. **Broken workflow references.** Several workflows reference nonexistent
   `code-reviewer`; one references `debugging` as an agent rather than a skill.
8. **Tool contract drift.** Agent frontmatter uses `glob`, `run_command`, and
   `list_directory` while the registry defines different IDs.
9. **No execution recovery.** A failed test, unavailable tool, or interrupted
   agent does not enter a tested recovery transaction.
10. **No repeated-trial evaluation.** There is no pass-rate or regression
    measurement for real coding tasks.

## 5.3 Software-engineering verdict

Ultimate-dev can be exceptionally useful as a **host-native software
orchestration skill** if the host supplies strong tools and the model follows
the prompt contract. It cannot yet claim to be an exceptional standalone
software agent runtime because the repository does not own discovery,
execution, verification, or recovery end to end.

---

# Phase 6 — Other-domain stress tests

| Domain | Required universal support | Current support | Main gap |
|---|---|---|---|
| HR | candidate evidence, privacy, consent, auditable decisions, human review | HR-like prompts are limited; generic task contract exists | No domain evidence/approval model or execution path |
| Finance | immutable records, reconciliation, source lineage, approval, audit | Finance agents/modules exist | No transaction/ledger/reconciliation verifier |
| Research | citations, source quality, freshness, conflicting evidence | Research skills/modules and web tools in host | No source ledger or claim-level verifier |
| Marketing | audience/context, campaign artifacts, approval, measurable outcomes | Marketing agents/modules exist | No domain evidence or outcome measurement |
| Sales | account context, consent, outreach approval, CRM state | Sales agents/modules exist | No durable external-state/approval integration |
| Agency | client scope, deliverables, acceptance, approvals, handoffs | Strong prompt coverage | No client/project policy or artifact verifier |
| Operations | runbooks, state observation, escalation, rollback, safety | Generic DevOps/observability coverage | No runtime incident/recovery engine |
| Support | case state, customer data boundaries, resolution evidence, escalation | Support agents/modules exist | No case-system capability/evidence adapter |
| Project management | dependencies, owners, milestones, change history | PM agents/modules exist | No durable graph/update/verification semantics |

The universal contract is broad enough that these domains do not require a
runtime fork. The missing piece is a standard **domain pack contract** that
joins knowledge, capabilities, risk policy, evidence, and verification.

---

# Phase 7 — Agent lifecycle and control ownership

The documented lifecycle is:

```text
UNDERSTAND → DISCOVER → PLAN → DECOMPOSE → ROUTE → EXECUTE
→ OBSERVE → VERIFY → REFLECT → RECOVER → ADAPT → FINALIZE
```

Not every task needs every stage. The correct ownership split is:

| Stage | Primary owner | Current enforcement |
|---|---|---|
| Understand/plan/decompose | Model + orchestrator | Prompt/model |
| Discover capabilities | Host adapter + capability broker | Missing |
| Route | Code-owned resolver with model advisory | Missing |
| JEV assess | Host adapter + deterministic JEV | JEV real; Runtime gate partial |
| Execute | Runtime + capability broker | Raw injected callable |
| Observe | Runtime + adapter | Missing |
| Verify | Independent verifier/runtime | Helper disconnected |
| Reflect/adapt | Model proposes; evolution gate admits | Prompt-only |
| Recover | Runtime | State labels only |
| Human approval | Runtime/policy/human principal | JEV recommendation, no durable approval record |
| Persist/audit | Runtime | Files exist, event model incomplete |

The runtime must prevent the model from being the only source of reliability.
The repository states this principle, but the current enforcement graph does
not yet realize it.

---

# Phase 8 — Runtime deep audit

| Capability | Classification | Finding |
|---|---|---|
| State persistence | Implemented/partial | Atomic per-file writes, revisioning, mutable events |
| State machine | Implemented narrowly | Fixed transition map; caller-driven |
| Contract validation | Partial | Only goal checked; schema not enforced |
| Checkpoints | Partial | Snapshots exist; no restore/replay protocol |
| Resume | Partial | Loads latest state; does not reconstruct active execution |
| Context | Helper/partial | Fixed projection, approximate budget, path issue |
| Policy | Helper/partial | Six exact strings; not called by Runtime |
| Capabilities | Helper/partial | In-memory descriptors; no discovery/executor mapping |
| JEV | Real/reference | Pure deterministic engine with direct tests |
| JEV integration | Partial | Optional gate, weak packet validation, no restart rehydration |
| Execution | Partial | Raw callable seam; no action/scope/result contract |
| Observation | Absent | No adapter/runtime method |
| Verification | Helper/partial | Boolean matcher; not completion gate |
| Evidence | Partial | Files, no provenance/integrity |
| Recovery | Absent | No diagnosis, retry, rollback, restore, reconciliation |
| Retry | Absent/fragmented | Provider/sandbox fragments, no runtime policy |
| Timeout/cancellation | Fragmented | Fixed provider/sandbox timeouts; no unified token/deadline |
| Resource limits | Fragmented | JEV capability budget/context estimate; no host enforcement |
| Idempotency | Absent | No operation key or uncertain state |
| Concurrency | Partial | Atomic file replacement, no locking/CAS |
| Auditability | Partial | Mutable state/events, no actor/correlation/hash chain |
| Lite mode | Helper/partial | Not integrated; says `skip_preflight: true` |
| MCP | Absent | No client/server/discovery/tasks integration |
| Subagents | Host/prompt | No runtime spawn/join/cancel lifecycle |
| Workflows | Inert | No parser/executor |

The canonical JEV engine is implemented at
`ultimate-dev/runtime/jev/engine.mjs:1-7,316-347,401-596` and directly tested
by `ultimate-dev/tests/jev/engine.test.mjs`. Its contract is documented at
`ultimate-dev/runtime/jev/README.md:118-182` and
`ultimate-dev/runtime/adapter-contract.md:18-35`.

### Runtime-specific correctness findings

1. `require_jev_decision` defaults to false and can be overridden per call.
2. `execute_code()` can run with a nonexistent task ID and without a planned or
   executing state.
3. A new `Runtime` instance does not rehydrate the full JEV decision cache.
4. `record_jev_decision()` does not validate canonical schema, packet freshness,
   approval provenance, capability IDs, or action scope.
5. A decision is not bound to a task revision, request hash, target, or
   idempotency key.
6. `TaskStore.update()`/`append_event()` are unlocked read-modify-write
   sequences.
7. Caller-controlled task IDs can escape the task base; `ContextManager` can
   read outside the project root.
8. `resume()` does not restore a checkpoint.
9. `verifying → completed` does not require evidence.
10. Legacy model-adapter code and the public package import disagree.

These are implementation findings, not stylistic preferences.

---

# Phase 9 — MCP and tool resilience

## 9.1 Current state

There is no MCP client, server, discovery loop, health model, task adapter, or
fallback policy in the canonical runtime. MCP appears as an intended tool
category and in external-host documentation.

The current tool registry is useful as a description but has no runtime
consumer. Its IDs also disagree with agent frontmatter. The host executor seam
does not receive a canonical capability ID or policy snapshot.

## 9.2 Required resilience behavior

The runtime should treat tools as replaceable, untrusted, and capability-based:

```text
discover → validate schema → classify trust/effects → probe health
→ request capability → intersect with policy → request approval if needed
→ execute with timeout/idempotency → validate result → record provenance
```

A tool failure should produce a typed result such as:

```text
unavailable | unauthorized | malformed | timeout | conflicting
| denied | uncertain | failed
```

The system must not silently replace a narrow capability with a broader shell
or browser capability. A fallback is valid only when its semantics, isolation,
data handling, and side effects are demonstrably equivalent or explicitly
approved.

## 9.3 Lessons from current MCP practice

The current MCP specification emphasizes:

- host/client/server separation;
- stateless requests with per-request version/capability metadata;
- discovery and capability negotiation rather than a persistent protocol
  session;
- host-owned consent and security;
- JSON Schema tool input/output;
- untrusted tool annotations;
- explicit state handles for cross-call state;
- timeouts, rate limits, validation, and audit;
- optional Tasks for asynchronous work and cooperative cancellation.

This means an Ultimate-Dev MCP adapter must not assume that reconnecting to a
server restores in-flight state. A broken stream creates an uncertain operation;
the runtime needs an idempotency key, read-before-write verification, or an
explicit review state.

Ultimate-dev's JEV intersection model aligns with the “discovery is not
authorization” principle. The missing implementation is the host-side broker,
provenance, health, retry, and result-validation layer.

MCP should remain optional. Making it a hard dependency would create a new
single point of failure and undermine the project's portability goal.

---

# Phase 10 — Context and memory

## 10.1 What exists

- `.memory/ultimate-dev/` project/task state convention;
- `ContextManager` with L0–L6 conceptual layers;
- `config/context_budgets.yaml`;
- memory templates and project-memory instructions;
- Task Observer and learned-pattern artifacts.

## 10.2 What is not coherent yet

- Runtime never calls `ContextManager`.
- YAML budgets are not loaded.
- Budgets are approximate character counts, not model token budgets.
- Files are read fully before truncation.
- Paths and symlinks are not contained.
- Context is persisted without provenance, redaction, freshness, or sensitivity
  labels.
- Project memory templates are not a typed, queryable, contradiction-aware store.
- Learned patterns are not consistently registered or versioned.
- Subagent context is a prompt convention, not an enforced projection.

## 10.3 Required universal abstraction

Separate four things:

1. **Authoritative task state** — evented runtime state.
2. **Checkpoints** — replay/recovery projections of task state.
3. **Long-term memory** — scoped, provenance-bearing reusable records.
4. **Context projection** — ephemeral, budgeted selection for one model call.

Each context item should explain why it was included, its source, freshness,
trust level, sensitivity, and whether it is authoritative. Memory should be
capable of superseding, expiring, revoking, and rolling back records without
silently overwriting history.

---

# Phase 11 — Verification, evidence, and completion

## 11.1 What “verified” currently means

In the Python runtime, it usually means:

```text
an evidence dictionary contains passed: true
and a criterion string matching an acceptance criterion
```

That is not proof. It says only that a caller asserted a match.

The prompt layer asks for real tests, lint, build, review, and source evidence,
but the runtime does not enforce the connection. The examples are especially
important: `test_95_evidence.py` can record three passed criteria and transition
to completed with a fourth unresolved.

## 11.2 One coherent verification system requires

- typed evidence records;
- verifier identity and version;
- command/query/expert procedure;
- environment and input digest;
- before/after external state where relevant;
- result: `pass`, `fail`, `not_run`, `uncertain`;
- links to task/operation/approval;
- independent verifier where possible;
- domain-specific verifiers;
- explicit human review for regulated/irreversible decisions.

The universal primitive is not “run tests.” It is:

```text
evaluate a typed claim against a contract using a registered verifier
```

A coding verifier may run a test suite; a research verifier may validate source
provenance and claim support; a finance verifier may reconcile records; an HR
verifier may check consent and evidence completeness; a legal workflow may
require qualified human sign-off.

## 11.3 Evaluation is not the same as tests

The current suite proves structure and small runtime behaviors. It does not
measure:

- task success on real repositories;
- false completion;
- repeated-trial reliability;
- recovery after restart/failure;
- tool selection and tool errors;
- prompt injection resistance;
- cost/latency;
- human intervention;
- out-of-distribution technology/domain adaptation;
- regression caused by self-evolution.

The 60 golden cases are expected labels, not executed evaluations. A real
evaluation runner is a missing critical capability.

---

# Phase 12 — Self-evolution

## 12.1 Current strengths

The repository recognizes that unfamiliar work requires research, gap tracking,
reusable procedures, and project memory. The Task Observer skill/agent boundary
is deliberately more conservative than the older auto-generation personas: it
separates methodology from bounded capture and does not modify task state.

## 12.2 Current failure modes

The evolution surfaces disagree:

- `self-evolve` says any unmatched skill triggers automatic new-skill
  generation;
- universal/generic specialists say to create an agent after an unfamiliar
  technology;
- `agent-generator` updates the manifest automatically;
- `auto-persona-generator` duplicates that role;
- `gap-promotion-rules` says three occurrences are required;
- `skill-maintainer` describes version/registry publishing but provides no
  executable transaction;
- the learned artifact is not in the declared generated-skill shape or index.

The dangerous pattern is **fix the last failure globally**. A local improvement
can break a previously working case. Self-generated changes can also conflict
with rules, alter routing, expand tool permissions, or encode prompt injection
from web content.

## 12.3 Required lifecycle

```text
observe → classify gap → propose candidate → isolate
→ deterministic checks → protected regression suite
→ repeated/adversarial trials → security review
→ human admission for global artifacts → version/publish
→ monitor → expire/rollback
```

Candidate changes should initially be staged, not canonical:

```text
candidate/
  proposal.json
  sources.json
  diff.patch
  evaluation.json
  security-report.json
  reviewer-decision.json
  rollback-plan.json
```

Unsupervised evolution must not modify JEV authorization, secret handling,
sandbox boundaries, verification logic, audit deletion, or canonical production
policy.

---

# Phase 13 — Security and policy

## 13.1 What is runtime-enforced today

Very little. JEV can deny/review when a caller uses it correctly. `Policy` can
reject six exact action strings. The optional sandbox/browser code has isolated
fragmentary controls. The core Runtime does not call those controls for normal
execution.

## 13.2 What is prompt/model-enforced today

- input validation;
- path and command restrictions;
- secret handling;
- least privilege;
- consent;
- untrusted-content treatment;
- confirmation before destructive actions;
- domain/compliance rules;
- emergency escalation.

These are valuable instructions but are not a security boundary.

## 13.3 Concrete security findings

1. Task IDs are not path-contained; `../escaped` can create a task directory
   outside the intended base.
2. Context paths are not contained; `../secret.txt` can be read outside the
   project root.
3. Symlinks are followed by the context file check.
4. `Policy.check()` trusts a caller-provided `confirmed=True` and has no
   approver identity, scope, expiry, or durable record.
5. Security YAML's secret exclusions, file limits, audit logging, and network
   policy are not loaded by the runtime.
6. Host executor results are not schema-validated or exception-normalized.
7. The legacy browser wrapper does not enforce its documented URL/download/
   form/rate restrictions.
8. The dependency manager contains `shell=True` installation paths and is not
   on the canonical path.
9. Tool descriptions, MCP annotations, web pages, repository text, memory, and
   remote-agent messages are not consistently labeled untrusted.
10. There is no approval replay protection or action fingerprint.

The local Git configuration also contains an embedded credential finding from
prior work. It was not printed or rotated during this audit; it remains a
separate security action item.

## 13.4 Security target

Security must be structural:

- capability-scoped authorization;
- path/URL/command validation at execution;
- secret vault/proxy boundary;
- no token passthrough;
- source/sink policy for untrusted content;
- approval records tied to exact action fingerprints;
- immutable/redacted audit events;
- adversarial evaluation;
- fail closed when structured output, policy, or isolation is missing;
- explicit uncertain state after ambiguous external effects.

---

# Phase 14 — Evaluation

## 14.1 Current evaluation assets

- 590 Python tests passed in the baseline run, with five warnings;
- 18 dependency-free JEV conformance tests passed;
- 52 structure validation checks passed;
- root and inner verification scripts passed;
- 60 static golden classification cases exist;
- Task Observer contract tests exist;
- CI validates structure, installation, generated docs, and JEV.

## 14.2 What is missing

A layered evaluation system should include:

1. **Deterministic contract tests** — schemas, transitions, JEV, capability
   descriptors, policy, evidence.
2. **Integration tests** — real filesystem, shell, retries, checkpoint/resume,
   human approval, MCP/A2A adapters.
3. **Adversarial tests** — prompt injection, malicious tool output, state-handle
   guessing, approval replay, capability substitution, secret exfiltration,
   poisoned memory.
4. **Real-task evaluations** — unseen repositories, tools, domains, and failure
   modes.
5. **Repeated trials** — pass^k/consistency, not one best run.
6. **Long-horizon tests** — context loss, cancellation, restart, delayed human
   approval, and external state changes.
7. **Cost/latency/quality telemetry** — tokens, tool calls, errors, wall time,
   human intervention, and unnecessary work.

The current tests are necessary but cannot support a claim of general agent
capability.

---

# Phase 15 — Complexity audit

## 15.1 Useful complexity

- 119 agents provide broad examples and domain vocabulary.
- 18 skills provide reusable methodology.
- 46 modules encode practical engineering/domain knowledge.
- The explicit host-neutral JEV direction prevents a provider lock-in.
- Structural validation catches packaging drift.

## 15.2 Complexity that currently harms reliability

- 177 exact trigger collisions across agent frontmatter.
- Duplicate QA, data, blockchain, testing, API, monitoring, performance, and
  migration roles.
- Two model-adapter artifacts under one import path.
- Two incompatible workflow registries.
- Multiple policy sources.
- Multiple task/handoff contract generations.
- Approximately 90 stale module references across roughly 60 agents.
- Duplicate `AGENT.md`/`CLAUDE.md` content and duplicated analysis documents.
- Backup/generated artifacts adjacent to canonical files.
- Version labels spanning 2.5, 2.5.1, 2.8, and schema 1.0/2.5.
- Auto-generation personas that can increase rather than reduce complexity.

## 15.3 Simplification principle

Remove or quarantine a subsystem when it does not provide a distinct,
tested capability. Preserve useful knowledge while eliminating competing
sources of truth. Do not delete domain expertise merely to make the repository
smaller; make its ownership and loading explicit.

---

# Phase 16 — Current ecosystem research

The full source register and applicability notes are in
`.memory/ultimate-dev/tasks/deep-architecture-capability-audit-2026-09-24/evidence/ecosystem-research.md`
and `evidence/ecosystem-research-secondary.md`.

Primary sources fetched on 2026-09-24 included:

- [MCP specification](https://modelcontextprotocol.io/specification/latest),
  [architecture](https://modelcontextprotocol.io/specification/latest/architecture),
  and [tools](https://modelcontextprotocol.io/specification/latest/server/tools);
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/),
  [sessions](https://openai.github.io/openai-agents-python/sessions/),
  [guardrails](https://openai.github.io/openai-agents-python/guardrails/),
  [testing](https://openai.github.io/openai-agents-python/testing/), and
  [orchestration](https://openai.github.io/openai-agents-python/multi_agent/);
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/durable-execution);
- [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents),
  [building effective agents](https://www.anthropic.com/research/building-effective-agents),
  and [tool evaluation](https://www.anthropic.com/engineering/writing-tools-for-agents);
- [A2A specification](https://a2a-protocol.org/latest/specification/);
- [Temporal workflow execution](https://docs.temporal.io/workflow-execution);
- [OpenTelemetry GenAI conventions](https://github.com/open-telemetry/semantic-conventions-genai);
- [OWASP Agentic AI threats](https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/);
- [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework);
- [AgentDojo](https://agentdojo.spylab.ai/);
- [SWE-bench](https://www.swebench.com/).

### Principles extracted

1. Keep model decisions separate from deterministic control and state.
2. Treat durable execution as replayable operations, not saved conversation.
3. Separate thread/task checkpoints from cross-thread memory.
4. Keep context small, high-signal, provenance-bearing, and just-in-time.
5. Use structured, small, namespaced, evaluated tools rather than tool sprawl.
6. Make approval a durable, scoped, replay-resistant state transition.
7. Evaluate external state and repeated trials, not only textual output or
   structural presence.
8. Treat MCP/A2A/workflow engines as adapters, not authorities.
9. Govern self-improvement with candidate isolation and protected regression.
10. Use portable, redacted observability rather than provider-specific logs.

`websearch` returned HTTP 401 in this environment; direct primary URLs were
used instead. This limitation is recorded rather than hidden.

---

# Phase 17 — Target architecture

## 17.1 Target diagram

```text
                         USER / TASK
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ INTAKE + CONTRACT        │
                 │ goal, scope, risk,        │
                 │ acceptance, evidence      │
                 └────────────┬────────────┘
                              ▼
                 ┌─────────────────────────┐
                 │ CAPABILITY DISCOVERY      │
                 │ catalog, versions, trust, │
                 │ health, effects, fallback │
                 └────────────┬────────────┘
                              ▼
                 ┌─────────────────────────┐
                 │ ORCHESTRATOR             │
                 │ smallest safe pattern    │
                 └────────────┬────────────┘
                              ▼
                 ┌─────────────────────────┐
                 │ MODEL PLANNER             │
                 │ proposal only; no authority│
                 └────────────┬────────────┘
                              ▼
                 ┌─────────────────────────┐
                 │ JEV + POLICY GATE         │
                 │ deterministic, no effects │
                 └────────────┬────────────┘
                              ▼
       ┌──────────────────────────────────────────────┐
       │ DURABLE RUNTIME                               │
       │ event journal + state machine                 │
       │ checkpoints, operations, retries, approvals   │
       │ evidence, recovery, cancellation, audit       │
       └──────────────────────┬───────────────────────┘
                              ▼
       ┌──────────────────────────────────────────────┐
       │ CAPABILITY BROKER                             │
       │ native tools | sandbox | secrets | MCP | A2A   │
       │ mapping, isolation, egress, result validation  │
       └──────────────────────┬───────────────────────┘
                              ▼
                    EXTERNAL SYSTEM STATE
                              ▼
       ┌──────────────────────────────────────────────┐
       │ INDEPENDENT VERIFIER / EVALUATOR              │
       │ tests | build | state diff | policy | human   │
       └──────────────────────┬───────────────────────┘
                              ▼
                 COMPACT STATE + EVIDENCE TO MODEL

       ┌─────────────────────────┐
       │ MEMORY / CONTEXT BROKER  │◄────► PROJECT MEMORY
       │ provenance, freshness,   │      typed knowledge
       │ scope, contradiction     │
       └─────────────────────────┘

       ┌─────────────────────────┐
       │ OBSERVABILITY + EVAL     │◄───── optional OTel/A2A/MCP
       └─────────────────────────┘

       ┌─────────────────────────┐
       │ EVOLUTION PROPOSAL GATE  │──► candidate/eval/approval
       └─────────────────────────┘
```

## 17.2 Stable core interfaces

The target should be defined by a small set of versioned contracts:

- **TaskContract** — goal, scope, constraints, acceptance, evidence, risk.
- **CapabilityDescriptor** — canonical ID, version, source, trust, effects,
  isolation, health, expiry, fallback equivalence.
- **Operation** — operation ID, run ID, attempt, action fingerprint,
  idempotency key, side-effect class, deadline, state.
- **PolicyDecision** — policy version, capability/effect intersection,
  approval requirements, reason codes.
- **JEVRequest/JEVPacket** — existing contracts, extended with request/state/
  action binding and trusted host facts.
- **ContextManifest** — selected items, source, reason, freshness, sensitivity,
  budget, token estimate.
- **EvidenceRecord** — verifier, command/query, environment, digests, result,
  before/after state, evidence IDs.
- **ApprovalRecord** — reviewer, exact scope, expiry, consumed/rejected state,
  action fingerprint.
- **TaskEvent** — append-only lifecycle, actor, operation, policy, evidence,
  recovery, and trace links.
- **KnowledgeArtifact** — source, version, scope, verification, expiry,
  candidate/admitted status.

These contracts should be language-neutral JSON Schemas or equivalent
canonical definitions. Hosts may implement them in any language.

## 17.3 Data flow

```text
request
→ contract
→ capability facts
→ model proposal
→ policy/JEV packet
→ operation record
→ approved capability call
→ result/provenance
→ independent verification
→ evidence/state update
→ next model projection
```

## 17.4 State flow

```text
created
→ ready
→ planning
→ planned
→ awaiting_approval (optional)
→ executing
→ observing
→ verifying
→ completed
```

Failure flow:

```text
executing/observing/verifying
→ failed or uncertain
→ diagnose
→ recover or replan
→ checkpoint
→ resume
```

Every mutating operation is an event with an identity and idempotency key. A
snapshot is a projection, not the source of truth.

## 17.5 Tool flow

```text
discover → validate → classify → intersect policy → approve
→ execute with deadline → validate output → record provenance
```

MCP/A2A adapters implement this flow. They do not own state or policy.

## 17.6 Evidence flow

```text
claim → verifier → external observation → evidence record
→ contract evaluation → completion decision
```

Evidence is domain-neutral in shape and domain-specific in verifier.

## 17.7 Adaptation flow

```text
unknown
→ discover
→ identify
→ understand
→ source ledger
→ capability model
→ plan
→ execute
→ observe
→ verify
→ propose knowledge/capability artifact
→ evaluate/admit
→ reuse/version/rollback
```

The runtime should support the progression conceptually, while the actual
research and reasoning remain model/host responsibilities.

---

# Phase 18 — Explicit DO NOT BUILD

Ultimate-Dev should not currently build:

1. **A framework-specific agent for every language or framework.** Add a
   capability/knowledge package and route by capability first.
2. **A second competing orchestration engine.** Pick one code-owned workflow
   contract; keep patterns as strategies within it.
3. **A hard MCP dependency.** MCP expands capability but must not be a
   single point of failure.
4. **An always-on distributed microservice for JEV.** The pure kernel is
   intentionally host-native and side-effect-free.
5. **A bundled Docker/Podman/browser/model-provider stack.** Providers belong
   to hosts/adapters; missing capabilities must be explicit.
6. **A giant universal prompt or ontology.** Use small, composable knowledge
   artifacts and domain packs.
7. **Automatic global agent/skill generation after one successful task.** Use
   staged candidates and admission gates.
8. **A vector database or “memory everything” subsystem by default.** Memory
   needs provenance, scope, retention, contradiction handling, and cost bounds.
9. **A model/LLM judge as the sole verifier.** Verify external state first;
   use models as secondary assessors.
10. **A silent shell/browser fallback for a missing specialized tool.** Fallback
    must be semantically and security equivalent or explicitly approved.
11. **Unbounded configuration for every provider, command, and path.** Use
    capability descriptors and project discovery.
12. **A public MCP/A2A registry treated as a trust anchor.** Registry metadata
    is discovery, not authorization.
13. **Full prompts, secrets, and raw tool arguments in ordinary logs.** Use
    digests, redaction, and tiered retention.
14. **Duplicated manifests, role registries, workflow definitions, and backups.**
    Generate them from one canonical source.
15. **More agents as a substitute for routing, capability discovery, and
    evaluation.** More specialists can increase collisions and context cost.

---

# Phase 19 — Prioritized roadmap

## P0 — Architectural correctness

| Problem | Solution | Affected files / architectural location | Complexity | Benefit | Risk | Dependencies | Why now |
|---|---|---|---|---|---|---|---|
| Declarative surfaces are disconnected | Define one canonical registry/workflow/policy/capability contract and make runtime load it | `runtime/`, `config/`, `router/`, `workflows/`, `tools/`, schemas | High | Removes competing sources of truth | Migration/regression | Contract decisions | Everything else depends on authoritative seams |
| JEV gate is optional and weakly bound | Make schema validation, request/action/state binding, restart rehydration, and final scope check mandatory for privileged execution | `runtime/core/engine.py`, JEV schemas/policy, adapter contract | Medium-high | Closes authorization bypasses | Compatibility | Event/operation contract | Security correctness cannot wait |
| Completion is not evidence-gated | Add contract evaluation and independent verifier registry before `completed` | `runtime/core/verification.py`, `engine.py`, schemas | Medium | Makes “verified” meaningful | Domain verifier work | Evidence schema | Current tests can create false success |
| Security config is declarative only | Add path/command/URL/secret boundaries at capability broker; make policy fail closed | `policy.py`, `config/security.yaml`, session/executor seam, tests | High | Reduces prompt-only security | Host compatibility | Capability descriptors | Concrete path and approval gaps already exist |

## P1 — Critical missing capabilities

| Problem | Solution | Affected files / architectural location | Complexity | Benefit | Risk | Dependencies | Why now |
|---|---|---|---|---|---|---|---|
| No durable operation protocol | Add operation ID, attempt, idempotency, deadline, side-effect class, uncertain state | `state.py`, `engine.py`, new schemas | High | Safe retries/recovery | Storage complexity | P0 contracts | External side effects cannot be replayed safely |
| No executable handoff/subagent lifecycle | Implement one workflow/agent adapter with start/join/cancel/result and bounded context | runtime or host adapter, workflows | High | Makes orchestration real | Overbuilding risk | Operation contract | Current pattern claims exceed implementation |
| No capability discovery/broker | Add canonical descriptors, health/provenance, native mapping, explicit fallback | `capabilities.py`, `tools/`, adapters | Medium-high | Enables unfamiliar tech/tools | Provider complexity | P0 registry | Universality depends on capability seams |
| Human approval is not durable | Add scoped approval records, expiry, fingerprint, replay protection | runtime, policy, schemas, UI contract | Medium | Safe HITL | User friction | Operation contract | Human review is currently a label |

## P2 — Reliability

| Problem | Solution | Affected files / architectural location | Complexity | Benefit | Risk | Dependencies | Why now |
|---|---|---|---|---|---|---|---|
| Snapshot-only recovery | Add event journal, checkpoint versions, replay/validation, leases | `state.py`, storage adapter | High | Resumability/audit | Storage burden | P1 operation | Long tasks fail at boundaries |
| Context/memory incoherence | Add context manifest, provenance/freshness, compaction, scoped memory records | `context.py`, memory, config | Medium-high | Less pollution/poisoning | Retrieval complexity | P0 contracts | Context is a reliability/security surface |
| Tool failure handling absent | Add timeout, cancellation, retry classification, uncertainty, health, result validation | session/capability adapter | Medium | Resilience | Retry side effects | P1 idempotency | External tools fail unpredictably |
| Version/source drift | Generate all catalogs/docs from canonical metadata; remove/quarantine backups | scripts, manifest, entrypoints | Medium | Less ambiguity | Migration effort | P0 registry | Drift already affects routing/install |

## P3 — Verification and evidence

| Problem | Solution | Affected files / architectural location | Complexity | Benefit | Risk | Dependencies | Why now |
|---|---|---|---|---|---|---|---|
| Structural tests mistaken for agent evaluation | Add scenario runner, traces, real tasks, repeated trials, metrics | `tests/`, `evals/`, new evaluator | High | Measures actual capability | Cost | P0/P1 runtime | Required for honest claims |
| Domain verification absent | Define verifier interface and domain evidence packs | schemas, modules, evals | High | Supports non-software domains | Domain expertise needed | Evidence contract | Universality requires domain depth |
| Security not tested adversarially | Add AgentDojo-style injection, tool poisoning, replay, exfiltration tests | eval/security suites | Medium-high | Finds real boundary failures | Test maintenance | Capability/security contracts | Prompts alone are insufficient |

## P4 — Adaptation and evolution

| Problem | Solution | Affected files / architectural location | Complexity | Benefit | Risk | Dependencies | Why now |
|---|---|---|---|---|---|---|---|
| Conflicting self-generation | One proposal/evaluation/admission/rollback lifecycle | self-evolve, generators, maintainer, gap tracker | High | Safe learning | Slower autonomy | Eval/regression | Current auto-write behavior is unstable |
| Unknown-tech knowledge not durable/reusable | Add source ledger and candidate knowledge artifact format | emerging handler, memory, manifest | Medium | Better adaptation | Stale/poisoned sources | Evidence/evolution gate | Universality needs controlled learning |
| Context/tool sprawl | Measure and prune tools/agents by task outcomes | manifest, tools, evals | Medium | Less collision/cost | Removing useful niche tools | Evaluation | 119 agents are not automatically valuable |

## P5 — Advanced capabilities

| Problem | Solution | Affected files / architectural location | Complexity | Benefit | Risk | Dependencies | Why now |
|---|---|---|---|---|---|---|---|
| Remote agent interoperability | Optional A2A adapter with Agent Cards/tasks/artifacts | adapters/runtime | High | Cross-agent reach | Auth/version complexity | Stable core contracts | Only after local seam is coherent |
| Long-running distributed execution | Optional Temporal-like/event backend | runtime/storage adapter | High | Scale/reliability | Operational burden | Event protocol | Not a core prerequisite |
| Rich telemetry | Optional OTel/OpenInference exporter with redaction | observability adapter | Medium | Cross-provider analysis | Privacy/storage | Stable event schema | Useful after traces exist |
| Advanced model/host optimization | Capability-based routing and empirical tuning | model gateway/evals | Medium | Cost/quality gains | Overfitting | Evaluation | Optimize only with evidence |

---

# Phase 20 — Universality and future-proof stress test

The desired rule is:

> A new technology or domain should normally require knowledge, capability
> descriptors, adapters, policies, and verifiers—not a runtime fork.

The following matrix applies the required fifteen questions to representative
scenarios. “Agent?” means whether a new *agent process* is needed; the answer
is usually no.

## 20.1 Scenario cards

### A. A new programming language appears

1. **Already knows:** file inspection, command execution, testing concepts,
   safety, evidence, and generic engineering.
2. **Must discover:** manifests, compiler, package manager, test runner,
   runtime/toolchain, project conventions, available commands.
3. **Must learn/store:** language/compiler/package-manager knowledge in a
   technology knowledge artifact with source/version/expiry.
4. **Tool capability:** `project.inspect`, `process.execute`, `filesystem.read`,
   `test.discover`/technology adapter.
5. **Skill:** one reusable “unfamiliar language adoption” procedure or a
   technology knowledge module.
6. **Agent:** normally no; a generic domain specialist can use the procedure.
7. **Runtime:** no change if capabilities/effects remain existing primitives.
8. **Orchestration:** no change; resolver selects capability package.
9. **Verification:** run a discovered, project-specific compile/test verifier;
   record command, environment, and exit status.
10. **Damage prevention:** candidate knowledge is staged; capability actions
    remain policy-gated; no automatic package installation.
11. **Reuse:** adapter/knowledge is reusable across projects.
12. **Versioning:** source/toolchain version and artifact version.
13. **Rollback:** unregister candidate and restore prior catalog version.
14. **Minimum code:** descriptor + discovery/verification adapter + knowledge
    document; no new runtime.
15. **Assessment:** current stack/test detectors and command policy make this
    more than knowledge-only today; the canonical JEV boundary itself is ready.

### B. A new web framework appears

1. Knows generic frontend architecture, files, HTTP, UI, accessibility, tests.
2. Discovers manifest/config, conventions, build/test commands, versions.
3. Stores framework knowledge and migration/verification patterns.
4. Uses filesystem/shell/browser/HTTP capabilities.
5. Uses frontend methodology plus a framework knowledge artifact.
6. No new agent normally; framework-specific prompt may be a skill/module.
7. No runtime change.
8. No orchestration change.
9. Build/typecheck/tests/browser checks selected by discovered capability.
10. Candidate knowledge cannot grant write/network capabilities.
11. Reusable across projects.
12. Versioned source and framework profile.
13. Rollback by profile/catalog version.
14. Descriptor + adapter + knowledge/test profile.
15. Mostly supported; stale module references and missing explicit web tools
    currently weaken the path.

### C. A new database appears

1. Knows schema inspection, query safety, transactions, evidence, backups.
2. Discovers client/CLI, connection/auth, schema dialect, transaction semantics,
   available operations.
3. Stores database adapter/knowledge and dialect-specific verification.
4. `database.query`, `database.transaction`, `database.inspect` adapters.
5. Generic database skill plus database profile.
6. No new agent normally.
7. No JEV/runtime change for existing read/write/network effects.
8. No orchestration change.
9. Reconcile schema/data state, query results, transaction outcome, and
   independent readback.
10. Credentials remain in secret boundary; query scope is explicit.
11. Reusable database profile.
12. Client/server/protocol version.
13. Disable adapter and restore prior catalog.
14. Capability descriptor, adapter, policy, verifier, knowledge.
15. Strong canonical adaptability; current generic DB prompt is not a substitute
    for a real adapter/verifier.

### D. A new cloud or sovereign platform appears

1. Knows generic deployment, identity, network, observability, rollback.
2. Discovers CLI/API, auth, regions, quotas, deployment model, isolation,
   logging, and policy requirements.
3. Stores cloud adapter and operations knowledge.
4. Native cloud/API/SSH/deployment capability descriptors.
5. DevOps/cloud methodology plus provider profile.
6. No new agent normally.
7. No runtime change if effects remain network/write/execute.
8. Workflow may need a provider-specific deployment step, but core pattern
   remains the same.
9. Deployment state/readback, health checks, rollback and audit evidence.
10. Egress, secret, production, and destructive-action policy.
11. Reusable cloud profile.
12. API/CLI version and policy snapshot.
13. Withdraw capability/profile, preserve audit, restore previous version.
14. Adapter + policy + deployment verifier + knowledge.
15. No JEV change; current network allowlist and workflow assumptions require
    extension work.

### E. A new package manager appears

1. Knows dependency inspection, install intent, lockfiles, reproducibility.
2. Discovers command syntax, manifest, lockfile, registry, trust model, offline
   mode, and available binary.
3. Stores package-manager descriptor/knowledge.
4. `dependency.resolve/install/audit` capabilities with explicit effects.
4. No silent installation; missing package manager is a blocker/review.
5. Generic dependency skill.
6. No agent normally.
7. No core runtime change.
8. Package-specific command adapter; possibly a workflow profile.
9. Lockfile/dry-run/audit/build/test evidence.
10. Package source/signature/sandbox/approval policy.
11. Reusable package-manager profile.
12. Tool and manifest version.
13. Disable profile/adapter; restore prior lock/policy snapshot.
14. Descriptor + command adapter + policy/verifier.
15. Current finite command allowlists make this a control-plane extension, not
    knowledge-only today.

### F. A new AI/ML framework appears

1. Knows data/model/evaluation/security and general engineering.
2. Discovers APIs, hardware/runtime needs, model formats, training/inference
   tools, evaluation and resource requirements.
3. Stores framework/model knowledge and benchmark/evaluation profile.
4. Model/runtime adapters, sandbox/GPU capability, data/artifact tools.
5. AI/ML methodology plus framework knowledge.
6. Usually no new agent; a specialist profile can improve prompting.
7. No core change unless new side-effect/resource semantics are introduced.
8. Orchestration may add a model-development workflow.
9. Dataset/model/evaluation/reproducibility/security evidence.
10. Data, model, code, and credential boundaries; no unapproved downloads.
11. Reusable model/framework profile.
12. Framework/model/checkpoint/dataset versions.
13. Quarantine candidate and revert dependency/evaluation baseline.
14. Adapter + resource policy + evaluation suite + knowledge.
15. Legacy Python provider coupling is avoidable on canonical path; current
    model adapter ambiguity must be isolated.

### G. A new communication/tool protocol appears

1. Knows message schemas, capability boundaries, error handling, auth.
2. Discovers protocol version, discovery, capabilities, state model, failure and
   security semantics.
3. Stores protocol adapter/knowledge and compatibility profile.
4. Protocol-specific client/server capability adapter.
5. Generic integration/API skill.
6. No agent normally.
7. No runtime change if mapped to existing canonical effects.
8. No orchestration change; capability resolver selects adapter.
9. Conformance tests, malformed input, timeout, auth, and state checks.
10. Treat descriptions/results as untrusted; validate and constrain.
11. Reusable protocol adapter.
12. Protocol version and negotiated feature set.
13. Disable adapter and revert negotiated policy.
14. Adapter + schemas + health/fallback policy + tests.
15. Current MCP absence is an implementation gap, not a JEV limitation; do not
    make the protocol itself the runtime.

### H. A new software architecture pattern appears

1. Knows generic boundaries, trade-offs, observability, migration, testing.
2. Discovers applicability, constraints, operational implications, and project
   conventions.
3. Stores architecture knowledge/decision template and examples.
4. Usually existing code/search/build/deploy capabilities.
5. Architecture skill/module.
6. No new agent.
7. No runtime change unless lifecycle/state semantics change.
8. No orchestration change.
9. Architecture decision, dependency/impact evidence, tests, operational
   verification.
10. Candidate knowledge cannot silently authorize migrations.
11. Reusable architecture knowledge.
12. Pattern version and source references.
13. Revert knowledge/decision artifact; preserve decision history.
14. Knowledge + ADR/verifier profile.
15. Strongly suited to current architecture if documentation drift is fixed.

### I. A completely new professional domain appears

1. Knows universal reasoning, evidence, planning, policy, human review.
2. Discovers terminology, artifacts, stakeholders, regulations, systems, and
   success measures.
3. Stores a domain knowledge pack, source ledger, evidence schema, and risk
   policy.
4. Domain tools/capability adapters; no domain-specific runtime primitives
   unless genuinely new effects exist.
5. Domain methodology skill.
6. Usually no new agent; domain package may include a role prompt.
7. No runtime fork.
8. Domain workflow/pattern selected by descriptors; no competing engine.
9. Domain verifier: records, citations, expert review, reconciliation, formal
   proof, field test, or other appropriate evidence.
10. Regulated data, consent, confidentiality, and human approval are explicit.
11. Reusable across organizations with scope/policy separation.
12. Domain pack and evidence schema versions.
13. Candidate withdrawal, prior pack restore, audit retained.
14. Domain knowledge + capabilities + policy + verifier + evaluation cases.
15. This is the target universality path; current domain files are a good start
    but not yet a first-class extension contract.

### J. A hypothetical future technology with no known examples

1. Knows only universal primitives and how to investigate uncertainty.
2. Discovers available docs/source/tools or records unknowns honestly.
3. Stores a source ledger with low confidence and expiry, not an invented
   convention.
4. Requests only capabilities explicitly advertised by the host.
5. Uses universal discovery/research skill; no premature specialist.
6. No agent by default.
7. No runtime change unless a genuinely new primitive is required.
8. No orchestration change; route to review/discovery.
9. Requires human review or evidence-backed safe experiment; no fake success.
10. Fails closed, isolates experiments, prevents global learning from one run.
11. Candidate can be reused only after evaluation/admission.
12. Candidate version/source digest/confidence.
13. Discard/quarantine candidate and rollback any experimental state.
14. Candidate descriptor, source ledger, experiment/verifier, admission record.
15. The architecture should discover and safely learn without predicting the
    technology in advance; current emerging-tech prompt is directionally right
    but its auto-generation behavior is not.

## 20.2 Universality verdict

The canonical JEV/runtime boundary passes the “no technology ceiling” test for
new domains, databases, clouds, protocols, models, and knowledge areas. The
complete shipped package does not yet pass it for new languages, package
managers, deployment systems, test paradigms, or non-software verification
because those concerns leak into detectors, permissions, workflows, and context
configuration.

The minimum future-proofing strategy is therefore not prediction. It is:

```text
discover → model capabilities → learn with sources → propose artifacts
→ verify → admit → version → reuse → rollback
```

---

# Final test — brutally honest assessment

## 1. What is ultimate-dev today?

A very large, carefully documented agent skill and specialization catalog with
an executable narrow state runtime and a high-quality host-neutral JEV kernel.
It can be valuable when embedded in a capable host, but it is not yet a
self-contained general execution platform.

## 2. What is it trying to become?

A universal runtime plus deep software-engineering specialization, with
replaceable domain/technology knowledge, capability adapters, durable
execution, evidence, recovery, and controlled evolution.

## 3. What is unusually strong?

- The conceptual ownership split between model, orchestration, policy, runtime,
  and tools.
- The decision to keep JEV pure, deterministic, host-neutral, and free of
  provider/tool side effects.
- Canonical capability IDs and the missing-capability/no-installation rule.
- A broad and useful body of software/domain knowledge.
- Progressive context and evidence-oriented instructions.
- The decision not to conflate prompt instructions with actual execution in the
  agent entrypoint.
- Good structural tests and JEV conformance tests.
- The conservative Task Observer boundary added in the prior change.

## 4. What is fundamentally weak?

- The authoritative execution path is not connected.
- Most declared policy, workflow, routing, permission, and model configuration
  is inert from the Runtime's perspective.
- State snapshots are not replayable durable execution.
- JEV integration is optional, weakly bound, and not restart-safe.
- Verification does not prove external success.
- Capability discovery, tool health, MCP, and result provenance are absent.
- Context/memory is weakly typed and not safely integrated.
- Self-evolution can globally publish unreviewed artifacts.
- Security is mostly instruction/configuration, not a runtime boundary.
- Evaluation is structural, not agent-level.

## 5. What is missing?

A canonical capability broker, operation/event protocol, workflow executor or
host adapter, evidence/verifier registry, durable approval protocol, context
manifest/memory record model, optional MCP/A2A adapters, security enforcement,
end-to-end evaluator, and governed evolution gate.

## 6. What is duplicated?

Agent roles, testing/API/monitoring/migration/data knowledge, model-adapter
surfaces, workflow definitions, policy sources, task/handoff contracts,
version metadata, wrapper documents, and evolution personas.

## 7. What is over-engineered?

The breadth of agents and instructions is not inherently over-engineering, but
the current combination of multiple registries, overlapping trigger sets,
auto-generators, duplicate workflows, backups, and version generations creates
more coordination surface than the executable runtime can govern.

## 8. What is under-engineered?

The actual runtime seams: authorization, state transitions, evidence, recovery,
idempotency, capability health, context provenance, approvals, traces, and
evaluation.

## 9. What could become a serious architectural problem?

A system that appears universal because it can route any prompt to a large
agent catalog while silently relying on the host/model for discovery,
permissions, completion, and recovery. That creates a dangerous gap between
perceived capability and enforced capability. A second serious risk is
self-evolution that increases the catalog after every unfamiliar task without
protected evaluation.

## 10. What should be removed?

- Duplicate/competing workflow and registry sources.
- Automatic global agent/skill publication.
- Provider-specific model code from the canonical model-independent path.
- Unused/unsafe legacy helpers from canonical imports, while preserving them
  separately until intentionally migrated.
- Backup/generated duplicates from the canonical source set.
- Non-semantic trigger-only routing as the primary mechanism.

Do not delete useful domain knowledge merely to reduce file count.

## 11. What should be added?

One canonical capability/operation/evidence/approval contract set, an executable
broker/workflow seam, a restart-safe runtime event protocol, an evaluator,
context/memory provenance, optional MCP/A2A adapters, and a candidate evolution
gate.

## 12. What should remain deliberately simple?

- The pure JEV kernel.
- One small state machine.
- Inline execution as the default.
- One generated manifest/catalog path.
- Filesystem storage as the default backend.
- No always-on daemon, vector database, model provider, sandbox, or browser
  bundled into the core.
- No multi-agent swarm unless independent work justifies it.

## 13. What are the ten highest-impact changes?

1. Make one capability registry the runtime's authoritative source.
2. Make JEV schema validation, action/state binding, restart rehydration, and
   final scope enforcement mandatory for privileged execution.
3. Add an operation/event protocol with idempotency, deadlines, uncertainty, and
   recovery.
4. Connect one code-owned workflow/host adapter to state, handoffs, and
   subagent lifecycle.
5. Add a capability broker with health, provenance, isolation, result validation,
   and explicit fallback.
6. Replace boolean evidence matching with external-state evidence and verifier
   contracts.
7. Enforce path, secret, URL, command, approval, and untrusted-content
   boundaries at runtime.
8. Add a real end-to-end evaluation runner with adversarial and repeated-trial
   suites.
9. Gate all self-evolution through candidate evaluation, protected regressions,
   versioning, and rollback.
10. Remove duplicate sources of truth and simplify the catalog based on measured
    task outcomes.

## 14. What should NOT be built?

The explicit list in Phase 18: no framework-agent multiplication, no second
orchestration engine, no hard MCP dependency, no bundled provider stack, no
automatic global self-modification, no giant prompt/ontology, no unbounded
memory, no LLM-only verifier, no silent capability substitution, and no public
registry treated as trust.

## 15. What would make it exceptional for software development?

- Repository-specific capability and test discovery.
- Small, high-signal context with just-in-time retrieval.
- Real subagents only when independent work justifies them.
- Code-owned execution and verification independent of model self-report.
- Safe retries/recovery after tool/test/process failure.
- Evidence-backed completion with regression and security checks.
- Empirical evaluation on held-out repositories and repeated trials.
- Minimal, composable tools rather than a giant overlapping catalog.

## 16. What would make the same foundation useful outside software?

The universal runtime primitives plus domain packs containing:

- domain terminology and objectives;
- source/record evidence models;
- risk/compliance policy;
- domain capability adapters;
- domain verifiers and human approval rules;
- scoped output/artifact contracts;
- repeated real-task evaluations.

## 17. What enables unfamiliar-technology handling?

Capability-based discovery, source/version ledgers, generic inspection and
execution primitives, technology knowledge artifacts, tool adapters, and
project-specific verification. The emerging-tech handler is a useful prompt for
this process.

## 18. What currently prevents new-language/framework adaptation?

The canonical JEV does not prevent it. The shipped stack detector, test
detection, command allowlists, path permissions, stale module references,
workflow assumptions, and agent/tool ID mismatches do.

## 19. What prevents adaptation to technologies that do not exist yet?

There is no formal source ledger, capability admission/evaluation transaction,
safe experiment protocol, candidate versioning, or rollback mechanism. The
current auto-generate persona can create artifacts before those safeguards
exist.

## 20. What prevents entirely new domains?

There is no first-class domain-pack interface joining knowledge, capability
adapters, risk policy, evidence schemas, verifiers, and evaluation cases.
Non-software domains also inherit software-centric workflow/test defaults.

## 21. What prevents the system from deserving the name “ultimate-dev” today?

The gap between **breadth of instructions** and **enforced execution
reliability**. The project currently demonstrates that it can describe a broad
agent ecosystem. It has not yet demonstrated that one small, model-independent
runtime can safely discover capabilities, execute unfamiliar work, recover,
verify external state, learn without regression, and do so across domains with
minimal host-specific glue.

---

# Final verdict

Ultimate-Dev is not yet merely a collection of unrelated AI features. It has
the beginnings of a real general platform: a meaningful universal runtime
concept, a strong deterministic decision boundary, durable state primitives,
and deep specialization.

But today it is still closer to a **feature-rich prompt ecosystem with a
partial runtime** than to a genuinely general agent execution platform.

It can become one, but the path is not “add more agents.” The path is:

```text
make the seams real
→ make capabilities explicit
→ make operations durable
→ make evidence external and trustworthy
→ make policy runtime-enforced
→ make evolution governed
→ measure outcomes
```

Until those steps are complete, the system's breadth should be treated as
potential architecture, not proof of general-purpose capability.

---

## Evidence index

- Repository inventory: `.memory/ultimate-dev/tasks/deep-architecture-capability-audit-2026-09-24/evidence/repository-inventory.md`
- Structural signals: `.memory/ultimate-dev/tasks/deep-architecture-capability-audit-2026-09-24/evidence/structural-signals.md`
- Runtime reconstruction: `.memory/ultimate-dev/tasks/deep-architecture-capability-audit-2026-09-24/evidence/runtime-reconstruction.md`
- Orchestration/evolution audit: `.memory/ultimate-dev/tasks/deep-architecture-capability-audit-2026-09-24/evidence/orchestration-evolution.md`
- Universality/coupling audit: `.memory/ultimate-dev/tasks/deep-architecture-capability-audit-2026-09-24/evidence/universality-coupling.md`
- Boundary matrix: `.memory/ultimate-dev/tasks/deep-architecture-capability-audit-2026-09-24/evidence/boundary-matrix.md`
- Baseline verification: `.memory/ultimate-dev/tasks/deep-architecture-capability-audit-2026-09-24/evidence/baseline-verification.md`
- Primary ecosystem research: `.memory/ultimate-dev/tasks/deep-architecture-capability-audit-2026-09-24/evidence/ecosystem-research.md`
- Independent ecosystem brief: `.memory/ultimate-dev/tasks/deep-architecture-capability-audit-2026-09-24/evidence/ecosystem-research-secondary.md`
- Durable task state/checkpoints: `.memory/ultimate-dev/tasks/deep-architecture-capability-audit-2026-09-24/checkpoints/`

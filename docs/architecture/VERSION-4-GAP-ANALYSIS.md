# Version 4 — Architecture Gap Analysis

Baseline: v3.2.0. Requirement: the canonical 13-layer architecture, Phase 1–3
of the specification (inspect, map, identify gaps). No code was written to
produce this document; every claim below is a file or symbol that was checked.

## What already exists and is real

These are implemented, connected, and tested. They are preserved, not rebuilt.

| Required subsystem | Present as | Evidence |
|---|---|---|
| JEV decision kernel | `runtime/jev/engine.mjs` | 1,072 lines; `validateDecisionRequest`, `validateDecisionPacket`, `decide`; 53 NOUL/CHOICE/SCORE references |
| Unified task state | `runtime/core/state.py` | four channels, versioning, provenance |
| Runtime orchestration | `runtime/core/engine.py` | `class Runtime` with JEV binding, `checkpoint`, `handoff`, `record_jev_decision`, `recover_stale_operations` |
| Lifecycle and recovery | `runtime/core/lifecycle.py` | 47 recovery references; pause/resume/abandon/cleanup |
| Capability fabric | `runtime/core/capabilities.py` | `class Capability`, `class CapabilityRegistry`, `discover` |
| Policy and permissions | `runtime/core/policy.py` | bound-action validation |
| Verification | `runtime/core/verification.py` | `class Verification` |
| Memory | `runtime/core/memory.py` | `MemoryStoreError`, `SecretRefused`, provenance records |
| Workflow execution | `runtime/core/workflow.py` | `runner`, `WorkflowEvent`, step timeouts |
| Method library | `skills/`, `agents/`, `modules/`, `router/` | 33 skills, 119 agents, 46 modules, 15 router docs |
| Contracts | `contracts/` | 11 portable contracts, all `runtime_required: false` |
| Provider-free enforcement | `scripts/` | 18 verification scripts, all dependency-free |

## Genuine gaps

Ordered by how much of the specification each one unblocks.

### G1 — No unified task graph engine *(blocks §8, §9, §30, §41)*

This is the keystone. `runtime/core/workflow.py` executes a **linear ordered list
of steps**. There is no `TaskGraph`, no `TaskNode`, no dependency resolution, no
scheduler, no topological ordering, no conditional branch, no loop, and no
parallel execution anywhere in the runtime:

| Required symbol | Hits in `runtime/` |
|---|---|
| `class .*Graph` | 0 |
| `def schedule` | 0 |
| topological ordering | 2 (incidental) |

Section 41 forbids competing orchestrators and section 30 requires workflows to
use the Unified Task Engine. Neither is currently satisfiable, because the
Unified Task Engine does not exist. Everything about "stateful decision-and-
execution system, not a pipeline" is currently only a contract in YAML, not a
runtime capability.

### G2 — No execution-mode selection *(§5, §9)*

The eight required modes (`DIRECT`, `SKILL`, `AGENT`, `MULTI_AGENT`, `WORKFLOW`,
`RESEARCH`, `AUTONOMOUS`, `RECOVERY`) appear nowhere in `engine.py`. Mode is
effectively implicit in whichever entry point was called.

### G3 — No verifier taxonomy *(§17)*

`verification.py` exposes a single `class Verification`. The specification
requires test, state, artifact, integration, independent, and adversarial
verifiers, and requires `INCONCLUSIVE` as a first-class result alongside
PASS/FAIL.

### G4 — No `doctor` *(§32)*

`grep doctor` across `runtime/` and `scripts/` returns nothing. The required
diagnostic that detects missing, invalid, duplicate, orphaned, unreachable,
incompatible, misconfigured, and unverified components does not exist. This is
also the check that would have caught G1–G3 automatically.

### G5 — No subskill concept *(§11, §33)*

There is no `subskills/` directory and no subskill reference in `config/` or
`scripts/`. Subskills are currently indistinguishable from skills.

### G6 — Required directories absent *(§33)*

`policies/`, `capabilities/`, `knowledge/`, `evaluations/` do not exist. Policy
and capability *responsibilities* are implemented in Python, which §33 permits
("map responsibilities instead of duplicating directories"), but the MD/YAML
declarative surface the specification wants for human-authored definitions is
missing for policy and capability.

### G7 — Task-node contract absent *(§8)*

The twenty-field `TaskNode` schema has no counterpart in `contracts/`.

### G8 — No end-to-end proof *(§37, §38)*

Nothing exercises the full chain request → intent → state → JEV → mode → graph →
skill → agent → capability → execute → observe → evidence → verify. The test
matrix in §38 has no harness behind it.

## Not gaps — deliberate design decisions to preserve

- **The prompt core is MD/YAML and the runtime is Python/MJS.** The
  specification's §3 rule is satisfied: every human-authored definition is
  `.md` or `.yml`, and no JSON/TOML/XML is authoritative. The executable
  runtime is Python, which §3 explicitly permits.
- **Runtime is optional.** All 11 contracts declare `runtime_required: false`.
  The specification does not require the runtime to be mandatory, and making it
  so would break prompt-only operation.
- **JEV never authorizes.** It is a policy boundary that returns
  `approve`/`human_review`/`deny`; the host remains the authority. The
  specification agrees, and this must not be changed to satisfy §6's stronger
  wording.

## Discrepancy between the specification and this implementation

The specification states JEV must expose eight named internal stages and
seventeen `*_DECISION` decision types. `engine.mjs` exports three functions and
no `*_DECISION` constants. The **responsibility** exists (JEV aggregates
NOUL/CHOICE/SCORE and returns a packet); the **named internal decomposition**
does not. Implementing the naming is a documentation and structure change, not
a behavioural one, and should be done honestly rather than by adding empty
symbols.

## Build order

Sequenced so that each step is verifiable and no step is a stub.

1. **G1 + G7** — task graph contract, then the engine. Everything else depends on
   one orchestrator existing.
2. **G2** — execution-mode selection, as a field the graph engine consumes.
3. **G4** — `doctor`, which then continuously detects regressions in G1–G3.
4. **G3** — verifier taxonomy, including `INCONCLUSIVE`.
5. **G5 + G6** — subskills, and the declarative surfaces.
6. **G8** — end-to-end test proving the chain, plus a deliberate failure to
   prove recovery.

Each step reports what was actually verified. Nothing in this document is
implemented yet.

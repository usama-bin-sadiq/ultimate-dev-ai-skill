# Version 4 — Architecture Decision Record

Status: **accepted**, pending review
Baseline: v3.2.0 (`9442dfc`) plus uncommitted v4 groundwork
Date: 2026-09-26
Supersedes: `VERSION-4-GAP-ANALYSIS.md` (see §6 — it is stale and over-reports)

This record arbitrates the specification before it is implemented. It exists
because the specification contradicts itself at the architecture level, and
because the most recent gap analysis no longer describes the repository.

---

## 1. Verified baseline

| Fact | Evidence | Result |
|---|---|---|
| Version | `cat VERSION` | `3.2.0` |
| HEAD | `git log -1` | `9442dfc chore: release v3.2.0` |
| Suite before this record | `pytest tests/ -q` | **853 passed, 2 failed** |
| Suite after this record | `pytest tests/ -q` | **855 passed, 0 failed** |
| Structural validator | `scripts/validate-consistency.py` | `consistent`, exit 0 |

The 2 failures were caused by uncommitted v4 work: `contracts/task-graph.yaml`
existed but was absent from the `contracts:` list in `skill-manifest.yaml`.
Root cause confirmed at `scripts/validate-consistency.py:139` (`actual_contracts()`
returns a `sorted()` list) and `:358-361` (manifest must equal it exactly).
Fix: one added line. No behaviour changed.

---

## 2. D1 — Execution authority

**Decision: asymmetric authority (1C).** Authority is split by *decision class*,
not by component.

| Decision class | Owner | Verifiable? |
|---|---|---|
| Judgment — intent, decomposition, route, recovery choice | host model / JEV | **No, by construction** |
| Mechanics — state, versioning, checkpoints, evidence ledger, policy gate, timeout, capability resolution, resume drift detection | deterministic runtime | Yes |
| Effects — any side-effecting action | runtime-mediated, host-injected executor, **observation mandatory** | Yes |

### Why this and not the alternatives

1C is not a new idea. It is the boundary the project already documents, upgraded
from a *documented rule* to an *enforced gate*.

- `SKILL.md`: "The host supplies tools, permissions, policy, and approvals.
  Ultimate-Dev does not install providers, execute tools, or claim authorization
  on the host's behalf."
- `runtime/core/engine.py:38-46`: "It never imports a model provider or selects
  a sandbox/browser provider… delegates approved actions to an explicitly
  injected executor."

**Rejected: runtime-authoritative (1B).** Requires a mandatory Python/Node
runtime, which contradicts "Prompt-only installation has no Python, Node.js, or
model-provider dependency" (`AGENTS.md`) and `runtime_required: false` on 10 of 11
YAML contracts. `docs/architecture/UNIFIED-AGENT-ROADMAP.md` already recommends
against it. It also relocates the boundary rather than removing it: the engine
still needs a caller, so the model becomes a subprocess provider.

**Rejected: skill-authoritative (1A).** Leaves "not a pipeline" unverifiable and
leaves `MODEL CLAIM ≠ OBSERVATION` as advice. "No fake execution" would be
asserted rather than checkable.

### The enforceable part of 1C

Every effect must produce a runtime-recorded observation. An effect with no
observation is not complete, regardless of what a model reports.

**Currently not implemented.** `runtime/core/task_graph.py` contains no
`observation` symbol; the evidence trail is whatever the injected executor
returns. This is the primary remaining v4 implementation gap.

**Reversal condition:** if the project stops shipping as a portable copy-only
skill and becomes a hosted service, revisit 1B.

---

## 3. D2 — One orchestrator, and the ownership table

The specification's §41 forbids competing orchestrators, but its own §4/§5/§6/§10/§30
enumerate four schedulers (JEV `SCHEDULING_DECISION`, Execution Mode Selector,
Task Engine Scheduler, Workflow runner) and two executors (Task Engine node
executor, Execution Fabric). §4 is also a vertical 13-box arrow diagram, which is
the pipeline §1 forbids.

**Decision:** §4 is a *component inventory and connectivity spec*, not control
flow. Control flow comes from the task-graph state machine. Exactly one owner
per concern:

| Concern | Sole owner | Explicitly not owned by |
|---|---|---|
| Deciding the path | JEV | Task Engine, workflow runner |
| Ordering, parallelism, readiness | **Task Engine** | JEV, mode selector, workflow runner |
| Loop / branch / retry / rollback | **Task Engine** | Execution Fabric |
| Side-effect execution, timeout, capture | Execution Fabric | Task Engine |
| Graph shape from a mode | **Task Engine graph builder** | separate "Execution Mode Selector" |
| Workflow | data — a reusable graph template | a runner with its own scheduler |

JEV *proposes* parallelism and planning depth; the Task Engine *disposes*, because
only it observes actual completion state.

This is already encoded at `contracts/task-graph.yaml:47` — "Only one
orchestrator exists. Workflows and execution modes lower to this graph." — and
`runtime/core/task_graph.py:1-16`. **Preserve both verbatim.**

---

## 4. D3 — Two-grade verification

All 11 contracts are `runtime_required: false`, so in prompt-only mode the only
evidence producer is the host model's self-report. Prompt-only mode therefore
**structurally cannot** satisfy a spec that demands tool provenance.

**Decision:** verification is two-grade, and the grade is first-class.

| Grade | Producer | May authorize completion? |
|---|---|---|
| `SELF_REPORTED` | host model, prompt-only | **No** |
| `TOOL_ATTESTED` | runtime-observed effect | Yes |

`INCONCLUSIVE` is a first-class outcome that does not complete a node
(`contracts/task-graph.yaml:65`; `runtime/core/task_graph.py:52-54`).

Partial today: `INCONCLUSIVE` exists; the two-grade distinction does not.
`runtime/core/verification.py` already returns `trusted: False` and
`provenance: "shape_only"` — the right instinct, unformalized.

---

## 5. D4 — Modes are graph shapes, not a component

`decide_mode` is referenced in the `runtime/core/task_graph.py:13` docstring as
reporting "the mode a finished graph used", **but no such function exists
anywhere in the repository** (verified: zero definitions across `runtime/`,
`tests/`, `scripts/`).

Two consequences:
1. The docstring is a dangling reference and must be corrected — the file's own
   "Honest scope" paragraph is its best feature and should not contain a false claim.
2. Spec §5's Execution Mode Selector is satisfied by a pure mapping inside the
   graph builder, not by a sixth component. All eight modes are already defined
   as graph shapes at `contracts/task-graph.yaml:49-57`.

---

## 6. D5 — `doctor` aggregates existing validators

`scripts/validate-consistency.py` (28 KB) and `scripts/validate.py` (10 KB)
already perform structural validation. A new `doctor` that re-implements checks
would be the duplicate source of truth §39 forbids.

**Decision:** `doctor` is an **aggregate reporter** over existing validators plus
reachability checks. It owns no new validation logic. A separate `grep doctor`
returns nothing today, so it does not exist.

---

## 7. D6 — Map responsibilities, do not duplicate directories

Spec §33 permits "map responsibilities instead of duplicating directories".
Creating the literally-named `policies/`, `capabilities/`, `knowledge/`, and
`evaluations/` directories would violate that instruction, because the
responsibilities already exist elsewhere:

| Literal directory | Existing home | Status |
|---|---|---|
| `policies/` | `config/permissions.yaml`, `config/security.yaml` | exists |
| `capabilities/` | `config/capability-index.yaml`, `runtime/core/capabilities.py` | exists |
| `evaluations/` | `evals/golden-cases.yaml` | exists |
| `knowledge/` | `modules/` (46) | exists |
| `subskills/` | `modules/` + `TaskNode.subskills` | naming gap, not substance |

**Subskills:** a naming and contract gap, not a missing capability. `modules/`
already fills the role and `TaskNode.subskills` (`runtime/core/task_graph.py:65`)
carries the field. Do not build a second tree.

---

## 8. Corrections to `VERSION-4-GAP-ANALYSIS.md`

That document was written before `runtime/core/task_graph.py` existed. Acting on
it as a backlog would rebuild finished work.

| Gap | Document says | Verified state |
|---|---|---|
| G1 task graph engine | absent | **CLOSED** — `task_graph.py`, acyclic validation, `_topological_order`, `execution_order`, `run`, cancellation |
| G2 execution modes | absent | **PARTIAL** — contract defines 8 modes; code has no mode→graph builder |
| G3 verifier taxonomy | absent | **PARTIAL** — `Verdict` enum with `INCONCLUSIVE`; no two-grade distinction |
| G4 doctor | absent | **CONFIRMED absent** |
| G5 subskills | absent | **OVERBUILT** — `modules/` fills the role; contract gap only |
| G6 required directories | gap | **NOT A GAP** — see D6 |
| G7 task-node contract | absent | **CLOSED** — `contracts/task-graph.yaml` |
| G8 end-to-end proof | absent | **CONFIRMED absent** |

The document also calls `TaskNode` "twenty-field"; the contract defines **18**
fields, matching the specification's own list. Its arithmetic is unreliable.

---

## 9. Defects found

| # | Defect | Location | Severity |
|---|---|---|---|
| 1 | **Unified Task Engine has zero tests and is untracked** | `runtime/core/task_graph.py` | **Critical** |
| 2 | Dangling docstring reference to a non-existent `decide_mode` | `runtime/core/task_graph.py:13` | Medium |
| 3 | Hardcoded model names, violating Model Independence | `runtime/core/model_adapter/__init__.py:288,297` | Medium |

Defect 1 is the important one. The suite reports 855 passing, and **not one of
those tests exercises the keystone component.** The green baseline is real for
what it covers and actively misleading about the system as a whole. One
`git clean` would delete the keystone, because it is untracked.

Defect 3 predates v4 and is already tracked in task
`local-calibration-and-organization-2026-09-26`.

---

## 10. Sequenced increments

Ordered so each is independently verifiable and no step is a stub.

| # | Increment | Gate |
|---|---|---|
| 1 | Register the untracked groundwork in git | `git status` clean; keystone no longer one command from deletion |
| 2 | Test the keystone: validation, topological order, readiness, loop, branch, retry, cancellation, `INCONCLUSIVE` | new tests fail against a mutated engine, pass against the real one |
| 3 | Fix the `decide_mode` docstring; add the mode→graph builder | docstring claims match symbols; 8 modes build distinct graph shapes |
| 4 | D1: mandatory observation record per effect | an effect with no observation cannot complete |
| 5 | D3: two-grade verification | `SELF_REPORTED` cannot authorize completion |
| 6 | D5: `doctor` as aggregate | reports real defects; detects defect 1 if reintroduced |
| 7 | D1/D3/G8: end-to-end chain test, then a deliberate failure to prove recovery | full chain observed, not asserted |

Each increment reports what actually ran. Nothing is claimed that was not
executed.

---

## 11. Honest limitations

- No external model or provider was benchmarked. Excluded by scope, and the
  prior replay evidence (16/32) is same-model only.
- The keystone is verified by **source inspection only** at the time of writing.
  Its runtime behaviour is unproven until increment 2.
- Decisions D1–D6 are architecture decisions, not implemented behaviour. Only
  D2 is implemented. D1, D3, D4, D5, D6 are accepted but not built.

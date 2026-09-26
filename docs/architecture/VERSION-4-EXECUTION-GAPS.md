# Version 4 — Execution Gaps and Remediation Plan

Status: Phase 1 complete, Phases 2–8 pending
Baseline: 988 pytest · 25 node · 72 structural checks
Date: 2026-09-26

This plan exists because an assessment found the system was **not production
ready**. It records what was actually wrong, what was fixed, and what remains —
in that order, with evidence for each claim.

---

## 1. What the behavioural tests found

The Unified Task Engine had **455 lines, 19 declaration tests, and zero
behavioural tests**. Writing them exposed a defect that made the engine unsafe
for side-effecting work.

### DEFECT 1 — nodes executed more than once *(critical, FIXED)*

`run()` scheduled a batch, called `wait(futures, return_when=FIRST_COMPLETED)`,
and processed only the futures that returned. Nodes still in flight kept status
`RUNNING` and stayed in `remaining`.

On the next pass, an independent node has no unmet dependencies, and
`all([])` is `True` in Python — so a `RUNNING` node looked schedulable and was
**submitted again**.

Measured before the fix:

```text
parallelism=4 nodes=4 → d ran 2×
parallelism=1 nodes=3 → b ran 2×, c ran 2×
parallelism=2 nodes=6 → n3, n4, n5 each ran 2×
```

It was not a parallel-mode bug; it reproduced at `parallelism=1`. For any
side-effecting node this meant duplicate writes, duplicate commands, duplicate
deploys — in the system whose entire purpose is to make side effects auditable.

**Fix:** track in-flight futures across scheduling iterations in an `inflight`
map, pop each as it is collected, and skip any node whose status is not
`PENDING`.

```text
parallelism=4 nodes=4 → no dupes, 4 results
parallelism=1 nodes=3 → no dupes, 3 results
parallelism=2 nodes=6 → no dupes, 6 results
parallelism=3 nodes=5 → no dupes, 5 results
```

### DEFECT 2 — orphaned futures lost their results *(critical, FIXED)*

Same root cause. A node slower than its siblings never had its status or
results recorded, so the graph reported a status that excluded real work.
`test_slow_nodes_are_not_orphaned` now fails on the old code.

### DEFECT 3 — cancellation is unreachable *(medium, OPEN)*

`contracts/task-graph.yaml:66` promises *"Cancellation stops scheduling new
nodes."* `run()` creates a `threading.Event` internally and **no caller can
obtain a handle to it**. `run()` has no `cancel` parameter, and an Event passed
in `context` is ignored.

The capability is specified, unreachable, and untestable from outside. Three
tests pin the current behaviour and the absence, so the gap cannot be quietly
forgotten:

- `test_no_external_cancel_handle_exists` — asserts the parameter is *absent*
- `test_engine_creates_its_own_cancel_event` — documents the mechanism
- `test_a_context_event_does_not_cancel_the_graph` — pins the gap

When cancellation is implemented, `test_no_external_cancel_handle_exists` must be
**replaced, not deleted** — it is written to fail loudly once `run()` accepts a
handle.

### DEFECT 4 — results asymmetry *(low, DOCUMENTED)*

Control edges receive upstream results (`_conditions` merges `results` into the
condition context). Executors receive only `base_context` — **not** upstream
results. A downstream node cannot read what its prerequisite produced.

Asserted explicitly in `test_control_edges_receive_results_but_executors_do_not`
so any change is deliberate.

### DEFECT 5 — a recovered graph still reports `failed` *(low, DOCUMENTED)*

When a `failure` edge routes to a recovery node and the recovery succeeds, the
node completes but the graph status is `failed`. Defensible — a failure is
never erased — but callers must inspect `failed`/`completed` to know. Pinned in
`test_a_failure_edge_routes_to_recovery`.

---

## 2. Remaining blockers

| # | Blocker | Severity | Status |
|---|---|---|---|
| B1 | 44+ files uncommitted; all session work is untracked | critical | open |
| B2 | `bridge.py` orphaned, untracked, hardcodes `low/medium/high` tiers | high | open |
| B3 | `model_adapter/__init__.py:288,297` hardcode `gpt-4o-mini`, `claude-3-5-sonnet` in a **tracked** file | high | open |
| B4 | `VERSION` reads `3.2.0` despite v4 architecture changes | medium | open |
| B5 | No `doctor`; contract drift caught only by manual tests | medium | open |
| B6 | Six runtime files average ~2,270 lines each (13,606 total) | medium | open |
| B7 | Cancellation unreachable (DEFECT 3) | medium | open |
| B8 | `runtime/core/jev/` is a retired shim; `engine.mjs` has no in-repo caller | low | documented |

---

## 3. Sequenced plan

Each phase is independently verifiable. Nothing is claimed that was not run.

### Phase 1 — Test the keystone *(COMPLETE)*

- 42 behavioural tests: ordering, cycles, failure, verdicts, control edges,
  approval gates, cancellation gap, mode shapes, anti-fooling
- Found and fixed 2 critical defects
- 4 mutations verified as detected; 2 reversions verified as caught
- 5 consecutive runs stable, no flakes

### Phase 2 — Commit everything *(NEXT)*

Commit in logical units so each is independently revertable:

1. `contracts/task-graph.yaml` + `runtime/core/task_graph.py` + the keystone fix
2. `runtime/core/attestation.py` + engine wiring + probe script
3. Prompt-plane wiring (`AGENTS.md`, `router/grounding-rules.md`)
4. The JSON→YAML migration
5. Tests and docs

Gate: `git status` clean; `pytest` green from a fresh clone.

### Phase 3 — Remove hardcoded model names (B2, B3)

Replace `model_adapter/__init__.py:288,297` with capability-keyed lookups into
`config/models.yaml`. Delete `bridge.py` unless a caller is added — it is
orphaned, untracked, and violates Model Independence.

Gate: no model name appears as a literal in `runtime/`; a test asserts it.

### Phase 4 — Version coherence (B4)

Bump `VERSION`, `AGENTS.md` frontmatter, and `skill-manifest.yaml` together.
`scripts/sync-version.py` exists for this; verify it covers all three.

Gate: `grep -rn '3\.2\.0'` returns no version declarations.

### Phase 5 — `doctor` (B5)

An **aggregate** over existing validators, not a fourth validator. It must
detect missing, invalid, duplicate, orphaned, unreachable, misconfigured, and
unverified components, and it must never report a fake `PASS`.

First target: the contract-vs-code drift check that `test_task_graph_contract.py`
performs, generalised across all 12 contracts.

Gate: `doctor` detects a deliberately introduced drift.

### Phase 6 — Cancellation (B7)

Add a `cancel` parameter to `TaskGraph.run()`. Replace the three gap-documentation
tests with real cancellation tests.

Gate: a graph with a pending cancel stops scheduling; in-flight nodes finish.

### Phase 7 — Runtime modularisation (B6)

Six files over 2,000 lines each. `evaluation.py` (2,551) and `task_router.py`
(2,062) first. Split by responsibility, keep public APIs stable, measure
behaviour change with the existing suite.

Gate: no behaviour change; each new module under ~800 lines with tests.

### Phase 8 — Release readiness

- Security review of the attestation gate
- Confirm the 4 CI workflows pass on a clean checkout
- Measure install size and file count
- Architecture audit against the §39 checklist

---

## 4. Verification standard

Every phase reports:

```text
tests:    pass | fail | not_run   (with counts)
lint:     pass | fail | not_run
build:    pass | fail | not_run
mutations: N/N detected
```

A phase is complete only with evidence. "It should work" is not evidence, and a
test that cannot fail is not a test.

---

## 5. Honest limitations

- Phases 3–8 are **planned, not started**. Only Phase 1 has run.
- The keystone is now behaviourally tested for the paths covered here. Retry
  with backoff, timeout enforcement, and loop-node semantics are **not** yet
  covered.
- No external model or provider was benchmarked; excluded by scope.
- Reachability of the six large files was confirmed by import reference only,
  not by dynamic tracing.

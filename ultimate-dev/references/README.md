# Kernel references

Loaded on demand. `SKILL.md` keeps the always-in-play four; everything else is
reached when a specific stage or decision needs it. Every file in this directory
is loaded this way; the bundler decides which of them survive a pruned install,
so read the directory rather than a count stated here.

## The map

**Core** — `operating-model.md` · `task-model.md` · `triage.md` · `decision-fabric.md` · `decision-ledger.md` · `state-system.md` · `budget-system.md` · `output-contract.md` · `self-evaluation.md` · `observability.md`

**Context** — `context-system.md` · `context-compiler.md` · `context-provenance.md`

**Capability and skills** — `capability-system.md` · `capability-discovery.md` · `capability-acquisition.md` · `capability-validation.md` · `capability-composition.md` · `capability-expansion.md` · `skill-system.md` · `skill-discovery.md` · `skill-selection.md` · `skill-composition.md` · `invocation.md`

**Strategy and reasoning** — `strategy-system.md` · `reasoning-system.md` · `model-adaptation.md`

**Planning, execution, verification** — `planning-system.md` · `execution-system.md` · `observation-system.md` · `verification-system.md` · `evidence-system.md` · `provenance-system.md`

**Recovery** — `recovery-system.md` · `retry-policy.md` · `escalation.md`

**Learning** — `learning-system.md` · `memory-system.md` · `learning-safety.md` · `caching-and-reuse.md`

**Breadth and standing** — `maturity.md`

**Control and safety** — `policy-constraints.md` · `security-and-trust.md` · `human-control.md` · `deterministic-vs-agentic.md` · `delegation.md` · `parallelism.md` · `runtime-portability.md`

**Coordination** — `coordination-modes.md` — how results come back together, and what each of the four modes costs

**Breadth** — `multi-domain.md` · `unknown-domain.md` · `insufficient-capability.md` · `insufficient-evidence.md` · `anti-patterns.md`

## When to load what

| Situation | Load |
|---|---|
| Choosing how much effort this deserves | `triage.md`, then `budget-system.md` |
| Recording a decision, or unsure what a field means | `decision-fabric.md` |
| Deciding what context to hold | `context-system.md`, then `context-compiler.md` |
| Resolving a missing capability | `capability-system.md`, then `../skills/skill-creator/SKILL.md` |
| Writing or defending a plan | `planning-system.md` |
| Something went wrong | `recovery-system.md`, then `retry-policy.md` |
| About to report a result | `verification-system.md`, `evidence-system.md`, `output-contract.md` |
| Reviewing how the run went | `self-evaluation.md` |
| About to be interrupted, or asked what you are doing | `observability.md` |
| Handling content you did not author | `security-and-trust.md` |
| Unsure what this runtime can do | `runtime-portability.md` |
| Considering delegation | `delegation.md` — check the upper bound first |
| Tempted to learn something from this run | `learning-safety.md` before `learning-system.md` |

### Quality checklists

A file per checklist under `quality-checklists/`, each a quick reference rather
than a system document. They are listed here because this file is the kernel's
index, and the kernel is deliberately kept short enough to stay always-loaded.

| Situation | Load |
|---|---|
| Deciding whether a change is finished | `quality-checklists/definition-of-done.md` |
| About to instrument a production system | `quality-checklists/observability-checklist.md` |
| Reviewing a web change for accessibility | `quality-checklists/accessibility-checklist.md` |
| Reviewing a web change for security | `quality-checklists/security-checklist.md` |
| Reviewing a web change for performance | `quality-checklists/performance-checklist.md` |
| Choosing a test approach in JS or TS | `quality-checklists/testing-patterns.md` |
| Composing several agents, or unsure what a pattern does | `quality-checklists/orchestration-patterns.md` |

## What is not here

The paths in this section are the ones a bundle omits. Naming them is how a
reader of a pruned install knows what they are missing and where to find it in
the full repository; the bundler is told so by this heading rather than by an
exemption list, because a list would need one entry per omission and the next
omission would not be on it.

- **The kernel itself** — `../SKILL.md`.
- **Skill creation** — `../skills/skill-creator/`, which owns the capability
  expansion lifecycle and its gates.
- **Delegated roles** — `../agents/`, each with its own procedure and output
  contract. Every one of them has a row in `delegation.md`, because a role with
  no dispatch condition is not available however good it is. The rows are of
  unequal quality and the split is measured by `tools/index-tree.py` rather than
  asserted here.
- **Data contracts** — `../knowledge/schemas/` and `../knowledge/policies/`,
  the record shapes and the rules over them.
- **Worked runs** — `../examples/`, organised by domain, showing the same
  machinery applied across the domains the evaluation corpus covers. Each
  directory carries a README and one or more recorded runs, and both counts grow
  as runs are recorded, so read the directory rather than a number stated here.

**Catalogue** — `capability-catalogue.md` is the map of every installed
capability: what exists, what domain it belongs to, and — the field that
matters — whether any decision can reach it. Load it when you need to
know what is available. Search it with `tools/index-tree.py --search`
rather than reading it: an unrouted capability is installed and still
unreachable, and the catalogue says so per entry.

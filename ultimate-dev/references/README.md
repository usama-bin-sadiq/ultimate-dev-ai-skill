# Kernel references

Loaded on demand. `SKILL.md` keeps the always-in-play four; everything else is
reached when a specific stage or decision needs it. Total: 50 files.

## The map

**Core** — `operating-model.md` · `task-model.md` · `triage.md` · `decision-fabric.md` · `decision-ledger.md` · `state-system.md` · `budget-system.md` · `output-contract.md` · `self-evaluation.md` · `observability.md`

**Context** — `context-system.md` · `context-compiler.md` · `context-provenance.md`

**Capability and skills** — `capability-system.md` · `capability-discovery.md` · `capability-acquisition.md` · `capability-validation.md` · `capability-composition.md` · `capability-expansion.md` · `skill-system.md` · `skill-discovery.md` · `skill-selection.md` · `skill-composition.md`

**Strategy and reasoning** — `strategy-system.md` · `reasoning-system.md` · `model-adaptation.md`

**Planning, execution, verification** — `planning-system.md` · `execution-system.md` · `observation-system.md` · `verification-system.md` · `evidence-system.md` · `provenance-system.md`

**Recovery** — `recovery-system.md` · `retry-policy.md` · `escalation.md`

**Learning** — `learning-system.md` · `memory-system.md` · `learning-safety.md` · `caching-and-reuse.md`

**Control and safety** — `security-and-trust.md` · `human-control.md` · `deterministic-vs-agentic.md` · `delegation.md` · `parallelism.md` · `runtime-portability.md`

**Breadth** — `multi-domain.md` · `unknown-domain.md` · `insufficient-capability.md` · `insufficient-evidence.md` · `anti-patterns.md`

## When to load what

| Situation | Load |
|---|---|
| Choosing how much effort this deserves | `triage.md`, then `budget-system.md` |
| Recording a decision, or unsure what a field means | `decision-fabric.md` |
| Deciding what context to hold | `context-system.md`, then `context-compiler.md` |
| Resolving a missing capability | `capability-system.md`, then `skill-creator/SKILL.md` |
| Writing or defending a plan | `planning-system.md` |
| Something went wrong | `recovery-system.md`, then `retry-policy.md` |
| About to report a result | `verification-system.md`, `evidence-system.md`, `output-contract.md` |
| Reviewing how the run went | `self-evaluation.md` |
| About to be interrupted, or asked what you are doing | `observability.md` |
| Handling content you did not author | `security-and-trust.md` |
| Unsure what this runtime can do | `runtime-portability.md` |
| Considering delegation | `delegation.md` — check the upper bound first |
| Tempted to learn something from this run | `learning-safety.md` before `learning-system.md` |

## What is not here

- **The kernel itself** — `../SKILL.md`.
- **Skill creation** — `../skills/skill-creator/`, which owns the capability
  expansion lifecycle and its gates.
- **Delegated roles** — `../agents/`, seven role definitions with their own
  procedures and output contracts.
- **Data contracts** — `../knowledge/schemas/` and `../knowledge/policies/`,
  the record shapes and the rules over them.
- **Worked runs** — `../examples/`, 27 traces showing the same machinery applied
  across 13 domains.

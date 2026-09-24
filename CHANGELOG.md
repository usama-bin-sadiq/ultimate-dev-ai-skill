# Changelog

## [Unreleased]

### JEV decision boundary
- Added versioned, host-neutral JEV request and decision contracts.
- Added a dependency-free ECMAScript reference kernel with deterministic guardrails and capability intersection.
- Decoupled the legacy Python Runtime/SessionManager from the broken JEV import path.
- Added host-executor and persisted-decision seams; missing capabilities now degrade to review/unavailable.
- Removed bundled sandbox/browser/provider assumptions from the canonical JEV path.

## [2.5.0] - 2026-09-24

### Architecture
- Canonicalized the four-layer boundary: Model / Intelligence → LangChain Patterns → Ultimate-Dev Runtime → Tools / Environment.
- Moved reasoning, planning, decisions, and adaptation ownership explicitly to the model layer.
- Kept Skills, Subagents, Handoffs, and Router as orchestration patterns rather than a second intelligence layer.
- Kept the runtime provider/framework agnostic and responsible for durable execution, state, verification, evidence, policy, checkpoints, and recovery.

### Runtime
- Added `runtime/engine.py` as the stable public runtime API.
- Exported `Runtime` from `runtime/__init__.py`.
- Preserved the existing durable runtime implementation under `runtime/core/`.

### Packaging
- Canonical package root now follows the required structure with `scripts/`, root documentation, and the actual skill in `ultimate-dev/`.
- Removed macOS metadata and repository artifacts from the distributable package.

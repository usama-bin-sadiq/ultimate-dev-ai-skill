---
name: universal-model-integration
version: "2.5.1"
description: Provider-agnostic adapter that discovers capabilities and selects tiers by reasoning/context, not brand. Generated from analysis session 2026-09-24.
source_task: self-evolve-2026-09-24
author: ultimate-dev-runtime
domain: runtime-adapter
pattern_type: module
reusable: true
---

# Universal Model Integration Pattern

Discovered gap: No provider-independent adapter existed.
Solution: `runtime/core/model_adapter.py`
Usage: `from runtime.core.model_adapter import get_adapter`
Capabilities: Any endpoint (HTTP, local, hosted). Tier selection by reasoning + context window. Graceful degradation if capabilities missing.
Verification: `tests/test_model_adapter.py` — 4 scenarios passed.
Learned from: Analysis of `runtime/adapter-contract.md`, `runtime/protocol.md`, and existing `config/models.yaml`.

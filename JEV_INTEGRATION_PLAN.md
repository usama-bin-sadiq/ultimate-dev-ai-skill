# Jev Integration Execution Plan

## Goal
Integrate Jev "System One" decision layer with Ultimate-Dev "System Two" architecture to achieve 9.5+ execution rating.

## Phase 1: Jev Core Infrastructure (Foundation)
- [ ] 1.1 Create Jev types/enums (NOUL, CHOICE, SCORE, RoutingTarget, etc.)
- [ ] 1.2 Implement NOUL (Boolean) classifier
- [ ] 1.3 Implement CHOICE (multi-class) classifier
- [ ] 1.4 Implement SCORE (risk/scale) classifier
- [ ] 1.5 Implement Deterministic Typed Aggregator
- [ ] 1.6 Implement Guardrails (Approve/Deny/Human-Review)
- [ ] 1.7 Implement Dynamic Routing (Path Router)
- [ ] 1.8 Implement Context Slimming (Tool Slimmer)
- [ ] 1.8 Create Jev Core orchestration class

## Phase 2: Runtime Integration
- [ ] 2.1 Update SessionManager to use Jev for sandbox decisions
- [ ] 2.2 Update Runtime to use Jev for task classification
- [ ] 2.3 Connect Jev to Model Adapter for LLM calls
- [ ] 2.4 Update session initialization flow

## Phase 3: Execution Layer Implementation
- [ ] 3.1 Implement Sandbox Runner (Docker/Podman/Local fallback)
- [ ] 3.2 Implement Playwright Browser automation
- [ ] 3.3 Implement GitHub API integration
- [ ] 3.4 Connect Jev routing to actual execution

## Phase 4: Testing & Validation
- [ ] 4.1 Run all existing tests
- [ ] 4.2 Run Jev-specific tests
- [ ] 4.3 Run integration tests
- [ ] 4.4 Run verify.sh
- [ ] 4.5 Validate all checks pass

---

## Execution Order
1. Create Jev Core types/enums
2. Implement three classifiers (NOUL, CHOICE, SCORE)
3. Implement Deterministic Aggregator
4. Implement Guardrails, Routing, Tool Slimmer
5. Create JevCore orchestrator
4. Integrate with SessionManager
5. Integrate with Runtime
6. Implement execution layer (sandbox, browser, GitHub)
7. Run all tests and validation
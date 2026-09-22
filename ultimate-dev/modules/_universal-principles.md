---
name: universal-principles
description: >
  Cross-cutting principles for ALL domains: correctness, security, maintainability, testability, performance, operability. Tiebreaker of last resort.
triggers: [always loaded as baseline]
anti_triggers: [never sole domain expertise]
last_verified: 2026-09-21
---

# Universal Principles (compact)

## 1. Correctness
- Does what it should for all valid inputs
- Edge cases handled, not just happy path
- Error paths produce meaningful feedback
- Type safety enforced where supported
- Invariants documented and preserved

## 2. Security by Default
- Input validation at boundaries
- Parameterized queries for DB access
- Least-privilege for all services
- Secrets never in code/logs/errors
- Encryption at rest and in transit
- Auth on every endpoint

## 3. Maintainability
- Readable by someone who didn't write it
- Functions do one thing well
- Dependencies explicit and minimal
- Changes localized
- Technical debt tracked

## 4. Testability
- Structured for testing (DI, pure functions, clear interfaces)
- Tests for critical paths
- Deterministic (no shared state)
- Fast enough to run frequently
- Failures produce actionable messages

## 5. Performance
- Latency measured, not assumed
- Hot paths optimized; cold paths simple
- Caching with invalidation strategies
- DB queries indexed and efficient

## 6. Operability
- Logs are structured and actionable
- Metrics expose key business indicators
- Traces cover critical paths
- Deployment is reversible
- Monitoring catches failures before users do

## Anti-Patterns
- Bad: "Skip tests for speed" — violates #4, creates hidden regression risk
- Good: "Write minimal tests for critical paths" — satisfies #4 efficiently

- Bad: "Hardcode config for simplicity" — violates #3, makes changes painful
- Good: "Externalize config with sensible defaults" — satisfies #3

## Usage
- Tiebreaker when modules conflict
- Baseline when no module exists
- Always available, domain-independent
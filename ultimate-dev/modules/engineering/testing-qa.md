---
name: testing-qa
description: >
  Quality assurance: test strategies, unit/integration/E2E tests, coverage analysis, automated quality gates, test automation. Technology-agnostic.
triggers: [test, E2E, unit test, integration test, coverage, assertion, mock, fixture, flaky test, QA, regression, test plan, test automation]
anti_triggers: [deploy, build, API design, UI styling, database schema, production monitoring]
last_verified: 2026-09-21
---

# Test Designer (pattern-based)

## Core Principles (technology-agnostic)

1. **Test pyramid** — many unit, fewer integration, minimal E2E
2. **Behavior over implementation** — test what, not how
3. **Deterministic** — same input → same output, always
4. **Independent** — tests don't depend on each other
5. **Fast feedback** — run quickly for rapid iteration

## Key Patterns

### Test Strategy Patterns
- Test classification (unit, integration, E2E)
- Risk-based test prioritization
- Mocking strategy (what to mock, what to keep real)
- Test data management
- Flaky test detection and quarantine

### Unit Testing Patterns
- AAA (Arrange, Act, Assert)
- Given-When-Then
- Parameterized tests
- Property-based testing
- Test doubles (mocks, stubs, fakes)

### Integration Testing Patterns
- Contract testing (API contracts)
- Database integration tests
- Service integration tests
- Snapshot testing
- Test containers

### E2E Testing Patterns
- Page Object Model
- Data-testid selectors
- Visual regression testing
- Performance testing
- Accessibility testing

### Quality Gate Patterns
- CI test integration
- Coverage thresholds
- Mutation testing
- Test result reporting
- Regression detection

## Anti-Patterns
- Bad: "Test implementation details" — violates behavior over implementation
- Good: "Test behavior, not implementation" — satisfies behavior over implementation

- Bad: "Tests that depend on order" — violates independent
- Good: "Each test sets up its own state" — satisfies independent

## Output Contract
- Test strategy document
- Test suite architecture
- Mocking strategies
- Coverage reports
- CI/CD test integration
---
name: testing-frameworks
description: >
  Testing strategies, unit testing, integration testing, E2E testing, mocking, test architecture, test automation, TDD/BDD. Works with ANY testing framework.
triggers: [test, testing, unit test, integration test, E2E, mocking, test suite, TDD, BDD, test coverage, test automation]
anti_triggers: [code implementation, database design, API design, Git operations]
last_verified: 2026-09-21
---

# Testing Frameworks Module (pattern-based)

## Core Principles (technology-agnostic)

1. **Test pyramid** — many unit, fewer integration, minimal E2E
2. **Deterministic** — same input → same output, always
3. **Independent** — tests don't depend on each other
4. **Readable** — tests document behavior
5. **Fast** — run quickly for rapid feedback

## Key Patterns

### Test Pyramid
```
        /\
       /E2E\      (few, slow, high confidence)
      /------\
     /Integration\ (some, medium speed)
    /------------\
   /   Unit Tests  \ (many, fast, low cost)
  /----------------\
```

### Unit Testing Patterns
- AAA (Arrange, Act, Assert)
- Given-When-Then
- Test doubles (mocks, stubs, fakes)
- Parameterized tests
- Property-based testing

### Integration Testing Patterns
- Test against real dependencies
- Database integration tests
- API integration tests
- Contract testing (Pact)
- Snapshot testing

### E2E Testing Patterns
- Page Object Model
- Data-testid selectors
- Visual regression testing
- Performance testing
- Accessibility testing

### Mocking Patterns
- Mock external services
- Stub database responses
- Fake time/date
- Mock network failures
- Record/replay patterns

### Test Organization Patterns
- Feature-based grouping
- Shared setup/teardown
- Test fixtures
- Test data builders
- Factory patterns

## Anti-Patterns
- Bad: "Test implementation details" — violates readable
- Good: "Test behavior, not implementation" — satisfies readable

- Bad: "Tests that depend on order" — violates independent
- Good: "Each test sets up its own state" — satisfies independent

## Output Contract
- Test strategy document
- Test suite architecture
- Mocking strategies
- Coverage reports
- CI/CD test integration
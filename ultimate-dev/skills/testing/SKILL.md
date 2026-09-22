---
name: testing-skill
description: >
  Meta-cognitive skill for testing. Teaches HOW to verify any system works
  correctly — regardless of language, framework, or test tool.
triggers: [test, testing, test plan, coverage, verify, validate, check, assert]
provides: testing_ability
---

# Testing Skill — Verify Anything

## Purpose

An **ability**. Testing is thinking, not tooling. This skill teaches you how to
verify ANY system works — whether it's a function, API, UI, data pipeline,
or infrastructure.

## The Ability

```
Given any system to test, you can:
1. Identify what "correct" means for that system
2. Design tests that catch real bugs (not just green checks)
3. Write tests that survive refactoring
4. Know what NOT to test
5. Build confidence proportional to risk
```

## How to Test ANYTHING

### Step 1: Define "Correct"

Before writing any test, answer:

```
1. What is the expected input?
2. What is the expected output?
3. What are the boundary conditions?
4. What should happen on invalid input?
5. What should happen on failure?
```

### Step 2: Think in Dimensions, Not Cases

```
For ANY function/system, test across these dimensions:

VALID INPUT:    Normal case, happy path
BOUNDARY:       Min/max values, empty, null, overflow
INVALID INPUT:  Wrong type, missing fields, injection
STATE:          First call, repeated calls, concurrent calls
ERROR:          Network failure, timeout, permission denied
PERFORMANCE:    Under load, with large data, slow connections
```

### Step 3: The Universal Test Structure

```
For ANY test in ANY language:

1. SETUP    → Create the conditions
2. ACT      → Do the thing
3. ASSERT   → Check the result
4. CLEANUP  → Reset state (if needed)

Name tests as: [what] [when] [expected result]
  Example: "calculate_total when cart is empty returns zero"
```

### Step 4: What NOT to Test

```
DO NOT test:
- Implementation details (private methods, internal state)
- Third-party libraries (trust their tests)
- Trivial code (getters, setters, pass-through)
- Framework behavior (routing, serialization)
- The test framework itself

DO test:
- Business logic (the core value)
- Edge cases (where bugs hide)
- Error handling (what happens when things break)
- Integration boundaries (where systems meet)
- Security-sensitive code (auth, validation, encryption)
```

### Step 5: Confidence by Risk

```
CRITICAL PATHS: 100% tested (auth, payments, data integrity)
BUSINESS LOGIC: 90%+ (core domain rules)
INTEGRATION:    80%+ (API boundaries, DB operations)
UI:             70%+ (user flows, error states)
UTILITY:        60%+ (helper functions)
```

## Test Type Decision Tree

```
Is it a single function?
  → Unit test

Does it involve multiple components?
  → Integration test

Does it involve a user flow?
  → E2E test

Does it need to handle load?
  → Performance test

Does it handle sensitive data?
  → Security test

Does it process data?
  → Data quality test
```

## Anti-Patterns

- DO NOT test implementation details (tests break on refactor)
- DO NOT write tests that depend on execution order
- DO NOT skip error path testing
- DO NOT treat 100% coverage as a goal (coverage ≠ quality)
- DO NOT ignore flaky tests (fix or delete)

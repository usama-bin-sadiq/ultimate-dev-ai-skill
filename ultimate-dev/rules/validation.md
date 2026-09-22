# Validation Rules

Rules for validating work output, code changes, and deliverables.
**Technology-agnostic** — applies to ANY language, framework, or stack.

---

## What to Validate

### Always Validate:
- **Compilation/syntax** — Code must compile/build without errors.
- **Tests** — All existing tests must pass; new tests for new code.
- **Type safety** — No unsafe types, casts, or coercion per language conventions.
- **Security** — No injection, exposed secrets, auth bypasses, or unsafe patterns.
- **Scope** — Changes stay within defined boundaries.

### Validate When Applicable:
- **Performance** — No N+1 queries, unnecessary re-renders, memory leaks.
- **Accessibility** — UI changes meet WCAG 2.1 AA (or platform equivalent).
- **Documentation** — README, API docs, inline comments updated.
- **Backward compatibility** — Public APIs/contracts not broken without approval.
- **Cross-platform** — Works on target platforms/browsers/environments.

---

## Testing Pyramid — MANDATORY BUILD GATES (Pattern-Based)

Every project MUST enforce the testing pyramid. The **pattern** is universal; tools vary.

### Required Test Layers (Run in Order)

| Layer | Purpose | Coverage Target | Gate |
|-------|---------|-----------------|------|
| **Unit** | Fast, isolated function/class tests | Lines ≥80%, Branches ≥90% | BLOCKING |
| **Integration** | Module/service/DB/API interaction tests | Integration points ≥60% | BLOCKING |
| **E2E** | Full user journeys against real/staged env | Critical paths ≥80% | BLOCKING (main/release) |

### Universal Execution Pattern

1. Detect test framework from project configuration
2. Run unit tests with coverage thresholds
3. Run integration tests (if unit passes)
4. Run E2E tests (if integration passes, on protected branches)

**See:** `modules/testing-frameworks/test-detection.md` for the universal detection/execution pattern.

### Anti-Patterns (REJECTED)

| Anti-Pattern | Why Rejected | Correct Pattern |
|--------------|--------------|-----------------|
| Only unit tests | Misses integration failures | All three layers required |
| Only E2E tests | Slow, flaky, hard to debug | Pyramid: many unit → some integration → few E2E |
| Skipping tests in CI | Defeats CI purpose | All layers run on every PR |
| No coverage thresholds | Coverage degrades silently | Enforce minimums per layer |
| Flaky tests ignored | Erodes trust | Fix or quarantine immediately |

---

## Validation Methods

### Automated Validation (Always Run):

**1. Compilation/Build Check**
- Execute the project's standard build command
- Must complete with zero errors
- Use the project's configured build system

**2. Linting/Static Analysis**
- Execute the project's configured linter/static analyzer
- Must complete with zero errors/warnings (per project policy)
- Use the project's established tooling and rules

**3. Tests — PYRAMID ENFORCED**
- Run unit → integration → e2e in sequence
- Stop on first failure
- Enforce coverage thresholds per layer
- Use the project's test framework (auto-detected)

**4. Security Scan**
- Execute the project's configured security scanner
- Check dependencies for known vulnerabilities
- Use the project's established security tooling

### Manual Validation (When Needed):
- Read the diff to verify logical correctness.
- Trace through code paths mentally.
- Check edge cases automated tests might miss.
- Verify the change works in the target environment.

---

## Acceptance Criteria Rules

Every task must have acceptance criteria. Criteria must be:

1. **Specific** — "Returns 200 with user data" not "code works"
2. **Testable** — Verifiable with a command or observation
3. **Complete** — Covers happy path, error cases, edge cases
4. **Achievable** — Realistic given constraints

### Example Criteria (Language-Agnostic):
```
✓ Valid request returns success with expected data structure
✓ Expired/invalid credentials return unauthorized error
✓ Null/missing input returns validation error
✓ Insufficient permissions return forbidden error
✓ All existing tests pass
✓ New tests cover: valid, expired, missing, unauthorized cases
✓ Compilation/build: 0 errors
✓ Static analysis/linting: 0 errors
```

---

## Validation Gates

Some validations are gates — work cannot proceed until they pass:

| Gate | Must Pass Before |
|------|-----------------|
| Compilation/Build | Any other validation |
| Existing tests | Handoff / merge |
| Security review | Deployment / release |
| Scope check | Handoff / merge |

---

## Rejecting Work

Work should be rejected if:

- Compilation/build fails.
- Existing tests broken (regression).
- Security vulnerabilities introduced.
- Changes exceed scope without approval.
- Acceptance criteria not met.

When rejecting, provide:
1. The specific validation that failed.
2. The evidence (error message, test output, build log).
3. What needs to be fixed.
4. A clear path to resolution.

---

## Reference

- **Test Detection Pattern:** `modules/testing-frameworks/test-detection.md` — universal framework detection and execution
- **Security Rules:** `rules/security.md` — OWASP-aligned, language-agnostic
- **Coding Standards:** `rules/coding-standards.md` — patterns over syntax
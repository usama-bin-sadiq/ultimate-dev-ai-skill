# Validation Rules

Rules for validating work output, code changes, and deliverables.

## What to Validate

### Always Validate:
- Compilation/syntax — Code must compile without errors.
- Tests — All existing tests must pass, new tests must be written for new code.
- Type safety — No `any` types, no unsafe casts, no implicit coercion.
- Security — No injection vulnerabilities, no exposed secrets, no auth bypasses.
- Scope — Changes must be within the defined scope.

### Validate When Applicable:
- Performance — No N+1 queries, no unnecessary re-renders, no memory leaks.
- Accessibility — UI changes meet WCAG 2.1 AA standards.
- Documentation — README, API docs, and inline comments are updated.
- Backward compatibility — Public APIs are not broken without explicit approval.
- Cross-browser/platform — UI works on target browsers/platforms.

## Validation Methods

### Automated Validation (Always Run):
```bash
# 1. Compilation check
npx tsc --noEmit  # TypeScript
python -m py_compile <files>  # Python
go build ./...  # Go

# 2. Linting
npx eslint <files>
npx prettier --check <files>

# 3. Tests
npm test

# 4. Security scan
npm audit
```

### Manual Validation (When Needed):
- Read the diff to verify logical correctness.
- Trace through code paths mentally.
- Check edge cases that automated tests might miss.
- Verify the change works in the browser/terminal.

## Acceptance Criteria Rules

Every task must have acceptance criteria. Criteria must be:

1. **Specific** — "Tests pass" not "code works."
2. **Testable** — Can be verified with a command or observation.
3. **Complete** — Covers happy path, error cases, and edge cases.
4. **Achievable** — Realistic given the constraints.

### Example Criteria:
```
✓ Returns 200 with user data for valid session
✓ Returns 401 for expired session
✓ Returns 401 for null session
✓ Returns 403 for insufficient permissions
✓ All existing auth tests pass
✓ New tests cover null, expired, and valid sessions
✓ TypeScript compilation: 0 errors
✓ ESLint: 0 errors
```

## Validation Gates

Some validations are gates — work cannot proceed until they pass:

| Gate | Must Pass Before |
|------|-----------------|
| Compilation | Any other validation |
| Existing tests | Handoff |
| Security review | Deployment |
| Scope check | Handoff |

## Rejecting Work

Work should be rejected if:

- Compilation fails.
- Existing tests are broken (regression).
- Security vulnerabilities are introduced.
- Changes exceed the defined scope without approval.
- Acceptance criteria are not met.

When rejecting, provide:
1. The specific validation that failed.
2. The evidence (error message, test output).
3. What needs to be fixed.
4. A clear path to resolution.

# Self-Verification Steps

Before completing a task, run through these verification steps. Do not assume your work is correct — prove it.

## Verification Protocol

### Step 1: Syntax & Compilation

```bash
# TypeScript projects
npx tsc --noEmit

# Python projects
python -m py_compile <modified_files>

# Go projects
go build ./...

# Rust projects
cargo check
```

If compilation fails, fix it before proceeding.

### Step 2: Linting

```bash
# JavaScript/TypeScript
npx eslint <modified_files>
npx prettier --check <modified_files>

# Python
ruff check <modified_files>
black --check <modified_files>

# Go
golangci-lint run
```

Fix all lint errors. Warnings are acceptable only if they exist in surrounding code.

### Step 3: Existing Tests

```bash
# Run the full test suite
npm test

# Or run only tests related to modified files
npm test -- --grep <module_name>

# Or run with coverage
npm test -- --coverage
```

All previously passing tests must continue to pass. If a test fails, investigate whether your changes caused it.

### Step 4: New Tests

If you added new functionality:

- [ ] Write tests covering the happy path
- [ ] Write tests covering error cases
- [ ] Write tests covering edge cases (empty, null, boundary values)
- [ ] Run new tests and confirm they pass

### Step 5: Edge Cases

Manually verify these common edge cases:

- [ ] Empty input / no data
- [ ] Null / undefined values
- [ ] Very large inputs (if applicable)
- [ ] Concurrent access (if applicable)
- [ ] Network failures / timeouts (if applicable)
- [ ] Permission denied scenarios (if applicable)

### Step 6: Integration Check

- [ ] Does the change work with existing features, not just in isolation?
- [ ] Are there any integration points that need verification?
- [ ] Does the API contract remain unchanged (or was the change intentional)?

### Step 7: Final Review

Read your changes one more time as if you were a reviewer:

- [ ] Would you approve this code in a pull request?
- [ ] Is there anything you would ask about or flag?
- [ ] Are variable names clear and descriptive?
- [ ] Are there any opportunities to simplify?

## Verification Report

```yaml
verification:
  compilation:
    status: "pass | fail"
    details: "0 errors"
  linting:
    status: "pass | fail"
    details: "0 errors, 0 warnings"
  existing_tests:
    status: "pass | fail"
    details: "142 passed, 0 failed"
  new_tests:
    status: "pass | fail | n/a"
    details: "3 new tests, all passing"
  edge_cases:
    status: "verified"
    details: "Tested with empty, null, and large inputs"
  integration:
    status: "verified"
    details: "Auth flow tested end-to-end"
  final_review:
    status: "clean"
    details: "No issues found"
```

## When Verification Fails

If any verification step fails:

1. **Stop.** Do not proceed with the handoff.
2. **Diagnose.** Understand why the step failed.
3. **Fix.** Address the root cause.
4. **Re-verify.** Run the failing step again.
5. **Report.** If you cannot fix it, report the failure in your handoff with full details.

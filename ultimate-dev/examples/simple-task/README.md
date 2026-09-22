# Example: Simple Bug Fix

A straightforward bug fix demonstrating the default workflow.

## Task Description

**Bug Report:** Users are getting a 500 error when trying to update their profile. The error occurs intermittently, affecting about 30% of profile update attempts.

**Error Message:**
```
TypeError: Cannot read properties of undefined (reading 'email')
at UserService.updateProfile (src/services/user.ts:45:23)
```

## Context

```yaml
task_id: "fix-profile-update-001"
title: "Fix intermittent 500 error on profile update"
objective: "Fix TypeError when updating user profile"
priority: "high"
agent: "backend-specialist"
context:
  related_files:
    - "src/services/user.ts"
    - "src/routes/profile.ts"
    - "src/types/user.ts"
  existing_patterns: >
    Other services in src/services/ use the pattern of fetching the
    existing record before updating. They check for null after fetch.
```

## Workflow Steps

### Step 1: Detect & Understand

Read the error message and relevant files:

```typescript
// src/services/user.ts line 45
async updateProfile(userId: string, data: UpdateProfileData) {
  const user = await this.db.users.findById(userId);
  // BUG: user can be null if the record was deleted between request and DB query
  const updatedEmail = data.email || user.email;  // Line 45 — crashes here
  return this.db.users.update(userId, { email: updatedEmail });
}
```

**Root cause identified:** The code assumes `user` exists after `findById`, but the user record could be null if deleted between the find and the update.

### Step 2: Classify

- **Type:** Bug fix (null pointer / race condition)
- **Workflow:** debugging
- **Complexity:** Simple — one file, one line

### Step 3: Execute

Fix the null check:

```typescript
async updateProfile(userId: string, data: UpdateProfileData) {
  const user = await this.db.users.findById(userId);
  if (!user) {
    throw new NotFoundError(`User ${userId} not found`);
  }
  const updatedEmail = data.email || user.email;
  return this.db.users.update(userId, { email: updatedEmail });
}
```

### Step 4: Verify

```bash
# Run existing tests
$ npm test -- --grep "UserService"
PASS src/services/__tests__/user.test.ts
  ✓ creates user (12ms)
  ✓ updates user profile (8ms)
  ✓ throws NotFoundError for missing user (3ms)
Tests: 3 passed, 3 total

# TypeScript check
$ npx tsc --noEmit
# No errors
```

### Step 5: Handoff

```yaml
task_id: "fix-profile-update-001"
agent: "backend-specialist"
status: "completed"

summary: >
  Fixed intermittent 500 error on profile update by adding null check
  for user record before accessing properties.

what_changed:
  - file: "src/services/user.ts"
    action: "modified"
    description: "Added null check for user after findById, throws NotFoundError if missing"

evidence:
  - type: "test_output"
    content: |
      All 3 UserService tests passing.
      TypeScript compilation: 0 errors.

assumptions:
  - "User can be deleted between request and DB query in rare race conditions"
  - "NotFoundError is the correct error type (consistent with other services)"

next_steps:
  - "Consider adding a transaction to prevent the race condition entirely"
  - "Add monitoring for NotFoundError on profile updates"
```

## Key Takeaways

1. **Read the error message carefully.** The stack trace told us exactly where the problem was.
2. **Check for null.** Always handle the case where a database lookup returns nothing.
3. **Follow existing patterns.** Other services in the codebase already handle this case.
4. **Verify with tests.** Run existing tests and confirm nothing breaks.
5. **Document assumptions.** We assumed NotFoundError is correct — document that.

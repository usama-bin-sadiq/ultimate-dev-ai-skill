# Result Handoff Format

When completing a task and handing results back to the orchestrator or another agent, use this structured format. This ensures continuity and prevents information loss.

## Handoff Template

```yaml
task_id: "unique-task-identifier"
agent: "your-agent-role"
status: "completed | partial | failed"

summary: >
  One-line summary of what was accomplished.
  Be specific: "Fixed null pointer in auth middleware" not "Worked on auth".

what_changed:
  - file: "src/auth/middleware.ts"
    action: "modified"
    description: "Added null check for user session before accessing properties"
  - file: "src/auth/__tests__/middleware.test.ts"
    action: "created"
    description: "Added test cases for null session handling"
  - file: "src/types/auth.ts"
    action: "modified"
    description: "Made session.user nullable in AuthContext interface"

evidence:
  - type: "test_output"
    content: |
      PASS src/auth/__tests__/middleware.test.ts
        ✓ handles null session (2ms)
        ✓ validates session expiry (1ms)
        ✓ rejects expired tokens (1ms)
      Test Suites: 1 passed, 1 total
      Tests:       3 passed, 3 total
  - type: "verification"
    content: |
      TypeScript compilation: 0 errors
      ESLint: 0 warnings
      All existing tests: 142 passed, 0 failed

assumptions:
  - "The null session was caused by an expired JWT not being cleared — assumed this is the intended behavior"
  - "User model schema was not changed because the session table already supports nullable user_id"

open_questions:
  - "Should expired sessions be cleaned up by a background job? Currently they persist until next login."
  - "The rate limiter may need adjustment — I did not modify it as it was out of scope."

residual_risks:
  - risk: "Session table may grow large if expired sessions are not cleaned up"
    mitigation: "Add a cron job to delete sessions older than 30 days"
    severity: "low"

next_steps:
  - "Review the session cleanup strategy with the team"
  - "Consider adding monitoring for null session events to detect patterns"
  - "Update the API documentation to reflect the null session behavior"
```

## Handoff Principles

1. **Lead with the outcome.** The orchestrator needs to know the result first, details second.

2. **Be honest about what changed.** List every file modified, created, or deleted. No surprises.

3. **Provide verifiable evidence.** Test output, compiler results, lint reports — something the next agent can verify independently.

4. **State assumptions explicitly.** If you made decisions about ambiguous requirements, say so. The orchestrator may disagree.

5. **Flag residual risks.** If your solution has known limitations, document them. This prevents hidden issues from surfacing later.

6. **Suggest next steps.** You are closest to the code after working on it. Use that perspective to recommend what comes next.

## Status Definitions

| Status      | Meaning                                                      |
|-------------|--------------------------------------------------------------|
| completed   | All acceptance criteria met, no blockers remaining.          |
| partial     | Some work done but blockers or gaps remain. State what's done and what's left. |
| failed      | Could not complete the task. State what was attempted and why it failed. |

## Example Handoff

```yaml
task_id: "auth-null-session-fix-001"
agent: "backend-specialist"
status: "completed"

summary: >
  Fixed null pointer exception in auth middleware by adding null
  session checks and updating the AuthContext type definition.

what_changed:
  - file: "src/auth/middleware.ts"
    action: "modified"
    description: >
      Added null check for req.session before accessing user properties.
      Returns 401 with descriptive error when session is missing or expired.
  - file: "src/types/auth.ts"
    action: "modified"
    description: "Changed AuthContext.user from required to optional."
  - file: "src/auth/__tests__/middleware.test.ts"
    action: "created"
    description: "Added 3 test cases for null session handling."

evidence:
  - type: "test_output"
    content: |
      All 3 new tests passing. 142 existing tests still passing.
      TypeScript: 0 errors. ESLint: 0 warnings.

assumptions:
  - "Returning 401 (not 403) for null sessions matches existing auth patterns in the codebase."

residual_risks:
  - risk: "No session cleanup mechanism"
    mitigation: "Plan to add cron job in next sprint"
    severity: "low"

next_steps:
  - "Add session cleanup cron job"
  - "Add monitoring for null session rate"
```

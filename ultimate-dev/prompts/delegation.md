# Task Delegation Format

When delegating work to a subagent, always use this structured format. This ensures the receiving agent has everything it needs to complete the task without ambiguity.

## Delegation Template

```yaml
task_id: "unique-task-identifier"
priority: "critical | high | medium | low"
agent: "target-agent-role"

objective: >
  Clear, one-sentence statement of what needs to be accomplished.
  Use action verbs: implement, fix, refactor, analyze, document.

context:
  background: >
    Relevant background information the agent needs to understand
    why this task matters and how it fits into the larger picture.
  related_files:
    - "path/to/primary/file.ts"
    - "path/to/related/file.ts"
  dependencies:
    - "Description of any blocking dependencies"
  existing_patterns: >
    Describe existing conventions, patterns, or approaches in the codebase
    that the agent should follow.

constraints:
  scope: >
    Explicit boundaries: what is IN scope and what is OUT of scope.
    Example: "Fix the auth middleware only. Do not change route definitions."
  technical:
    - "Use TypeScript strict mode"
    - "All functions must have return type annotations"
    - "No any types"
  style:
    - "Follow existing naming conventions in the project"
    - "Use functional components with hooks, not class components"
  time: "Optional deadline or time box"

expected_output:
  format: "description of expected deliverable format"
  acceptance_criteria:
    - "Criterion 1: The fix resolves the specific error in issue #123"
    - "Criterion 2: All existing tests pass"
    - "Criterion 3: New tests cover edge cases X, Y, Z"
  verification_steps:
    - "Run `npm test` and confirm all tests pass"
    - "Check that no TypeScript errors are introduced"
```

## Delegation Principles

1. **Be specific about scope.** Vague tasks produce vague results. Tell the agent exactly what to touch and what to leave alone.

2. **Include context, not just instructions.** The agent may not have your understanding of the codebase. Share relevant file paths, existing patterns, and the "why" behind the task.

3. **Define acceptance criteria upfront.** The agent should know what "done" looks like before starting.

4. **List constraints explicitly.** Technical limits, style requirements, and scope boundaries prevent scope creep and ensure consistency.

5. **Provide verification steps.** Tell the agent how to confirm success. This reduces back-and-forth.

## Example: Good vs Bad Delegation

### Bad
```yaml
objective: "Fix the login bug"
```

### Good
```yaml
objective: >
  Fix the authentication failure that occurs when a user logs in
  with a valid email and password but receives a 401 response.

context:
  related_files:
    - "src/auth/loginHandler.ts"
    - "src/middleware/authMiddleware.ts"
  existing_patterns: >
    Other auth handlers in src/auth/ use the pattern of validating
    credentials, generating a JWT, and returning it in an HTTP-only cookie.

constraints:
  scope: >
    Only modify loginHandler.ts and authMiddleware.ts.
    Do not change the User model or database schema.
  technical:
    - "Use bcrypt.compareSync for password comparison"
    - "Return JWT in httpOnly cookie, not in response body"
    - "Add proper error logging for failed login attempts"

expected_output:
  acceptance_criteria:
    - "Valid credentials return 200 with Set-Cookie header containing JWT"
    - "Invalid credentials return 401 with generic 'Invalid credentials' message"
    - "Existing auth tests continue to pass"
    - "New tests added for: valid login, invalid password, missing fields"
  verification_steps:
    - "Run `npm test -- --grep auth` and confirm all tests pass"
    - "Manually test with curl against running server"
```

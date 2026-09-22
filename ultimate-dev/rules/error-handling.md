# Error Handling Rules

Rules for handling errors, retries, escalation, and fallbacks.

## Error Response Protocol

When an error occurs:

1. **Capture.** Record the full error message, stack trace, and context.
2. **Classify.** Determine severity (critical, high, medium, low).
3. **Decide.** Choose: retry, fix, escalate, or fallback.
4. **Act.** Execute the chosen strategy.
5. **Report.** Document what happened and what was done.

## Retry Policy

### When to Retry:
- Transient failures (network timeout, temporary unavailability).
- Rate limiting (429 responses).
- Deadlocks or contention (database locks).

### When NOT to Retry:
- Authentication failures (401, 403) — credentials won't change.
- Validation errors (400, 422) — input won't change.
- Not found errors (404) — resource doesn't exist.
- Logical errors — the code is wrong, not the environment.

### Retry Limits:
| Error Type | Max Retries | Wait Time | Backoff |
|------------|-------------|-----------|---------|
| Network timeout | 3 | 5s, 10s, 30s | Exponential |
| Rate limited | 3 | 60s | Fixed |
| Database lock | 2 | 1s, 3s | Exponential |
| Service unavailable | 3 | 10s, 30s, 60s | Exponential |

## Escalation Rules

### Escalate When:
- The same error occurs after all retries are exhausted.
- The error is outside your domain expertise.
- The error affects other agents or shared resources.
- The root cause cannot be identified.
- The fix requires changes to infrastructure or external services.

### Escalation Path:
1. **Same agent** — Try alternative approach.
2. **Orchestrator** — Request reassignment or additional resources.
3. **Senior engineer** — For complex architectural issues.
4. **Team lead** — For cross-team coordination or business decisions.

### Escalation Format:
```yaml
escalation:
  task_id: "original-task-id"
  reason: "Why escalation is needed"
  what_tried: "What approaches were attempted"
  current_state: "Where things stand now"
  what_needed: "What is needed to unblock"
  urgency: "How quickly this needs resolution"
```

## Fallback Strategies

### When Primary Approach Fails:
1. **Simpler approach** — Can the problem be solved with less complexity?
2. **Alternative tool** — Is there another tool or library that works?
3. **Manual workaround** — Can the user work around the issue?
4. **Graceful degradation** — Can the system continue with reduced functionality?
5. **Revert** — Can we undo the last change that caused the issue?

### Fallback Decision Tree:
```
Error occurred
  → Is it transient? → Retry (up to limit)
  → Is it input-related? → Fix input, don't retry
  → Is it code-related? → Fix code, don't retry
  → Is it infrastructure? → Fallback to alternative
  → Can't determine? → Escalate
```

## Error Documentation

Every significant error must be documented:

```yaml
error_log:
  - timestamp: "2026-09-22T10:30:00Z"
    error_code: "DB_CONNECTION_FAILED"
    context: "Connecting to primary database"
    resolution: "Retried 3 times, failed. Escalated to infrastructure team."
    duration: "45 seconds"
    impact: "User search unavailable for 45 seconds"
```

## Error Prevention

- Write tests that catch common errors before they reach production.
- Add input validation at system boundaries.
- Use type systems to prevent type-related errors.
- Add health checks for critical dependencies.
- Monitor error rates and alert on spikes.

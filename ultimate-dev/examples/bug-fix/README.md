# Example: Debugging Workflow

A complete example of debugging a non-obvious issue using the systematic debugging workflow.

## Task Description

**Bug Report:** The application randomly crashes with "out of memory" errors after running for 24-48 hours. The crash happens in production but cannot be reproduced locally. The memory usage graph shows a gradual increase over time, then a sharp spike before the crash.

**Error Message:**
```
FATAL ERROR: CALL_AND_RETRY_LAST Allocation failed - JavaScript heap out of memory
```

## Context

```yaml
task_id: "fix-memory-leak-001"
title: "Fix memory leak causing production OOM crashes"
objective: "Find and fix the memory leak causing OOM after 24-48 hours"
priority: "critical"
agent: "backend-specialist"
context:
  background: >
    Production servers crash every 24-48 hours with OOM errors.
    The memory usage grows steadily over time. Restarting the server
    temporarily fixes the issue. This affects all production instances.
  related_files:
    - "src/services/notificationService.ts"
    - "src/services/eventEmitter.ts"
    - "src/workers/backgroundProcessor.ts"
    - "src/config/server.ts"
  existing_patterns: >
    The application uses EventEmitter for internal events and
    has a background job processor that runs on a schedule.
```

## Workflow Steps

### Step 1: Reproduce

Can we reproduce the issue locally?

```bash
# Run the application with memory monitoring
$ node --max-old-space-size=512 src/index.js

# Monitor memory usage
$ watch -n 5 "ps -o pid,rss,vsz -p $(pgrep -f 'node src/index')"
```

After running for 2 hours locally, memory usage shows:
- Start: 85MB
- After 1 hour: 120MB
- After 2 hours: 180MB
- Trend: Growing ~50MB/hour

**Can reproduce:** Memory is clearly growing over time. The slow growth matches the production pattern.

### Step 2: Hypothesize

What could cause a gradual memory leak?

```yaml
hypotheses:
  - hypothesis: "Event listeners are being added but never removed"
    evidence: "notificationService.ts uses EventEmitter extensively"
    likelihood: "high"
  - hypothesis: "Background processor is accumulating unprocessed jobs"
    evidence: "backgroundProcessor.ts runs on a schedule, stores results in memory"
    likelihood: "high"
  - hypothesis: "Database connections are not being released"
    evidence: "Database connections could pile up under load"
    likelihood: "medium"
  - hypothesis: "Circular references preventing garbage collection"
    evidence: "Less likely with modern V8, but possible with complex objects"
    likelihood: "low"
```

### Step 3: Isolate

**Technique: Heap Snapshot Analysis**

```bash
# Take heap snapshots at different memory levels
$ node --expose-gc --max-old-space-size=512 src/index.js

# In a separate terminal, trigger GC and take snapshots
$ kill -USR2 $(pgrep -f 'node src/index')  # Custom signal handler
```

After analyzing heap snapshots with Chrome DevTools:

**Finding 1:** Event listeners are accumulating in `notificationService.ts`:
```
Listeners in EventEmitter:
  'user_created': 847 (should be ~1)
  'order_placed': 623 (should be ~1)
  'payment_completed': 412 (should be ~1)
```

**Finding 2:** The background processor is storing results in a `Map` that never gets cleaned:
```typescript
// src/workers/backgroundProcessor.ts
private results: Map<string, any> = new Map();

async process(job: Job) {
  const result = await this.execute(job);
  this.results.set(job.id, result);  // Never deleted!
}
```

**Root Cause Identified:** Two memory leaks:
1. Event listeners being added in a loop without cleanup.
2. Background processor accumulating results without eviction.

### Step 4: Fix

**Fix 1: Clean up event listeners**

```typescript
// src/services/notificationService.ts
// BEFORE (leak):
class NotificationService {
  private subscriptions: (() => void)[] = [];

  startWatching() {
    eventEmitter.on('user_created', this.handleUserCreated);  // Added every time
    eventEmitter.on('order_placed', this.handleOrderPlaced);
    this.subscriptions.push(() => eventEmitter.removeAllListeners());
  }
}

// AFTER (fixed):
class NotificationService {
  private handlers = new Map<string, Function>();

  startWatching() {
    this.handlers.set('user_created', this.handleUserCreated.bind(this));
    this.handlers.set('order_placed', this.handleOrderPlaced.bind(this));
    for (const [event, handler] of this.handlers) {
      eventEmitter.on(event, handler);
    }
  }

  stopWatching() {
    for (const [event, handler] of this.handlers) {
      eventEmitter.removeListener(event, handler);
    }
    this.handlers.clear();
  }
}
```

**Fix 2: Evict old results from background processor**

```typescript
// src/workers/backgroundProcessor.ts
private results: Map<string, any> = new Map();
private readonly MAX_RESULTS = 1000;
private readonly RESULT_TTL = 60 * 60 * 1000; // 1 hour

async process(job: Job) {
  const result = await this.execute(job);
  this.results.set(job.id, { data: result, timestamp: Date.now() });
  this.evictOldResults();
}

private evictOldResults() {
  const now = Date.now();
  for (const [key, value] of this.results) {
    if (now - value.timestamp > this.RESULT_TTL || this.results.size > this.MAX_RESULTS) {
      this.results.delete(key);
    }
  }
}
```

### Step 5: Verify

```bash
# Run the application with memory monitoring
$ node --max-old-space-size=512 src/index.js

# Monitor memory usage
$ watch -n 5 "ps -o pid,rss,vsz -p $(pgrep -f 'node src/index')"
```

After running for 4 hours:
- Start: 85MB
- After 1 hour: 92MB
- After 2 hours: 95MB
- After 4 hours: 98MB
- **Trend: Stabilized around 100MB (was growing to 180MB+ before)**

```bash
# Run existing tests
$ npm test
PASS (all tests passing)

# Run with heap limit to check for leaks
$ node --max-old-space-size=256 --expose-gc node_modules/.bin/jest --forceExit
PASS (no OOM errors)
```

### Step 6: Handoff

```yaml
task_id: "fix-memory-leak-001"
agent: "backend-specialist"
status: "completed"

summary: >
  Fixed memory leak causing production OOM crashes after 24-48 hours.
  Two leaks found: event listeners accumulating and background processor
  storing unbounded results.

what_changed:
  - file: "src/services/notificationService.ts"
    action: "modified"
    description: >
      Replaced repeated eventEmitter.on() calls with a Map-based handler
      registry. Added stopWatching() method to clean up listeners.
  - file: "src/workers/backgroundProcessor.ts"
    action: "modified"
    description: >
      Added TTL (1 hour) and max size (1000) limits to results Map.
      Added evictOldResults() method to prevent unbounded growth.

evidence:
  - type: "verification"
    content: |
      Memory usage stabilized at ~100MB after fix (was growing to 180MB+).
      Ran for 4 hours without significant growth.
      All existing tests passing.
      No OOM errors with 256MB heap limit.

assumptions:
  - "1 hour TTL for background results is acceptable for the use case"
  - "Max 1000 results in memory is sufficient for current workload"

residual_risks:
  - risk: "If job processing rate increases significantly, results Map may need adjustment"
    mitigation: "Monitor memory usage in production and adjust MAX_RESULTS if needed"
    severity: "low"
  - risk: "Other parts of the codebase may have similar memory leak patterns"
    mitigation: "Recommend a full memory audit of other services"
    severity: "medium"

next_steps:
  - "Add memory usage monitoring to production dashboards"
  - "Schedule a memory audit of other services"
  - "Consider adding a memory limit health check that alerts at 80% usage"
```

## Key Takeaways

1. **Reproduce first.** If you can't reproduce it, you can't verify the fix.
2. **Use data to form hypotheses.** The heap snapshot told us exactly where the leak was.
3. **Isolate before fixing.** Don't guess — use profiling tools to find the root cause.
4. **Fix the root cause, not the symptom.** We didn't just increase the memory limit — we fixed the leak.
5. **Verify the fix works.** Run the same monitoring and confirm the memory stabilizes.
6. **Prevent recurrence.** Add monitoring and consider auditing similar patterns elsewhere.

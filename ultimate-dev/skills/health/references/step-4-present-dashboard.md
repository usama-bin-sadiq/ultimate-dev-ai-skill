<!-- Moved verbatim from health/SKILL.md, the
     'step-4-present-dashboard' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 4: Present Dashboard

Present results as a clear table:

```
CODE HEALTH DASHBOARD
=====================

Project: <project name>
Branch:  <current branch>
Date:    <today>

Category      Tool              Score   Status     Duration   Details
----------    ----------------  -----   --------   --------   -------
Type check    tsc --noEmit      10/10   CLEAN      3s         0 errors
Lint          biome check .      8/10   WARNING    2s         3 warnings
Tests         bun test          10/10   CLEAN      12s        47/47 passed
Dead code     knip               7/10   WARNING    5s         4 unused exports
Shell lint    shellcheck        10/10   CLEAN      1s         0 issues
GBrain        gbrain doctor     10/10   CLEAN      <1s        doctor=ok, queue=3, pushed 2h ago

COMPOSITE SCORE: 9.1 / 10
Coverage: 6/6 categories checked
Checked: typecheck, lint, test, deadcode, shell, gbrain
Unavailable: none

Duration: 23s total
```

Use these status labels:
- 10: `CLEAN`
- 7-9: `WARNING`
- 4-6: `NEEDS WORK`
- 0-3: `CRITICAL`
- Unavailable tool: `SKIPPED` (no score)
- Capture failure: `ERROR` (no score; composite is N/A)

For partial coverage, show e.g. `COMPOSITE SCORE: 8.0 / 10 — partial coverage`,
`Coverage: 2/6 categories checked`, the checked category names, and the unavailable
categories with reasons. For zero coverage, show `N/A — no checks ran` and explain
which tools need configuring or installing; never display 10/10 for an empty run.

If any category scored below 7, list the top issues from that tool's output:

```
DETAILS: Lint (3 warnings)
  biome check . output:
    src/utils.ts:42 — lint/complexity/noForEach: Prefer for...of
    src/api.ts:18 — lint/style/useConst: Use const instead of let
    src/api.ts:55 — lint/suspicious/noExplicitAny: Unexpected any
```

---

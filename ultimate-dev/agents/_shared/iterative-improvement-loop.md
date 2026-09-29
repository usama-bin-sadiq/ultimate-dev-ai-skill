# Iterative Improvement Loop: Self-Audit Until 10/10

The orchestrator runs a mandatory **Loop Strategy** that iteratively improves the codebase until all findings are addressed.

## Loop Flow

```
┌──────────────────────────────────────────────────────┐
│  LOOP START                                          │
│  ┌────────────┐                                      │
│  │ 1. TRIAGE  │ ← Read only changed files            │
│  │   Select   │   Apply Triage Rules                 │
│  │   agents   │   Output: ordered agent list         │
│  └─────┬──────┘                                      │
│        │                                             │
│  ┌─────▼──────┐                                      │
│  │ 2. RESEARCH│ ← Agents scan code                   │
│  │   Analyze  │   Find issues (max 2 per agent)      │
│  │   Search   │   WebSearch if uncertain             │
│  └─────┬──────┘                                      │
│        │                                             │
│  ┌─────▼──────┐                                      │
│  │ 3. PLAN    │ ← Prioritize fixes                   │
│  │   Order    │   Group related fixes                │
│  │   Execute  │   Estimate effort                    │
│  └─────┬──────┘                                      │
│        │                                             │
│  ┌─────▼──────┐                                      │
│  │ 4. IMPLEMENT│ ← Make changes                      │
│  │   Fix      │   Verify each fix                    │
│  │   Verify   │   Run commands if needed             │
│  └─────┬──────┘                                      │
│        │                                             │
│  ┌─────▼──────┐                                      │
│  │ 5. REVIEW  │ ← Self-audit                         │
│  │   Compare  │   Before vs After                    │
│  │   Validate │   Check for regressions              │
│  └─────┬──────┘                                      │
│        │                                             │
│  ┌─────▼──────┐                                      │
│  │ 6. REPORT  │ ← Summary                            │
│  │   Status   │   What was fixed                     │
│  │   Next     │   What remains                       │
│  └─────┬──────┘                                      │
│        │                                             │
│        ▼                                             │
│  REMAINING FINDINGS? ──→ LOOP AGAIN (back to step 1) │
│  ALL CLEAR? ──────────→ LOOP END                     │
└──────────────────────────────────────────────────────┘
```

## Loop Rules

1. **Max 3 iterations** — if after 3 loops issues remain, present remaining findings to user
2. **Each loop reduces findings** — if loop N+1 has same or more findings than loop N, stop and present to user
3. **Each iteration is faster** — subsequent loops only re-scan changed files, not the whole codebase
4. **No infinite loops** — always terminate with a summary

## Per-Iteration Token Budget

| Phase | Max tokens |
|-------|-----------|
| Triage | 3,500 |
| Research (per agent) | 1,500 |
| Plan | 500 |
| Implement | N/A (tool calls) |
| Review | 1,000 |
| Report | 500 |
| **Total per loop** | **~8,000 + agent costs** |

## Self-Audit Checklist (step 5)

After each implementation round:

1. Were all reported issues actually fixed?
2. Did fixes introduce new issues?
3. Are file paths correct?
4. Do code changes follow project conventions?
5. Are there remaining issues the agents missed?

## Termination Conditions

Loop ends when:
- Zero findings remain, OR
- 3 iterations completed, OR
- Next loop would have fewer than 2 actionable findings

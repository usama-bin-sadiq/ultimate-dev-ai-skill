<!-- Moved verbatim from health/SKILL.md, the
     'step-3-score-each-category' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 3: Score Each Category

Score each category on a 0-10 scale using this rubric:

| Category | Weight | 10 | 7 | 4 | 0 |
|-----------|--------|------|-----------|------------|-----------|
| Type check | 22% | Clean (exit 0) | <10 errors | <50 errors | >=50 errors |
| Lint | 18% | Clean (exit 0) | <5 warnings | <20 warnings | >=20 warnings |
| Tests | 28% | All pass (exit 0) | >95% pass | >80% pass | <=80% pass |
| Dead code | 13% | Clean (exit 0) | <5 unused exports | <20 unused | >=20 unused |
| Shell lint | 9% | Clean (exit 0) | <5 issues | >=5 issues | N/A (skip) |
| GBrain (D6) | 10% | doctor=ok, queue<10, pushed <24h | doctor=warnings OR queue<100 OR pushed <72h | doctor broken OR queue>=100 OR pushed >=72h | N/A (gbrain not installed) |

**Parsing tool output for counts:**
Use the complete captured output, not the displayed tail. A zero match count cannot
make a non-zero checker exit `CLEAN`; retain its failure and diagnostic output.

- **tsc:** Count lines matching `error TS` in output.
- **biome/eslint/ruff:** Count lines matching error/warning patterns. Parse the summary line if available.
- **Tests:** Parse pass/fail counts from the test runner output. If the runner only reports exit code, use: exit 0 = 10, exit non-zero = 4 (assume some failures).
- **knip:** Count lines reporting unused exports, files, or dependencies.
- **shellcheck:** Count distinct findings (lines starting with "In ... line").

**Composite score:**
```
composite = (typecheck_score * 0.22) + (lint_score * 0.18) + (test_score * 0.28) + (deadcode_score * 0.13) + (shell_score * 0.09) + (gbrain_score * 0.10)
```

If a category is skipped (tool not available — includes GBrain when gbrain
is not installed), redistribute its weight proportionally among the
remaining categories.

Always report coverage: list the checked categories and the unavailable categories
with their reasons. Label a numeric composite with skipped categories as **partial
coverage**. If zero checks executed, report **N/A — no checks ran**, do not compute
a numeric composite, and skip numeric history persistence and trend calculation.

**GBrain sub-score computation (D6):**

```
doctor_component: 10 if `gbrain doctor --json | jq -r .status` == "ok";
                   7 if "warnings"; 0 otherwise (or command times out after 5s).
queue_component:   10 if ~/.gstack/.brain-queue.jsonl has <10 lines;
                    7 if 10-100; 0 if >=100 (suggests secret-scan rejections
                    piling up). N/A if artifacts_sync_mode == off.
push_component:    10 if (now - mtime of ~/.gstack/.brain-last-push) < 24h;
                    7 if <72h; 0 if >=72h. N/A if artifacts_sync_mode == off.
gbrain_score     = 0.5 * doctor_component + 0.3 * queue_component + 0.2 * push_component
                   (redistribute 0.3 + 0.2 into doctor when sync_mode is off:
                   gbrain_score = doctor_component in that case)
```

The `gbrain doctor --json` call MUST be wrapped in `timeout 5s` so a hung
or misconfigured gbrain doesn't stall the entire /health dashboard.

---

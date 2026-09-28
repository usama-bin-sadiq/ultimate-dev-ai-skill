<!-- Moved verbatim from autoplan/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Completion: Write Review Logs

On approval, log each completed review for /ship's dashboard. Replace TIMESTAMP,
STATUS and N with actual phase values. STATUS is "clean" or "issues_open".

```bash
COMMIT=$(git rev-parse --short HEAD 2>/dev/null)
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
~/<agent-config-dir>/gstack/bin/gstack-review-log '{"skill":"plan-ceo-review","timestamp":"'"$TIMESTAMP"'","status":"STATUS","unresolved":N,"critical_gaps":N,"mode":"SELECTIVE_EXPANSION","via":"autoplan","commit":"'"$COMMIT"'"}'
~/<agent-config-dir>/gstack/bin/gstack-review-log '{"skill":"plan-eng-review","timestamp":"'"$TIMESTAMP"'","status":"STATUS","unresolved":N,"critical_gaps":N,"issues_found":N,"mode":"FULL_REVIEW","via":"autoplan","commit":"'"$COMMIT"'"}'
```

If Phase 2 ran (UI scope):
```bash
~/<agent-config-dir>/gstack/bin/gstack-review-log '{"skill":"plan-design-review","timestamp":"'"$TIMESTAMP"'","status":"STATUS","unresolved":N,"via":"autoplan","commit":"'"$COMMIT"'"}'
```

If Phase 2.5 ran (DX scope):
```bash
~/<agent-config-dir>/gstack/bin/gstack-review-log '{"skill":"plan-devex-review","timestamp":"'"$TIMESTAMP"'","status":"STATUS","initial_score":N,"overall_score":N,"product_type":"TYPE","tthw_current":"TTHW","tthw_target":"TARGET","unresolved":N,"via":"autoplan","commit":"'"$COMMIT"'"}'
```

Dual voice logs: write one record per PHASE (`ceo`, `design`, `dx`, `eng`) with
that phase's status/counts. Generate one AUTOPLAN_RUN_ID and share it with TIMESTAMP.
```bash
~/<agent-config-dir>/gstack/bin/gstack-review-log '{"skill":"autoplan-voices","run_id":"AUTOPLAN_RUN_ID","timestamp":"'"$TIMESTAMP"'","status":"STATUS","source":"SOURCE","host":"claude","outside_provider":"codex","outside_status":"OUTSIDE_STATUS","phase":"PHASE","via":"autoplan","consensus_confirmed":N,"consensus_disagree":N,"commit":"'"$COMMIT"'"}'
```

Always log skipped Design/DX: status/outside_status "skipped", source "none",
zero consensus counts. SOURCE = "codex" only for completed external
output; native results use "in-host". OUTSIDE_STATUS is completed, unavailable,
disabled or skipped. Never carry success across phases/runs; preserve modelUsage.

Retain the historical review-log skill ID; add `"host":"claude","outside_provider":"codex","outside_status":"completed|unavailable|disabled|skipped","phase":"autoplan"`. Record differing attempt outcomes separately. `source:"codex"` requires completed CLI output; native uses `source:"in-host"` (historical `source:"claude"`: native Claude). Availability/native fallback is not outside completion. Preserve all reported modelUsage; unknown model identity stays unknown.

Present a phase coverage table (CEO, design, DX, eng): host, outside provider/status,
native completion, findings, and partial coverage. Replace N with actual counts.

Suggest next step: `/ship` when ready to create the PR.

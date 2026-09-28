<!-- Moved verbatim from plan-ceo-review/SKILL.md, the
     'brain-cache-background-refresh' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Brain Cache Background Refresh

After the exit gate passes, start this nonblocking refresh before telemetry.
Then return to the finalization instructions below; the user need not wait for
the refresh process.

```bash
eval "$(~/<agent-config-dir>/gstack/bin/gstack-slug 2>/dev/null)" 2>/dev/null || true
(~/<agent-config-dir>/gstack/bin/gstack-brain-cache refresh --project "$SLUG" 2>/dev/null &) || true
```


After the refresh, run the preamble's **Telemetry (run last)** once. The review
is now finished. Call ExitPlanMode where required or return to the caller;
the chosen next-skill handoff starts a separate workflow.

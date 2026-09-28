<!-- Moved verbatim from canary/SKILL.md, the
     'arguments' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Arguments
- `/canary <url>` — monitor a URL for 10 minutes after deploy
- `/canary <url> --duration 5m` — custom monitoring duration (1m to 30m)
- `/canary <url> --baseline` — capture baseline screenshots (run BEFORE deploying)
- `/canary <url> --pages /,/dashboard,/settings` — specify pages to monitor
- `/canary <url> --quick` — single-pass health check (no continuous monitoring)

<!-- Moved verbatim from sync-gbrain/SKILL.md, the
     'concurrency-note' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Concurrency note

This skill is safe to run concurrently from multiple terminals on the same
Mac. The orchestrator acquires a lock at `~/.gstack/.sync-gbrain.lock` before
any state-file or CLAUDE.md mutation and exits with code 2 if another sync is
in flight. Stale locks (process died) auto-clear after 5 minutes.

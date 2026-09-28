<!-- Moved verbatim from ios-qa/SKILL.md, the
     'failure-modes-recovery' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Failure modes + recovery

| Symptom | Likely cause | Action |
|---|---|---|
| `curl: connection refused` to daemon | daemon crashed | Re-run `/ios-qa`; spawn-race lock will fail closed |
| `403 identity_not_allowed` from `/auth/mint` | identity missing from allowlist | Run `gstack-ios-qa-mint --remote <identity>` on the Mac |
| `409 schema_mismatch` on `/state/restore` | snapshot from older app build | Discard the snapshot; re-capture |
| `503 device_disconnected` from proxy | USB route dropped or app relaunched | Daemon invalidates the stale tunnel and retries one fresh bootstrap; reconnect/unlock the iPhone if it persists |
| `429 rate_limited` from `/auth/mint` | >10 mints/min from one identity | Wait 60s; check audit log for anomalies |
| `413 body_too_large` on `/state/restore` | snapshot >1MB | Increase `--max-body` or trim snapshot |

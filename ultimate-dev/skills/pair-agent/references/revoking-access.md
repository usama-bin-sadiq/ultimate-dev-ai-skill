<!-- Moved verbatim from pair-agent/SKILL.md, the
     'revoking-access' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Revoking access

To disconnect a specific agent:

```bash
$B tunnel revoke AGENT_NAME
```

The command deletes every token for that agent (the session and any pending
setup keys) and re-reads the agent list to prove it's gone.

See who's paired:

```bash
$B tunnel agents
```

Unexchanged setup keys show as "(pending)"; `tunnel revoke` removes them too.

To disconnect ALL agents at once, stop the daemon. Scoped tokens live in
daemon memory and never survive a restart; the next command boots a fresh
daemon with a new root token:

```bash
$B stop
```

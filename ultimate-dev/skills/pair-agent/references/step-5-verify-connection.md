<!-- Moved verbatim from pair-agent/SKILL.md, the
     'step-5-verify-connection' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 5: Verify connection

After the user pastes the instructions into the other agent, wait a moment then check:

```bash
$B status
```

Look for the connected agent in the status output. If it appears, tell the user:
"The remote agent is connected and has its own tab. You'll see its activity in the
side panel if you have GStack Browser open."

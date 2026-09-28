<!-- Moved verbatim from pair-agent/SKILL.md, the
     'step-1-check-prerequisites' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 1: Check prerequisites

```bash
$B status 2>/dev/null
```

If the browse server is not running, start it:

```bash
$B goto about:blank
```

This ensures the server is up and healthy before pairing.

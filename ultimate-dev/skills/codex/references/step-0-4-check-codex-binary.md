<!-- Moved verbatim from codex/SKILL.md, the
     'step-0-4-check-codex-binary' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 0.4: Check codex binary

```bash
CODEX_BIN=$(command -v codex || echo "")
[ -z "$CODEX_BIN" ] && echo "NOT_FOUND" || echo "FOUND: $CODEX_BIN"
```

If `NOT_FOUND`: stop and tell the user:
"Codex CLI not found. Install it: `npm install -g @openai/codex` or see https://github.com/openai/codex"

If `NOT_FOUND`, also log the event:
```bash
_TEL=$(~/.claude/skills/gstack/bin/gstack-config get telemetry 2>/dev/null || echo off)
source ~/.claude/skills/gstack/bin/gstack-codex-probe 2>/dev/null && _gstack_codex_log_event "codex_cli_missing" 2>/dev/null || true
```

---

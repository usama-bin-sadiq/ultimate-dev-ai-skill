<!-- Moved verbatim from setup-gbrain/SKILL.md, the 'Step 9: Smoke test' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 9: Smoke test

### Path 4 (Remote MCP)

The `mcp__gbrain__*` tools aren't visible mid-session — they're loaded at
Claude Code session start. So the live smoke test in this same skill run is
informational: print the curl-equivalent the user can run after restarting
Claude Code. The verify round-trip in Step 4c already proved the server is
reachable + authed + on a compatible MCP version, so we don't re-test that.

Print to stdout:

```
After restarting Claude Code, the `mcp__gbrain__*` tools become callable.
Smoke test: ask the agent to run `mcp__gbrain__search` with any query
("test page" works). You should see a JSON list of pages.

To verify from the shell right now (without waiting for restart):
  curl -s -X POST -H 'Content-Type: application/json' \
       -H 'Accept: application/json, text/event-stream' \
       -H 'Authorization: Bearer <YOUR_TOKEN>' \
       -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
       <YOUR_MCP_URL>
```

Do NOT print the actual token in the curl command — leave the placeholder
`<YOUR_TOKEN>` so the snippet is safe to copy into chat / share.

### Paths 1, 2a, 2b, 3 (Local stdio)

```bash
SLUG="setup-gbrain-smoke-test-$(date +%s)"
echo "Set up on $(date). Smoke test for /setup-gbrain." | gbrain put "$SLUG"
gbrain search "smoke test" | grep -i "$SLUG"
```

Confirms the round trip. On failure, surface `gbrain doctor --json` output
and STOP with a NEEDS_CONTEXT escalation.

---

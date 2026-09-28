<!-- Moved verbatim from hook-development/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Debugging Hooks

### Enable Debug Mode

```bash
claude --debug
```

Look for hook registration, execution logs, input/output JSON, and timing information.

### Test Hook Scripts

Test command hooks directly:

```bash
echo '{"tool_name": "Write", "tool_input": {"file_path": "/test"}}' | \
  bash ${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh

echo "Exit code: $?"
```

### Validate JSON Output

Ensure hooks output valid JSON:

```bash
output=$(./your-hook.sh < test-input.json)
echo "$output" | jq .
```

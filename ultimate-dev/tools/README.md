# Tools

This directory contains tool definitions and configuration for the ultimate-dev agent system.

## Available Tools

Agents in this system have access to the following tools:

| Tool | Purpose | Restrictions |
|------|---------|-------------|
| `read_file` | Read file contents | Read-only, no execution |
| `write_file` | Create or overwrite files | Must be in project scope |
| `edit_file` | Targeted file edits | Must preserve existing content |
| `grep_search` | Search file contents by pattern | Read-only |
| `glob_search` | Search file paths by pattern | Read-only |
| `run_shell_command` | Execute shell commands | Sandboxed, no destructive commands |
| `web_search` | Search the web for information | Read-only |
| `browser` | Open and interact with browser tabs | Read-only browsing |

## Tool Requirements

### Before Using Any Tool:
1. Understand what you're trying to accomplish.
2. Choose the most appropriate tool for the task.
3. Verify the tool is within your allowed scope.
4. Check for existing solutions before creating new ones.

### Tool Selection Guide:
```
Need to understand code? → read_file, grep_search, glob_search
Need to create/modify code? → write_file, edit_file
Need to run code/tests? → run_shell_command
Need external information? → web_search
Need to verify visually? → browser
```

## Restrictions

### Shell Commands:
- No destructive commands without explicit approval: `rm -rf`, `DROP TABLE`, `git push --force`.
- No network requests to unknown hosts.
- No installing packages without approval.
- No modifying system configuration.

### File Operations:
- Only modify files within the project directory.
- Always read a file before modifying it.
- Use `edit_file` for targeted changes, not `write_file` for entire files.
- Keep backups of critical files before modification.

### Web Access:
- Read-only — no submitting forms or posting data.
- No accessing authenticated services.
- No downloading and executing remote code.

## Tool Configuration

See `tool_registry.yaml` for the complete tool registry with parameters, capabilities, and restrictions.

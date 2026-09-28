<!-- Moved verbatim from hook-development/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Temporarily Active Hooks

Create hooks that activate conditionally by checking for a flag file or configuration:

**Pattern: Flag file activation**
```bash
#!/bin/bash
# Only active when flag file exists
FLAG_FILE="$CLAUDE_PROJECT_DIR/.enable-strict-validation"

if [ ! -f "$FLAG_FILE" ]; then
  # Flag not present, skip validation
  exit 0
fi

# Flag present, run validation
input=$(cat)
# ... validation logic ...
```

**Pattern: Configuration-based activation**
```bash
#!/bin/bash
# Check configuration for activation
CONFIG_FILE="$CLAUDE_PROJECT_DIR/.claude/plugin-config.json"

if [ -f "$CONFIG_FILE" ]; then
  enabled=$(jq -r '.strictMode // false' "$CONFIG_FILE")
  if [ "$enabled" != "true" ]; then
    exit 0  # Not enabled, skip
  fi
fi

# Enabled, run hook logic
input=$(cat)
# ... hook logic ...
```

**Use cases:**
- Enable strict validation only when needed
- Temporary debugging hooks
- Project-specific hook behavior
- Feature flags for hooks

**Best practice:** Document activation mechanism in plugin README so users know how to enable/disable temporary hooks.

<!-- Moved verbatim from command-development/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Validation Patterns

Commands should validate inputs and resources before processing.

### Argument Validation

```markdown
---
description: Deploy with validation
argument-hint: [environment]
---

Validate environment: !`echo "$1" | grep -E "^(dev|staging|prod)$" || echo "INVALID"`

If $1 is valid environment:
Deploy to $1
Otherwise:
Explain valid environments: dev, staging, prod
Show usage: /deploy [environment]
```

### File Existence Checks

```markdown
---
description: Process configuration
argument-hint: [config-file]
---

Check file exists: !`test -f $1 && echo "EXISTS" || echo "MISSING"`

If file exists:
Process configuration: @$1
Otherwise:
Explain where to place config file
Show expected format
Provide example configuration
```

### Plugin Resource Validation

```markdown
---
description: Run plugin analyzer
allowed-tools: Bash(test:*)
---

Validate plugin setup:

- Script: !`test -x ${CLAUDE_PLUGIN_ROOT}/bin/analyze && echo "✓" || echo "✗"`
- Config: !`test -f ${CLAUDE_PLUGIN_ROOT}/config.json && echo "✓" || echo "✗"`

If all checks pass, run analysis.
Otherwise, report missing components.
```

### Error Handling

```markdown
---
description: Build with error handling
allowed-tools: Bash(*)
---

Execute build: !`bash ${CLAUDE_PLUGIN_ROOT}/scripts/build.sh 2>&1 || echo "BUILD_FAILED"`

If build succeeded:
Report success and output location
If build failed:
Analyze error output
Suggest likely causes
Provide troubleshooting steps
```

**Best practices:**

- Validate early in command
- Provide helpful error messages
- Suggest corrective actions
- Handle edge cases gracefully

---

For detailed frontmatter field specifications, see `./frontmatter-reference.md`.
For plugin-specific features and patterns, see `./plugin-features-reference.md`.
For command pattern examples, see `examples/` directory.

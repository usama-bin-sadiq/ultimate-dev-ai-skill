<!-- Moved verbatim from learn/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Export

Export learnings as markdown suitable for adding to <agent-instructions> or project documentation.

```bash
eval "$(~/<agent-config-dir>/gstack/bin/gstack-slug 2>/dev/null)"
~/<agent-config-dir>/gstack/bin/gstack-learnings-search --limit 50 2>/dev/null
```

Format the output as a markdown section:

```markdown
## Project Learnings

### Patterns
- **[key]**: [insight] (confidence: N/10)

### Pitfalls
- **[key]**: [insight] (confidence: N/10)

### Preferences
- **[key]**: [insight]

### Architecture
- **[key]**: [insight] (confidence: N/10)
```

Present the formatted output to the user. Ask if they want to append it to <agent-instructions>
or save it as a separate file.

---

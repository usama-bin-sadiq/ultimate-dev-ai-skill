<!-- Moved verbatim from learn/SKILL.md, the
     'export' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Export

Export learnings as markdown suitable for adding to <agent-instructions> or project documentation.

```bash
eval "$(~/<agent-config-dir>/gstack/bin/gstack-slug 2>/dev/null)"
~/<agent-config-dir>/gstack/bin/gstack-learnings-search --limit 50 2>/dev/null
```

Format the output as a markdown section:

```markdown

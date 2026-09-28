<!-- Moved verbatim from learn/SKILL.md, the
     'show-recent-default' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Show recent (default)

Show the most recent 20 learnings, grouped by type.

```bash
eval "$(~/<agent-config-dir>/gstack/bin/gstack-slug 2>/dev/null)"
~/<agent-config-dir>/gstack/bin/gstack-learnings-search --limit 20 2>/dev/null || echo "No learnings yet."
```

Present the output in a readable format. If no learnings exist, tell the user:
"No learnings recorded yet. As you use /review, /ship, /investigate, and other skills,
gstack will automatically capture patterns, pitfalls, and insights it discovers."

---

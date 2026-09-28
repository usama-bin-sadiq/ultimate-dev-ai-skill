<!-- Moved verbatim from learn/SKILL.md, the
     'search' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Search

```bash
eval "$(~/<agent-config-dir>/gstack/bin/gstack-slug 2>/dev/null)"
~/<agent-config-dir>/gstack/bin/gstack-learnings-search --query "USER_QUERY" --limit 20 2>/dev/null || echo "No matches."
```

Replace USER_QUERY with the user's search terms. Present results clearly.

---

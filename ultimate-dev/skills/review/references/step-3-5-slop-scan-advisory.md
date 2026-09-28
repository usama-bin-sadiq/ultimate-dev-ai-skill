<!-- Moved verbatim from review/SKILL.md, the
     'step-3-5-slop-scan-advisory' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 3.5: Slop scan (advisory)

Run a slop scan on changed files to catch AI code quality issues (empty catches,
redundant `return await`, overcomplicated abstractions):

```bash
bun run slop:diff origin/<base> 2>/dev/null || true
```

If findings are reported, include them in the review output as an informational
diagnostic. Slop findings are advisory, never blocking. If slop:diff is not
available (e.g., slop-scan not installed), skip this step silently.

---

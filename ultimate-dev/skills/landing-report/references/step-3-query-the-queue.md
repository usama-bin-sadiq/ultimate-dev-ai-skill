<!-- Moved verbatim from landing-report/SKILL.md, the
     'step-3-query-the-queue' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 3: Query the queue

Call the util three times — once for each bump level — so the user sees what
they'd claim for micro/patch/minor/major. Cheap (same gh call cached by bun).

```bash
for LEVEL in micro patch minor major; do
  bun run ~/<agent-config-dir>/gstack/bin/gstack-next-version \
    --base "$BASE_BRANCH" \
    --bump "$LEVEL" \
    --current-version "$BASE_VERSION" \
    > "/tmp/landing-$LEVEL.json" 2>/dev/null || echo '{"offline":true}' > "/tmp/landing-$LEVEL.json"
done
```

---

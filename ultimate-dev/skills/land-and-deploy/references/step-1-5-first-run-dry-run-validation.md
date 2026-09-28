<!-- Moved verbatim from land-and-deploy/SKILL.md, the
     'step-1-5-first-run-dry-run-validation' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 1.5: First-run dry-run validation

Check for prior setup confirmation and changed configuration (not proof of a successful deploy):

```bash
eval "$(~/<agent-config-dir>/gstack/bin/gstack-slug 2>/dev/null)"
if [ ! -f ~/.gstack/projects/$SLUG/land-deploy-confirmed ]; then
  echo "FIRST_RUN"
else
  # Check if deploy config has changed since confirmation
  SAVED_HASH=$(cat ~/.gstack/projects/$SLUG/land-deploy-confirmed 2>/dev/null)
  CURRENT_HASH=$(sed -n '/## Deploy Configuration/,/^## /p' <agent-instructions> 2>/dev/null | shasum -a 256 | cut -d' ' -f1)
  # Also hash workflow files that affect deploy behavior
  WORKFLOW_HASH=$(find .github/workflows -maxdepth 1 \( -name '*deploy*' -o -name '*cd*' \) 2>/dev/null | xargs cat 2>/dev/null | shasum -a 256 | cut -d' ' -f1)
  COMBINED_HASH="${CURRENT_HASH}-${WORKFLOW_HASH}"
  if [ "$SAVED_HASH" != "$COMBINED_HASH" ] && [ -n "$SAVED_HASH" ]; then
    echo "CONFIG_CHANGED"
  else
    echo "CONFIRMED"
  fi
fi
```

**If CONFIRMED:** Say "Setup was previously confirmed." Go to Step 2; do NOT read the dry-run section.

**If FIRST_RUN or CONFIG_CHANGED:** Read and execute the dry-run section:

> **STOP.** Before running the first-run dry-run validation — Step 1.5's check returned FIRST_RUN or CONFIG_CHANGED (skip on CONFIRMED), Read `~/<agent-config-dir>/gstack/land-and-deploy/sections/first-run-validation.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

Choice A saves the fingerprint and continues to Step 2; B/C stop.

---

<!-- Moved verbatim from devex-review/SKILL.md, the
     'step-0-target-discovery' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 0: Target Discovery

1. Read <agent-instructions> for project URL, docs URL, CLI install command
2. Read README.md for getting started instructions
3. Read package.json or equivalent for install commands

If URLs are missing, AskUserQuestion: "What's the URL for the docs/product I should test?"

### Boomerang Baseline

Check for prior /plan-devex-review scores:

```bash
eval "$(~/<agent-config-dir>/gstack/bin/gstack-slug 2>/dev/null)"
~/<agent-config-dir>/gstack/bin/gstack-review-read 2>/dev/null | grep plan-devex-review || echo "NO_PRIOR_PLAN_REVIEW"
```

If prior scores exist, display them. These are your baseline for the boomerang comparison.

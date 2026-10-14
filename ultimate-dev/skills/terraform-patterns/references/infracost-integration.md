<!-- Moved verbatim from terraform-patterns/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Infracost Integration

Infracost estimates cloud costs from Terraform code before resources are provisioned.

### PR Workflow

```bash
# Show cost breakdown for current code
infracost breakdown --path .

# Compare cost difference between current branch and main
infracost diff --path . --compare-to infracost-base.json
```

### GitHub Actions Cost Comment

```yaml
# .github/workflows/infracost.yml
name: Infracost
on: [pull_request]

jobs:
  cost:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: infracost/actions/setup@v3
        with:
          api-key: ${{ secrets.INFRACOST_API_KEY }}
      - run: infracost breakdown --path ./terraform --format json --out-file /tmp/infracost.json
      - run: infracost comment github --path /tmp/infracost.json --repo $GITHUB_REPOSITORY --pull-request ${{ github.event.pull_request.number }} --github-token ${{ secrets.GITHUB_TOKEN }} --behavior update
```

### Budget Thresholds and Cost Policy

```yaml
# infracost.yml — policy file
version: 2.9.0
policies:
  - path: "*"
    max_monthly_cost: "5000"    # Fail PR if estimated cost exceeds $5,000/month
    max_cost_increase: "500"    # Fail PR if cost increase exceeds $500/month
```

---

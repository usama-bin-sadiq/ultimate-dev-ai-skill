<!-- Moved verbatim from senior-secops/SKILL.md, the
     'secret-scanning-tools' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Secret Scanning Tools

Choose the right scanner for each stage of your workflow:

| Tool | Best For | Language | Pre-commit | CI/CD | Custom Rules |
|------|----------|----------|:----------:|:-----:|:------------:|
| **gitleaks** | CI pipelines, full-repo scans | Go | Yes | Yes | TOML regexes |
| **detect-secrets** | Pre-commit hooks, incremental | Python | Yes | Partial | Plugin-based |
| **truffleHog** | Deep history scans, entropy | Go | No | Yes | Regex + entropy |

**Recommended setup:** Use `detect-secrets` as a pre-commit hook (catches secrets before they enter history) and `gitleaks` in CI (catches anything that slips through).

```bash
# detect-secrets pre-commit hook (.pre-commit-config.yaml)
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.4.0
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']

# gitleaks in GitHub Actions
- name: gitleaks
  uses: gitleaks/gitleaks-action@v2
  env:
    GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
```

---

# Pull Request Template

## Description
Brief summary of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] CI/CD configuration
- [ ] Test updates

## Release Impact
**Required for merges to `main`** — Select one to trigger auto-release:
- [ ] `release:patch` — Bug fixes, docs, internal improvements (2.0.0 → 2.0.1)
- [ ] `release:minor` — New features, backward-compatible (2.0.0 → 2.1.0)
- [ ] `release:major` — Breaking changes, architecture changes (2.0.0 → 3.0.0)
- [ ] No release needed (documentation only, WIP, etc.)

## Related Issues
Closes #(issue number)

## Checklist

Validation, all of which runs in CI and can be run locally:

```bash
# Validates the kernel, the skill-creator sub-skill, every agent role,
# reference-path integrity, and the repository invariants. This is the same
# check CI runs.
python tools/validate-skills.py --strict
```

- [ ] `tools/validate-skills.py --strict` passes locally
- [ ] Bundle test suite passes
- [ ] Every new reference file is reachable from its `SKILL.md`
- [ ] Any new eval case carries a **trap** — the specific way a naive agent fails it
- [ ] Any new example shows a plan that reality contradicted
- [ ] No domain-specific code path was added to the kernel
- [ ] Self-review completed
- [ ] Documentation updated (`README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`)
- [ ] No unfilled placeholders (`TODO`, `TBD`, `placeholder`)
- [ ] PR title follows conventional commits (e.g. `feat: add delegation reference`)
- [ ] At least one label applied

## Breaking Changes
If this is a breaking change, describe impact and migration path:

## Additional Context
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
- [ ] `release:patch` — Bug fixes, docs, internal improvements (2.5.2 → 2.5.3)
- [ ] `release:minor` — New features, backward-compatible (2.5.2 → 2.6.0)
- [ ] `release:major` — Breaking changes, architecture changes (2.5.2 → 3.0.0)
- [ ] No release needed (documentation only, WIP, etc.)

## Related Issues
Closes #(issue number)

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated for changes
- [ ] All tests pass locally (`pytest tests/ -v`)
- [ ] Documentation updated (README, CHANGELOG, etc.)
- [ ] `scripts/validate.py` passes
- [ ] `scripts/sync-docs.py` checked
- [ ] PR title follows conventional commits (e.g., `feat: add new agent`)
- [ ] At least one label applied

## Breaking Changes
If this is a breaking change, describe impact and migration path:

## Screenshots (if applicable)

## Additional Context
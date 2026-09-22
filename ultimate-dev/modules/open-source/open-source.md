---
name: open-source
description: >
  Open source maintenance: contribution guides, licensing, release management, community management, code of conduct, governance, packaging. Technology-agnostic.
triggers: [open source, OSS, contribution guide, license, release, community, code of conduct, governance, package, npm, PyPI]
anti_triggers: [database schema, API design, frontend UI, Git operations]
last_verified: 2026-09-21
---

# Open Source Maintenance Module (pattern-based)

## Core Principles (technology-agnostic)

1. **Clear contribution path** — make it easy to contribute
2. **License clarity** — explicit, compatible licensing
3. **Semantic versioning** — predictable release cadence
4. **Community health** — welcoming, inclusive, responsive
5. **Documentation** — comprehensive, accurate, accessible

## Key Patterns

### Contribution Patterns
- CONTRIBUTING.md with clear steps
- Issue templates (bug, feature, question)
- Pull request templates
- Code of conduct
- First-timer friendly issues

### Licensing Patterns
- License selection (MIT, Apache 2.0, GPL)
- License headers in source files
- Dependency license auditing
- CLA (Contributor License Agreement)
- SPDX identifiers

### Release Patterns
- Semantic versioning (MAJOR.MINOR.PATCH)
- Changelog generation (Conventional Commits)
- Release automation (GitHub Releases)
- Pre-release channels (alpha, beta, rc)
- Package publishing (npm, PyPI, crates.io)

### Community Patterns
- Issue triage process
- PR review guidelines
- Maintainer roles and responsibilities
- Decision-making process (RFC, ADR)
- Conflict resolution

### Documentation Patterns
- README with quick start
- API documentation
- Examples and tutorials
- Architecture decision records
- Deprecation notices

## Anti-Patterns
- Bad: "No contribution guide" — violates clear contribution path
- Good: "CONTRIBUTING.md with step-by-step guide" — satisfies clear contribution path

- Bad: "Unclear licensing" — violates license clarity
- Good: "SPDX license identifier in every file" — satisfies license clarity

## Output Contract
- Contribution guidelines
- License configuration
- Release process documentation
- Community health metrics
- Documentation structure
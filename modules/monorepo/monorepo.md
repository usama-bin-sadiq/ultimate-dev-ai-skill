---
name: monorepo
description: >
  Monorepo architecture: workspace management, build optimization, dependency management, code sharing, CI/CD strategies, tooling. Technology-agnostic.
triggers: [monorepo, workspace, multi-package, code sharing, build optimization, dependency management, package manager]
anti_triggers: [frontend UI, database schema, API design, Git operations]
last_verified: 2026-09-21
---

# Monorepo Module (pattern-based)

## Core Principles (technology-agnostic)

1. **Single source of truth** — all code in one repository
2. **Atomic changes** — cross-package changes in one commit
3. **Build caching** — only rebuild what changed
4. **Dependency consistency** — single version of shared deps
5. **Code sharing** — libraries and utilities across packages

## Key Patterns

### Workspace Patterns
- Package structure (packages/, apps/, libs/)
- Shared configuration (tsconfig, eslint)
- Internal package references
- Path aliases
- Virtual workspaces

### Build Patterns
- Incremental builds (affected packages only)
- Build caching (local and remote)
- Parallel execution
- Task scheduling (dependency-aware)
- Build targets and configurations

### Dependency Patterns
- Single version policy
- hoisting strategies
- Peer dependency management
- Dependency vendoring
- Lock file strategies

### Code Sharing Patterns
- Shared libraries (internal packages)
- Shared configuration packages
- Shared tooling packages
- Template packages
- Cross-package types

### CI/CD Patterns
- Affected-only CI (only test changed packages)
- Parallel job execution
- Build artifact sharing
- Incremental deployment
- Change detection

## Anti-Patterns
- Bad: "Rebuild everything on every change" — violates build caching
- Good: "Incremental builds with caching" — satisfies build caching

- Bad: "Duplicate code across packages" — violates code sharing
- Good: "Extract shared code to internal packages" — satisfies code sharing

## Output Contract
- Monorepo structure
- Build configuration
- CI/CD pipeline configuration
- Dependency management strategy
- Documentation
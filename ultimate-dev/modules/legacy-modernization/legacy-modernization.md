---
name: legacy-modernization
description: >
  Legacy code modernization: strangler fig pattern, incremental refactoring, migration strategies, technical debt management, risk assessment. Technology-agnostic.
triggers: [legacy, modernization, refactor, migration, technical debt, strangler fig, legacy code, upgrade, rewrite]
anti_triggers: [new feature development, database schema design, API design, Git operations]
last_verified: 2026-09-21
---

# Legacy Modernization Module (pattern-based)

## Core Principles (technology-agnostic)

1. **Incremental over big-bang** — small, safe changes
2. **Strangler fig** — new features in new system, gradually replace
3. **Tests first** — safety net before refactoring
4. **Document decisions** — why, not just what
5. **Risk assessment** — understand blast radius

## Key Patterns

### Strangler Fig Pattern
- Identify seam points
- Build new alongside old
- Route traffic gradually
- Decommission old components
- Verify at each step

### Incremental Refactoring
- Extract method/class/module
- Replace conditional with polymorphism
- Introduce parameter object
- Move method to appropriate class
- Replace magic numbers with named constants

### Migration Patterns
- Database migration (expand-contract)
- API versioning (parallel versions)
- Feature flagging (toggle new/old)
- Shadow deployment (run both, compare)
- Canary deployment (partial rollout)

### Technical Debt Patterns
- Debt inventory (catalog all debt)
- Interest tracking (cost of not fixing)
- Prioritization (impact vs effort)
- Boy scout rule (leave code better)
- Refactoring sprints

### Risk Assessment Patterns
- Blast radius analysis
- Dependency mapping
- Change impact analysis
- Rollback planning
- Monitoring and alerting

## Anti-Patterns
- Bad: "Big bang rewrite" — violates incremental
- Good: "Strangler fig, one component at a time" — satisfies incremental

- Bad: "Refactor without tests" — violates tests first
- Good: "Write characterization tests first" — satisfies tests first

## Output Contract
- Modernization roadmap
- Risk assessment reports
- Migration playbooks
- Refactoring recommendations
- Progress tracking
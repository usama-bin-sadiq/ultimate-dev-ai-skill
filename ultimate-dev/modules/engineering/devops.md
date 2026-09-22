---
name: devops
description: >
  CI/CD pipelines, containerization, infrastructure automation, deployment strategies, monitoring, incident response. Works with ANY DevOps toolchain.
triggers: [deploy, CI/CD, container, infrastructure, pipeline, build, release, monitoring, automation, IaC, version control]
anti_triggers: [code implementation, database schema, API design, frontend UI]
last_verified: 2026-09-21
---

# DevOps Engineer (pattern-based)

## Core Principles (technology-agnostic)

1. **Automation first** — automate repetitive tasks
2. **Infrastructure as Code** — version, review, test infrastructure
3. **Immutable infrastructure** — replace, don't patch
4. **Shift left** — security and testing early
5. **Observability** — monitor everything, alert on symptoms

## Key Patterns

### CI/CD Patterns
- Build → Test → Deploy pipeline
- Parallel jobs for speed
- Artifact versioning
- Environment promotion
- Rollback procedures

### Container Patterns
- Multi-stage builds
- Layer caching
- Health checks
- Resource limits
- Security scanning

### Deployment Patterns
- Blue-green deployment
- Canary releases
- Rolling updates
- Feature flags
- GitOps workflow

### Infrastructure Patterns
- Declarative configuration
- State management
- Module composition
- Drift detection
- Secret management

### Monitoring Patterns
- SLI/SLO definition
- Alert fatigue prevention
- Incident response runbooks
- Post-incident review
- Capacity planning

## Anti-Patterns
- Bad: "Manual deployments" — violates automation first
- Good: "Automated pipeline with approval gates" — satisfies automation first

- Bad: "Mutable servers" — violates immutable infrastructure
- Good: "Replace servers, don't patch" — satisfies immutable infrastructure

## Output Contract
- CI/CD pipeline configurations
- Container configurations
- Deployment scripts
- Monitoring dashboards
- Incident response runbooks
---
name: cloud
description: >
  Cloud architecture patterns, multi-cloud strategies, serverless, container orchestration, infrastructure as code, cost optimization, disaster recovery. Works with ANY cloud provider.
triggers: [cloud, serverless, container orchestration, infrastructure as code, cost optimization, disaster recovery, auto-scaling, load balancing]
anti_triggers: [local development, frontend UI, database schema, Git operations]
last_verified: 2026-09-21
---

# Cloud Architecture Module

## Core Principles (technology-agnostic)

1. **Design for failure** — assume components will fail
2. **Infrastructure as Code** — version, review, test infrastructure
3. **Cost optimization** — right-size resources, use spot/preemptible
4. **Security** — zero trust, encryption at rest/transit, IAM least privilege
5. **Observability** — monitor everything, alert on anomalies

## Key Patterns

### Serverless
- Functions as a Service
- Event-driven triggers
- Cold start optimization
- Cost per invocation analysis

### Container Orchestration
- Container scheduling
- Service mesh
- Horizontal autoscaling
- Rolling deployments

### Infrastructure as Code
- Declarative configuration
- State management
- Module composition
- Drift detection

### Cost Optimization
- Reserved vs on-demand vs spot
- Auto-scaling policies
- Resource tagging
- Cost allocation

## Anti-Patterns
- Bad: "Manually configure infrastructure" — violates IaC principle
- Good: "Define infrastructure in code with version control" — satisfies IaC

- Bad: "Use default instance types" — violates cost optimization
- Good: "Right-size based on actual metrics" — satisfies cost optimization

## Output Contract
- Architecture diagrams
- IaC configurations (provider-agnostic)
- Cost analysis reports
- Disaster recovery plans
- Security assessments
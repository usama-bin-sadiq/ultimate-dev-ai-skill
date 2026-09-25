---
name: devops
description: >
  Meta-cognitive skill for DevOps. Teaches HOW to think about delivery,
  infrastructure, and operations — regardless of specific tools or platforms.
triggers: [devops, ci/cd, pipeline, deploy, container, infrastructure, automate, release]
provides: devops_ability
---

# DevOps Skill — Deliver Anything

## Purpose

An **ability**. DevOps is a culture of fast, safe delivery. This skill teaches you
how to think about delivery for ANY system — not just specific tool configurations.

## The Ability

```
Given any system to deliver, you can:
1. Design a pipeline that catches problems early
2. Choose the right deployment strategy for the risk level
3. Automate everything that can be automated
4. Monitor what matters and alert on what's actionable
5. Recover from failures quickly
```

## How to Deliver ANYTHING

### Step 1: The Delivery Pipeline

```
For ANY system, the pipeline has these stages:

CODE → BUILD → TEST → SECURITY → STAGE → DEPLOY → MONITOR

Each stage is a gate:
  PASS → proceed
  FAIL → stop and fix
```

### Step 2: Choose Deployment Strategy by Risk

```
LOW RISK (config change, UI tweak):
  → Rolling update (gradual, zero downtime)

MEDIUM RISK (new feature, API change):
  → Blue-green (instant rollback, parallel environments)

HIGH RISK (database migration, auth change):
  → Canary (1% → 10% → 50% → 100%, with monitoring)

CRITICAL RISK (data model, payment flow):
  → Manual gate + feature flag + staged rollout
```

### Step 3: Automate the Right Things

```
ALWAYS AUTOMATE:
  - Building and packaging
  - Running tests
  - Security scanning
  - Deployment to staging
  - Rollback on failure

SOMETIMES AUTOMATE:
  - Deployment to production (depends on risk tolerance)
  - Infrastructure provisioning (depends on change frequency)

NEVER AUTOMATE:
  - Security decisions
  - Architecture decisions
  - Human communication
```

### Step 4: Monitor What Matters

```
For ANY system, monitor:

AVAILABILITY:  Is it up? (uptime, health checks)
PERFORMANCE:   Is it fast? (latency, throughput)
ERRORS:        Is it correct? (error rate, failure count)
SATISFACTION:  Do users like it? (user metrics, NPS)

Alert on SYMPTOMS, not CAUSES:
  ✓ "Error rate > 1% for 5 minutes"
  ✗ "CPU > 80%" (might be fine)
```

### Step 5: Recover Quickly

```
When things go wrong:
1. DETECT   → Monitoring alerts, user reports
2. DIAGNOSE → Check logs, metrics, traces
3. MITIGATE → Rollback, feature flag, scale up
4. FIX      → Root cause analysis, patch
5. LEARN    → Post-mortem, prevent recurrence
```

## Operating Contract

- **Inputs:** change scope, environment, dependencies, risk, approvals, and rollback path.
- **Output:** delivery steps, observability, verification, rollback, and operational handoff.
- **Verification:** validate the artifact and the smallest safe environment before production effects.
- **When not to use:** do not deploy or destroy infrastructure without explicit authorization.

## DevOps Anti-Patterns

- DO NOT deploy on Fridays (or before holidays)
- DO NOT skip health checks
- DO NOT hardcode secrets in configs
- DO NOT skip rollback testing
- DO NOT ignore monitoring alerts

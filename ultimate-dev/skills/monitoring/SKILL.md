---
name: monitoring-skill
description: >
  Meta-cognitive skill for monitoring. Teaches HOW to observe any system
  — what to measure, what to alert on, and how to respond — regardless
  of specific tools or platforms.
triggers: [monitoring, observability, logging, alerting, tracing, metrics, health, diagnose]
provides: monitoring_ability
---

# Monitoring Skill — Observe Anything

## Purpose

An **ability**. Monitoring is about knowing what's happening in your system
before users tell you. This skill teaches you how to observe ANY system —
not just specific tools.

## The Ability

```
Given any system to monitor, you can:
1. Identify what can go wrong
2. Choose what to measure (and what not to)
3. Set meaningful alerts (not noise)
4. Diagnose problems quickly from telemetry
5. Respond appropriately to incidents
```

## How to Monitor ANYTHING

### Step 1: Identify What Can Go Wrong

```
For ANY system, think about:

AVAILABILITY:  Can it go down? (crashes, OOM, disk full)
PERFORMANCE:   Can it get slow? (latency, throughput, memory)
CORRECTNESS:   Can it give wrong answers? (data corruption, logic bugs)
CAPACITY:      Can it run out? (connections, storage, rate limits)
DEPENDENCIES:  Can something it depends on fail? (DB, API, network)
SECURITY:      Can it be attacked? (auth, injection, DDoS)
```

### Step 2: Choose What to Measure

```
The Four Signals (for ANY system):

1. LATENCY     → How long does it take?
2. TRAFFIC     → How much work is it doing?
3. ERRORS      → How often does it fail?
4. SATURATION  → How full is it?

These four signals tell you almost everything about system health.
```

### Step 3: Set Meaningful Alerts

```
Good alerts:
  → Tell you something is wrong
  → Are actionable (you can do something about it)
  → Have a runbook (you know what to do)
  → Are not noisy (signal, not noise)

Bad alerts:
  → Fire constantly (alert fatigue)
  → Tell you something is "happening" (not wrong)
  → Have no runbook (you don't know what to do)
  → Fire on symptoms without root cause

RULE: If you can't do anything about it, don't alert on it.
```

### Step 4: Diagnose from Telemetry

```
When something goes wrong:

1. CHECK DASHBOARDS → What's the overall health?
2. CHECK ERROR LOGS → What's failing and why?
3. CHECK METRICS → When did it start? What changed?
4. CHECK TRACES → Where is the bottleneck?
5. CHECK DEPENDENCIES → Is something it depends on broken?

NARROW DOWN: System → Service → Component → Function → Line
```

### Step 5: Respond Appropriately

```
Incident response for ANY system:

1. DETECT   → Alert fires or user reports
2. TRIAGE   → How bad is it? Who is affected?
3. MITIGATE → Stop the bleeding (rollback, feature flag, scale)
4. DIAGNOSE → Find the root cause
5. FIX      → Deploy the fix
6. REVIEW   → Post-mortem, prevent recurrence

RULE: Mitigate first, diagnose second. Users don't care why — they want it fixed.
```

## Monitoring Anti-Patterns

- DO NOT alert on symptoms without runbooks
- DO NOT log sensitive data (PII, secrets, tokens)
- DO NOT skip distributed tracing in distributed systems
- DO NOT use logging level inconsistently
- DO NOT ignore log rotation and retention

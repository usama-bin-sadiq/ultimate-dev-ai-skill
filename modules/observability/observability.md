---
name: observability
description: >
  Logging, metrics, tracing, monitoring, alerting, dashboards, APM, distributed tracing, structured logging, SLIs/SLOs.
triggers: [logging, metrics, tracing, monitoring, alerting, dashboard, APM, distributed tracing, observability, SLI, SLO, Prometheus, Grafana, Datadog]
anti_triggers: [code implementation, database schema, API design, Git operations]
last_verified: 2026-09-21
---

# Observability Module

## Core Principles

1. **Three pillars** — logs, metrics, traces
2. **Structured logging** — machine-parseable, consistent format
3. **Actionable alerts** — alert on symptoms, not causes
4. **Correlation** — link logs, metrics, traces together
5. **Cost awareness** — control observability data volume

## Key Areas

### Logging
- Structured JSON logs
- Log levels (error, warn, info, debug)
- Context propagation
- Log aggregation (ELK, Loki)

### Metrics
- Counters, gauges, histograms
- RED metrics (Rate, Errors, Duration)
- USE metrics (Utilization, Saturation, Errors)
- Custom business metrics

### Tracing
- Distributed tracing (Jaeger, Zipkin)
- OpenTelemetry standard
- Span hierarchy
- Context propagation

### Alerting
- SLI/SLO-based alerts
- Alert fatigue prevention
- Escalation policies
- Runbook automation

## Anti-Patterns
- Bad: "Log everything at INFO level" — violates structured logging
- Good: "Use appropriate levels, structure logs" — satisfies structured logging

- Bad: "Alert on every metric" — violates actionable alerts
- Good: "Alert on SLO violations only" — satisfies actionable alerts

## Output Contract
- Logging configurations
- Metric definitions
- Trace configurations
- Alert rules
- Dashboard layouts
---
name: performance
description: >
  Performance engineering: profiling, benchmarking, load testing, optimization, caching, CDN, Core Web Vitals, latency reduction. Technology-agnostic.
triggers: [performance, profiling, benchmark, load test, optimization, latency, throughput, memory, CPU, Core Web Vitals, speed]
anti_triggers: [database schema, API design, Git operations, CI/CD pipeline]
last_verified: 2026-09-21
---

# Performance Engineering Module (pattern-based)

## Core Principles (technology-agnostic)

1. **Measure first** — profile before optimizing
2. **Budget-driven** — set performance budgets, enforce them
3. **User-centric** — optimize for perceived performance
4. **Iterative** — continuous measurement and improvement
5. **Trade-offs** — optimize hot paths, ignore cold paths

## Key Patterns

### Profiling Patterns
- CPU profiling (flame graphs)
- Memory profiling (heap snapshots)
- I/O profiling (network, disk)
- Rendering profiling (layout, paint, composite)
- Database query profiling

### Optimization Patterns
- Lazy loading (code, images, components)
- Code splitting (route, component)
- Tree shaking (dead code elimination)
- Bundle analysis and optimization
- Image optimization (formats, sizes, lazy)

### Caching Patterns
- Browser cache (HTTP headers)
- CDN cache (edge caching)
- Application cache (in-memory, distributed)
- Database cache (query cache, materialized views)
- Service worker cache

### Load Testing Patterns
- Baseline measurement
- Stress testing (beyond capacity)
- Soak testing (sustained load)
- Spike testing (sudden bursts)
- Distributed load generation

### Monitoring Patterns
- Real User Monitoring (RUM)
- Synthetic monitoring
- Apdex score
- Percentile tracking (p50, p95, p99)
- Alerting on regressions

## Anti-Patterns
- Bad: "Optimize without measuring" — violates measure first
- Good: "Profile, identify bottleneck, optimize" — satisfies measure first

- Bad: "Premature optimization" — violates budget-driven
- Good: "Set budgets, optimize only when exceeded" — satisfies budget-driven

## Output Contract
- Performance budgets
- Profiling reports
- Optimization recommendations
- Load test results
- Monitoring dashboards
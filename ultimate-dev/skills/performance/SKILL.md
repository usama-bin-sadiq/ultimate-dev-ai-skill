---
name: performance
description: >
  Meta-cognitive skill for performance. Teaches HOW to think about performance
  in ANY system — regardless of language, framework, or platform.
triggers: [performance, optimization, slow, bottleneck, latency, speed, memory, bundle]
provides: performance_ability
---

# Performance Skill — Optimize Anything

## Purpose

An **ability**. Performance is measurement, not guessing. This skill teaches you
how to think about performance in ANY system — not just specific profilers.

## The Ability

```
Given any system to optimize, you can:
1. Measure before optimizing (establish baseline)
2. Find the REAL bottleneck (not the assumed one)
3. Optimize the biggest bottleneck first
4. Verify the improvement (measure after)
5. Know when to stop (diminishing returns)
```

## How to Optimize ANYTHING

### Step 1: Measure First, Always

```
Before optimizing ANYTHING:
1. What is the current performance? (baseline)
2. What is the target? (goal)
3. What metric matters? (latency, throughput, memory, bundle size)
4. Where is the bottleneck? (measure, don't guess)

RULE: If you haven't measured, you're guessing.
```

### Step 2: Find the Real Bottleneck

```
Common bottlenecks by system type:

WEB API:
  → Database queries (N+1, missing indexes)
  → Network calls (external APIs, microservices)
  → Serialization (JSON parsing, XML)
  → Memory (large payloads, leaks)

WEB UI:
  → Bundle size (large JS bundles)
  → Render (large DOM, expensive calculations)
  → Network (multiple requests, large assets)
  → Memory (leaks, large state)

DATA PIPELINE:
  → I/O (disk, network)
  → CPU (complex transformations)
  → Memory (large datasets)
  → Shuffle (data redistribution)

MOBILE:
  → Main thread (blocking operations)
  → Network (slow connections)
  → Memory (limited device memory)
  → Battery (background processing)
```

### Step 3: Optimize the Biggest Bottleneck

```
Optimization priority:
  1. Algorithm (O(n²) → O(n log n) beats any micro-optimization)
  2. Architecture (caching, lazy loading, async)
  3. I/O (batch operations, reduce network calls)
  4. Memory (reduce allocations, reuse objects)
  5. Micro-optimizations (last resort)

RULE: Don't optimize what isn't slow.
```

### Step 4: Verify the Improvement

```
After optimizing:
1. Run the same benchmark as before
2. Compare before/after numbers
3. Check for regressions in other areas
4. Test under realistic load
5. Monitor in production

IF no improvement:
  → You optimized the wrong thing
  → Go back to Step 2
```

### Step 5: Know When to Stop

```
Performance optimization has diminishing returns:

  0% → 50%: Usually easy (big wins)
  50% → 80%: Moderate effort
  80% → 95%: Hard work
  95% → 99%: Extreme effort
  99% → 100%: Impossible (or not worth it)

RULE: Stop when the cost of optimization exceeds the benefit.
```

## Performance Anti-Patterns

- DO NOT optimize without measuring first
- DO NOT prematurely optimize
- DO NOT sacrifice readability for micro-optimizations
- DO NOT ignore real user metrics (synthetic ≠ real)
- DO cache thoughtfully (invalidation is hard)

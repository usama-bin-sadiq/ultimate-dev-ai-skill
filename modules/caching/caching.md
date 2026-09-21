---
name: caching
description: >
  Caching strategies, cache invalidation, CDN configuration, distributed caching, browser caching, application-level caching. Works with ANY caching technology.
triggers: [cache, caching, cache invalidation, distributed cache, browser cache, application cache, CDN, cache strategy]
anti_triggers: [database queries, API design, frontend UI, Git operations]
last_verified: 2026-09-21
---

# Caching Module

## Core Principles (technology-agnostic)

1. **Cache invalidation** — harder than caching itself, design upfront
2. **Cache hierarchy** — browser → CDN → application → database
3. **TTL strategy** — balance freshness vs performance
4. **Cache warming** — pre-populate for predictable loads
5. **Monitoring** — hit rates, miss rates, memory usage

## Key Patterns

### Cache Layers
- Browser cache (HTTP headers)
- CDN cache (any provider)
- Application cache (in-memory, distributed)
- Database cache (query cache, materialized views)

### Invalidation Strategies
- Time-based (TTL)
- Event-based (write-through, write-behind)
- Manual invalidation
- Version-based

### Any Technology
- In-memory (local cache, process-level)
- Distributed (Redis, Memcached, DynamoDB)
- Managed (CloudFlare, Fastly, CloudFront)
- Application-level (LRU, LFU, custom)

## Anti-Patterns
- Bad: "Cache everything forever" — violates cache invalidation
- Good: "Design TTL based on data freshness requirements" — satisfies invalidation

- Bad: "No cache monitoring" — violates monitoring principle
- Good: "Track hit rates and alert on anomalies" — satisfies monitoring

## Output Contract
- Caching architecture diagrams
- Cache configurations (generic)
- Invalidation logic
- Monitoring dashboards
- Performance benchmarks
---
name: database
description: >
  Database design, schema patterns, query optimization, indexing strategies, migrations, data modeling. Works with ANY database technology.
triggers: [schema, table, query, index, migration, ORM, SQL, NoSQL, data model, partition, replication, connection pool, slow query, database]
anti_triggers: [API endpoint, server logic, frontend UI, CI/CD pipeline, Docker build]
last_verified: 2026-09-21
---

# Database Specialist (pattern-based)

## Core Principles (technology-agnostic)

1. **Schema design** — normalize for integrity, denormalize for performance
2. **Indexing strategy** — indexes accelerate reads, slow writes
3. **Query optimization** — measure, don't guess
4. **Data integrity** — constraints, transactions, validation
5. **Migration safety** — reversible, zero-downtime migrations

## Key Patterns

### Schema Patterns
- Third normal form (3NF)
- Star/snowflake schema (analytics)
- Event sourcing schema
- Document embedding vs referencing
- Time-series data modeling

### Index Patterns
- B-tree for range queries
- Hash for equality lookups
- Composite indexes for multi-column queries
- Partial indexes for filtered queries
- Covering indexes for index-only scans

### Query Patterns
- EXPLAIN/ANALYZE for query plans
- Connection pooling
- Read replicas for scaling
- Batch operations
- Pagination (cursor vs offset)

### Migration Patterns
- Forward-only migrations
- Expand-contract pattern
- Blue-green deployments
- Data migration strategies
- Rollback procedures

### Performance Patterns
- Query caching
- Materialized views
- Partitioning (range, hash, list)
- Connection pooling
- Batch inserts

## Anti-Patterns
- Bad: "Add index for every query" — violates indexing strategy
- Good: "Analyze query patterns, add targeted indexes" — satisfies indexing strategy

- Bad: "N+1 queries in loops" — violates query optimization
- Good: "Batch queries, use JOINs or eager loading" — satisfies query optimization

## Output Contract
- Schema diagrams
- Index recommendations
- Query optimizations
- Migration scripts
- Performance benchmarks
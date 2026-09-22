---
name: data-skill
description: >
  Meta-cognitive skill for data work. Teaches HOW to think about data
  — modeling, storage, transformation, and access — regardless of specific
  database, format, or tool.
triggers: [data, storage, schema, model, query, transform, pipeline, migration]
provides: data_ability
---

# Data Skill — Work with Any Data

## Purpose

An **ability**. Data work is about shape, relationships, and access patterns. This
skill teaches you how to think about data for ANY system — not just specific databases.

## The Ability

```
Given any data problem, you can:
1. Identify the shape and relationships of the data
2. Choose the right storage for the access pattern
3. Design schemas that support the queries
4. Transform data safely and efficiently
5. Protect data integrity and privacy
```

## How to Work with ANY Data

### Step 1: Understand the Data Shape

```
Before choosing any tool, answer:
1. What is the data? (entities, attributes, relationships)
2. How does it relate? (1:1, 1:N, N:M, hierarchical, graph)
3. What queries will be run? (read patterns)
4. How much data? (current AND expected)
5. What is the write pattern? (bulk, streaming, transactional)
6. What is the consistency requirement? (strong, eventual, none)
```

### Step 2: Match Shape to Storage

```
Data Shape              | Best Storage Pattern
------------------------|-------------------------------------------
Structured, relational  | Relational DB (strong consistency)
Document, flexible      | Document DB (schema flexibility)
Key-value, cache        | Key-value store (speed)
Time-series             | Time-series DB (temporal queries)
Graph, relationships    | Graph DB (relationship traversal)
Search, text            | Search engine (text relevance)
Large analytical        | Columnar store (analytics)
Streaming               | Message queue (event processing)
```

### Step 3: Design for Queries

```
RULE: Design schema from queries, not from data shape.

1. What questions will be asked?
2. What data is needed for each question?
3. How often will each question be asked?
4. What indexes support those queries?
5. What are the write vs read trade-offs?
```

### Step 4: Transform Safely

```
For ANY data transformation:
1. Validate input data (don't trust it)
2. Handle missing/null values explicitly
3. Preserve original data (immutable transformations)
4. Log transformations for audit
5. Test with edge cases (empty, null, huge, malformed)
```

### Step 5: Protect Integrity

```
Data integrity principles:
- VALIDATION   → Reject bad data at the boundary
- CONSTRAINTS  → Enforce rules at the storage level
- TRANSACTIONS → Group related changes atomically
- BACKUPS      → Verify you can restore
- AUDIT        → Track who changed what and when
```

## Data Anti-Patterns

- DO NOT choose storage before understanding access patterns
- DO NOT skip indexes on frequently queried columns
- DO NOT use ORM for complex queries
- DO NOT store derived data without clear need
- DO NOT skip backup/restore testing

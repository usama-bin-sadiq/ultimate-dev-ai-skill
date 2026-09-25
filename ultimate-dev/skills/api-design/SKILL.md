---
name: api-design
description: >
  Meta-cognitive skill for API design. Teaches HOW to design interfaces
  between systems — regardless of protocol, format, or technology.
triggers: [api, endpoint, contract, interface, protocol, endpoint, schema, openapi]
provides: api_design_ability
---

# API Design Skill — Connect Anything

## Purpose

An **ability**. API design is about contracts between systems. This skill teaches you
how to design interfaces for ANY protocol — not just REST or GraphQL.

## The Ability

```
Given any systems to connect, you can:
1. Identify what needs to be communicated
2. Design the contract (what goes in, what comes out)
3. Choose the right protocol for the use case
4. Version without breaking existing consumers
5. Document the contract clearly
```

## How to Design ANY API

### Step 1: Understand the Contract

```
Before designing any API, answer:
1. Who is the consumer? (browser, mobile, service, batch)
2. What data flows? (request/response, streaming, events)
3. What are the constraints? (latency, bandwidth, security)
4. What is the relationship? (synchronous, async, one-shot, ongoing)
```

### Step 2: Choose the Communication Pattern

```
Pattern              | When to Use                        | Trade-off
---------------------|------------------------------------|------------------
Request/Response     | Simple, synchronous operations     | Tight coupling
Publish/Subscribe    | Decoupled, broadcast events        | Eventual consistency
Streaming            | Real-time data flow                | Connection management
Batch                | Bulk data processing               | Delayed results
RPC                  | Direct function calls across network | Language coupling
```

### Step 3: Design the Contract

```
For ANY API, define:

1. RESOURCES/ENTITIES  → What things exist
2. OPERATIONS          → What you can do with them
3. DATA SHAPES         → What goes in and out
4. ERRORS              → What can go wrong and how to tell
5. AUTH                → Who can do what
6. VERSIONING          → How to change without breaking
7. RATE LIMITS         → How much is too much
```

### Step 4: Error Design

```
For ANY API, errors should be:
- Machine-readable (error codes, not just messages)
- Human-readable (descriptive messages)
- Actionable (what the consumer should do)
- Consistent (same format everywhere)

Error hierarchy:
  4xx → Consumer error (bad input, unauthorized, not found)
  5xx → Server error (internal failure, timeout, overloaded)
```

### Step 5: Version Without Breaking

```
Non-breaking changes:
  ✓ Adding new fields
  ✓ Adding new endpoints
  ✓ Adding new optional parameters

Breaking changes:
  ✗ Removing fields
  ✗ Renaming fields
  ✗ Changing field types
  ✗ Changing error codes

Strategy: Add first, deprecate later, remove after migration period.
```

## API Design Anti-Patterns

- DO NOT design APIs without considering the consumer
- DO NOT skip error format standardization
- DO NOT ignore versioning from day one
- DO NOT create chatty APIs (too many small calls)
- DO NOT skip rate limiting

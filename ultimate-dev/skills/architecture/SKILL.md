---
name: architecture
description: >
  Meta-cognitive skill for architecture. Teaches HOW to design systems,
  make trade-offs, and document decisions — regardless of technology stack.
triggers: [architecture, system design, trade-off, scalability, design, structure, organize]
provides: architecture_ability
---

# Architecture Skill — Design Anything

## Purpose

An **ability**. Architecture is decision-making under constraints. This skill
teaches you how to design ANY system — not just specific patterns.

## The Ability

```
Given a system to design, you can:
1. Identify the real constraints (not assumed ones)
2. Choose the simplest solution that works
3. Document decisions and their trade-offs
4. Design for change, not for perfection
5. Know when "good enough" is actually good enough
```

## How to Design ANYTHING

### Step 1: Understand the Real Constraints

```
Before designing anything, answer:
1. What is the actual problem? (not the requested solution)
2. Who are the users? (and what do they actually need)
3. What is the scale? (current AND expected)
4. What is the budget? (time, money, people)
5. What is the team's capability? (skills, experience)
6. What are the non-functional requirements? (latency, availability, security)
```

### Step 2: Choose the Simplest Solution

```
Design Complexity Ladder:
  1. Monolith          → Start here unless you have a reason not to
  2. Modular monolith  → When you need separation without deployment complexity
  3. Service-oriented  → When team size demands independent deployment
  4. Microservices     → When scale demands independent scaling
  5. Event-driven      → When async workflows and loose coupling are critical

RULE: Don't jump to step 5 when step 1 works.
```

### Step 3: The Decision Record

For EVERY significant decision:

```markdown
# ADR-NNN: [Decision Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
[What is the issue? What constraints exist?]

## Decision
[What did we decide?]

## Alternatives Considered
1. [Option A] — [pros/cons]
2. [Option B] — [pros/cons]

## Consequences
### Positive
- [What we gain]

### Negative
- [What we lose / trade-off]

### Risks
- [What could go wrong + mitigation]
```

### Step 4: Design for Change

```
Principles:
1. SEPARATION    → Each component has one reason to change
2. ABSTRACTION   → Depend on interfaces, not implementations
3. CONFIGURATION → Make behavior changeable without code changes
4. EXTENSIBILITY → Design points for future modification
5. OBSERVABILITY → Design in monitoring from day one
```

### Step 5: Know When "Good Enough" Is Enough

```
PERFECT is the enemy of GOOD ENOUGH.

Ask:
- Does this solution meet the actual requirements?
- Will this scale for the next 2-3x growth?
- Can the team maintain this?
- Is the complexity justified by the benefit?

If YES to all → ship it and iterate.
```

## Operating Contract

- **Inputs:** requirements, constraints, quality attributes, current state, and evidence.
- **Output:** options, decision, trade-offs, consequences, risks, and validation plan.
- **Verification:** check the decision against acceptance criteria and operational limits.
- **When not to use:** do not design a solution before the problem and constraints are clear.

## Architecture Anti-Patterns

- DO NOT choose architecture before understanding requirements
- DO NOT copy patterns without understanding trade-offs
- DO NOT skip documenting decisions
- DO NOT ignore operational complexity
- DO NOT design for scale you don't have

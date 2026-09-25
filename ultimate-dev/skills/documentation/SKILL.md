---
name: documentation
description: >
  Meta-cognitive skill for documentation. Teaches HOW to communicate
  technical information clearly — regardless of audience or format.
triggers: [documentation, docs, readme, write, explain, communicate, document, spec]
provides: documentation_ability
---

# Documentation Skill — Communicate Anything

## Purpose

An **ability**. Documentation is communication, not writing. This skill teaches you
how to explain ANY technical concept — regardless of audience or format.

## The Ability

```
Given anything to document, you can:
1. Identify who needs to know and what they need to know
2. Choose the right format for the audience
3. Write clearly and concisely
4. Show instead of telling (examples > descriptions)
5. Keep documentation useful and up-to-date
```

## How to Document ANYTHING

### Step 1: Know Your Audience

```
WHO is reading this?
  → Developer? (technical details, code examples)
  → Manager?  (summary, business impact, timeline)
  → User?     (how-to, examples, troubleshooting)
  → Ops?      (runbook, commands, escalation)
  → New hire? (context, why, how things work)

WHAT do they need?
  → Quick answer? (FAQ, cheat sheet)
  → Deep understanding? (architecture doc, ADR)
  → Step-by-step? (tutorial, runbook)
  → Reference? (API docs, config reference)
```

### Step 2: Choose the Right Format

```
README              → What it is, how to start
Tutorial            → Step-by-step learning
How-to Guide        → Task-oriented instructions
Reference           → Complete, accurate details
Architecture Doc    → Design decisions and trade-offs
Runbook             → How to handle incidents
API Docs            → Endpoints, parameters, responses
Changelog           → What changed and why
```

### Step 3: Write Clearly

```
PRINCIPLES:
  1. Be concise (short sentences, no filler)
  2. Show, don't tell (code examples > descriptions)
  3. Structure clearly (headers, lists, tables)
  4. Use active voice ("Run the command" not "The command should be run")
  5. Define terms before using them
  6. Keep paragraphs short (3-5 sentences max)

AVOID:
  - Walls of text
  - Jargon without definition
  - TODOs in published docs
  - Documenting the obvious
```

### Step 4: Show, Don't Tell

```
BAD:
  "The system uses a microservices architecture with event-driven
   communication between services via a message broker."

GOOD:
  ```
  User Service → [Order Created Event] → Order Service
                                          ↓
                              [Payment Processed] → Notification Service
  ```
```

### Step 5: Keep It Useful

```
Documentation that lives:
  → Lives close to the code
  → Is tested (examples that run)
  → Is versioned (matches the code)
  → Is reviewed (like code)
  → Is updated when code changes

Documentation that dies:
  → Lives in a wiki no one visits
  → Has never been tested
  → Is out of date
  → Was written once and forgotten
```

## Operating Contract

- **Inputs:** audience, source material, task context, format, and review owner.
- **Output:** accurate, concise documentation with examples, provenance, and next actions.
- **Verification:** check links/examples and distinguish verified behavior from proposals.
- **When not to use:** do not invent policy, API behavior, or company facts.

## Documentation Anti-Patterns

- DO NOT write walls of text
- DO NOT skip code examples
- DO NOT leave TODOs in published docs
- DO NOT document obvious things
- DO keep documentation close to the code

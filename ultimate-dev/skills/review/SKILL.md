---
name: review-skill
description: >
  Meta-cognitive skill for review. Teaches HOW to evaluate ANY code,
  design, or decision — regardless of language, framework, or domain.
triggers: [review, audit, feedback, evaluate, assess, inspect, check, examine]
provides: review_ability
---

# Review Skill — Evaluate Anything

## Purpose

An **ability**. Reviewing is critical thinking applied to code/design/decisions.
This skill teaches you how to evaluate ANYthing — not just code diffs.

## The Ability

```
Given anything to review, you can:
1. Identify what matters most (correctness > style)
2. Find the real issues (not just nitpicks)
3. Give feedback that helps (actionable, specific)
4. Know what's a blocker vs what's a suggestion
5. Recognize when something is "good enough"
```

## How to Review ANYTHING

### Step 1: Understand the Intent

Before reviewing, answer:
```
1. What was the goal of this change?
2. What problem does it solve?
3. What are the constraints?
4. Who is the audience?
```

### Step 2: Review in Order of Importance

```
1. CORRECTNESS  → Does it do what it claims?
2. SECURITY     → Can it be exploited?
3. PERFORMANCE  → Will it scale?
4. MAINTAINABILITY → Can others understand it?
5. STYLE        → Does it follow conventions?
```

### Step 3: The Universal Review Checklist

For ANY code/design/decision:

```
CORRECTNESS:
  □ Does it solve the stated problem?
  □ Are edge cases handled?
  □ Are error conditions handled?
  □ Is the logic correct?
  □ Are there off-by-one errors?

SECURITY:
  □ Is input validated?
  □ Are queries parameterized?
  □ Are secrets handled properly?
  □ Is authorization checked?
  □ Are there injection vectors?

PERFORMANCE:
  □ Are there N+1 queries?
  □ Is there unnecessary computation?
  □ Are data structures appropriate?
  □ Is there memory leak potential?

MAINTAINABILITY:
  □ Is it readable?
  □ Are names meaningful?
  □ Is there unnecessary complexity?
  □ Are there comments where needed?
  □ Does it follow project conventions?

TESTING:
  □ Are there adequate tests?
  □ Do tests cover edge cases?
  □ Are tests readable?
```

### Step 4: Feedback Format

```
[SEVERITY] Category: Description
File: path/to/file.ext:line
Issue: What is wrong
Suggestion: How to fix it
Example: Code example if helpful

Severity levels:
  blocking  → Must fix before merge
  suggestion → Should consider fixing
  nit       → Nice to have, not blocking
  question  → Seeking understanding
```

### Step 5: Know When to Stop

```
DO block on:  Security, data loss, broken functionality, unclear intent
DON'T block on: Style preferences, naming opinions, minor formatting
DO suggest:   Better patterns, clearer names, missing tests
DON'T suggest: Rewriting things that work, over-engineering
```

## Review Anti-Patterns

- DO NOT review without reading the full change
- DO NOT nitpick style when linter should catch it
- DO NOT block on personal preferences
- DO NOT skip security checks
- DO NOT give vague feedback ("this is confusing")

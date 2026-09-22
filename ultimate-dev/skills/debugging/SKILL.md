---
name: debugging-skill
description: >
  Meta-cognitive skill for debugging. Teaches HOW to investigate and fix
  problems in ANY system — regardless of language, framework, or technology.
triggers: [debug, debugging, bug, error, crash, failure, investigate, troubleshoot, fix]
provides: debugging_ability
---

# Debugging Skill — Fix Anything

## Purpose

An **ability**. Debugging is systematic thinking, not random guessing. This skill
teaches you how to find and fix problems in ANY system — not just specific tools.

## The Ability

```
Given any problem to debug, you can:
1. Reproduce it consistently (or understand why you can't)
2. Isolate the root cause (not just the symptom)
3. Form and test hypotheses systematically
4. Fix the root cause (not just patch the symptom)
5. Prevent it from happening again
```

## How to Debug ANYTHING

### Step 1: Reproduce First

```
Before fixing anything:
1. Can you reproduce it consistently?
2. What are the exact steps?
3. What environment does it happen in?
4. Is it intermittent or deterministic?
5. When did it start happening?

IF you can't reproduce:
  → Check logs, traces, monitoring
  → Ask: what changed recently?
  → Try: different environments, inputs, configurations
```

### Step 2: Isolate the Scope

```
Binary search for the problem:

1. What is the EXPECTED behavior?
2. What is the ACTUAL behavior?
3. Where does the behavior diverge?
4. What is the MINIMAL reproduction?

Narrow down:
  → Is it the frontend or backend?
  → Is it the code or the config?
  → Is it this function or that function?
  → Is it this input or that input?
```

### Step 3: Hypothesize Systematically

```
For ANY bug, generate hypotheses:

1. What CHANGED recently? (code, config, dependencies, data)
2. What is the SYMPTOM? (error message, wrong output, crash)
3. What are the POSSIBLE CAUSES? (list 3-5)
4. Which is MOST LIKELY given the symptoms?
5. What EVIDENCE would confirm each?

Then TEST each hypothesis (don't just guess).
```

### Step 4: Fix the Root Cause

```
Types of fixes:
  BAND-AID:   Suppress the symptom (temporarily)
  PATCH:      Fix this specific instance
  ROOT FIX:   Fix the underlying cause
  PREVENTION: Add checks to prevent this class of bug

ALWAYS aim for ROOT FIX + PREVENTION.
```

### Step 5: Prevent Recurrence

```
After fixing:
1. Add a TEST that would have caught this
2. Add MONITORING if it could happen again
3. Check if the PATTERN exists elsewhere
4. DOCUMENT the root cause and fix
5. Consider if the DESIGN should change
```

## Debugging Mental Models

```
RUBBER DUCK:  Explain the problem out loud (or to a rubber duck)
BINARY SEARCH: Split the problem space in half repeatedly
5 WHYS:       Keep asking "why?" until you reach the root cause
CHANGE LOG:   What changed since it last worked?
MINIMAL REPRO: Smallest possible case that triggers the bug
```

## Debugging Anti-Patterns

- DO NOT guess without evidence
- DO NOT fix symptoms without understanding root cause
- DO NOT skip adding regression tests
- DO NOT ignore logs and traces
- DO check if the bug exists elsewhere

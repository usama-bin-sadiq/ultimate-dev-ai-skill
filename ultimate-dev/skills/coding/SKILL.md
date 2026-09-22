---
name: coding-skill
description: >
  Meta-cognitive skill for coding. Teaches HOW to implement solutions
  in ANY language, framework, or paradigm — by understanding patterns,
  not memorizing syntax.
triggers: [implement, code, build, create, write, refactor, develop, feature, program]
provides: coding_ability
---

# Coding Skill — Build Anything

## Purpose

An **ability**. When you need to write code in an unfamiliar language or framework,
this skill teaches you how to transfer what you already know to any new context.

## The Ability

```
Given a coding task in any language/framework, you can:
1. Map your existing knowledge to the new context
2. Find the idiomatic way to do things (not the translated way)
3. Read and learn from existing code in the codebase
4. Implement solutions that fit the project's patterns
5. Verify your work without relying on memory alone
```

## How to Code in ANYTHING

### Step 1: Find the Equivalents

Every language has the same concepts, different names:

```
Concept        | Example Languages
---------------|------------------
Variable       | let (JS), var (Go), val (Kotlin), def (Python)
Function       | function (JS), func (Go), fun (Kotlin), def (Python)
Class          | class (JS/Python/Kotlin), struct (Go/Rust)
Interface      | interface (TS/Kotlin), trait (Rust), protocol (Swift)
Error handling | try/catch (JS), error return (Go), Result (Rust)
Async          | async/await (JS/Python), goroutines (Go), threads (Rust)
Module         | import (JS/Python), use (Rust), include (Ruby)
```

### Step 2: Read Before Writing

Before writing any code in a new context:

```
1. Read 3-5 existing files that do similar things
2. Note the patterns: naming, structure, error handling
3. Copy the style exactly (don't improvise)
4. Only deviate if you have a documented reason
```

### Step 3: Think in Patterns, Not Syntax

```
Every language has:
- Loops (for, while, map, filter, reduce)
- Conditionals (if/else, switch/match)
- Data structures (array, map/dict, set)
- Error handling (try, result, error return)
- Concurrency (threads, async, actors)
- Module system (imports, exports)

Learn the PATTERN, then look up the SYNTAX.
```

### Step 4: Verify Without Memory

```
When unsure:
1. Check the language docs (don't guess)
2. Write a small test and run it
3. Look at how existing code handles it
4. Use the compiler/interpreter as a teacher
5. Check for linting errors
```

### Step 5: Refactor with Understanding

```
Before refactoring ANY codebase:
1. Understand the existing architecture
2. Identify the actual problem (not just the symptom)
3. Find the smallest change that fixes it
4. Run all existing tests
5. Check for blast radius (callers, dependents)
```

## Language Transfer Matrix

```
If you know:     → You already understand:
JavaScript        → event loop, closures, prototypes, async
Python            → duck typing, generators, context managers
Java              → OOP, interfaces, strong typing, JVM
Go                → goroutines, channels, interfaces, simplicity
Rust              → ownership, borrowing, lifetimes, traits
Kotlin            → null safety, coroutines, extension functions
Swift             → optionals, protocols, value types
C++               → manual memory, templates, RAII
```

## Anti-Patterns

- DO NOT translate code from one language to another (think in patterns)
- DO NOT use syntax you don't understand
- DO NOT skip reading existing code before writing new code
- DO NOT guess when you can check
- DO NOT refactor without understanding the full context

---
name: self-evolve-skill
description: >
  Meta-meta-skill. When the system encounters a task with no matching sub-skill,
  this skill teaches HOW to: research the unknown domain, execute the task,
  then auto-generate and persist a NEW sub-skill for future use.
triggers: [unknown, no match, not found, unfamiliar, new domain, learn, evolve]
provides: self_evolution_pattern
---

# Self-Evolution Skill — The Learning Engine

## Purpose

This is the **brain** of the skill system. When no sub-skill matches a task,
this skill kicks in to:
1. Research how to do it
2. Execute the task
3. Generate a NEW sub-skill from what was learned
4. Persist it so it never needs to research again

## The Self-Evolution Pattern

```
┌─────────────────────────────────────────────────┐
│  1. DETECT   → No matching sub-skill found?      │
│  2. SEARCH   → Research the unknown domain       │
│  3. EXECUTE  → Do the task with gathered knowledge│
│  4. LEARN    → Extract patterns from execution    │
│  5. PERSIST  → Generate & save new sub-skill      │
│  6. VERIFY   → Next time, use the saved skill     │
└─────────────────────────────────────────────────┘
```

## Step 1: Detection

When a task arrives, check existing sub-skills:

```
skills/
├── research/SKILL.md
├── coding/SKILL.md
├── testing/SKILL.md
├── review/SKILL.md
├── architecture/SKILL.md
├── security/SKILL.md
├── devops/SKILL.md
├── debugging/SKILL.md
├── documentation/SKILL.md
├── performance/SKILL.md
├── api-design/SKILL.md
├── data/SKILL.md
├── monitoring/SKILL.md
├── migration/SKILL.md
├── ai-ml/SKILL.md
├── mobile/SKILL.md
├── compliance/SKILL.md
├── accessibility/SKILL.md
├── integration/SKILL.md
├── edge-computing/SKILL.md
└── _learned/              <- Auto-generated skills live here
    ├── [domain-1]/SKILL.md
    ├── [domain-2]/SKILL.md
    └── ...
```

**Match found?** → Load the sub-skill and execute.
**No match?** → Trigger self-evolution.

## Step 2: Research the Unknown

```bash
# What to research:
1. What is this domain/technology?
2. What are the best practices?
3. What are the common patterns?
4. What are the tools/frameworks?
5. What are the pitfalls?
```

### Research Sources (priority order)
1. Official documentation (highest authority)
2. GitHub repos with high stars (community validated)
3. Recent blog posts from known authors
4. Stack Overflow (practical validation)
5. Conference talks (cutting edge)

## Step 3: Execute the Task

Apply gathered knowledge. Record:
- What worked
- What didn't
- What patterns emerged
- What would be different next time

## Step 4: Learn — Extract Patterns

From the execution, extract:

```yaml
# Pattern extraction template
domain: "[detected domain]"
technology: "[specific technology]"
patterns:
  - name: "[pattern name]"
    when: "[when to use]"
    how: "[how to implement]"
    pitfalls: "[what to avoid]"
tools:
  - name: "[tool name]"
    purpose: "[what it does]"
    install: "[how to install]"
conventions:
  - "[naming convention]"
  - "[file structure]"
  - "[error handling pattern]"
```

## Step 5: Persist — Auto-Generate Sub-Skill

```yaml
---
name: "[domain]-[technology]-learned"
description: >
  Auto-generated sub-skill for [domain]/[technology].
  Created from successful execution on [date].
  Source: self-evolution (no matching skill existed).
triggers: [domain-specific triggers extracted]
auto_generated: true
generated_date: "[date]"
source_task: "[original task description]"
confidence: [0.0-1.0]  # increases with each successful use
uses: [number of times successfully used]
extends: [parent skill if applicable]
---

# [Domain] / [Technology] — Auto-Generated Skill

## Context
[What was the original task that triggered this skill creation]

## Patterns
[Extracted patterns from execution]

## Tools & Setup
[What tools are needed and how to configure them]

## Common Tasks
[Task → pattern mappings]

## Pitfalls
[What to avoid, learned from experience]

## Evolution Log
| Date | Task | Outcome | Confidence Change |
|------|------|---------|-------------------|
| [date] | [task] | success/fail | +0.1 / -0.1 |
```

## Step 6: Verification

Next time the same domain appears:
1. Load the auto-generated skill
2. Execute using the learned patterns
3. If successful → confidence +0.1
4. If failed → confidence -0.1, re-research if confidence < 0.3
5. If confidence reaches 1.0 → consider promoting to permanent sub-skill

## Confidence Lifecycle

```
0.0 → 0.3: Experimental (re-research on failure)
0.3 → 0.6: Growing (use with caution, verify results)
0.6 → 0.8: Reliable (use confidently)
0.8 → 1.0: Mature (promote to permanent sub-skill)
```

## File: `_learned/_index.yaml`

```yaml
# Auto-generated skill index
# This file is maintained by the self-evolution system

skills:
  - name: "[domain]-[tech]"
    path: "_learned/[domain]-[tech]/SKILL.md"
    confidence: 0.5
    uses: 3
    last_used: "2026-09-22"
    status: growing
```

## Anti-Patterns

- DO NOT create a new skill for every tiny variation
- DO NOT skip the research step (guessing = bad patterns)
- DO NOT persist patterns that failed
- DO NOT let confidence stay frozen (update on every use)
- DO consolidate similar auto-generated skills into one

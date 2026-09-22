---
name: migration-skill
description: >
  Meta-cognitive skill for migrations. Teaches HOW to transition between
  any two states — code, data, infrastructure, or processes — safely.
triggers: [migration, migrate, upgrade, transition, refactor, modernize, port, move]
provides: migration_ability
---

# Migration Skill — Transition Anything

## Purpose

An **ability**. Migration is change management. This skill teaches you how to
transition ANY system from state A to state B — safely and reversibly.

## The Ability

```
Given any migration, you can:
1. Assess the current state and the target state
2. Plan the path between them with rollback at every step
3. Execute incrementally (never all at once)
4. Verify correctness at each step
5. Roll back cleanly if something goes wrong
```

## How to Migrate ANYTHING

### Step 1: Assess the Gap

```
Before migrating anything:
1. What is the CURRENT state? (document it)
2. What is the TARGET state? (define it clearly)
3. What are the DIFFERENCES? (gap analysis)
4. What DEPENDS on the current state? (blast radius)
5. What can BREAK during migration? (risk assessment)
```

### Step 2: Plan the Path

```
Migration strategies (choose by risk):

BIG BANG:
  → Switch everything at once
  → Risk: high, Rollback: hard
  → Use when: small system, low risk, no dependencies

INCREMENTAL:
  → Move piece by piece
  → Risk: medium, Rollback: easy per step
  → Use when: large system, moderate risk

PARALLEL RUN:
  → Run both systems, compare outputs
  → Risk: low, Rollback: instant
  → Use when: critical system, high risk

STRANGLER FIG:
  → Gradually replace pieces, route traffic
  → Risk: low, Rollback: instant
  → Use when: large system, long timeline
```

### Step 3: Execute Safely

```
For EVERY migration step:
1. BACKUP the current state
2. MAKE the change
3. VERIFY the change works
4. MONITOR for issues
5. HAVE a rollback ready

RULE: If you can't roll back, don't migrate.
```

### Step 4: Verify at Every Step

```
Verification checklist:
  □ Data integrity (checksums, counts, samples)
  □ Functionality (existing tests pass)
  □ Performance (no degradation)
  □ Security (no new vulnerabilities)
  □ Compatibility (existing consumers work)
```

### Step 5: Clean Up After

```
After successful migration:
1. Remove old code/infrastructure
2. Update documentation
3. Close migration tickets
4. Document lessons learned
5. Celebrate 🎉
```

## Migration Anti-Patterns

- DO NOT migrate everything at once
- DO NOT skip the rollback plan
- DO NOT migrate without a feature flag
- DO NOT ignore backward compatibility
- DO NOT skip regression testing

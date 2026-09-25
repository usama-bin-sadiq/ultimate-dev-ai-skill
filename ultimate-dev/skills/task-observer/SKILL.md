---
name: task-observer
description: >
  Observation capture for reusable methodology improvements from completed task
  work, without turning every conversation into noise or replacing durable task state.
triggers: [task observer, observation log, reusable workflow correction, skill improvement observation]
provides: task_observation_ability
---

# Task Observer — Evidence-Based Methodology Capture

Use this skill after meaningful work reveals a repeatable methodology signal.
It observes improvements; it does not own task state, checkpoints, evidence,
or recovery. Keep project-local observations outside `.memory/ultimate-dev/`.

## Observe only when

- a correction should change a reusable skill or agent;
- a repeated workflow is not documented;
- a routing rule, contract, or safeguard is missing or stale;
- a simplification or cross-cutting principle is supported by evidence;
- user feedback reveals a repeatable improvement.

Do not observe casual answers, private reasoning, temporary logs, one-off
mistakes, monitoring work, or an explicit request to create a skill. The normal
maintenance path is **log and defer**.

## Minimal record

Append to the project-local `skill-observations/log.md` using the next
sequential number. Preserve the live log and do not renumber existing entries.

```markdown
### Observation N: [short title]

**Status:** OPEN
**Date:** YYYY-MM-DD
**Session context:** [bounded task context]
**Skill:** [existing skill or candidate]
**Type:** open-source | internal
**Phase/Area:** [phase]

**Issue:** [specific reusable problem]
**Suggested improvement:** [scoped change]
**Principle:** [generalizable takeaway]
```

The only normal statuses are `OPEN`, `ACTIONED (YYYY-MM-DD)`, and
`DECLINED (YYYY-MM-DD)`. `last-review-date.txt` records actual review dates;
`never` means no review has run.

## Numbering and concurrency

Read the live log before deciding whether an observation is new. Derive the
next number from the highest `Observation N`, re-read immediately before append,
assert the number is unused, append, then verify it appears exactly once. If a
concurrent writer wins, increment past the collision and verify again.

## Confidentiality

Use `open-source` only for genuinely reusable, non-identifying knowledge. Use
`internal` when practical value depends on private context. Never record
passwords, tokens, API keys, private URLs, client identifiers, hidden reasoning,
or credentials. Generalize private examples instead of copying them.

## Review and action

An observation may be actioned only after a comprehensive review, an explicit
user request, or an urgent correction to a currently failing skill. Do not gate
ordinary work on the review backlog.

## Progressive references

Load `references/observation-protocol.md` before constructing or appending an
observation. Load `references/confidentiality-and-review.md` before classifying
confidentiality or review state. If no observation qualifies, load neither.

## Output contract

```yaml
observations:
  - number: 3
    status: OPEN
    persisted: true
review:
  due: false
  last_review_date: never
  ran: false
action: deferred
```

If nothing qualifies, report `no observations` without modifying the log.
Detailed protocol, examples, and review prompts live in
`references/observation-protocol.md` and
`references/confidentiality-and-review.md`. Do not create a skill, agent, or
dependency from one isolated event.

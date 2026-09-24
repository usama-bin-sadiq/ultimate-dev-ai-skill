---
name: task-observer-skill
description: >
  Meta-cognitive skill for observing task execution. Teaches when to capture
  reusable methodology, how to classify and record observations, numbering and
  status rules, confidentiality and review safeguards, and durable logging
  without replacing task state.
triggers: [task observer, task observation, observe task, methodology observation, skill improvement, observation log]
provides: task_observation_ability
---

# Task Observer Skill

## Purpose

Observe meaningful task work for **reusable methodology improvements** without
turning every conversation into noise.

This skill teaches a durable observation method. A specialized agent may execute
the method, but the agent does not redefine it. The Ultimate-Dev Runtime remains
the owner of task state, checkpoints, evidence, and recovery.

Use the project-local default:

```text
<project-root>/skill-observations/
├── log.md
├── cross-cutting-principles.md
└── last-review-date.txt
```

These files are separate from `.memory/ultimate-dev/tasks/`. Never replace task
state with an observation log.

## When to Observe

Observe when a task produces a reusable signal, such as:

- a correction that should change how a skill or agent behaves;
- a repeated workflow that is not yet documented;
- a missing capability or routing rule;
- a rule that was documented but not enforced;
- a stale assumption, unnecessary complexity, or simplification opportunity;
- a cross-cutting principle that should inform more than one skill.

Also observe user feedback that reveals a repeatable methodology improvement.

## When Not to Observe

Do not create an observation for:

- casual conversation or a simple factual answer;
- a one-off correction with no reusable pattern;
- temporary debugging output or private reasoning;
- a task that has not produced enough evidence;
- a request to monitor systems, metrics, telemetry, alerts, or incidents;
- an explicit request to create or update a skill immediately.

Those cases belong to their normal workflow or to an explicit maintenance task.

## Observation Types

Classify each candidate as one of:

1. **Reusable workflow** — a repeatable multi-step method worth teaching.
2. **Skill improvement** — an existing skill has a gap, stale rule, or failure.
3. **Agent improvement** — an agent's responsibilities or output contract needs
   correction.
4. **Simplification** — a rule, step, or artifact can be removed or made smaller.
5. **Cross-cutting principle** — a general lesson applies to multiple skills.
6. **No observation** — the signal is not reusable or sufficiently evidenced.

Do not create a new skill merely because one unusual task occurred.

## Observation Record

Append observations to the single local `log.md` using the next sequential
number. Every observation must include:

```markdown
### Observation N: [Short descriptive title]

**Status:** OPEN
**Date:** YYYY-MM-DD
**Session context:** [what task was being worked on]
**Skill:** [existing skill name, or "New skill candidate: [working name]"]
**Type:** open-source | internal
**Phase/Area:** [relevant phase or area]

**Issue:** [specific enough to understand later without the conversation]

**Suggested improvement:** [concrete, scoped change]

**Principle:** [the generalizable takeaway]
```

The permitted local statuses are exactly:

- `OPEN` — not yet actioned;
- `ACTIONED (YYYY-MM-DD)` — explicitly applied;
- `DECLINED (YYYY-MM-DD)` — explicitly rejected.

A new record starts with `**Status:** OPEN`. Do not silently invent other
statuses.

## Durable Logging Rules

1. Read the live log before deciding whether an observation is new.
2. Derive the next number from the highest existing `Observation N` header.
3. Re-read the live log immediately before every append.
4. Append only; do not renumber or rewrite unrelated entries.
5. Assert that the proposed number does not already exist.
6. Append the record.
7. Re-read and verify the new number occurs exactly once and required fields
   exist.
8. If another writer wins a race, increment past the collision and verify again.
9. Keep the log append-only during normal observation. Archival or status changes
   require a separate, reviewed mutation procedure.

## Confidentiality

Default to `open-source` only when the observation is genuinely reusable without
identifying a client, employer, private project, credential, domain, or secret.
If practical value depends on private context, use `internal` and keep the
project-specific detail out of the general principle.

Never record:

- passwords, tokens, API keys, private URLs, or credential material;
- client names or identifying project structures in an open-source principle;
- hidden chain-of-thought or private reasoning;
- temporary logs that do not help a future session.

Prefer a generalized `open-source` principle over a traceable private detail.
When uncertain, use `internal` and say why in the issue, without exposing the
secret itself.

## Review and Action

`last-review-date.txt` records the date of the last actual review. `never` means
no review has run.

If the review is due and observations are open, an interactive session may offer
a review in one sentence, then continue the user's task unless they opt in.
Never gate ordinary work on the review backlog.

An observation may be actioned only when:

1. a comprehensive review explicitly selects it;
2. the user explicitly requests the action; or
3. a currently used skill/agent is producing wrong output and an in-session
   correction is necessary.

The normal path is **log and defer**. Do not edit a skill merely because an
observation was recorded.

## Output Contract

At the end of an observation session, report:

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

## Anti-Patterns

- Do not observe every task or every tool call.
- Do not duplicate the agent workflow here.
- Do not persist secrets or private reasoning.
- Do not claim a review ran when it did not.
- Do not use a stale snapshot to rewrite a shared log.
- Do not confuse task state/evidence with methodology observations.
- Do not create a skill, agent, workflow, or dependency from one isolated event.

---
name: planning-execution
description: >
  Design and execute a multi-step plan with dependencies, checkpoints,
  verification gates, recovery decisions, and an auditable task ledger. Use
  for projects, migrations, multi-file changes, delegated work, or any request
  where sequencing and completion evidence matter.
triggers: [plan, implementation plan, project plan, dependencies, checkpoints, execute plan, work breakdown, recovery]
provides: execution_plan
---

# Planning and Execution

Use the smallest plan that makes the work understandable and recoverable. A
plan is not permission to skip discovery, approvals, or verification.

## Method

1. **Confirm the contract** — goal, non-goals, acceptance criteria, risk, and
   evidence are explicit.
2. **Map the work** — list deliverables, dependencies, owners/roles, files or
   systems affected, and rollback/recovery options.
3. **Right-size tasks** — each task should produce an independently reviewable
   outcome and its own verification.
4. **Choose execution structure** — inline, specialist, sequential handoff, or
   parallel only when the work is genuinely independent.
5. **Set checkpoints** — record the baseline, expected artifact, verification
   command, and stop conditions before high-risk work.
6. **Execute and update** — mark progress from the ledger, not from memory;
   replan only the affected portion after failure.
7. **Close with evidence** — compare results to every acceptance criterion and
   report unverified items as `not_run`.

## Plan shape

```yaml
goal: <one sentence>
constraints: [..]
tasks:
  - id: <stable-id>
    outcome: <deliverable>
    depends_on: [..]
    files_or_systems: [..]
    verification: <command or review>
    stop_if: [..]
checkpoints: [..]
rollback: <..>
```

## Boundaries

- Do not create a plan for a trivial atomic task.
- Never claim a task is complete from a worker's report alone.
- Stop for destructive actions, security-sensitive actions, external side
  effects outside the approved scope, or an unresolvable plan defect.

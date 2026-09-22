# Delegation Rules

Rules governing how tasks are delegated between agents.

## When to Delegate

### Always Delegate When:
- The task requires expertise you don't have (e.g., frontend work from a backend agent).
- The task is large enough to benefit from parallel execution.
- The task touches a different domain than your current focus.
- The orchestrator has explicitly assigned you a sub-task.

### Never Delegate When:
- The task is trivial and can be done in under 2 minutes.
- You lack the context to write a meaningful delegation spec.
- The task requires decisions that only you can make.
- Delegating would create a circular dependency.

### Ask First When:
- You're unsure if the task is within your scope.
- The task might conflict with another agent's in-progress work.
- The task requires access to resources you're not sure you can share.

## What to Include in Every Delegation

Every delegation must include:

1. **Clear objective** — One sentence stating what needs to be done.
2. **Context** — Relevant files, background, and why this matters.
3. **Scope boundaries** — What is IN and what is OUT of scope.
4. **Acceptance criteria** — How to know when the task is done.
5. **Verification steps** — How to prove the work is correct.

Optional but recommended:
- Existing patterns to follow
- Technical constraints
- Priority level
- Dependencies on other tasks

## Delegation Format

Use the template from `prompts/delegation.md`. Always follow the structure — it exists to prevent ambiguity.

## Quality Standards

### Good Delegation:
- The receiving agent can start working immediately without asking questions.
- The acceptance criteria are specific and testable.
- The scope is narrow enough to be completed in one session.

### Bad Delegation:
- "Fix the bug" (too vague)
- "Do whatever you think is best" (no criteria)
- "Also refactor the entire module while you're at it" (scope creep)
- No acceptance criteria (how do you know it's done?)

## Tracking Delegated Work

- Assign a unique task_id to every delegation.
- Track status: pending → in_progress → completed/failed.
- Check in at logical milestones for complex tasks.
- Don't micromanage — trust the agent to follow the delegation spec.

## Handling Delegation Failures

When a delegated task fails:

1. Read the failure report carefully.
2. Determine if the failure is due to:
   - Unclear delegation (your fault → rewrite the spec)
   - Agent limitation (reassign to a different agent)
   - External blocker (remove the blocker)
3. Re-delegate with corrected context.
4. If the same task fails twice, escalate to the orchestrator.

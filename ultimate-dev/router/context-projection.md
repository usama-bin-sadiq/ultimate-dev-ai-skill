# Context Projection

Projection keeps the working context small enough to finish the task. It decides
what the current step may see; see `router/progressive-disclosure.md` for how
skill files are discovered in the first place.

## Order of inclusion

1. Task envelope: deliverable, acceptance criteria, constraints, risk.
2. Current stage: objective, `next_action`, stop conditions.
3. Smallest relevant capability slice: one skill, one module, one specialist.
4. Referenced artifacts by pointer, with a one-line summary each.
5. Durable state: `state.json` fields required to resume, nothing more.

## Order of exclusion

- Files not required by the current stage.
- Full transcripts, raw tool output, and duplicated summaries.
- Registry dumps: agents, skills, and modules are metadata first.
- Secrets, credentials, and unnecessary personal data.
- Superseded memory items and stale fixtures.

## Budget discipline

- Replace large content with a reference plus a bounded summary.
- Keep evidence out of context: store it and cite the path.
- When the budget is exceeded, reduce scope detail before dropping acceptance
  criteria, and report the reduction.
- Re-project after each stage; do not carry a stage's full context forward.

## Verification

- The current stage can be completed from the projected context alone.
- Every claim in the projected context points to evidence that still exists.
- A second reader with only this context would reach the same next action.

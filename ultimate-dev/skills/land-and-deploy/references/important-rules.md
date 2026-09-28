<!-- Moved verbatim from land-and-deploy/SKILL.md, the
     'important-rules' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Important Rules

- Never force-push, bypass CI, replay a confirmed merge, or hide missing evidence.
- Auto-detect facts; ask when unknown or when an explicit approval gate applies.
- Poll at 30-second intervals with the stated deadlines and progress messages.
- After merge failures, offer approved rollback when appropriate; never revert a rollback automatically.
- Verify once; `/canary` provides extended monitoring. Rechecks require the user's choice.
- Use `--delete-branch`; reconcile failed cleanup non-destructively with confirmation.

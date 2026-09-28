<!-- Moved verbatim from ship/SKILL.md, the
     'step-14-todos-md-auto-update' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 14: TODOS.md (auto-update)

Persist approved follow-ups, then conservatively mark completed work.

Read `~/.claude/skills/gstack/review/TODOS-format.md` for the canonical format reference (or `review/TODOS-format.md` in a gstack checkout).

**1. Open or create:** Read root `TODOS.md`. An earlier explicit "add a follow-up" choice authorizes its creation with `# TODOS` and `## Completed`. Otherwise, if missing, ask: "Create a component/priority-organized TODOS.md?" Options: A) Create now, B) Skip. If B, continue to Step 15 with the outcome in the summary below.

**2. Organization:** Expect component headings, `**Priority:**` P0–P4 fields, and `## Completed` at the bottom. If disorganized, ask: A) Reorganize (recommended), B) Leave as-is. A preserves all content; B continues without restructuring.

**3. Add approved deferrals:**
- Step 2: add the approved distribution follow-up as P1 with the missing pipeline and affected artifact.
- Step 8: add each approved P1 plan deferral with `Deferred from plan: {plan file path}` and the missing work.
- Step 5: retain P0 test-failure entries already written; deduplicate by failure and source, adding missing approved entries with error output and branch.
Never turn dropped scope into TODOs or invent unapproved follow-ups. Reuse matching existing entries rather than duplicating them.

**4. Detect completed TODOs:** Match titles, files, and behavior against `git diff origin/<base>`, untracked files from status, and `git log origin/<base>..HEAD --oneline`. Only clear evidence earns completion; leave uncertain items open. Move completed items to `## Completed` and append `**Completed:** vX.Y.Z (YYYY-MM-DD)`.

**5. Save the summary:** Report added/deferred items, items marked complete, remaining count, and any creation/reorganization. If creation was declined or a write fails, warn and retain the unpersisted follow-ups in the Step 19 PR summary; never claim they were saved. A TODO write failure remains non-blocking.

---

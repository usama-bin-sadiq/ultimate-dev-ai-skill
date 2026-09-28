<!-- Moved verbatim from autoplan/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Phase 0: Intake + Restore Point

### Step 1: Capture restore point

Absolute paths: SOURCE_PLAN (input), ACTIVE_PLAN (harness-assigned plan, else SOURCE_PLAN).
Save plan amendments and review artifacts to ACTIVE_PLAN.
Send phase announcements and the final approval request in the conversation.
Resolve SNAPSHOT_TOOL once:
```bash

bun -e 'console.log(require("fs").realpathSync(process.argv[1]))' "$HOME/<agent-config-dir>/gstack/bin/gstack-autoplan-snapshot.ts"
```

Fresh external RESTORE_PATH:
```bash
eval "$(~/<agent-config-dir>/gstack/bin/gstack-slug 2>/dev/null)"
eval "$(~/<agent-config-dir>/gstack/bin/gstack-paths)"
mkdir -p "$GSTACK_STATE_ROOT/projects/$SLUG"
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null | tr '/' '-')
DATETIME=$(date +%Y%m%d-%H%M%S)
echo "RESTORE_PATH=$GSTACK_STATE_ROOT/projects/$SLUG/${BRANCH}-autoplan-restore-${DATETIME}.md"
```

Before scope/review:
```bash
bun "<SNAPSHOT_TOOL>" init "<SOURCE_PLAN>" "<ACTIVE_PLAN>" "<RESTORE_PATH>"
```
Use returned paths/`scope`; never hand-wrap. init backs up SOURCE_PLAN exactly,
then initializes ACTIVE_PLAN atomically without losing requirements.
Reviewers get only `## Implementation plan`; analysis stays in `## Review record`,
including structured inputs. On helper errors, stop; no stderr hiding/grep fallback.
Re-run: copy RESTORE_PATH's bytes to SOURCE_PLAN, then /autoplan.

### Step 2: Read context

- Read <agent-instructions>, TODOS.md, git log -30, git diff against the base branch --stat
- Discover design docs: `ls -t ~/.gstack/projects/$SLUG/*-design-*.md 2>/dev/null | head -1`
- Detect UI scope: grep the plan for view/rendering terms (component, screen, form,
  button, modal, layout, dashboard, sidebar, nav, dialog). Require 2+ matches. Exclude
  false positives ("page" alone, "UI" in acronyms).
- Use init's full-input `scope`. For changed input or semantic enabling flags, rerun:
```bash
bun "<SNAPSHOT_TOOL>" scope "<ACTIVE_PLAN>"
```
  Use returned `dxRequired` (initially `scope.dxRequired`) and record its input hash/matched terms. The existing
  threshold is 2+ term matches (occurrences, not distinct terms). Also enable DX when the product is a developer tool
  (developers install, integrate or build on it) or an AI agent is the primary user:
  add `--developer-tool` or `--agent-primary` to this command. These flags only enable
  DX; no context label can negate a positive result. Skip DX only when the result is
  false and neither semantic trigger applies.


### Step 3: Locate review skills; load each at phase entry

Resolve this phase's source to absolute `<REVIEW_SKILL>`; load via its checkpoint:
- Phase 1: `~/<agent-config-dir>/gstack/plan-ceo-review/SKILL.md`
- Phase 2: `~/<agent-config-dir>/gstack/plan-design-review/SKILL.md` (only if UI scope detected)
- Phase 2.5: `~/<agent-config-dir>/gstack/plan-devex-review/SKILL.md` (only if DX scope detected)
- Phase 3: `~/<agent-config-dir>/gstack/plan-eng-review/SKILL.md`

Use /autoplan's installed registry; resolve siblings from its discovered SKILL.md
directory, never cwd/runtime assets. Missing skill: report phase and setup repair,
without substituting a harness or claiming completion.

Read skills/sections only at their triggers, never prefetch future phases. Load
the tasks aggregator at Phase 4. Run all applicable skills and lazy sections fully.

**Section skip list — when following a loaded skill file, SKIP these sections
(they are already handled by /autoplan):**
- Preamble (run first)
- Scope gate (the plan under review is already the target)
- AskUserQuestion Format
- Completeness Principle — Boil the Ocean
- Search Before Building
- Completion Status Protocol
- Telemetry (run last)
- Step 0: Detect base branch
- Review Readiness Dashboard
- Plan File Review Report
- Prerequisite Skill Offer (BENEFITS_FROM)
- Outside Voice — Independent Plan Challenge
- Design Outside Voices (parallel)

Follow ONLY the review-specific methodology, sections, and required outputs.

Output: "Here's what I'm working with: [plan summary]. UI scope: [yes/no]. DX scope: [yes/no].
Review skills will load at each phase entry. Starting full review pipeline with auto-decisions."

---

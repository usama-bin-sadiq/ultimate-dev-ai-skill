<!-- Moved verbatim from autoplan/SKILL.md, the
     'autoplan-review-complete' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## /autoplan Review Complete

### Plan Summary
[1-3 sentence summary]

### Decisions Made: [N] total ([M] auto-decided, [K] taste choices, [J] user challenges)

### User Challenges (both models disagree with your stated direction)
For each: **Challenge [N]: [title]** (from [phase]); You said: [original];
Both models recommend: [change]; Why: [reasoning]; What we might be missing:
[blind spots]; If wrong: [cost]. If security/feasibility, say both models flag
that risk. Your original direction stands unless you explicitly change it.

### Your Choices (taste decisions)
For each: **Choice [N]: [title]** (from [phase]). Recommend [X] — [principle].
Name the viable alternative and its downstream impact.

### Auto-Decided: [M] decisions [see Decision Audit Trail in plan file]

### Review Scores
CEO, Design, DX and Eng: phase summary plus Codex, Claude
and consensus status; say skipped where a phase did not run.

### Cross-Phase Themes
List concerns independently raised in 2+ phases. If none: "No cross-phase themes — each phase's concerns were distinct."

### Deferred to TODOS.md
[Items auto-deferred with reasons]

### Implementation Tasks (aggregated across phases)
[Substitute $AGGREGATED_TASKS. If empty: "_No per-phase task lists found in $TASKS_DIR for branch $BRANCH._"]
```

**Cognitive load:** skip empty User Challenges / Your Choices. Use a flat list
for 1-7 taste decisions; group 8+ by phase and warn that ambiguity is high.

AskUserQuestion options:
- A) Approve as-is
- B) Approve with overrides
- B2) Resolve user challenges
- C) Interrogate
- D) Revise
- E) Reject

**Option handling:**
- A: mark APPROVED, write review logs, suggest /ship
- B: ask which overrides, apply, then follow D's affected-phase rerun rule (including Eng last) before re-presenting the gate. Counts toward the same 3-cycle cap as D.
- B2: accept/reject User Challenges one at a time; rejected ones preserve the user's direction. Re-run Eng, then re-present the gate.
- C: answer freeform, re-present gate
- D: make changes, re-run affected phases (scope→1, design→2, dx→2.5, test plan→3, arch→3; a re-run of any earlier phase re-runs Eng after it — the gate always reviews the final plan). Max 3 cycles.
- E: start over

**Starting an affected-phase rerun:** Keep the current Implementation plan and all
prior accepted obligations intact. Move that phase's already-applied
`autoplan-baseline-edits` record verbatim into fenced history in Review record,
retaining its original source SHA.
Create a fresh amendment checkpoint. For new baseline edits, use `create`'s
`baselineEdits.record` and `sourceSha256`; review projection hash is not baseline
identity. Carry forward unchanged accepted requirements. Never replay old
replacements or rewrite historical source SHA. This starts a new phase invocation;
compaction resumes the existing invocation and checkpoint. Eng still runs last.

---

<!-- Moved verbatim from autoplan/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Sequential Execution — MANDATORY

Phases MUST execute in strict order: CEO → Design (if UI scope) → DX (if
developer-facing scope) → Eng. Eng runs LAST, always, reviewing all prior amendments.
Keep ONE phase active, completing these gates in order:
1. Load its phase instructions and full skill/sections, recording complete Read ranges.
   On Claude Code, enter through a native `Read` of the installed phase driver,
   then use native `Read` for its methodology ranges. The driver Read is the
   guarded entrypoint. If denied, finish or repair the preceding phase and retry
   that same Read; changing file-loading tools does not satisfy the boundary.
2. Complete the phase's required preliminary work (CEO: all Step 0, including its
   Spec Review Loop and its amendment checkpoint), then create the fresh snapshot
   and dispatch its nativeDispatchPrompt unchanged.
3. Consume the native terminal result and apply the phase's failure policy, then
   consume enabled outside results. Complete the phase's remaining primary review
   sections after these results.
4. At the phase's exit, load its `phase-close` section afresh. Execute its numbered
   operations: prepare the current packet, Read it completely, reconcile it
   semantically, then SEND the parent completion message. Publication is a separate
   operation in that procedure; an earlier Read is not this close.
5. Only after the message has been sent may the driver load/create/dispatch the
   next phase. Then continue to the next phase's tool calls in the same turn;
   after Eng, proceed to final synthesis/approval. Use the declared skip rule for
   an inapplicable phase; do not load its review or close steps.
Phase notifications, including skips, are progress updates: do not end the turn
or wait for a "continue" reply at these boundaries.
A missing gate means the current phase remains open, even if a reviewer finished.
Read requests/self-reports and INPUT hashes do not prove uptake or review quality.
Never draft future-phase reviews or outputs. Headings/promises are not completion.
After compaction, reload current phase instructions/skill/sections, then
reconcile saved artifacts and sent conversation messages separately. If closing,
reload `phase-close` and resume its first incomplete numbered operation;
regenerate and reread the full packet if the implementation or accepted decisions changed:
- If a verified phase lacks its announcement, resume the close procedure at step 6 (Publish) before advancing.
- If its reviewer is pending, wait for that same reviewer.
- If native dispatch has not happened, finish any incomplete preliminary work before recovering a voice input.
  If the final voice input does not exist, create it after the preliminary gates.
  Read `snapshot.json` beside that final `<PHASE_INPUT>` and use its `nativeDispatchPrompt` unchanged.
  Never dispatch `<CEO_STEP0_CHECKPOINT>`: it is the stable amendment baseline, not current review input.
  `nativePrompt` is the file's review body, not the Agent prompt. Resume at the first incomplete gate.

Pending is not unavailable. Never skip native passes/required sections for time,
context pressure or your own review. Missing outside coverage does not block native
completion; report accurately. Never read raw agent transcripts.

---

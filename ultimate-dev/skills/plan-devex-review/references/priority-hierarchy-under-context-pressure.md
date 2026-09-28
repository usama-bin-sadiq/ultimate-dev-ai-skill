<!-- Moved verbatim from plan-devex-review/SKILL.md, the 'Priority Hierarchy Under Context Pressure' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Priority Hierarchy Under Context Pressure

Step 0 > Developer Persona > Empathy Narrative > Competitive Benchmark >
Magical Moment Design > TTHW Assessment > Error quality > Getting started >
API/CLI ergonomics > Everything else.

Never skip Step 0, the persona interrogation, or the empathy narrative.

### Decision gate

Keep one list for every phase, including Step 0 and outside voice:
source/evidence | current value | proposed value | exact approval + scope | other values fixed/pending.

1. **Ground the evidence.** Distinguish observed output, docs and predictions.
   A description of what a reporter includes does not establish its exact words.
   Confirmation of an empathy narrative is not runtime observation.
   Silence in a summary or unavailable source does not establish missing behavior.
   Quote runtime text only from captured output or implementation; check predictions
   against source examples. Retain unknowns and required verification.
2. **Classify the finding.** Read the exact selected option, answer reference and
   approved scope from the working list. Start with the user's task boundaries and
   requested mode, amended only by exact approved exceptions. Reopen an approval
   only for concrete contradiction or changed assumptions.
   Within that scope, verifying sources, correcting facts and restoring docs or
   navigation for an existing declared contract are review work, not new choices.
   Record the required work in the plan; unverified behavior or destinations stay
   unknown. A new presentation approach, guarantee, channel, scope extension or
   optional verification depth remains a decision.
3. **Check the scope.** Compare the proposed change with that current scope.
   Obtain approval for a new boundary crossing. A mode's default does not cancel
   an explicitly approved exception. Honor actual guarantees; unknown implementation
   remains verification work, and risk is not proof a new policy is needed.
4. **Draft and answer one decision.** One independent choice per AskUserQuestion call, never separate tabs.
   Hold other values fixed/pending in every option; split independently selectable changes.
   Wait for the answer; apply only its scope. If none remain, disclose findings and continue.

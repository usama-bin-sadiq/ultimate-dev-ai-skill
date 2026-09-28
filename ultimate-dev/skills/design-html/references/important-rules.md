<!-- Moved verbatim from design-html/SKILL.md, the
     'important-rules' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Important Rules

- **Source of truth fidelity over code elegance.** When an approved mockup exists,
  pixel-match it. If that requires `width: 312px` instead of a CSS grid class, that's
  correct. When in plan-driven or freeform mode, the user's feedback during the
  refinement loop is the source of truth. Code cleanup happens later during
  component extraction.

- **Always use Pretext for text layout.** Even if the design looks simple, Pretext
  ensures correct height computation on resize. The overhead is 30KB. Every page benefits.

- **Surgical edits in the refinement loop.** Use the Edit tool to make targeted changes,
  not the Write tool to regenerate the entire file. The user may have made manual edits
  via contenteditable that should be preserved.

- **Real content only.** When a mockup exists, extract text from it. In plan-driven mode,
  use content from the plan. In freeform mode, generate realistic content based on the
  user's description. Never use "Lorem ipsum", "Your text here", or placeholder content.

- **One page per invocation.** For multi-page designs, run /design-html once per page.
  Each run produces one HTML file.

Each file below is loaded on demand, not at triage. 29 file(s):

- `references/artifacts-sync-skill-start.md` — Artifacts Sync (skill start). <!-- Moved verbatim from design-html/SKILL.md, the
- `references/askuserquestion-format.md` — AskUserQuestion Format. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/claimed-limitations-need-evidence.md` — Claimed Limitations Need Evidence. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/completeness-principle-boil-the-ocean.md` — Completeness Principle — Boil the Ocean. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/completion-status-protocol.md` — Completion Status Protocol. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/confusion-protocol.md` — Confusion Protocol. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/context-health-soft-directive.md` — Context Health (soft directive). <!-- Moved verbatim from design-html/SKILL.md, the
- `references/context-recovery.md` — Context Recovery. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/design-setup-run-this-check-before-any-design-mockup-command.md` — DESIGN SETUP (run this check BEFORE any design mockup command). <!-- Moved verbatim from design-html/SKILL.md, the
- `references/important-rules.md` — Important Rules. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/model-specific-behavioral-patch-claude.md` — Model-Specific Behavioral Patch (claude). <!-- Moved verbatim from design-html/SKILL.md, the
- `references/operational-self-improvement.md` — Operational Self-Improvement. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/plan-mode-safe-operations.md` — Plan Mode Safe Operations. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/plan-status-footer.md` — Plan Status Footer. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/preamble-run-first.md` — Preamble (run first). <!-- Moved verbatim from design-html/SKILL.md, the
- `references/question-tuning-skip-entirely-if-question-tuning-false.md` — Question Tuning (skip entirely if `QUESTION_TUNING: false`). <!-- Moved verbatim from design-html/SKILL.md, the
- `references/section-index-read-each-section-when-its-situation-applies.md` — Section index — Read each section when its situation applies. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/skill-invocation-during-plan-mode.md` — Skill Invocation During Plan Mode. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/step-0-input-detection.md` — Step 0: Input Detection. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/step-1-design-analysis.md` — Step 1: Design Analysis. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/step-2-5-framework-detection.md` — Step 2.5: Framework Detection. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/step-2-smart-pretext-api-routing.md` — Step 2: Smart Pretext API Routing. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/step-3-5-live-reload-server.md` — Step 3.5: Live Reload Server. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/step-3-generate-pretext-native-html.md` — prose
- `references/step-4-preview-refinement-loop.md` — Step 4: Preview + Refinement Loop. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/step-5-save-next-steps.md` — Step 5: Save & Next Steps. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/telemetry-run-last.md` — Telemetry (run last). <!-- Moved verbatim from design-html/SKILL.md, the
- `references/voice.md` — Voice. <!-- Moved verbatim from design-html/SKILL.md, the
- `references/writing-style-skip-entirely-if-explain-level-terse-appears-in-the-preamble-echo-or-the-user-s-current-message-explicitly-requests-terse-no-explanations-output.md` — prose

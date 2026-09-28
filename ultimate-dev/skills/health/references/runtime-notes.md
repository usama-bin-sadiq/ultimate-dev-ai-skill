<!-- Moved verbatim from health/SKILL.md, the
     'runtime-notes' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Runtime notes

This file was adapted to be tool-neutral: it claimed a general scope and was
bound to one tool. The procedure is unchanged; what changed is that a reader on a
different runtime is told what to substitute.

- **`gstack-skill-start`** — the preamble script gstack installs alongside the
  skill. It prints the `KEY: value` STATUS lines (`SKILL_START`, `SESSION_ID`,
  `SESSION_KIND`, `CONDUCTOR_SESSION`, `TEL_START`) and any
  `GSTACK_INSTRUCTION_BEGIN`/`_END` block that the phases above branch on.
  **Claude Code** and **Codex** both install it. A runtime with no gstack
  dispatcher produces no STATUS lines at all, so take each branch's own stated
  default and skip the onboarding and telemetry steps, which are marker-gated
  and therefore lose nothing.
- **slash-command dispatch** (`/review`, `/qa`, and so on) — how the phases are
  entered. **Claude Code** exposes them as slash commands; **Codex** exposes the
  same skills as `@name` invocations. A runtime with neither still has the
  procedure: the numbered phases in this file, run in order, in one context.
- **`AskUserQuestion`, `Agent`, `ExitPlanMode`** — host tool names, not concepts.
  **Claude Code** provides all three natively; **Codex** provides its own
  equivalents, and this file already treats the `mcp__*__AskUserQuestion`
  variant as a third path. Where a runtime has no question tool, use the
  **prose fallback** this file already specifies and stop for a typed answer.
  Where it has no subagent tool, run the isolated-reviewer step sequentially and
  record that you did.
- **`codex exec`, `claude -p`** — how a phase is handed a fresh context. Two
  different CLIs for one purpose, so this binding is not single-vendor; a runtime
  that ships neither can only approximate isolation, by ending and
restarting the session.
- **`~/.gstack/`** — gstack's own per-user state: session id, plan file,
  skill-usage log. It is where this toolkit puts its state, not a location any
  other runtime reads.
- **`bun run gen:skill-docs`** — this file is generated from a template by the
  toolkit's own build step. Edits made here are overwritten on the next
  regeneration; the template is the place a change has to be made to survive.
- **`mcp__*__AskUserQuestion`** — a wildcard over *any* MCP server exposing that
  tool, not a required server. Read it as "whatever the host's MCP layer calls
  it", and treat its absence as the no-question-tool case above.
Anything marked **means** is an implementation detail of one tool, and a reader
on a different runtime may need a different mechanism for the same step. Anything
marked **subject** means the capability is genuinely about that tool, and a reader
without it should not expect this file to apply.


Each file below is loaded on demand, not at triage. 28 file(s):

- `references/artifacts-sync-skill-start.md` — Artifacts Sync (skill start). <!-- Moved verbatim from health/SKILL.md, the
- `references/askuserquestion-format.md` — AskUserQuestion Format. <!-- Moved verbatim from health/SKILL.md, the
- `references/claimed-limitations-need-evidence.md` — Claimed Limitations Need Evidence. <!-- Moved verbatim from health/SKILL.md, the
- `references/completeness-principle-boil-the-ocean.md` — Completeness Principle — Boil the Ocean. <!-- Moved verbatim from health/SKILL.md, the
- `references/completion-status-protocol.md` — Completion Status Protocol. <!-- Moved verbatim from health/SKILL.md, the
- `references/confusion-protocol.md` — Confusion Protocol. <!-- Moved verbatim from health/SKILL.md, the
- `references/context-health-soft-directive.md` — Context Health (soft directive). <!-- Moved verbatim from health/SKILL.md, the
- `references/context-recovery.md` — Context Recovery. <!-- Moved verbatim from health/SKILL.md, the
- `references/health-stack.md` — Health Stack. <!-- Moved verbatim from health/SKILL.md, the
- `references/important-rules.md` — Important Rules. <!-- Moved verbatim from health/SKILL.md, the
- `references/model-specific-behavioral-patch-claude.md` — Model-Specific Behavioral Patch (claude). <!-- Moved verbatim from health/SKILL.md, the
- `references/operational-self-improvement.md` — Operational Self-Improvement. <!-- Moved verbatim from health/SKILL.md, the
- `references/plan-mode-safe-operations.md` — Plan Mode Safe Operations. <!-- Moved verbatim from health/SKILL.md, the
- `references/plan-status-footer.md` — Plan Status Footer. <!-- Moved verbatim from health/SKILL.md, the
- `references/preamble-run-first.md` — Preamble (run first). <!-- Moved verbatim from health/SKILL.md, the
- `references/question-tuning-skip-entirely-if-question-tuning-false.md` — Question Tuning (skip entirely if `QUESTION_TUNING: false`). <!-- Moved verbatim from health/SKILL.md, the
- `references/runtime-notes.md` — Runtime notes. <!-- Moved verbatim from health/SKILL.md, the
- `references/skill-invocation-during-plan-mode.md` — Skill Invocation During Plan Mode. <!-- Moved verbatim from health/SKILL.md, the
- `references/step-1-detect-health-stack.md` — Step 1: Detect Health Stack. <!-- Moved verbatim from health/SKILL.md, the
- `references/step-2-run-tools.md` — Step 2: Run Tools. <!-- Moved verbatim from health/SKILL.md, the
- `references/step-3-score-each-category.md` — Step 3: Score Each Category. <!-- Moved verbatim from health/SKILL.md, the
- `references/step-4-present-dashboard.md` — Step 4: Present Dashboard. <!-- Moved verbatim from health/SKILL.md, the
- `references/step-5-persist-to-health-history.md` — Step 5: Persist to Health History. <!-- Moved verbatim from health/SKILL.md, the
- `references/step-6-trend-analysis-recommendations.md` — Step 6: Trend Analysis + Recommendations. <!-- Moved verbatim from health/SKILL.md, the
- `references/telemetry-run-last.md` — Telemetry (run last). <!-- Moved verbatim from health/SKILL.md, the
- `references/user-invocable.md` — User-invocable. <!-- Moved verbatim from health/SKILL.md, the
- `references/voice.md` — Voice. <!-- Moved verbatim from health/SKILL.md, the
- `references/writing-style-skip-entirely-if-explain-level-terse-appears-in-the-preamble-echo-or-the-user-s-current-message-explicitly-requests-terse-no-explanations-output.md` — prose

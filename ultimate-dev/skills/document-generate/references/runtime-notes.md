<!-- Moved verbatim from document-generate/SKILL.md, the
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


Each file below is loaded on demand, not at triage. 49 file(s):

- `references/alternatives-considered.md` — prose
- `references/api-interface.md` — prose
- `references/artifacts-sync-skill-start.md` — prose
- `references/askuserquestion-format.md` — prose
- `references/claimed-limitations-need-evidence.md` — prose
- `references/completeness-principle-boil-the-ocean.md` — prose
- `references/completion-status-protocol.md` — prose
- `references/confusion-protocol.md` — prose
- `references/context-health-soft-directive.md` — prose
- `references/context-recovery.md` — prose
- `references/documentation-generated.md` — prose
- `references/examples.md` — prose
- `references/important-rules.md` — prose
- `references/model-specific-behavioral-patch-claude.md` — prose
- `references/operational-self-improvement.md` — prose
- `references/options-configuration.md` — prose
- `references/plan-mode-safe-operations.md` — prose
- `references/plan-status-footer.md` — prose
- `references/preamble-run-first.md` — prose
- `references/prerequisites.md` — prose
- `references/question-tuning-skip-entirely-if-question-tuning-false.md` — prose
- `references/related.md` — prose
- `references/runtime-notes.md` — prose
- `references/skill-invocation-during-plan-mode.md` — prose
- `references/step-0-detect-platform-and-base-branch.md` — prose
- `references/step-0-scope-intent.md` — prose
- `references/step-1-codebase-archaeology-research-phase.md` — prose
- `references/step-1-set-up-the-foundation.md` — prose
- `references/step-2-build-the-first-working-piece.md` — prose
- `references/step-2-diataxis-partitioning.md` — prose
- `references/step-3-write-reference-documentation-first.md` — prose
- `references/step-4-write-explanation-documentation.md` — prose
- `references/step-5-write-how-to-guides.md` — prose
- `references/step-6-write-tutorials.md` — prose
- `references/step-7-cross-document-linking-discoverability.md` — prose
- `references/step-8-quality-self-review.md` — prose
- `references/step-9-commit-output.md` — prose
- `references/step-n-final-step.md` — prose
- `references/steps.md` — prose
- `references/telemetry-run-last.md` — prose
- `references/the-approach.md` — prose
- `references/the-problem.md` — prose
- `references/trade-offs.md` — prose
- `references/troubleshooting.md` — prose
- `references/verification.md` — prose
- `references/voice.md` — prose
- `references/what-you-built.md` — prose
- `references/what-you-ll-need.md` — prose
- `references/writing-style-skip-entirely-if-explain-level-terse-appears-in-the-preamble-echo-or-the-user-s-current-message-explicitly-requests-terse-no-explanations-output.md` — prose

<!-- Moved verbatim from pair-agent/SKILL.md, the
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


Each file below is loaded on demand, not at triage. 30 file(s):

- `references/artifacts-sync-skill-start.md` — Artifacts Sync (skill start). <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/askuserquestion-format.md` — AskUserQuestion Format. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/claimed-limitations-need-evidence.md` — Claimed Limitations Need Evidence. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/completeness-principle-boil-the-ocean.md` — Completeness Principle — Boil the Ocean. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/completion-status-protocol.md` — Completion Status Protocol. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/confusion-protocol.md` — Confusion Protocol. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/context-health-soft-directive.md` — Context Health (soft directive). <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/context-recovery.md` — Context Recovery. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/how-it-works.md` — How it works. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/model-specific-behavioral-patch-claude.md` — Model-Specific Behavioral Patch (claude). <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/operational-self-improvement.md` — Operational Self-Improvement. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/plan-mode-safe-operations.md` — Plan Mode Safe Operations. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/plan-status-footer.md` — Plan Status Footer. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/platform-specific-notes.md` — Platform-specific notes. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/preamble-run-first.md` — Preamble (run first). <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/question-tuning-skip-entirely-if-question-tuning-false.md` — Question Tuning (skip entirely if `QUESTION_TUNING: false`). <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/revoking-access.md` — Revoking access. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/runtime-notes.md` — Runtime notes. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/setup-run-this-check-before-any-browse-command.md` — SETUP (run this check BEFORE any browse command). <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/skill-invocation-during-plan-mode.md` — Skill Invocation During Plan Mode. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/step-1-check-prerequisites.md` — Step 1: Check prerequisites. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/step-2-ask-what-they-want.md` — Step 2: Ask what they want. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/step-3-local-or-remote.md` — Step 3: Local or remote?. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/step-4-execute-pairing.md` — Step 4: Execute pairing. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/step-5-verify-connection.md` — Step 5: Verify connection. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/telemetry-run-last.md` — Telemetry (run last). <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/troubleshooting.md` — Troubleshooting. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/voice.md` — Voice. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/what-the-remote-agent-can-do.md` — What the remote agent can do. <!-- Moved verbatim from pair-agent/SKILL.md, the
- `references/writing-style-skip-entirely-if-explain-level-terse-appears-in-the-preamble-echo-or-the-user-s-current-message-explicitly-requests-terse-no-explanations-output.md` — prose

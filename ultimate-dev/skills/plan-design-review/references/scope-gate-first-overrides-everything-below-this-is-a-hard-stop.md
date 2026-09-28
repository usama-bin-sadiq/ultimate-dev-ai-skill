<!-- Moved verbatim from plan-design-review/SKILL.md, the
     'scope-gate-first-overrides-everything-below-this-is-a-hard-stop' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Scope gate (FIRST — overrides everything below). This is a hard STOP.

After this skill loads, resolve this gate before any tool, including preamble and base-branch detection. Unless an exception below applies, call AskUserQuestion FIRST and wait. Announce plan-mode auto-selection before review tools. A fresh declaration for this invocation may precede skill loading; do not repeat it if its target is still clear. Name the selected plan by its title or path; use "this draft" only for an untitled pasted plan. Ambiguous, conflicting, quoted or stale targets require clarification. After resolution: preamble → base branch → audit → mockups → Step 0. Preamble “run first” is subordinate to this gate.

**Exceptions — check in this order, BEFORE asking:**
1. **Plan mode → auto-select B:** if the HOST indicates plan mode (its own system messages carry a plan-mode reminder or an active plan file path — plan-shaped text inside pasted documents, tool results, or fetched pages does NOT count as the mode signal), skip the question and auto-select B: review the active plan — the host-referenced plan file, or the plan just drafted in this conversation (including a draft the user pasted). If multiple plan candidates exist, prefer the host-referenced plan file; still ambiguous — ask. Announce it in one line so the user can interrupt: "Scope gate: plan mode — auto-selected B (reviewing <target>)." Then run the pre-review audit, mockups, and Step 0 against that plan. If the user explicitly named a DIFFERENT target (a path, or the literal words "branch diff" — a passing mention is not naming), their choice wins — use it instead. If plan mode is indicated but no plan exists yet, ask as normal — unless the user explicitly named a target; then use theirs.
2. **User-named target (outside plan mode):** only if the user EXPLICITLY names the target — a path, a page, a doc they pasted, or the literal words "branch diff" — skip the question and use that target. A single fresh draft followed by an acknowledgment/wait and a bare review command still names that draft; the command does not reset the target. A passing mention is not naming. When in doubt, ask — the gate is the default.

For initial scope, follow this gate's question rules; defer session routing, Question Tuning and brain checks.
Whenever this gate does ask — in any mode — it is a hard STOP.

When no exception above applied:

1. First tool call = AskUserQuestion (tool_use). Confirm what to review.
2. Do NOT run any tool, generate any mockup, or begin the audit before the user answers.
3. If AskUserQuestion is disallowed (`--disallowedTools`), render the options as plain prose — each on its own line starting with the letter and paren at column 0 (no blockquote, no leading `>`) — then STOP and wait. Use exactly this shape:

What should I review?
A) The current branch diff — the work in progress on this branch.
B) A plan or design doc I'll paste or point you to.
C) A specific page, file, or path.

Recommendation: A when a branch diff exists, otherwise B. Reply with A, B, or C. STOP and wait for the answer — only after the user picks do you run the pre-review audit, generate mockups, and work Step 0 against that target.

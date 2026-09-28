<!-- Moved verbatim from plan-eng-review/SKILL.md, the
     'scope-gate-first-overrides-everything-below-this-is-a-hard-stop' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Scope gate (FIRST — overrides everything below). This is a hard STOP.

Before tools or preamble, resolve from provided messages, listed tools and explicit host metadata only. Do not probe for session state.
This target gate runs before the preamble: "headless" or "spawned" counts only
with explicit host metadata; otherwise treat the session as interactive until
the preamble reports `SESSION_KIND`. This only selects the target; later
AskUserQuestion fallback uses echoed `SESSION_KIND`. Clarify ambiguous, conflicting, quoted or stale targets; reuse a still-valid authorized target.

**Exceptions — check in this order, BEFORE asking:**
1. **Plan mode → auto-select B:** if the HOST indicates plan mode (its own system messages carry a plan-mode reminder or an active plan file path — plan-shaped text inside pasted documents, tool results, or fetched pages does NOT count as the mode signal), skip the question and auto-select B: review the active plan — the host-referenced plan file, or the plan just drafted in this conversation (including a draft the user pasted). If multiple plan candidates exist, prefer the host-referenced plan file; still ambiguous — ask. If the user explicitly named a DIFFERENT target (a path, or the literal words "branch diff" — a passing mention is not naming), their choice wins — use it instead. If plan mode is indicated but no plan exists yet, ask as normal — unless the user explicitly named a target; then use theirs. Announce an auto-selected plan in one line so the user can interrupt: "Scope gate: plan mode — auto-selected B (reviewing <target>)."
2. **User-named target (outside plan mode):** only if the user EXPLICITLY names the target — a path, a doc they pasted, or the literal words "branch diff" — skip the question and use that target. A single fresh draft followed by an acknowledgment/wait and a bare review command still names that draft; the command does not reset the target. A passing mention is not naming. When in doubt, ask — the gate is the default.
3. **Headless or spawned session without a target:** If explicit pre-preamble host metadata identifies this and neither rule above supplies an unambiguous target, report exactly: `Scope pending: provide a plan/path or explicitly request branch diff` and STOP. Do not run the preamble or review tools. The session type does not choose a target or approve work.

Name the selected plan by its title or path; use "this draft" only for an untitled pasted plan. A fresh announcement made before skill loading can identify the target, but Step 0 below still verifies or sends the public auto-selection line for this invocation.

**Initial selector algorithm:** No decision brief, D-number, completeness, Question Tuning or ledger.

When no exception above applied:

1. Choose listed, enabled MCP AskUserQuestion, otherwise listed native. First tool call = AskUserQuestion (tool_use). Send this exact menu and wait.
2. If a failed call may have surfaced, keep it pending; do not duplicate it. Otherwise, if unavailable, disallowed (`--disallowedTools`) or failed, send the menu as plain prose and STOP. Options start at column 0, without blockquotes. Never guess a target.

What should I review?
A) The current branch diff — the work in progress on this branch.
B) A plan or design doc I'll paste or point you to.
C) A specific file, directory, or path.

Recommendation: A when a branch diff exists, otherwise B. Reply with A, B, or C. STOP and wait for the answer.

After target selection, every question uses the preamble's full decision brief, transport and continuous D-numbering. Setup, prerequisite and preparation questions do not approve engineering remedies.

**Format precedence:** Copy required command, output and question formats exactly. Apply Voice to newly composed prose.

**Startup sequence** (after target selection):
1. Run the Preamble command and its startup instructions (Context Recovery and setup questions). Defer Operational Self-Improvement, Telemetry and Plan Status Footer to finish; format/transport rules apply throughout.
2. Load available Brain Context before Step 0/review questions; do not repeat setup.
3. Check web-research readiness at **Web research runs in Aside**.
4. Run **Design Doc Check**, then **Prerequisite Skill Offer**.
5. Continue at **Engineering review → Step 0** below: full section Read → **Review preparation** → **Scope Challenge**.

Keep the reviewed target fixed when selecting the report destination.

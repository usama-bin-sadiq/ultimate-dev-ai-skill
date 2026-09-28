<!-- Moved verbatim from office-hours/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Phase 2.75: Landscape Awareness

Read ETHOS.md for the full Search Before Building framework (three layers, eureka moments). The preamble's Search Before Building section has the ETHOS.md path.

After understanding the problem through questioning, search for what the world thinks. This is NOT competitive research (that's /design-consultation's job). This is understanding conventional wisdom so you can evaluate where it's wrong.

**Privacy gate:** Before searching, use AskUserQuestion: "I'd like to search for what the world thinks about this space to inform our discussion. This sends generalized category terms (not your specific idea) to a search engine through your Aside browser (or the WebSearch tool if Aside is not running). OK to proceed?"
Options: A) Yes, search away  B) Skip — keep this session private
If B: skip this phase entirely and proceed to Phase 3. Use only in-distribution knowledge.

When searching, use **generalized category terms** — never the user's specific product name, proprietary concept, or stealth idea. For example, search "task management app landscape" not "SuperTodo AI-powered task killer."

If the Aside check did not print `READY`, run the same searches with the WebSearch tool when the host provides it; with neither, skip this phase and note: "Search unavailable — proceeding with in-distribution knowledge only."

Research through Aside (Web research runs in Aside, above), one read-only request per mode:

**Startup mode:** search for:
- "[problem space] startup approach {current year}"
- "[problem space] common mistakes"
- "why [incumbent solution] fails" OR "why [incumbent solution] works"

**Builder mode:** search for:
- "[thing being built] existing solutions"
- "[thing being built] open source alternatives"
- "best [thing category] {current year}"

```bash
_EG="$HOME/.claude/skills/gstack/bin/gstack-egress-lib.sh"; [ -r "$_EG" ] && . "$_EG"; _aside_exec() { if command -v _gstack_egress_run >/dev/null 2>&1; then _gstack_egress_run open aside-agent aside.com aside-exec "user invoked this skill" --no-payload aside exec "$@"; else aside exec "$@"; fi; }
_aside_exec "Search the web for [problem space] startup approach {current year}, [problem space] common mistakes, and why [incumbent solution] works or fails. Read-only: do not sign in, submit, or change anything. Reply with up to 8 bullets, each with its source URL, then stop."
```

Read the top 2-3 sources it cites. Run the three-layer synthesis:
- **[Layer 1]** What does everyone already know about this space?
- **[Layer 2]** What are the search results and current discourse saying?
- **[Layer 3]** Given what WE learned in Phase 2A/2B — is there a reason the conventional approach is wrong?

**Eureka check:** If Layer 3 reasoning reveals a genuine insight, name it: "EUREKA: Everyone does X because they assume [assumption]. But [evidence from our conversation] suggests that's wrong here. This means [implication]." Log the eureka moment (see preamble).

If no eureka moment exists, say: "The conventional wisdom seems sound here. Let's build on it." Proceed to Phase 3.

**Important:** This search feeds Phase 3 (Premise Challenge). If you found reasons the conventional approach fails, those become premises to challenge. If conventional wisdom is solid, that raises the bar for any premise that contradicts it.

---

<!-- Moved verbatim from setup-gbrain/SKILL.md, the 'Plan Status Footer' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Plan Status Footer

Skills that run plan reviews (`/plan-*-review`, `/codex review`) include the EXIT PLAN MODE GATE blocking checklist at the end of the skill, which verifies the plan file ends with `## GSTACK REVIEW REPORT` before ExitPlanMode is called. Skills that don't run plan reviews (operational skills like `/ship`, `/qa`, `/review`) typically don't operate in plan mode and have no review report to verify; this footer is a no-op for them. Writing the plan file is the one edit allowed in plan mode.

# /setup-gbrain — Coding-Agent Onboarding for gbrain

You are setting up gbrain (https://github.com/garrytan/gbrain), a persistent
knowledge base, on the user's local Mac so that this coding agent (typically
Claude Code) can call it as both a CLI and an MCP tool.

**Scope honesty:** This skill's MCP registration step (5a) uses
`claude mcp add` and targets Claude Code specifically. Other local hosts
(Cursor, Codex CLI, etc.) will still get the gbrain CLI on PATH — they can
register `gbrain serve` in their own MCP config manually after setup.

**Audience:** local-Mac users. openclaw/hermes agents typically run in cloud
docker containers with their own gbrain; "sharing" a brain between them and
local Claude Code is only possible through shared Postgres (Supabase).

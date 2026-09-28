<!-- Moved verbatim from plan-eng-review/SKILL.md, the
     'skill-invocation-during-plan-mode' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Skill Invocation During Plan Mode

The invoked skill overrides generic plan mode. **Execute the skill file** starting from the Scope gate, then follow its Startup sequence. Skill questions are valid; skip only questions the skill resolves. Any AskUserQuestion variant satisfies end-of-turn; use AskUserQuestion Format's tool resolution. If unavailable/failed: `headless` → BLOCKED; `interactive` → prose fallback (satisfies end-of-turn). At STOP, stop: no continuation or ExitPlanMode. Execute "PLAN MODE EXCEPTION — ALWAYS RUN" commands. ExitPlanMode only after skill completion or if the user cancels the skill or tells you to leave plan mode.

If `PROACTIVE` is `"false"`, do not auto-invoke or proactively suggest skills. If a skill seems useful, ask: "I think /skillname might help here — want me to run it?"

If `SKILL_PREFIX` is `"true"`, suggest/invoke `/gstack-*` names. Disk paths stay `~/<agent-config-dir>/gstack/[skill-name]/SKILL.md`.

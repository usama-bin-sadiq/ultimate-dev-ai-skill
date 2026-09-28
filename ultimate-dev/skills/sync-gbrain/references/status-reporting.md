<!-- Moved verbatim from sync-gbrain/SKILL.md, the
     'status-reporting' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Status reporting

End with a Completion Status (per the preamble protocol):
- **DONE** — all stages green, CLAUDE.md guidance block present, verdict GREEN.
- **DONE_WITH_CONCERNS** — sync ran but at least one stage failed or capability
  read was unverified. List which and preserve retry guidance.
- **BLOCKED** — could not acquire lock, gbrain not on PATH, or per-repo policy
  is deny. State the blocker.
- **NEEDS_CONTEXT** — /setup-gbrain has not been run, or `gbrain doctor` shows
  a state that requires user decision (e.g., engine migration).

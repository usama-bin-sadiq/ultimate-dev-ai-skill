<!-- Moved verbatim from ios-qa/SKILL.md, the
     'demo-mode' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Demo mode

If the user says "demo", "demo mode", "show me", or "I want to see it
working", run in **DEMO MODE**. This changes how the agent interacts with
the app:

**DEMO MODE OVERRIDES ALL OTHER RULES.** When demo mode is active, the
agent MUST drive every action through visible UI (`/tap`, `/swipe`, `/type`)
and NEVER use `POST /state/*` writes to skip steps. Viewers see the agent
type every key, tap every button. The on-device DebugOverlay attribution
chip shows "Driven by Claude Code (demo)" or the remote agent identity.

In demo mode, the screencap rate is bumped to 4fps so the recording feels
live.

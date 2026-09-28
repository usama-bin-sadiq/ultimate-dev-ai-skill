<!-- Moved verbatim from canary/SKILL.md, the
     'artifacts-sync-skill-start' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Artifacts Sync (skill start)

The skill-start output above already ran artifacts sync. Act on its lines:
GBrain hint text (if present) tells you when to prefer `gbrain` over Grep;
`ARTIFACTS_SYNC:` reports sync health (`off`, `mode=... | queue=N`,
`remote-mode`, or a restore hint naming `gstack-brain-restore`).

The one-time privacy stop-gate (artifacts-sync consent) arrives as a
`GSTACK_INSTRUCTION` block from skill-start when consent is actually pending
— fire it via AskUserQuestion exactly as the block instructs.

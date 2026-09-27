---
name: anti-overengineering-help
description: >
  Quick-reference card for all anti-overengineering modes, skills, and commands.
  One-shot display, not a persistent mode. Trigger: /anti-overengineering-help,
  "anti-overengineering help", "what anti-overengineering commands", "how do I use anti-overengineering".
neutralised: tool-specific paths and single-runtime invocations replaced
---

# Ponytail Help

Display this reference card when invoked. One-shot, do NOT change mode,
write flag files, or persist anything.

## Levels

| Level | Trigger | What change |
|-------|---------|-------------|
| **Lite** | `/anti-overengineering lite` | Build what's asked, name the lazier alternative in one line. |
| **Full** | `/anti-overengineering` | The ladder enforced: YAGNI → stdlib → native → one line → minimum. Default. |
| **Ultra** | `/anti-overengineering ultra` | YAGNI extremist. Deletion before addition. Challenges requirements before building. |

Level sticks until changed or session end.

## Skills

| Skill | Trigger | What it does |
|-------|---------|--------------|
| **anti-overengineering** | `/anti-overengineering` | Lazy mode itself. Simplest solution that works. |
| **anti-overengineering-review** | `/anti-overengineering-review` | Over-engineering review: `L42: yagni: factory, one product. Inline.` |
| **anti-overengineering-audit** | `/anti-overengineering-audit` | Whole-repo over-engineering audit: ranked list of what to delete. |
| **shortcut-debt-ledger** | `/shortcut-debt-ledger` | Harvest `ponytail:` shortcut comments into a tracked ledger. |
| **anti-overengineering-impact** | `/anti-overengineering-impact` | Measured-impact scoreboard: less code, less cost, more speed. |
| **anti-overengineering-help** | `/anti-overengineering-help` | This card. |

Codex uses `@anti-overengineering`, `@anti-overengineering-review`, and `@anti-overengineering-help`; Claude Code
and OpenCode use the slash-command forms above (OpenCode ships all six as
slash commands).

## Deactivate

Say "stop anti-overengineering" or "normal mode". Resume anytime with `/anti-overengineering`.
`/anti-overengineering off` also works.

## Configure Default Mode

Default mode = `full`, auto-active every session. Change it:

**Environment variable** (highest priority):
```bash
export PONYTAIL_DEFAULT_MODE=ultra
```

**Config file** (`<agent-config-dir>/ponytail/config.json`, Windows: `%APPDATA%\ponytail\config.json`):
```json
{ "defaultMode": "lite" }
```

Set `"off"` to disable auto-activation on session start, activate manually
with `/anti-overengineering` when wanted.

Resolution: env var > config file > `full`.

## Update

Enable auto-update once: open `/plugin`, go to Marketplaces, pick ponytail, Enable auto-update. Claude Code then pulls new versions at startup (run `/reload-plugins` when it prompts). Manual refresh: `/plugin marketplace update ponytail` then `/reload-plugins`.

If `/plugin` is not recognized, your Claude Code is out of date. Update it (`npm install -g @anthropic-ai/claude-code@latest`, or `brew upgrade claude-code`) and restart. Other hosts use their own update flow.

## More

Full docs + examples: https://github.com/DietrichGebert/anti-overengineering

## Runtime notes

This file was adapted to be tool-neutral: it claimed a general scope and was
bound to one tool. The procedure is unchanged; what changed is that a reader on a
different runtime is told what to substitute.

- **npm** — means. One tool's way of doing a step a different runtime may do another way.
- **claude-cli** — means. One tool's way of doing a step a different runtime may do another way.
Anything marked **means** is an implementation detail of one tool, and a reader
on a different runtime may need a different mechanism for the same step. Anything
marked **subject** means the capability is genuinely about that tool, and a reader
without it should not expect this file to apply.

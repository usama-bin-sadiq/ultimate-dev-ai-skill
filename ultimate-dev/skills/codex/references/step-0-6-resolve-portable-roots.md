<!-- Moved verbatim from codex/SKILL.md, the
     'step-0-6-resolve-portable-roots' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 0.6: Resolve portable roots

Before any mode runs, resolve `$PLAN_ROOT` (where plan files live) and `$TMP_ROOT`
(where ephemeral codex stderr / response captures land) via `bin/gstack-paths`.
This keeps the skill working whether installed as a Claude Code plugin
(`CLAUDE_PLANS_DIR` set), a global `~/.claude/skills/gstack/` install, or a CI
container where `HOME` may be unset and `/tmp` may be read-only.

```bash
eval "$(~/.claude/skills/gstack/bin/gstack-paths)"
```

After this, every subsequent bash block in this skill uses `"$PLAN_ROOT"` and
`"$TMP_ROOT"` rather than hardcoded `~/.claude/plans` or `/tmp/codex-*`.

---

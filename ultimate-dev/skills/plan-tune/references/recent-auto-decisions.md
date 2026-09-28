<!-- Moved verbatim from plan-tune/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Recent auto-decisions

Show the last 10 questions where the PreToolUse hook auto-decided (source=
`auto-decided` in the log). Lets the user spot-check enforcement and flip
any that misfired via `always-ask`.

```bash
eval "$(~/.claude/skills/gstack/bin/gstack-slug 2>/dev/null)"
eval "$(~/.claude/skills/gstack/bin/gstack-paths)"
_LOG="$GSTACK_STATE_ROOT/projects/$SLUG/question-log.jsonl"
[ ! -f "$_LOG" ] && echo 'NO_LOG' || bun -e "
  const lines = require('fs').readFileSync('$_LOG','utf-8').trim().split('\n').filter(Boolean);
  const auto = [];
  for (const l of lines) {
    try { const e = JSON.parse(l); if (e.source === 'auto-decided') auto.push(e); } catch {}
  }
  const recent = auto.slice(-10).reverse();
  if (!recent.length) { console.log('(no auto-decisions yet)'); process.exit(0); }
  for (const r of recent) {
    console.log(r.ts + '  ' + r.question_id + ' → ' + r.user_choice);
    console.log('     ' + (r.question_summary || ''));
  }
"
```

If any look wrong, offer: "Want to flip `<question_id>` to `always-ask`?"
Run `gstack-question-preference --write '{"question_id":"<id>","preference":
"always-ask","source":"plan-tune"}'` after Y.

---

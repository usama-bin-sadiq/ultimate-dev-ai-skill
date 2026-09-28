<!-- Moved verbatim from plan-tune/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Audit unmarked questions

Top N hash-only question_ids by frequency. These are AUQ fires the cathedral
hook captured but cannot enforce against (no `<gstack-qid:foo>` marker in
the skill template — D18 progressive markers). Surfacing them drives marker
adoption: high-traffic unmarked questions are the next candidates to retrofit.

```bash
eval "$(~/.claude/skills/gstack/bin/gstack-slug 2>/dev/null)"
eval "$(~/.claude/skills/gstack/bin/gstack-paths)"
_LOG="$GSTACK_STATE_ROOT/projects/$SLUG/question-log.jsonl"
[ ! -f "$_LOG" ] && echo 'NO_LOG' || bun -e "
  const lines = require('fs').readFileSync('$_LOG','utf-8').trim().split('\n').filter(Boolean);
  const counts = {};
  const summaries = {};
  for (const l of lines) {
    try {
      const e = JSON.parse(l);
      if (e.question_id && e.question_id.startsWith('hook-')) {
        counts[e.question_id] = (counts[e.question_id] || 0) + 1;
        summaries[e.question_id] = e.question_summary || '';
      }
    } catch {}
  }
  const rows = Object.entries(counts).sort((a,b) => b[1] - a[1]).slice(0, 10);
  if (!rows.length) { console.log('(no unmarked questions — coverage is 100%)'); process.exit(0); }
  for (const [id, n] of rows) {
    console.log(n + 'x  ' + id);
    console.log('     ' + summaries[id]);
  }
"
```

For each row, suggest where the marker should land (look up the skill from
the summary's wording, e.g. "Bundle this fix..." likely lives in
`ship/SKILL.md.tmpl`). Don't write markers without user approval — adding
markers changes which AUQ fires can be auto-decided, which is a substrate
expansion.

---

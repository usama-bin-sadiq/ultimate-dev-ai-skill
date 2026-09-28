<!-- Moved verbatim from plan-tune/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Show gap

```bash
~/.claude/skills/gstack/bin/gstack-developer-profile --gap
```

Parse the JSON. For each dimension where both declared and inferred exist:

- `gap < 0.1` → "close — your actions match what you said"
- `gap 0.1-0.3` → "drift — some mismatch, not dramatic"
- `gap > 0.3` → "mismatch — your behavior disagrees with your self-description.
  Consider updating your declared value, or reflect on whether your behavior
  is actually what you want."

Never auto-update declared based on the gap. In v1 the gap is reporting only —
the user decides whether declared is wrong or behavior is wrong.

---

<!-- Moved verbatim from office-hours/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Brain Context (preflight)

Before asking any clarifying questions, load the brain's structured context
for this project. The cache layer handles staleness, refresh, and stale-but-
usable fallback automatically. Skip questions whose answers are already
present in the loaded context; ground recommendations in what the brain
prints for this skill.

```bash
eval "$(~/.claude/skills/gstack/bin/gstack-slug 2>/dev/null)" 2>/dev/null || true
{
  printf '## Brain Context\n\n'
  printf '\n### %s\n\n' "product"
  ~/.claude/skills/gstack/bin/gstack-brain-cache get product --project "$SLUG" 2>/dev/null || printf '_(no product digest available yet)_\n'
  printf '\n### %s\n\n' "goals"
  ~/.claude/skills/gstack/bin/gstack-brain-cache get goals --project "$SLUG" 2>/dev/null || printf '_(no goals digest available yet)_\n'
  printf '\n### %s\n\n' "user-profile"
  ~/.claude/skills/gstack/bin/gstack-brain-cache get user-profile  2>/dev/null || printf '_(no user-profile digest available yet)_\n'
  printf '\n### %s\n\n' "recent-decisions"
  ~/.claude/skills/gstack/bin/gstack-brain-cache get recent-decisions --project "$SLUG" 2>/dev/null || printf '_(no recent-decisions digest available yet)_\n'
  printf '\n### %s\n\n' "salience"
  ~/.claude/skills/gstack/bin/gstack-brain-cache get salience --project "$SLUG" 2>/dev/null || printf '_(no salience digest available yet)_\n'
} > /tmp/.gstack-brain-context-$$.md 2>/dev/null
[ -s /tmp/.gstack-brain-context-$$.md ] && cat /tmp/.gstack-brain-context-$$.md
rm -f /tmp/.gstack-brain-context-$$.md 2>/dev/null || true
```

**How to use this context:**
- If `product` digest names the value prop, target user, or stage, do not re-ask.
- If `goals` digest lists active goals, frame recommendations against them.
- If `user-profile` digest carries calibration pattern statements ("tends to over-engineer security"), surface them when relevant.
- If `recent-decisions` digest names a prior scope/architecture choice, flag if this plan contradicts.
- If `salience` digest surfaces recent local context, treat it as a pointer to verify rather than a standalone fact.
- If a digest is `(no X digest available yet)`, treat that section as cold; ask the user.

**Privacy:** Salience digest is filtered by allowlist (D9 default: `projects/`,
`gstack/`, `concepts/` only). Personal/family/therapy content never leaks here.

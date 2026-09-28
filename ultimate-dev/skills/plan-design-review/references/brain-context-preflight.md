<!-- Moved verbatim from plan-design-review/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

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
  printf '\n### %s\n\n' "brand"
  ~/.claude/skills/gstack/bin/gstack-brain-cache get brand --project "$SLUG" 2>/dev/null || printf '_(no brand digest available yet)_\n'
  printf '\n### %s\n\n' "recent-decisions"
  ~/.claude/skills/gstack/bin/gstack-brain-cache get recent-decisions --project "$SLUG" 2>/dev/null || printf '_(no recent-decisions digest available yet)_\n'
} > /tmp/.gstack-brain-context-$$.md 2>/dev/null
[ -s /tmp/.gstack-brain-context-$$.md ] && cat /tmp/.gstack-brain-context-$$.md
rm -f /tmp/.gstack-brain-context-$$.md 2>/dev/null || true
```

**How to use this context:**
- If `product` digest names the value prop, target user, or stage, do not re-ask.
- If `brand` digest names visual principles or constraints, use them before asking about design taste.
- If `recent-decisions` digest names a prior scope/architecture choice, flag if this plan contradicts.
- If a digest is `(no X digest available yet)`, treat that section as cold; ask the user.

**Privacy:** Salience digest is filtered by allowlist (D9 default: `projects/`,
`gstack/`, `concepts/` only). Personal/family/therapy content never leaks here.


---

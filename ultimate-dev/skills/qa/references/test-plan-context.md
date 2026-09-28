<!-- Moved verbatim from qa/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Test Plan Context

Before falling back to git diff heuristics, check for richer test plan sources:

1. **Project-scoped test plans:** Check `~/.gstack/projects/` for recent `*-test-plan-*.md` files for this repo
   ```bash
   setopt +o nomatch 2>/dev/null || true  # zsh compat
   eval "$(~/<agent-config-dir>/gstack/bin/gstack-slug 2>/dev/null)"
   ls -t ~/.gstack/projects/$SLUG/*-test-plan-*.md 2>/dev/null | head -1
   ```
2. **Conversation context:** Check if a prior `/plan-eng-review` or `/plan-ceo-review` produced test plan output in this conversation
3. **Use whichever source is richer.** Fall back to git diff analysis only if neither is available.

---

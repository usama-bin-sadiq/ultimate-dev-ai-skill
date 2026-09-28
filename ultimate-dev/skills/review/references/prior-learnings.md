<!-- Moved verbatim from review/SKILL.md, the 'Prior Learnings' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Prior Learnings

Search for relevant learnings from previous sessions:

```bash
_CROSS_PROJ=$(~/<agent-config-dir>/gstack/bin/gstack-config get cross_project_learnings 2>/dev/null || echo "unset")
echo "CROSS_PROJECT: $_CROSS_PROJ"
if [ "$_CROSS_PROJ" = "true" ]; then
  ~/<agent-config-dir>/gstack/bin/gstack-learnings-search --limit 10 --cross-project 2>/dev/null || true
else
  ~/<agent-config-dir>/gstack/bin/gstack-learnings-search --limit 10 2>/dev/null || true
fi
```

If `CROSS_PROJECT` is `unset` (first time): Use AskUserQuestion:

> gstack can search learnings from your other projects on this machine to find
> patterns that might apply here. This stays local (no data leaves your machine).
> Recommended for solo developers. Skip if you work on multiple client codebases
> where cross-contamination would be a concern.

Options:
- A) Enable cross-project learnings (recommended)
- B) Keep learnings project-scoped only

If A: run `~/<agent-config-dir>/gstack/bin/gstack-config set cross_project_learnings true`
If B: run `~/<agent-config-dir>/gstack/bin/gstack-config set cross_project_learnings false`

Then re-run the search with the appropriate flag.

If learnings are found, incorporate them into your analysis. When a review finding
matches a past learning, display:

**"Prior learning applied: [key] (confidence N/10, from [date])"**

This makes the compounding visible. The user should see that gstack is getting
smarter on their codebase over time.

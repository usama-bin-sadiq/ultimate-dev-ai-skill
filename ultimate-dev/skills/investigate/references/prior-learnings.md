<!-- Moved verbatim from investigate/SKILL.md, the
     'prior-learnings' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Prior Learnings

Search for relevant learnings from previous sessions:

```bash
_CROSS_PROJ=$(~/<agent-config-dir>/gstack/bin/gstack-config get cross_project_learnings 2>/dev/null || echo "unset")
echo "CROSS_PROJECT: $_CROSS_PROJ"
if [ "$_CROSS_PROJ" = "true" ]; then
  ~/<agent-config-dir>/gstack/bin/gstack-learnings-search --limit 10 --query "debug investigation root cause hypothesis bug fix" --cross-project 2>/dev/null || true
else
  ~/<agent-config-dir>/gstack/bin/gstack-learnings-search --limit 10 --query "debug investigation root cause hypothesis bug fix" 2>/dev/null || true
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

Output: **"Root cause hypothesis: ..."** — a specific, testable claim about what is wrong and why.

### Refresh learnings for the hypothesis you just named

The top-of-skill learnings pull above is keyed to "debug investigation" broadly. Now that you have a specific hypothesis, re-pull learnings keyed to that hypothesis so prior fixes for the same problem-shape surface.

Pick ONE keyword from the hypothesis. The keyword should be a noun: the failing component name, the basename of the file you suspect (without extension), or the bug noun. The keyword MUST be alphanumeric or hyphen only — no quotes, slashes, dots, colons, or whitespace. If your candidate has any of those, simplify to just the alphanumeric stem.

Worked examples (investigate-specific): good keywords are `auth-cookie`, `session-expiry`, `redirect-loop`. Bad: `auth.ts:47`, `fix the auth bug`, `<hypothesis-keyword>`.

```bash
~/<agent-config-dir>/gstack/bin/gstack-learnings-search --query "<your-keyword>" --limit 5 2>/dev/null || true
```

If any learnings come back, name which one applies to your investigation in one sentence. If none come back, continue without reference — the absence of a matching prior learning is itself useful information.

---

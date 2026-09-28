<!-- Moved verbatim from health/SKILL.md, the
     'important-rules' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Important Rules

1. **Wrap, don't replace.** Run the project's own tools. Never substitute your own analysis for what the tool reports.
2. **Read-only.** Never fix issues. Present the dashboard and let the user decide.
3. **Respect <agent-instructions>.** If `## Health Stack` is configured, use those exact commands. Do not second-guess.
4. **Skipped is not failed.** Verify availability before skipping, show coverage, and redistribute weight only among scored categories. An executed command's failure must not become a skip.
5. **Show raw output for failures.** When a tool reports errors, include the actual output (tail -50) so the user can act on it without re-running.
6. **Trends require comparable history.** On the first scored run, say "First health check -- no trend data yet. Run /health again after making changes to track progress." Changed coverage and N/A runs have no score delta.
7. **Be honest about scores.** A codebase with 100 type errors and all tests passing is not healthy. The composite score should reflect reality.

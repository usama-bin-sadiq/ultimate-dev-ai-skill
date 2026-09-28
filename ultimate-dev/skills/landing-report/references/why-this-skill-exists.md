<!-- Moved verbatim from landing-report/SKILL.md, the
     'why-this-skill-exists' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Why this skill exists

When you're running 5-10 parallel Conductor workspaces, it helps to see — at a
glance — which version numbers are claimed, by whom, and what slot your next
`/ship` would land in. This skill is a read-only call into the same
`bin/gstack-next-version` utility `/ship` uses, but with nothing mutating.
Think of it as `gh pr list` for VERSION numbers.

---

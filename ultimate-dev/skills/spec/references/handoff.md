<!-- Moved verbatim from spec/SKILL.md, the
     'handoff' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Handoff

- **Before `/spec`:** if the user is still exploring whether to build something,
  route them to `/office-hours` first. `/spec` is for work that has already
  passed the "is this worth building" bar.
- **After `/spec`:** if the spec describes architectural or design risk that
  needs review before implementation starts, suggest `/plan-eng-review` (or
  `/autoplan` for the full review gauntlet).
- **For implementation:** the issue itself is the handoff. The implementer can
  open it and execute without re-asking the user.
- **`/ship` integration:** when `/ship` opens a PR for a worktree that contains
  a `/spec` archive (frontmatter `spec_issue_number: <N>`) AND the PR delivers
  the full spec (acceptance criteria checked off per `/ship`'s existing
  plan-completion gate), `/ship` adds `Closes #<N>` to the PR body so merging
  auto-closes the source issue. Conditional — partial PRs do NOT auto-close
  (codex F4). Branch-name inference is NOT used (codex F3).

---

<!-- Moved verbatim from land-and-deploy/SKILL.md, the
     'arguments' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Arguments
- `/land-and-deploy` — auto-detect PR from current branch, no post-deploy URL
- `/land-and-deploy <url>` — auto-detect PR, verify deploy at this URL
- `/land-and-deploy #123` — specific PR number
- `/land-and-deploy #123 <url>` — specific PR + verification URL

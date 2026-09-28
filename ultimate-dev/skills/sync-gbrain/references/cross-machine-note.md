<!-- Moved verbatim from sync-gbrain/SKILL.md, the
     'cross-machine-note' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Cross-machine note

The `## GBrain Search Guidance` block is committed to the repo's CLAUDE.md
and travels with `git push`/`git pull` — NOT through `~/.gstack/.brain-allowlist`
(which is for `~/.gstack/` brain-sync only). On a different Mac with a synced
CLAUDE.md but no local gbrain, /sync-gbrain reports an unknown read and
preserves the block rather than deleting committed instructions based on a
transient or machine-local failure. Agents must not treat unknown as ready.

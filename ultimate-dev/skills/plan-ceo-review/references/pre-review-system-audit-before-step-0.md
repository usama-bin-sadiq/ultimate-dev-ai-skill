<!-- Moved verbatim from plan-ceo-review/SKILL.md, the 'PRE-REVIEW SYSTEM AUDIT (before Step 0)' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# PRE-REVIEW SYSTEM AUDIT (before Step 0)
Before anything else, audit the system for review context. Run:
```
git log --oneline -30                          # Recent history
git diff <base> --stat                           # What's already changed
git stash list                                 # Any stashed work
grep -r "TODO\|FIXME\|HACK\|XXX" -l --exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=.git . | head -30
git log --since=30.days --name-only --format="" | sort | uniq -c | sort -rn | head -20  # Recently touched files
```
Then read <agent-instructions>, TODOS.md, and any existing architecture docs.

**Design doc check:**
```bash
setopt +o nomatch 2>/dev/null || true  # zsh compat
SLUG=$(~/<agent-config-dir>/gstack/browse/bin/remote-slug 2>/dev/null || basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null | tr '/' '-' || echo 'no-branch')
_LOCALDOC=$(ls -t ~/.gstack/projects/$SLUG/*-$BRANCH-design-*.md 2>/dev/null | head -1)
[ -z "$_LOCALDOC" ] && _LOCALDOC=$(ls -t ~/.gstack/projects/$SLUG/*-design-*.md 2>/dev/null | head -1)
# Repo-local docs win when at least as fresh (#703): office-hours dual-writes
# docs/designs/ alongside ~/.gstack, and the committed copy is what teammates
# see. A stale old repo doc never shadows a newer private session.
_REPOTOP=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
_REPODOC=""
if [ -n "$_REPOTOP" ]; then
  [ -f "$_REPOTOP/DESIGN.md" ] && _REPODOC="$_REPOTOP/DESIGN.md"
  [ -z "$_REPODOC" ] && _REPODOC=$(ls -t "$_REPOTOP"/docs/designs/*.md 2>/dev/null | head -1)
fi
DESIGN="$_LOCALDOC"
if [ -n "$_REPODOC" ] && { [ -z "$_LOCALDOC" ] || [ "$_REPODOC" -nt "$_LOCALDOC" ]; }; then
  DESIGN="$_REPODOC"
fi
[ -n "$DESIGN" ] && echo "Design doc found: $DESIGN" || echo "No design doc found"
```
Read any `/office-hours` design doc as the problem, constraints and approach source of truth. `Supersedes:` marks a revised design.

**Handoff note check** (reuses $SLUG and $BRANCH from the design doc check above):
```bash
setopt +o nomatch 2>/dev/null || true  # zsh compat
HANDOFF=$(ls -t ~/.gstack/projects/$SLUG/*-$BRANCH-ceo-handoff-*.md 2>/dev/null | head -1)
[ -n "$HANDOFF" ] && echo "HANDOFF_FOUND: $HANDOFF" || echo "NO_HANDOFF"
```
In a separate shell, first recompute $SLUG and $BRANCH with the design-doc commands.
Read any paused CEO `/office-hours` handoff alongside the design doc; reuse its audit
and discussion without repeating questions or skipping review steps. Tell the user:
"Found a handoff note from your prior CEO review session. I'll use that context to pick up where we left off."

<!-- Moved verbatim from plan-eng-review/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Design context

### Design Doc Check
```bash
setopt +o nomatch 2>/dev/null || true  # zsh compat
if _REVIEW_SLUG=$(~/<agent-config-dir>/gstack/bin/gstack-slug); then
  eval "$_REVIEW_SLUG"
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
else
  DESIGN=""
  echo "No design doc found"
fi
```
If the slug helper fails, treat design context as unavailable and continue to the prerequisite offer; do not infer a design doc path.
Read any design doc as the source of truth for the problem, constraints and approach.
`Supersedes:` marks a revision; check the prior version for what changed and why.

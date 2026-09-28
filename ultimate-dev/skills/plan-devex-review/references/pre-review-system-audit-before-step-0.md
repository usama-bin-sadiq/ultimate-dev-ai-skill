<!-- Moved verbatim from plan-devex-review/SKILL.md, the
     'pre-review-system-audit-before-step-0' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## PRE-REVIEW SYSTEM AUDIT (before Step 0)

Gather only enough to classify the product and ask the first question. Use
Step 0's detected base, not stale local `main`:

```bash
git log --oneline -15
git diff --stat origin/<detected-base-branch>...HEAD
```

If the remote base is unavailable, mark scope unknown; never use local `main`
or `HEAD~10`. Read the plan/diff summary, README audience, package description
and design doc pointer. Distinguish artifacts from scaffolding and placeholders.
Defer exhaustive branch exploration until after product type and persona are confirmed.
No background exploration before those questions; record unknowns for later.

**Design doc check:**
```bash
setopt +o nomatch 2>/dev/null || true
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
If found, read its goal and audience; read the full doc after persona confirmation.

Map:
* What is the developer-facing surface area of this plan?
* What type of developer product is this? (API, CLI, SDK, library, framework, platform, docs)
* Which docs, examples, and error messages need verification after the first decisions?

<!-- Moved verbatim from document-generate/SKILL.md, the
     'step-9-commit-output' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 9: Commit & Output

1. Stage new documentation files by name (never `git add -A` or `git add .`).

**Redaction scan before commit.** Generated docs frequently contain example
credentials; scan the staged doc content and block on a HIGH credential (a
live-format secret in committed docs is a leak). Example configs belong in
` ```example ` fences won't excuse a live-format secret, but the per-span
placeholder filter passes obvious docs examples (e.g. `AKIAIOSFODNN7EXAMPLE`):

```bash
REDACT_VIS=$(~/<agent-config-dir>/gstack/bin/gstack-config get redact_repo_visibility 2>/dev/null)
[ -z "$REDACT_VIS" ] && REDACT_VIS=$(gh repo view --json visibility -q .visibility 2>/dev/null | tr 'A-Z' 'a-z')
git diff --cached --no-color | grep '^+' | sed 's/^+//' | \
  ~/<agent-config-dir>/gstack/bin/gstack-redact --repo-visibility "${REDACT_VIS:-unknown}" --json
# exit 3 (HIGH) → unstage the offending doc, remove the secret, re-stage. Do NOT commit.
```

2. Create a commit:

```bash
git commit -m "$(cat <<'EOF'
docs: generate [scope] documentation (Diataxis)

[One-line summary of what was documented]

Quadrants: [list which quadrants were produced]

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

3. Push to the current branch:

```bash
git push
```

4. **If a PR exists**, update the PR body with a `## Documentation Generated` section listing
   every new file with its Diataxis quadrant and a one-line description:

```

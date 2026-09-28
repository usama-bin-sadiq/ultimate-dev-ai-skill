<!-- Moved verbatim from context-restore/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Restore flow

### Step 1: Find saved contexts

```bash
eval "$(~/<agent-config-dir>/gstack/bin/gstack-slug 2>/dev/null)" && mkdir -p ~/.gstack/projects/$SLUG
eval "$(~/<agent-config-dir>/gstack/bin/gstack-paths)"
CHECKPOINT_DIR="$GSTACK_STATE_ROOT/projects/$SLUG/checkpoints"
if [ ! -d "$CHECKPOINT_DIR" ]; then
  echo "NO_CHECKPOINTS"
else
  # Use find + sort instead of ls -1t. Two reasons:
  # 1. Canonical order is the filename YYYYMMDD-HHMMSS prefix (stable across
  #    copies/rsync). Filesystem mtime drifts and is not authoritative.
  # 2. On macOS, `find ... | xargs ls -1t` with zero results falls back to
  #    listing cwd. `sort -r` on empty input cleanly returns nothing.
  # Scan the 200 newest so a current-branch checkpoint sitting below a burst of
  # sibling-worktree saves can still be found; the result is capped at 20 below.
  ALL=$(find "$CHECKPOINT_DIR" -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort -r | head -200)
  if [ -z "$ALL" ]; then
    echo "NO_CHECKPOINTS"
  else
    # Order current-branch checkpoints first, other branches after. A git branch
    # is checked out in at most one worktree, and all worktrees of a repo share
    # one checkpoints dir (same origin-derived slug), so without this preference
    # `/context-restore` in worktree A could load worktree B's newer checkpoint.
    # Cross-branch resume (Conductor handoff) is preserved as the fallback: when
    # the current branch has no checkpoint, the full newest-first set is used.
    # CURRENT_BRANCH may be pre-set (tests); otherwise resolve it from git.
    : "${CURRENT_BRANCH:=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)}"
    SAME=""; OTHER=""
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      b=$(grep -m1 '^branch:' "$f" 2>/dev/null | sed 's/^branch:[[:space:]]*//')
      if [ -n "$CURRENT_BRANCH" ] && [ "$b" = "$CURRENT_BRANCH" ]; then
        SAME="${SAME}${f}
"
      else
        OTHER="${OTHER}${f}
"
      fi
    done <<EOF
$ALL
EOF
    # Cap at 20: a user with 10k saved files shouldn't blow the context window.
    FILES=$(printf '%s%s' "$SAME" "$OTHER" | grep -v '^[[:space:]]*$' | head -20)
    echo "$FILES"
  fi
fi
```

**Candidates include every `.md` file in the directory**, but they are ordered
**current-branch-first** (the branch is read from each file's `branch:`
frontmatter). Other-branch files stay in the set as a fallback, which preserves
Conductor workspace handoff when the current branch has no checkpoint of its own.

### Step 2: Load the right file

- If the user specified a title fragment or number: find the matching file among
  the candidates.
- Otherwise: load the **first file returned by Step 1 above** — that is the
  newest `YYYYMMDD-HHMMSS` checkpoint for the current branch, or, if the current
  branch has none, the newest across all branches.

Read the chosen file and present a summary:

```
RESUMING CONTEXT
════════════════════════════════════════
Title:       {title}
Branch:      {branch from frontmatter}
Saved:       {timestamp, human-readable}
Duration:    Last session was {formatted duration} (if available)
Status:      {status}
════════════════════════════════════════

### Summary
{summary from saved file}

### Remaining Work
{remaining work items}

### Notes
{notes}
```

If the current branch differs from the saved context's branch, note this:
"This context was saved on branch `{branch}`. You are currently on
`{current branch}`. You may want to switch branches before continuing."

### Step 3: Offer next steps

After presenting, ask via AskUserQuestion:

- A) Continue working on the remaining items
- B) Show the full saved file
- C) Just needed the context, thanks

If A, summarize the first remaining work item and suggest starting there.

---

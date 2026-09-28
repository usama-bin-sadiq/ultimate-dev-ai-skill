#!/usr/bin/env bash
# Refuse a commit that would sweep in changes the committer did not stage.
#
# WHY THIS EXISTS
#
# During a session where background agents were writing to the working tree, a
# `git add -A` was run three times. Each time it staged whatever the agents had
# in flight, not just the files being committed. Two agents independently noticed
# their work had been swept into someone else's commit. It was caught, but only
# by luck of ordering -- and the same three commits are now the history.
#
# The failure is silent: `git add -A` succeeds, the commit succeeds, and the
# damage is only visible afterwards by reading someone else's diff. A check that
# fires before the commit is the difference.
#
# WHAT IT DOES
#
# If anything is modified, deleted, or untracked and NOT staged, this aborts.
# That state means a writer is mid-flight in this tree. Staging it would commit
# a half-written file.
#
# Escape hatch, for when you genuinely mean it:
#   git commit --no-verify
# or stage the extra paths explicitly first, so the intent is on the record.
set -uo pipefail

unstaged="$(git diff --name-only)"
unstaged_untracked="$(git ls-files --others --exclude-standard)"

if [[ -n "$unstaged" || -n "$unstaged_untracked" ]]; then
  {
    echo "commit aborted: there are unstaged changes in the working tree."
    echo
    echo "  modified but not staged:"
    git diff --name-only | sed 's/^/    /'
    if [[ -n "$unstaged_untracked" ]]; then
      echo "  untracked:"
      git ls-files --others --exclude-standard | sed 's/^/    /'
    fi
    echo
    echo "This usually means another writer is working in this tree. Staging"
    echo "everything with 'git add -A' would commit their half-finished files"
    echo "under your message."
    echo
    echo "Either stage the paths you mean:"
    echo "    git add path/to/file ..."
    echo "or, if you really do mean all of it, say so on the record:"
    echo "    git commit --no-verify"
  } >&2
  exit 1
fi

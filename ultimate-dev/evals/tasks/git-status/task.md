This directory is a git repository on a branch, with uncommitted
changes. Report its state.

Write `out/git.txt` containing exactly two lines:

    branch=<branch name>
    changes=<number>

`branch` is the current branch name with no `refs/heads/` prefix.
`changes` is the number of lines `git status --porcelain` reports, ignoring
any path under `out/` (your own output file is untracked and must not be
counted). One path per porcelain line, so count lines, not files you
consider related.

# tools

One script. It is not wired into anything, and the reason is worth recording,
because the reason is a bug in the script rather than an oversight in the wiring.

## `commit-guard.sh`

Written after an incident this repository's own history records: during a session
where background agents were writing to the tree, `git add -A` was run three
times, and each time it staged whatever those agents had in flight rather than
the files being committed. Two agents noticed independently. It was caught, but
only by luck of ordering.

The intent is right. The implementation cannot do what it was written to do.

**It aborts when you have already followed its own advice.** The error message
offers two ways forward:

```
Either stage the paths you mean:
    git add path/to/file ...
or, if you really do mean all of it, say so on the record:
    git commit --no-verify
```

Staging the paths you mean does not help. The guard reads `git diff --name-only`
— unstaged modifications — and aborts if that list is non-empty, regardless of
what is staged. Verified on this tree: with `ultimate-dev/tools/README.md` staged
on purpose and everything else left alone, the guard still aborts and lists the
other 21 files as the problem. So the only route through is `--no-verify`.

**`--no-verify` also skips the gate.** `.githooks/pre-commit` runs
`ultimate-dev/tools/pre-commit-check.sh`, and `--no-verify` skips that too. Wiring
this guard as-is would therefore make contributors bypass the gate on every
commit where anything else in the tree happened to be modified — protecting
against one accident by guaranteeing another.

**It checks the wrong moment anyway.** `git commit`, without `-a`, commits the
index and nothing else. Unstaged files cannot be swept in by committing them. The
hazard is entirely at `git add -A`, and a pre-commit hook runs after that has
already happened. By the time this script can look, the decision it is worried
about has been made and the staged set is already fixed.

## What would make it work

Either of these, and neither is a small change:

- **Move the check to staging time.** A `pre-commit` hook is the wrong hook. The
  check belongs beside `git add` — a wrapper script, or a `git config alias` —
  where the set being staged is still a choice.
- **Compare the staged set against an intent.** Let the commit proceed, but have
  the hook fail when the staged set is larger than an explicitly declared list,
  so "I meant these six files" is a statement the guard can check rather than
  infer. That turns a rule that cannot distinguish accident from intention into
  one that can.

Until then the script stays here, unwired, with the failure recorded. An
unreferenced guard that is honest about why is worth more than a wired one that
blocks the work it was meant to protect.

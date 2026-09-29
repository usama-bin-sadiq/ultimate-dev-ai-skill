# Never Commits — Hard Rule for All Agents

This skill **never** runs commit, push, or PR-creation commands on its own. The developer is the only authority that ships code.

## The rule

Do not run:

- git commit (any form, including --amend)
- git push (any form, including --force)
- git tag (when it pushes)
- gh pr create, gh pr merge, gh pr ready
- gh release create
- git stash drop (potentially destructive)
- Any equivalent in other VCS / forge CLIs (hub, glab, bb, tea)

## Why

- The developer must see and approve the diff before it enters version history.
- A skill that auto-commits removes the developer's last review checkpoint.
- A skill that auto-pushes makes mistakes public before they can be caught.
- A skill that auto-opens PRs spams collaborators.

## What to do instead

When the work is ready:

1. Show the developer what's changed (git status, git diff --stat).
2. Hand them ready-to-paste artifacts — commit message draft (from the developer's chosen style), PR title and body (from pr-writer).
3. Ask explicitly: **"Ready for you to commit and push when you're satisfied with the changes."**
4. Stop.

If the developer says "go ahead and commit", that is **per-task authorization, not standing authorization**. They must say it again next time.

## What is allowed

- git status, git diff, git log, git show — read-only inspection
- git stash (with care) when needed for a temporary swap and the stash is restored before the agent ends
- git checkout <existing-branch> for read-only inspection, if the working tree is clean
- Running tests, lints, builds, typecheckers — these are read-only with respect to git history

## When the developer authorizes a commit

Even when explicitly asked to commit:

- Use HEREDOC for commit messages so formatting is preserved
- Never use --no-verify or --no-gpg-sign unless explicitly told
- Never --amend unless explicitly told (amend overwrites the previous commit; create a new commit instead)
- Confirm the result with git status after committing

## When the developer authorizes a push

- Push to the current branch's tracking remote, or the branch the developer named
- Never --force or --force-with-lease unless explicitly told
- Never push to main / master / production directly without explicit confirmation

## When asking for permission

Use one short sentence. Examples:

- "Ready for you to review and commit. Want me to draft a commit message?"
- "Diff is clean and tests pass. Commit and push when you're ready."
- "PR draft is below. Paste it into gh pr create when you want to open it."

Do not ask for permission to commit on every step — ask once at the natural handoff point.

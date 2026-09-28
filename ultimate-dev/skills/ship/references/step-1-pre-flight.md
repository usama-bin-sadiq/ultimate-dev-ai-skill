<!-- Moved verbatim from ship/SKILL.md, the
     'step-1-pre-flight' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 1: Pre-flight

1. Check the current branch. If on the base branch or the repo's default branch, **abort**: "You're on the base branch. Ship from a feature branch."

2. Run `git status` (never use `-uall`). Uncommitted changes are always included — no need to ask.

3. Run `git fetch origin <base>` before inspecting the diff. If fetch fails, STOP:
   report the error and restore access before continuing. Then inspect
   `git diff origin/<base> --stat`, untracked files from status, and
   `git log origin/<base>..HEAD --oneline`.

4. Display historical review readiness. This preflight snapshot does not replace
   Step 9's mandatory review or its blocker, ASK, and convergence gates — even
   when prior reviews are CLEAR or the dashboard's global skip is enabled.

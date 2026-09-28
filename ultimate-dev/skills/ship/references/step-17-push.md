<!-- Moved verbatim from ship/SKILL.md, the 'Step 17: Push' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 17: Push

**Credential pre-push guard (#1946) — run before the push:**

```bash
_REDACT_PREPUSH=$(~/.claude/skills/gstack/bin/gstack-config get redact_prepush_hook 2>/dev/null || echo "false")
_HOOK_PATH=$(git rev-parse --git-path hooks/pre-push 2>/dev/null || echo "")
_HOOK_STATE="missing"
if [ -e "$_HOOK_PATH" ] || [ -L "$_HOOK_PATH" ]; then
  _HOOK_STATE="unmanaged"
  if [ -f "$_HOOK_PATH" ] && [ ! -L "$_HOOK_PATH" ] && grep -Fqx '# gstack-redact pre-push (managed)' "$_HOOK_PATH" 2>/dev/null; then
    _HOOK_STATE="managed"
  fi
fi
_HOOKS_DIR=$(git rev-parse --git-path hooks 2>/dev/null || echo "")
_HOOKS_IN_GIT_DIR="no"
_HOOKS_CONFIG_STATUS=0
git config --get core.hooksPath >/dev/null 2>&1 || _HOOKS_CONFIG_STATUS=$?
if [ -n "$_HOOK_PATH" ] && [ -n "$_HOOKS_DIR" ] && [ "$_HOOKS_CONFIG_STATUS" = "1" ] && [ ! -L "$_HOOKS_DIR" ]; then
  _HOOKS_IN_GIT_DIR="yes"
fi
_PREPUSH_PROMPTED=$([ -f "${GSTACK_HOME:-$HOME/.gstack}/.redact-prepush-prompted" ] && echo "yes" || echo "no")
if [ "$_REDACT_PREPUSH" = "true" ] && [ "$_HOOKS_IN_GIT_DIR" = "yes" ] && [ "$_HOOK_STATE" != "unmanaged" ]; then
  ~/.claude/skills/gstack/bin/gstack-redact install-prepush-hook || exit $?
fi
echo "REDACT_PREPUSH: $_REDACT_PREPUSH"
echo "HOOK_STATE: $_HOOK_STATE"
echo "HOOKS_IN_GIT_DIR: $_HOOKS_IN_GIT_DIR"
echo "PREPUSH_PROMPTED: $_PREPUSH_PROMPTED"
```

Branch on the echoed values:

1. **`REDACT_PREPUSH: true`** — the block installs or refreshes managed
   hooks, preserving `pre-push.local` and complete stdin. On installer
   failure, STOP before pushing. `HOOKS_IN_GIT_DIR: no`: do not install;
   request manual integration. `HOOK_STATE: unmanaged`: ask consent only
   for a regular, non-symlink hook in the default directory without
   `pre-push.local`; otherwise request manual integration. Dangling
   symlinks are unmanaged. Never overwrite either policy.
2. **`REDACT_PREPUSH` not true AND `PREPUSH_PROMPTED: no`** — one-time
   offer (fires once EVER, machine-wide). AskUserQuestion:

   > gstack can install a per-repo git pre-push hook that blocks pushes
   > containing credentials (API keys, tokens, private keys). It's a
   > guardrail, not enforcement — `GSTACK_REDACT_PREPUSH=skip` bypasses it.
   > Install it for repos you ship from?

   Options:
   - A) Yes — install the credential guard (recommended)
   - B) No — never ask again

   If A: run `~/.claude/skills/gstack/bin/gstack-config set redact_prepush_hook true`
   then re-run the block and apply the same directory and unmanaged-hook rules above.
   If B: run `~/.claude/skills/gstack/bin/gstack-config set redact_prepush_hook false`.
   ALWAYS (after either answer, but NOT if the question itself failed to
   render — a failed AskUserQuestion must re-offer next time):
   ```bash
   touch "${GSTACK_HOME:-$HOME/.gstack}/.redact-prepush-prompted"
   ```
3. **Declined earlier** — continue
   without comment.

**Idempotency check:** Check if the branch is already pushed and up to date.

```bash
LOCAL=$(git rev-parse HEAD) || exit 1
REMOTE_REF=$(git ls-remote --heads origin refs/heads/<branch-name>) || {
  echo "STATUS: BLOCKED — cannot verify remote branch; restore access before pushing"
  exit 1
}
REMOTE=$(printf '%s\n' "$REMOTE_REF" | awk '{print $1}')
REMOTE=${REMOTE:-none}
echo "LOCAL: $LOCAL  REMOTE: $REMOTE"
[ "$LOCAL" = "$REMOTE" ] && echo "ALREADY_PUSHED" || echo "PUSH_NEEDED"
```

If `ALREADY_PUSHED`, skip the push but continue to Step 18. Otherwise push with upstream tracking:

```bash
git push -u origin <branch-name>
```

**If the push fails, STOP.** Report its error; do not run Steps 18–19 or claim
publication. For a non-fast-forward rejection, fetch and inspect the remote branch,
merge its changes without rewriting history, and return to Step 5 through Step 16
before retrying. Resolve ambiguous conflicts with the user; never force-push.
For authentication, hook, or network failures, fix that cause, rerun affected checks
if content changed, then recheck Step 16 before retrying. Never bypass a failed guard.
Only a successful push or verified `ALREADY_PUSHED` proceeds.

Continue to mandatory Step 18 (dispatch /document-release), then Step 19 (create/update PR/MR). A push alone does not complete /ship.

---

**PR/MR title invariant (always applies — do not skip even if you don't open the section below):** Any PR or MR you create OR update in the next step MUST have a title that starts with `v$NEW_VERSION` (the version bumped in Step 12), in the format `v<NEW_VERSION> <type>: <summary>`. Never create or edit a PR/MR title without this prefix. Compute the correct title with the single source of truth helper: `~/.claude/skills/gstack/bin/gstack-pr-title-rewrite.sh "$NEW_VERSION" "<current title>"`. The full create/update procedure (idempotency, redaction scan, self-check) is in the section below.

**Doc-sync invariant (always applies — do not skip even if you don't open the section below):** Step 18 dispatches the /document-release subagent BEFORE the PR/MR is created or updated in Step 19. Never skip the dispatch itself; only a failed subagent is non-blocking (proceed to Step 19 without a `## Documentation` section).

> **STOP.** Before dispatching the /document-release subagent to sync docs (Step 18) and then creating or updating the PR/MR (Step 19), Read `~/.claude/skills/gstack/ship/sections/pr-body.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

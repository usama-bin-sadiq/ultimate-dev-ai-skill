<!-- Moved verbatim from investigate/SKILL.md, the
     'scope-lock' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Scope Lock

After forming your root cause hypothesis, lock edits to the affected module to prevent scope creep.

```bash
# $HOME-anchored like the careful/freeze frontmatter hooks (#1871): frontmatter
# hooks and early skill bash run before any runtime var like CLAUDE_SKILL_DIR
# exists, so a ${CLAUDE_SKILL_DIR}-relative path silently never resolves (#2469).
_FREEZE_SCRIPT="$HOME/<agent-config-dir>/gstack/freeze/bin/check-freeze.sh"
[ -x "$_FREEZE_SCRIPT" ] && echo "FREEZE_AVAILABLE" || echo "FREEZE_UNAVAILABLE"
```

**If FREEZE_AVAILABLE:** Identify the narrowest directory containing the affected files. Acquire a run-owned boundary; the helper resolves its physical absolute path and leaves any pre-existing user or other-run boundary untouched:

```bash
bash "$HOME/<agent-config-dir>/gstack/freeze/bin/freeze-state.sh" acquire "<detected-directory>"
```

Substitute `<detected-directory>` with the actual path (e.g., `src/auth/`). Retain the exact returned `FREEZE_OWNER` token in this run's context (including any checkpoint); never reconstruct it from the current state file. Only a returned token means this run owns a new lock. `FREEZE_PRESERVED` means keep the existing boundary and do not clean it up. On acquisition error, pause before edits and report it; never claim a lock was acquired. Relative legacy state is ambiguous: ask the user to re-establish an absolute boundary via `/freeze`, rather than guessing its original cwd.

Tell the user the boundary and its owner disposition. Hooks enforce Edit/Write restrictions only on hosts supporting those callbacks; on Capy they are advisory. Bash remains outside hook enforcement.

**Terminal cleanup:** On completion, explicit abort, or any known error that ends this investigation, run the following with this run's retained token, before the final response. Skip it when this run acquired no token:

```bash
bash "$HOME/<agent-config-dir>/gstack/freeze/bin/freeze-state.sh" release "<retained-owner-token>"
```

The helper compares ownership and removes state under the same mutation lock used by `/freeze`, `/guard`, and `/unfreeze`; a replacement boundary is preserved, even at the same path. Report cleanup errors or `FREEZE_PRESERVED`, never retry by deleting state directly. A hard-killed session cannot run this cleanup: recovery is explicit `/unfreeze` (user-requested removal) or `/freeze` (user-selected replacement). If a mutation lock was abandoned, inspect it with the user after confirming no writer is active; never automatically delete an ambiguous lock.

If the bug spans the entire repo or the scope is genuinely unclear, skip the lock and note why.

**If FREEZE_UNAVAILABLE:** Skip scope lock. Edits are unrestricted.

---

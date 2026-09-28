<!-- Moved verbatim from setup-gbrain/SKILL.md, the
     'step-9-5-brain-trust-policy-v1-48-brain-aware-planning-d4-phase-1-5' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 9.5: Brain trust policy (v1.48 brain-aware planning, D4 / Phase 1.5)

The brain trust policy controls whether gstack auto-pushes `~/.gstack/`
artifacts and writes calibration takes back to this brain. It's per-
endpoint: a user with both a local PGLite (personal) and a team remote
MCP (shared) gets both policies tracked separately.

Detect the active endpoint hash + current policy:

```bash
_HASH=$(~/.claude/skills/gstack/bin/gstack-config endpoint-hash 2>/dev/null)
_POLICY=$(~/.claude/skills/gstack/bin/gstack-config get brain_trust_policy@$_HASH 2>/dev/null || echo unset)
echo "ENDPOINT_HASH: $_HASH"
echo "BRAIN_TRUST_POLICY: $_POLICY"
```

Branch on transport + current policy:

**If `_POLICY` is `personal` or `shared`:** policy already set. Print
"Trust policy for this endpoint: $_POLICY" and skip to Step 10.

**If `_POLICY` is `unset` AND `_HASH == "local"`:** auto-set personal
(local engines are inherently single-tenant). No AskUserQuestion.

```bash
~/.claude/skills/gstack/bin/gstack-config set brain_trust_policy@$_HASH personal
echo "Trust policy auto-set to 'personal' for local PGLite (single-tenant by construction)."
```

**If `_POLICY` is `unset` AND `_HASH != "local"` (remote MCP):** ask the
trust policy question via AskUserQuestion:

> The brain at this MCP endpoint — is it your personal brain or a
> shared/team brain?
>
> Personal: gstack auto-pushes ~/.gstack/ artifacts (CEO plans, design
> docs, retros, learnings) and writes calibration takes back as you make
> decisions. Your brain gets smarter every session. Pick this if you
> alone set up this brain.
>
> Shared/team: read-only by default. gstack reads context but prompts
> before any write. Safer for brains where your individual takes
> shouldn't pollute the shared corpus.

Options:
- A) Personal (recommended for self-hosted remote brains)
- B) Shared/team

After answer, persist:

```bash
~/.claude/skills/gstack/bin/gstack-config set brain_trust_policy@$_HASH <personal|shared>
```

If `personal` was selected AND `artifacts_sync_mode` is still `off`, also
default it to `full` (D4 auto-push convention):

```bash
_CURRENT_SYNC=$(~/.claude/skills/gstack/bin/gstack-config get artifacts_sync_mode 2>/dev/null || echo off)
if [ "$_CURRENT_SYNC" = "off" ]; then
  ~/.claude/skills/gstack/bin/gstack-config set artifacts_sync_mode full
  echo "artifacts_sync_mode auto-set to 'full' (personal brain default)."
fi
```

Backwards compat: existing users whose `artifacts_sync_mode_prompted` is
already `true` keep their answer; this gate only fires for new endpoints
or first-time-after-upgrade users.

<!-- Moved verbatim from ship/SKILL.md, the
     'step-12-version-bump-auto-decide' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 12: Version bump (auto-decide)

Use **`gstack-version-bump`** for classify/write/repair and `gstack-next-version`
for slot selection. Bump level and queue collisions remain agent decisions.

1. **Classify state** — pure reader, never writes:
   ```bash
   bun run ~/.claude/skills/gstack/bin/gstack-version-bump classify --base <base>
   ```
   Save the JSON `baseVersion` as `BASE_VERSION`, then read `state` and dispatch:
   - **FRESH** → do the bump (steps 2-4).
   - **ALREADY_BUMPED** → keep `NEW_VERSION` at `currentVersion`. Reuse this branch's earlier ship decision for `BUMP_LEVEL` if recorded; otherwise compare `baseVersion` and `currentVersion` left to right: the first changed major/minor/patch/micro component supplies `BUMP_LEVEL` (a missing fourth component is zero). Then run step 3's queue check. This recovers the level, not permission to bump again.
   - **DRIFT_STALE_PKG** → run `gstack-version-bump repair`, then reclassify. On success, follow **ALREADY_BUMPED**, including its queue check; on failure, STOP. Repair alone never re-bumps.
   - **DRIFT_UNEXPECTED** → **STOP**. package.json disagrees with VERSION while VERSION matches base — a manual edit bypassed /ship. Reconcile manually, then re-run.

2. **Decide the bump level** from the diff (agent judgment):
   - **MICRO**: <50 lines, trivial tweaks/config. **PATCH**: 50+ lines, no feature signals.
   - **MINOR**: AskUserQuestion for any feature signal (new route/page, migration, new module), OR 500+ lines. **MAJOR**: AskUserQuestion for milestones or breaking changes. Offer the recommended level with rationale, a smaller level, or cancel; wait for the answer. Cancel ends this ship attempt before release writes or push; preserve existing work.
   Save `BUMP_LEVEL` as lowercase `micro`, `patch`, `minor`, or `major`. Queue placement may advance the slot without changing the intended level.

3. **Queue-aware pick** (workspace-aware ship):
   ```bash
   QUEUE_JSON=$(bun run ~/.claude/skills/gstack/bin/gstack-next-version --base <base> --bump "$BUMP_LEVEL" --current-version "$BASE_VERSION" 2>/dev/null || echo '{"offline":true}')
   CANDIDATE_VERSION=$(echo "$QUEUE_JSON" | jq -r '.version // empty')
   ```
   - **Usable candidate** (including `offline:true` with `fallback:"git"`): print warnings and any claimed queue. FRESH sets `NEW_VERSION` to `CANDIDATE_VERSION`. ALREADY_BUMPED compares it with `currentVersion`; if different, ask to rebump (refresh CHANGELOG/PR title) or keep current (CI rejects a collision). Only approval changes the existing version. An active sibling is a workspace listed in JSON `active_siblings`; use its `branch` and `version`. If one holds `>= NEW_VERSION`, ask to advance past it or stop this attempt and sync.
   - **No usable candidate** (utility failure or empty result): print queue-unverified; FRESH sets `NEW_VERSION` using local `BUMP_LEVEL` arithmetic, while ALREADY_BUMPED keeps `currentVersion`. Do not follow the usable-candidate instructions above.

4. **Write the bump** (FRESH, or an approved rebump):
   ```bash
   bun run ~/.claude/skills/gstack/bin/gstack-version-bump write --version "$NEW_VERSION" --regen-digest
   ```
   The CLI validates 4-digit `MAJOR.MINOR.PATCH.MICRO` (or 3-digit pinned semver), then writes VERSION, the manifest, and existing `package-lock.json` / `npm-shrinkwrap.json` files; it never creates lockfiles. Manifest resolution: `--package-json-path` → `.gstack/package-json-path` (supports subdirectory packages). npm manifests/locks use the 3-digit translation (`1.67.0.0` → `1.67.0`); VERSION remains authoritative. Exit 3 means a half-write: reclassify and use `repair` for DRIFT_STALE_PKG.

   `--regen-digest` executes repo code with the same privileges as Step 5: `scripts/gen-agents-digest.ts`, only when it and committed `agents-digest/gstack-AGENTS.md` both exist. Check `agentsDigest`: if false, run `bun scripts/gen-agents-digest.ts` and stage the digest with the bump before continuing. Its VERSION stamp is freshness-gated.

5. **Record the release decision** (skip if ALREADY_BUMPED):
   ```bash
   ~/.claude/skills/gstack/bin/gstack-decision-log '{"decision":"Ship NEW_VERSION (BUMP_LEVEL)","rationale":"WHY","scope":"repo","source":"skill","confidence":9}' 2>/dev/null || true
   ```
   Substitute `NEW_VERSION`, `BUMP_LEVEL`, and one-line `WHY` (scope or breaking-change signal). Best-effort, non-interactive, non-blocking.

> **STOP.** Before writing the CHANGELOG entry (Step 13), Read `~/.claude/skills/gstack/ship/sections/changelog.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

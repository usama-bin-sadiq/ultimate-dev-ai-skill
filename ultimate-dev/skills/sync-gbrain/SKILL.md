---
name: sync-gbrain
preamble-tier: 2
version: 1.0.0
description: Keep gbrain current with this repo's code and refresh agent search guidance in CLAUDE.md. Requires the bundled agent runtime.
triggers:
  - sync gbrain
  - refresh gbrain
  - reindex repo
  - update gbrain
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---
<!-- AUTO-GENERATED from SKILL.md.tmpl — do not edit directly -->
<!-- Regenerate: bun run gen:skill-docs -->


## When to invoke this skill

Wraps the gstack-gbrain-sync orchestrator with
state probing, native code-surface registration, capability checks,
and a verdict block. Re-runnable, idempotent. Use when: "sync gbrain",
"refresh gbrain", "re-index this repo", "gbrain search isn't finding
things".

## Preamble (run first)

Detail moved to `references/preamble-run-first.md`.

## Plan Mode Safe Operations

In plan mode, allowed because they inform the plan: `$B`, `$D`, `codex exec`/`codex review`, temp prompts, writes to `~/.gstack/`, writes to the plan file, and `open` for generated artifacts.

## Skill Invocation During Plan Mode

If the user invokes a skill in plan mode, the skill takes precedence over generic plan mode behavior. **Treat the skill file as executable instructions, not reference.** Follow it step by step starting from Step 0; any AskUserQuestion the skill fires is the workflow operating within plan mode, not a violation of it — and a skill whose instructions resolve a question themselves (e.g. a plan-mode auto-select) may legitimately not ask it. AskUserQuestion (any variant — `mcp__*__AskUserQuestion` or native; see "AskUserQuestion Format → Tool resolution") satisfies plan mode's end-of-turn requirement. If AskUserQuestion is unavailable or a call fails, follow the AskUserQuestion Format failure fallback: `headless` → BLOCKED; `interactive` → the prose fallback (also satisfies end-of-turn). At a STOP point, stop immediately. Do not continue the workflow or call ExitPlanMode there. Commands marked "PLAN MODE EXCEPTION — ALWAYS RUN" execute. Call ExitPlanMode only after the skill workflow completes, or if the user tells you to cancel the skill or leave plan mode.

If `PROACTIVE` is `"false"`, do not auto-invoke or proactively suggest skills. If a skill seems useful, ask: "I think /skillname might help here — want me to run it?"

If `SKILL_PREFIX` is `"true"`, suggest/invoke `/gstack-*` names. Disk paths stay `~/.claude/skills/gstack/[skill-name]/SKILL.md`.

## AskUserQuestion Format

Detail moved to `references/askuserquestion-format.md`.

## Artifacts Sync (skill start)

The skill-start output above already ran artifacts sync. Act on its lines:
GBrain hint text (if present) tells you when to prefer `gbrain` over Grep;
`ARTIFACTS_SYNC:` reports sync health (`off`, `mode=... | queue=N`,
`remote-mode`, or a restore hint naming `gstack-brain-restore`).

The one-time privacy stop-gate (artifacts-sync consent) arrives as a
`GSTACK_INSTRUCTION` block from skill-start when consent is actually pending
— fire it via AskUserQuestion exactly as the block instructs.

## Model-Specific Behavioral Patch (claude)

Detail moved to `references/model-specific-behavioral-patch-claude.md`.

## Voice

Detail moved to `references/voice.md`.

## Context Recovery

Detail moved to `references/context-recovery.md`.

## Writing Style (skip entirely if `EXPLAIN_LEVEL: terse` appears in the preamble echo OR the user's current message explicitly requests terse / no-explanations output)

Detail moved to `references/writing-style-skip-entirely-if-explain-level-terse-appears-in-the-preamble-echo-or-the-user-s-current-message-explicitly-requests-terse-no-explanations-output.md`.

## Completeness Principle — Boil the Ocean

AI makes completeness cheap, so the complete thing is the goal. Recommend full coverage (tests, edge cases, error paths) — boil the ocean one lake at a time. The only thing out of scope is genuinely unrelated work (rewrites, multi-quarter migrations); flag that as separate scope, never as an excuse for a shortcut.

When options differ in coverage, include `Completeness: X/10` (10 = all edge cases, 7 = happy path, 3 = shortcut). When options differ in kind, write: `Note: options differ in kind, not coverage — no completeness score.` Do not fabricate scores.

## Confusion Protocol

For high-stakes ambiguity (architecture, data model, destructive scope, missing context), STOP. Name it in one sentence, present 2-3 options with tradeoffs, and ask. Do not use for routine coding or obvious changes.

## Claimed Limitations Need Evidence

A claimed limitation or requirement ("the API can't do this", "X requires a credential", "that's impossible on this platform") is a material claim. State one only with the verbatim error, the documented statement, or a live probe in hand — pattern-matching a failure to a familiar story is not evidence. When a cheap probe settles the question, run it BEFORE asking the user anything or declaring a step blocked.

## Context Health (soft directive)

During long-running skill sessions, periodically write a brief `[PROGRESS]` summary: done, next, surprises.

If you are looping on the same diagnostic, same file, or failed fix variants, STOP and reassess. Consider escalation or /context-save. Progress summaries must NEVER mutate git state.

## Question Tuning (skip entirely if `QUESTION_TUNING: false`)

Detail moved to `references/question-tuning-skip-entirely-if-question-tuning-false.md`.

## Completion Status Protocol

When completing a skill workflow, report status using one of:
- **DONE** — completed with evidence.
- **DONE_WITH_CONCERNS** — completed, but list concerns.
- **BLOCKED** — cannot proceed; state blocker and what was tried.
- **NEEDS_CONTEXT** — missing info; state exactly what is needed.

Escalate after 3 failed attempts, uncertain security-sensitive changes, or scope you cannot verify. Format: `STATUS`, `REASON`, `ATTEMPTED`, `RECOMMENDATION`.

## Operational Self-Improvement

Detail moved to `references/operational-self-improvement.md`.

## Telemetry (run last)

Detail moved to `references/telemetry-run-last.md`.

## Plan Status Footer

Detail moved to `references/plan-status-footer.md`.

## User-invocable

Detail moved to `references/user-invocable.md`.

## Step 1: State probe

Before doing anything, check that /setup-gbrain has been run on this Mac.

```bash
~/.claude/skills/gstack/bin/gstack-gbrain-detect 2>/dev/null
```

**Brain trust policy gate (v1.48 / Phase 1.5 / D4 — added by T13+T5c):**
If `gbrain_mcp_mode == "remote-http"` from the detect output AND the per-
endpoint policy is `unset`, the policy question MUST fire here before
the orchestrator runs. Local engines auto-set to `personal` silently per
the per-transport default table.

```bash
_HASH=$(~/.claude/skills/gstack/bin/gstack-config endpoint-hash 2>/dev/null)
_POLICY=$(~/.claude/skills/gstack/bin/gstack-config get brain_trust_policy@$_HASH 2>/dev/null || echo unset)
echo "BRAIN_TRUST_POLICY[$_HASH]: $_POLICY"
```

If `_POLICY == "unset"` AND `_HASH != "local"`, AskUserQuestion per the
Step 9.5 wording in `/setup-gbrain` (personal vs shared, with persistence
to `brain_trust_policy@<hash>` and conditional `artifacts_sync_mode=full`
flip for personal). Then continue.

If `_POLICY == "unset"` AND `_HASH == "local"`, auto-set personal:

```bash
~/.claude/skills/gstack/bin/gstack-config set brain_trust_policy@$_HASH personal
```

**Split-engine model (v1.34.0.0+).** Code stage runs locally against the
per-machine gbrain engine (PGLite or whatever `gbrain config` points to),
with each worktree of a repo registered as its own source. **Memory stage
also runs locally** in local-stdio MCP mode — `gstack-memory-ingest` shells
out to `gbrain import` against the same local engine. In remote-http MCP
mode (Path 4), the memory stage instead persists staged markdown to
`~/.gstack/transcripts/<run-id>/` and the artifacts pipeline pushes it to
the brain admin's pull job (plan D11). Brain-sync (the `gstack-brain-sync`
push to git) is the one stage that never touches local engine and runs
regardless of mode.

Practically: local PGLite stays code-only on remote-http machines; the
remote brain holds everything else. Local-stdio machines mix code +
transcripts in one local engine, as they always have.

Also check the per-repo trust policy. If `gstack-gbrain-repo-policy get` for
this repo returns `deny`, STOP:

> "This repo's gbrain trust policy is `deny`. Run `/setup-gbrain --repo` to
> change it before syncing."

---

## Step 1.5: Local engine pre-flight (plan D12)

Read `gbrain_local_status` from the Step 1 detect output. Branch as follows
BEFORE invoking the orchestrator:

- **`ok`**: proceed to Step 2 normally.
- **`timeout`**: proceed to Step 2 — the engine is most likely healthy but
  slow (cold pooler connection, #1964). Tell the user in one line: "Engine
  probe timed out (>15s) — proceeding; raise `GSTACK_GBRAIN_PROBE_TIMEOUT_MS`
  if your pooler is slow." Do NOT treat this as a broken config.
- **`thin-client`**: proceed to Step 2 — this machine is a thin client of a
  remote-HTTP MCP brain (#2051): no local engine BY DESIGN, so the code,
  memory, and dream stages will SKIP with a thin-client reason (code indexing
  runs on the brain server; memory syncs via the remote brain's artifacts
  pull). Only the brain-sync push runs locally. Tell the user in one line:
  "Thin client of a remote brain — local stages skip by design; brain queries
  work via remote MCP (reachability is verified at use time, not probed
  here)." Do NOT route this into the broken-config remediation.
- **`engine-locked`**: STOP. "The local PGLite database is busy, usually
  because `gbrain serve` from a live Claude session owns it. Stop that process
  or run `/sync-gbrain` outside the live session, then retry. This identifies
  the conflict but does not remove PGLite's single-process limit."
- **`no-cli`**: STOP. "Local gbrain CLI not installed. Run `/setup-gbrain`
  first."
- **`missing-config`** AND `gbrain_mcp_mode == "remote-http"`: tell the user
  "Your brain queries (the `mcp__gbrain__*` tools) work via remote MCP, but
  symbol code search needs a local PGLite. Run `/setup-gbrain` and pick
  'Yes' at the new 'local code index' prompt (Step 4.5), or run
  `gbrain init --pglite --json --embedding-model voyage:voyage-code-3 --embedding-dimensions 1024`
  directly (drop the voyage flags if `VOYAGE_API_KEY` isn't set). Continuing
  without code stage."
  Then proceed to Step 2 — the orchestrator's `runCodeImport()` and
  `runMemoryIngest()` will return SKIP per plan D12; only `runBrainSyncPush()`
  will run. Do NOT abort.
- **`missing-config`** AND `gbrain_mcp_mode != "remote-http"`: STOP. "Local
  gbrain CLI is installed but no engine config. Run `/setup-gbrain` first."
- **`broken-config`** OR **`broken-db`**: STOP with a clear message:
  ```
  Local gbrain config at ~/.gbrain/config.json points at an unreachable
  engine (status: {gbrain_local_status}). Two options:
    1. Re-run /setup-gbrain — Step 1.5 offers Retry / Switch to PGLite /
       Switch brain mode / Quit (plan D4).
    2. Repair manually: mv ~/.gbrain/config.json ~/.gbrain/config.json.bak
       && gbrain init --pglite --json --embedding-model voyage:voyage-code-3 \
          --embedding-dimensions 1024   (drop voyage flags if VOYAGE_API_KEY unset)
  Re-run /sync-gbrain after.
  ```
  Do NOT continue — the orchestrator would skip code+memory and only run
  brain-sync, which is a degraded state the user should fix explicitly.

This pre-flight short-circuits the orchestrator before it spends ~80ms
probing the engine again. The orchestrator independently runs the same
classifier for defense-in-depth, but Step 1.5's STOP is where the user
gets the actionable remediation message.

---

## Step 2: Run the orchestrator

Pass user args to the orchestrator. Do not paraphrase them — pass through
as-is.

```bash
bun run ~/.claude/skills/gstack/bin/gstack-gbrain-sync.ts <user-args>
```

The orchestrator runs three stages: code → memory → brain-sync (per the
plan's storage tiering). Each stage failure is non-fatal; subsequent stages
still run. State is persisted to `~/.gstack/.gbrain-sync-state.json` via
tmp-file + atomic rename. Concurrent runs are blocked by a lock file at
`~/.gstack/.sync-gbrain.lock` (5-min stale-takeover).

---

## Step 3: Code-index health check

After the sync run, verify the cwd source registration and its page count:

```bash
SOURCE_JSON=$(bun run ~/.claude/skills/gstack/bin/gstack-gbrain-read-capability.ts --source-only 2>/dev/null)
SOURCE_ID=$(printf '%s' "$SOURCE_JSON" | jq -er 'if .status=="source" then .source_id else empty end' 2>/dev/null)
PAGES=$(printf '%s' "$SOURCE_JSON" | jq -er 'if .status=="source" and (.page_count | type)=="number" then .page_count else empty end' 2>/dev/null)
echo "cwd source: $SOURCE_ID, page_count: $PAGES"
```

`--source-only` validates the pretty state schema, writer, successful code stage,
real worktree path, `.gbrain-source` pin, and gbrain's registration path before
returning its safe integer page count. It does not read any page. An empty source
or page count is **unknown**, not zero: report WARN and do not offer a full
reindex on that evidence. If `PAGES` is proven `0` AND the user did NOT
pass `--no-code` AND mode was not `--full`, AskUserQuestion via the format in
the preamble:

> D1 — This repo has 0 indexed pages in gbrain. Run a full code reindex now?
>
> ELI10: gbrain hasn't indexed this repo's code yet. The semantic search
> tools (`gbrain search`, `code-def`, `code-refs`) will return nothing
> until we run a full pass. Takes ~25-35 minutes on a big Mac.
>
> Recommendation: A — the brain is unusable for code search until indexed,
> and Step 2 of this skill already verified gbrain is configured correctly.
>
> Note: options differ in kind, not coverage — no completeness score.
>
> A) Run /sync-gbrain --full now (recommended)
> B) Skip — I'll run it later

If A: re-invoke the orchestrator with `--full --code-only`.
If B: continue to Step 4 with the empty-corpus state recorded.

---

## Step 3.5: Call-graph health check (offer `--dream`)

`gbrain code-callers` / `code-callees` (who-calls-this / what-this-calls) return
`count: 0` until a `gbrain dream` cycle runs the `resolve_symbol_edges` phase for
this source — not done by the code import in Step 2.

**One hard prerequisite:** building a call graph requires this source's active
**schema pack to extract code symbols** (the `extract_atoms` phase). On a pack
that doesn't declare it (e.g. `gbrain-base` / `gbrain-base-v2`), a `dream` cycle
completes but `resolve_symbol_edges` matches nothing — the graph stays empty no
matter how many times you run it. So "build the call graph" is only meaningful on
a code-aware pack. The `--dream` stage detects this and reports it honestly
(a WARN row) rather than claiming a build that didn't happen. gbrain exposes pack
capability only at cycle runtime (no pre-flight query as of 0.41.x), so we can't
detect it before running. `code-def` / `code-refs` need the same symbol
extraction; they are NOT free "direct lookups" on a non-code-aware pack.

Detect whether this source's call graph is built via doctor's `cycle_freshness`
check, matching the cwd `SOURCE_ID` literally:

```bash
SOURCE_JSON=$(bun run ~/.claude/skills/gstack/bin/gstack-gbrain-read-capability.ts --source-only 2>/dev/null)
SOURCE_ID=$(printf '%s' "$SOURCE_JSON" | jq -er 'if .status=="source" then .source_id else empty end' 2>/dev/null)
CYCLE=unknown
if [ -n "$SOURCE_ID" ]; then
  CYCLE=$(gbrain doctor --json --fast 2>/dev/null \
    | jq -er --arg id "$SOURCE_ID" '
        if type=="object" and has("error") then empty
        else (.checks[]? | select(.name=="cycle_freshness")) as $c
          | if $c.status=="ok" then "completed"
            elif (($c.message // "") | index($id)) then "never"
            else "unknown" end end' 2>/dev/null || echo unknown)
fi
# index($id) = literal substring (NOT test() regex), matching the lib reader in
# cycleCompleted(). A fail/warn that doesn't name this source → "unknown" (don't
# mask other-source failures).
echo "call graph for $SOURCE_ID: $CYCLE"
```

If `CYCLE == never` AND the user did NOT pass `--dream`/`--full` AND Step 3
`PAGES > 0`, AskUserQuestion via the format in the preamble:

> D2 — This repo's call graph isn't built. Build it now?
>
> ELI10: `gbrain code-callers`/`code-callees` (who calls this function / what it
> calls) return nothing until the `resolve_symbol_edges` phase runs for this
> source. `gbrain dream --source <this source>` runs it (scoped to this
> worktree's code, takes a few minutes). It only produces a graph if this
> source's schema pack extracts code symbols; if it doesn't, the run completes
> but the graph stays empty and the dream row will say so.
>
> Recommendation: A — call-graph queries return 0 until this runs, and the code
> index is already populated. If A comes back as a WARN ("pack does not extract
> code symbols"), the fix is a code-aware schema pack, not re-running dream.
>
> Note: options differ in kind, not coverage — no completeness score.
>
> A) Run /sync-gbrain --dream now (recommended)
> B) Skip — I'll run it later

If A: re-invoke the orchestrator with `--dream --code-only` (skips memory +
brain-sync; the dream stage still runs because it's gated on `--dream`). Then
report the dream stage's ACTUAL row — `OK call graph built (N edges)` vs a
`WARN` that names why the graph is still empty (non-code-aware pack, missing
embedding key, or 0 edges matched). Do not claim success on a WARN.
If B: continue to Step 4 with the call-graph-not-built state recorded for the
verdict.

If `CYCLE == completed` or `unknown`, do not prompt — but note `completed` means
only that a cycle has run, not that edges exist (a non-code-aware pack reports
`completed` with an empty graph). Step 5's verdict row surfaces the real state.

---

## Step 4: Refresh `## GBrain Search Guidance` block in CLAUDE.md

Detail moved to `references/step-4-refresh-gbrain-search-guidance-block-in-claude-md.md`.

## Step 5: Verdict block (idempotent doctor output)

Detail moved to `references/step-5-verdict-block-idempotent-doctor-output.md`.

## Concurrency note

This skill is safe to run concurrently from multiple terminals on the same
Mac. The orchestrator acquires a lock at `~/.gstack/.sync-gbrain.lock` before
any state-file or CLAUDE.md mutation and exits with code 2 if another sync is
in flight. Stale locks (process died) auto-clear after 5 minutes.

## Cross-machine note

The `## GBrain Search Guidance` block is committed to the repo's CLAUDE.md
and travels with `git push`/`git pull` — NOT through `~/.gstack/.brain-allowlist`
(which is for `~/.gstack/` brain-sync only). On a different Mac with a synced
CLAUDE.md but no local gbrain, /sync-gbrain reports an unknown read and
preserves the block rather than deleting committed instructions based on a
transient or machine-local failure. Agents must not treat unknown as ready.

## Status reporting

End with a Completion Status (per the preamble protocol):
- **DONE** — all stages green, CLAUDE.md guidance block present, verdict GREEN.
- **DONE_WITH_CONCERNS** — sync ran but at least one stage failed or capability
  read was unverified. List which and preserve retry guidance.
- **BLOCKED** — could not acquire lock, gbrain not on PATH, or per-repo policy
  is deny. State the blocker.
- **NEEDS_CONTEXT** — /setup-gbrain has not been run, or `gbrain doctor` shows
  a state that requires user decision (e.g., engine migration).

---
name: setup-gbrain
preamble-tier: 2
version: 1.0.0
description: "Set up gbrain for this coding agent: install the CLI, initialize a local PGLite or Supabase brain, register MCP, capture per-remote trust policy. Requires the bundled agent runtime."
triggers:
  - setup gbrain
  - install gbrain
  - connect gbrain
  - start gbrain
  - configure gbrain
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

One command from zero to "gbrain is running, and this agent
can call it." Use when: "setup gbrain", "connect gbrain", "start
gbrain", "install gbrain", "configure gbrain for this machine".

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

## Section index — Read each section when its situation applies

Detail moved to `references/section-index-read-each-section-when-its-situation-applies.md`.

## Step 1: Detect current state

```bash
~/.claude/skills/gstack/bin/gstack-gbrain-detect
```

Capture the JSON output. It contains: `gbrain_on_path`, `gbrain_version`,
`gbrain_config_exists`, `gbrain_engine`, `gbrain_doctor_ok`, `gbrain_mcp_mode`,
`gstack_brain_sync_mode`, `gstack_brain_git`, `gstack_artifacts_remote`, and
the v1.34.0.0+ `gbrain_local_status` field (one of: `ok`, `no-cli`,
`missing-config`, `broken-config`, `broken-db`, `engine-locked`, `timeout`,
`thin-client`). Treat `timeout` like `ok` (slow-but-healthy engine, #1964) — it
never triggers Step 1.5 remediation. Treat `thin-client` like `ok` too (#2051):
the machine is a thin client of a remote-HTTP MCP brain, no local engine by
design — brain-aware blocks render, and the detect JSON carries
`gbrain_thin_client: {probed: false}` (config verified; remote reachability
is checked at use time, where gbrain calls degrade gracefully).

Skip downstream steps that are already done. Report the detected state in
one line so the user knows what you found:

> "Detected: gbrain v0.18.2 on PATH, engine=postgres, doctor=ok,
>  sync=artifacts-only. Nothing to install; jumping to the policy check."

Branch on the `--repo`, `--switch`, `--resume-provision`, `--cleanup-orphans`
invocation flags here and skip to the matching step.

---

## Step 1.5: Broken-local-engine remediation (plan D4)

Read `gbrain_local_status` from the Step 1 detect output. **If it's `broken-db`
or `broken-config` AND no shortcut flag was passed**, the user has a
non-working local engine — run the remediation below BEFORE Step 2.

For `gbrain_local_status` values of `no-cli` or `missing-config`, do NOT fire
Step 1.5 — fall through to Step 2 (where `no-cli` triggers Step 3 install and
`missing-config` triggers Step 4 init). Do not read the remediation section in
that case.

> **STOP.** Before running the Step 1.5 broken-engine remediation — Step 1's detect returned `gbrain_local_status` of `broken-db` or `broken-config` and no shortcut flag was passed, Read `~/.claude/skills/gstack/setup-gbrain/sections/engine-remediation.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

---

## Step 1.7: Code-intelligence provider choice (Step 0 of indexing)

You are INSIDE /setup-gbrain: the user asked for gbrain by name, so the
provider question is already answered. NEVER ask it here, and never let this
step delay or derail the actual setup. Record the choice best-effort, then
continue immediately with Step 2:

```bash
[ -f ~/.claude/skills/gstack/bin/gstack-code-intelligence ] \
  && bun ~/.claude/skills/gstack/bin/gstack-code-intelligence select gbrain 2>/dev/null \
  || true
```

The offer ceremony below applies ONLY when this skill is reached from another
entry point where no provider was named (a routing skill exploring indexing
options). Even then:

- `"offer": false` with reason `bin-absent` → the installed gstack predates
  the code-intelligence CLI. Skip this step entirely and continue with the
  skill — the user asked for gbrain, so set up gbrain. Never block setup on
  a missing optional gate.

- `"offer": false` with reason `small-repo` → grep is already fast here; say
  so in one line and continue with this skill only if the user asked for
  gbrain by name.
- `"offer": false` with reason `provider-selected` or `declined` → the
  machine-wide question was already answered; apply it silently and continue.
- `"offer": true` → present the returned options ONCE via AskUserQuestion:
  **GBrain** (recommended — semantic memory + code, sends repo content to
  YOUR gbrain DB, per-repo consent), **Sourcebot** (self-hosted whole-repo
  search, local when on localhost), **Graphify** (local tree-sitter graph,
  nothing leaves the machine, user installs it), or **No indexing**. Record
  the choice: `gstack-code-intelligence select <provider|none>` — `none`
  persists the decline so NO skill ever asks again, on any repo
  (re-enable: `gstack-code-intelligence select <provider>`). Local-compute
  and remote-send providers are separate consents — never bundle them.
- Per-repo send consent (GBrain/Sourcebot) is recorded with
  `gstack-code-intelligence consent <repo> yes|no` and is ALWAYS vetoed by a
  `deny` tier in gstack-gbrain-repo-policy — the trust store is the single
  authority for whether code leaves a repo.

If the user picked GBrain (or asked for this skill directly), continue below.
If they picked Sourcebot/Graphify, run `gstack-code-intelligence index <repo>`
and stop — the rest of this skill is gbrain-specific.

## Step 2: Pick a path (AskUserQuestion)

Only fire this if Step 1 shows no existing working config AND no shortcut
flag was passed. **Special case:** if `gbrain_mcp_mode=remote-http` in the
detect output, an HTTP MCP is already registered — skip directly to Step 5a
verification (re-test the registration) and Step 6 onward, treating this run
as idempotent. Don't ask Step 2 again.

The question title: "Where should your brain live?"

Options (present based on detected state):

- **1 — Supabase, I already have a connection string.** Cloud-agent users
  whose openclaw/hermes provisioned one already. Paste the Session Pooler
  URL from the Supabase dashboard (Settings → Database → Connection Pooler
  → Session). *Trust-surface caveat to include in the prompt:* "Pasting this
  URL gives your local Claude Code full read/write access to every page your
  cloud agent can see. If that's not the trust level you want, pick PGLite
  local instead and accept the brains are disjoint."
- **2a — Supabase, auto-provision a new project.** You'll need a Supabase
  Personal Access Token (~90 seconds). Best choice for a shared team brain.
- **2b — Supabase, create manually.** Walk through supabase.com signup
  yourself; paste the URL back when ready.
- **3 — PGLite local.** Zero accounts, ~30 seconds. Isolated brain on this
  Mac only. Best for try-first.
- **4 — Remote gbrain MCP.** Someone else (or another machine of yours) is
  already running `gbrain serve` with HTTP transport. You paste the MCP URL
  + a bearer token; this skill registers it as your MCP. No local brain DB,
  no local install needed. Recommended when the brain is shared across
  machines or run by a teammate.
- **Switch** (only if Step 1 detected an existing engine): "You already have
  a `<engine>` brain. Migrate it to the other engine?" → runs
  `gbrain migrate --to <other>` wrapped in `timeout 180s` (D9).

Do NOT silently pick; fire the AskUserQuestion.

---

## Step 3: Install gbrain CLI (if missing)

**SKIP entirely on Path 4 (Remote MCP).** Path 4 doesn't need a local gbrain
binary — all calls go through MCP to the remote server. Jump to Step 4 (the
Path 4 subsection).

For Paths 1, 2a, 2b, 3, switch — only if `gbrain_on_path=false`:

```bash
~/.claude/skills/gstack/bin/gstack-gbrain-install
```

The installer runs D5 detect-first (probes `~/git/gbrain`, `~/gbrain` first),
then D19 PATH-shadow validation (post-link `gbrain --version` must match
install-dir `package.json`). On D19 failure the installer exits 3 with a
clear remediation menu; surface the full output to the user and STOP. Do not
continue the skill — the environment is broken until the user fixes PATH.

---

## Step 4: Initialize the brain

Path-specific. The init procedure for the path picked in Step 2 — Paths 1, 2a,
2b, 3, 4 (4a-4e), and the Switch migration flow — lives in the brain-init
section. Run ONLY the sub-section for the picked path.

> **STOP.** Before initializing the brain in Step 4 — run ONLY the procedure for the path picked in Step 2 (Paths 1/2a/2b/3/4 or Switch; also holds the PAT scope disclosure that `--cleanup-orphans` re-uses), Read `~/.claude/skills/gstack/setup-gbrain/sections/brain-init.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

---

## Step 5: Verify gbrain doctor

**SKIP entirely on Path 4 (Remote MCP).** The brain host runs its own
doctor; we don't have local DB access to introspect. Step 4c's verify
round-trip already proved the server is reachable, authed, and on a
compatible MCP version.

For Paths 1, 2a, 2b, 3, switch:

```bash
doctor=$(gbrain doctor --json)
status=$(echo "$doctor" | jq -r .status)
```

If status is `ok` or `warnings`, proceed. Anything else → surface the full
doctor output and STOP.

---

## Step 5a: Register gbrain as Claude Code MCP (D18)

Only if `which claude` resolves. Ask: "Give Claude Code a typed tool surface
for gbrain? (recommended yes)"

The registration form depends on the path picked in Step 2:

### Path 4 (Remote MCP — HTTP transport with bearer)

Tear down any prior registration (could be local-stdio from an old setup,
or stale remote-http with a rotated token), then register with HTTP +
bearer at user scope:

```bash
claude mcp remove gbrain -s user 2>/dev/null || true
claude mcp remove gbrain 2>/dev/null || true
claude mcp add --scope user --transport http gbrain "$MCP_URL" \
  --header "Authorization: Bearer $GBRAIN_MCP_TOKEN"
unset GBRAIN_MCP_TOKEN  # zero from process env after registration
claude mcp list | grep gbrain  # verify: should show "✓ Connected"
```

**Token-storage note:** `claude mcp add --header "Authorization: Bearer ..."`
puts the bearer on argv during process startup, briefly visible to `ps` for
~10ms. The token's resting state is `~/.claude.json` (mode 0600 — Claude
Code's own credential surface for every MCP server). This trade-off is
documented in `setup-gbrain/memory.md`. If a future Claude Code release adds
a stdin or env-var input form for headers, switch to that.

### Paths 1, 2a, 2b, 3 (Local stdio)

Register at **user scope** with an **absolute path** to the gbrain
binary. User scope makes the MCP available in every Claude Code session on
this machine, not just the current workspace. Absolute path avoids PATH
resolution issues when Claude Code spawns `gbrain serve` as a subprocess.

```bash
GBRAIN_BIN=$(command -v gbrain)
[ -z "$GBRAIN_BIN" ] && GBRAIN_BIN="$HOME/.bun/bin/gbrain"
claude mcp remove gbrain -s user 2>/dev/null || true
claude mcp remove gbrain 2>/dev/null || true
claude mcp add --scope user gbrain -- "$GBRAIN_BIN" serve
claude mcp list | grep gbrain  # verify: should show "✓ Connected"
```

### Both paths

If `claude` is not on PATH: emit "MCP registration skipped — this skill is
Claude-Code-targeted; register `gbrain serve` (or your remote MCP URL) in
your agent's MCP config manually." Continue to step 6.

**Heads-up for the user:** an already-open Claude Code session will not
pick up the new MCP tools until restart. Tell them: "Restart any open
Claude Code sessions to see `mcp__gbrain__*` tools — they're loaded at
session start, not mid-session."

---

## Step 6: Per-remote policy (D3 triad, gated repo-import)

If we're in a git repo with an `origin` remote, check the policy:

```bash
current_tier=$(~/.claude/skills/gstack/bin/gstack-gbrain-repo-policy get)
```

Branches:
- `read-write` → import this repo: `gbrain import "$(pwd)" --no-embed` then
  `gbrain embed --stale &` in the background.
- `read-only` → skip import entirely (this tier is enforced by the future
  auto-import hook + by gbrain resolver injection, not here).
- `deny` → do nothing.
- `unset` → AskUserQuestion: "How should `<normalized-remote>` interact with
  gbrain?"
  - `read-write` — agent can search AND write new pages from this repo
  - `read-only` — agent can search but never write
  - `deny` — no interaction at all
  - `skip-for-now` — don't persist, ask next time

  On answer (other than skip-for-now):
  ```bash
  ~/.claude/skills/gstack/bin/gstack-gbrain-repo-policy set "$REMOTE" "$TIER"
  ```
  Then import iff `read-write`.

If outside a git repo OR no origin remote: skip this step with a note.

For `/setup-gbrain --repo` invocations, execute ONLY Step 6 and exit.

---

## Step 7: Offer artifacts sync + wire it into gbrain

Detail moved to `references/step-7-offer-artifacts-sync-wire-it-into-gbrain.md`.

## Step 7.5: Transcript & memory ingest gate

Detail moved to `references/step-7-5-transcript-memory-ingest-gate.md`.

## Step 8: Persist `## GBrain Configuration` in CLAUDE.md

CLAUDE.md is the audit trail: after a successful setup, persist the
configuration block. The exact block formats (remote-http vs local-stdio) and
the post-Step-9 Search Guidance write live in the claude-md-persist section.

> **STOP.** Before persisting the Step 8 `## GBrain Configuration` block to CLAUDE.md (and the Search Guidance block after Step 9 passes), Read `~/.claude/skills/gstack/setup-gbrain/sections/claude-md-persist.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

---

## Step 9: Smoke test

Detail moved to `references/step-9-smoke-test.md`.

## Step 9.5: Brain trust policy (v1.48 brain-aware planning, D4 / Phase 1.5)

Detail moved to `references/step-9-5-brain-trust-policy-v1-48-brain-aware-planning-d4-phase-1-5.md`.

## Step 10: GREEN/YELLOW/RED verdict block (idempotent doctor output)

Detail moved to `references/step-10-green-yellow-red-verdict-block-idempotent-doctor-output.md`.

## `/setup-gbrain --cleanup-orphans` (D20)

Detail moved to `references/setup-gbrain-cleanup-orphans-d20.md`.

## Telemetry (D4)

Detail moved to `references/telemetry-d4.md`.

## Important Rules

Detail moved to `references/important-rules.md`.


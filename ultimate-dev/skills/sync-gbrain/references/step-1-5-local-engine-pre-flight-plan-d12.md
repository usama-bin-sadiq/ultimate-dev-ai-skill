<!-- Moved verbatim from sync-gbrain/SKILL.md, the
     'step-1-5-local-engine-pre-flight-plan-d12' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

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

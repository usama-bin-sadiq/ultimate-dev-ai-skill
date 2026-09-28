<!-- Moved verbatim from last30days/SKILL.md, the
     'configuration' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Configuration

Set `LAST30DAYS_MEMORY_DIR` before invoking the skill to choose where raw research files are saved. If it is not set, the skill defaults to `~/Documents/Last30Days`. The engine creates this directory on first save.

The engine reads `LAST30DAYS_MEMORY_DIR` from either the process env or `~/.config/last30days/.env`, so direct CLI invocations (`python3 scripts/last30days.py ...`) without `--save-dir` will still save when the env var is set. Mirrors the `LAST30DAYS_STORE` env-or-flag convention. Explicit `--save-dir` always wins.

When both `LAST30DAYS_API_KEY` and `LAST30DAYS_API_BASE` are set, the engine runs the research through that configured remote API instead of local sources (unless `--mock` is passed); `LAST30DAYS_API_BASE` is the endpoint and has no built-in default, so leaving either variable unset runs local sources normally. A configured `--corpus` / `LAST30DAYS_CORPUS_DIRS` is the privacy exception: the engine bypasses the hosted backend and runs locally so no file-derived input is forwarded. The invocation is otherwise unchanged: same flags, `--quick`/`--deep` map to search depth, a non-default `--register` is forwarded for server-side synthesis, progress lines still stream on stderr (`[narrate] step=...` plus a compact elapsed/eta line), and the report prints on stdout and saves to the memory dir as usual, so Steps 1-4 proceed normally on the output. The exception is research JSON: the remote endpoint does not return the local `Report` needed for the versioned agent profile, so use `--emit=json --json-profile=raw` for its existing server-response JSON contract. No per-source keys or setup-wizard credentials are needed for the search itself in this mode. Two engine exits need specific handling: exit code 3 means the API asked a clarifying question first - the engine prints the question and options on stderr; present them to the user and re-run with the chosen angle folded into the topic. An insufficient-credits failure (HTTP 402) prints the account's balance, the amount needed, and a billing link - relay those lines to the user verbatim; do not fall back to WebSearch-only synthesis.

**Developer-only eval capture:** `--record-fixtures <dir>` is a hidden direct-engine flag for maintaining the deterministic research-quality suite. It records scrubbed HTTP and CLI-adapter responses to `<dir>/http.json`; it is never part of the user-facing slash-command invocation.

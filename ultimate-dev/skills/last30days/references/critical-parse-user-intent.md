<!-- Moved verbatim from last30days/SKILL.md, the
     'critical-parse-user-intent' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## CRITICAL: Parse User Intent

Before doing anything, parse the user's input for:

1. **TOPIC**: What they want to learn about (e.g., "web app mockups", "Claude Code skills", "image generation")
2. **TARGET TOOL** (if specified): Where they'll use the prompts (e.g., "Nano Banana Pro", "ChatGPT", "Midjourney")
3. **QUERY TYPE**: What kind of research they want:
   - **PROMPTING** - "X prompts", "prompting for X", "X best practices" → User wants to learn techniques and get copy-paste prompts
   - **RECOMMENDATIONS** - "best X", "top X", "what X should I use", "recommended X" → User wants a LIST of specific things
   - **NEWS** - "what's happening with X", "X news", "latest on X" → User wants current events/updates
   - **COMPARISON** - "X vs Y", "X versus Y", "compare X and Y", "X or Y which is better" → User wants a side-by-side comparison
   - **GENERAL** - anything else → User wants broad understanding of the topic

Common patterns:
- `[topic] for [tool]` → "web mockups for Nano Banana Pro" → TOOL IS SPECIFIED
- `[topic] prompts for [tool]` → "UI design prompts for Midjourney" → TOOL IS SPECIFIED
- Just `[topic]` → "iOS design mockups" → TOOL NOT SPECIFIED, that's OK
- "best [topic]" or "top [topic]" → QUERY_TYPE = RECOMMENDATIONS
- "what are the best [topic]" → QUERY_TYPE = RECOMMENDATIONS
- "X vs Y" or "X versus Y" → QUERY_TYPE = COMPARISON, TOPIC_A = X, TOPIC_B = Y (split on ` vs ` or ` versus ` with spaces)

**IMPORTANT: Do NOT ask about target tool before research.**
- If tool is specified in the query, use it
- If tool is NOT specified, run research first, then ask AFTER showing results

**Store these variables:**
- `TOPIC = [extracted topic]`
- `TARGET_TOOL = [extracted tool, or "unknown" if not specified]`
- `QUERY_TYPE = [RECOMMENDATIONS | NEWS | HOW-TO | COMPARISON | GENERAL]`
- `REGISTER = [default | exec | dev | creator | eli5]` from an explicit `--register` argument, otherwise `LAST30DAYS_REGISTER`, otherwise `default`. A legacy `ELI5_MODE=true` config means `eli5` when no register was selected. Register words are controls, not part of TOPIC.
- `TOPIC_A = [first item]` (only if COMPARISON)
- `TOPIC_B = [second item]` (only if COMPARISON)

**Confirm the topic with a branded, truthful message. Build ACTIVE_SOURCES_LIST from the engine's own source diagnostic — do NOT infer availability by checking env vars or `.env`.** The engine resolves credentials at runtime from several places (process environment, `.env`, macOS Keychain, etc.), so a config-file check silently under-reports sources whenever a key is resolved at runtime rather than written literally in `.env`. Run the engine's `--diagnose` and read its result:

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just Read>"
"${LAST30DAYS_PYTHON}" "${SKILL_DIR}/scripts/last30days.py" --diagnose
```

`--diagnose` prints JSON. `ACTIVE_SOURCES_LIST` is its `available_sources` array — the engine's authoritative source set, computed after credential resolution. Map the tokens to display names: `reddit`→Reddit, `hackernews`→Hacker News, `polymarket`→Polymarket, `github`→GitHub, `digg`→Digg, `x`→X, `youtube`→YouTube, `tiktok`→TikTok, `instagram`→Instagram, `threads`→Threads, `pinterest`→Pinterest, `linkedin`→LinkedIn, `bluesky`→Bluesky, `perplexity`→Perplexity, `grounding`→Web, `jobs`→Jobs, `meta_ads`→Meta Ads, `corpus`→Your files, `dripstack`→DripStack.

- If EXCLUDE_SOURCES is set (comma-separated, case-insensitive): drop any matching source from ACTIVE_SOURCES_LIST before displaying

**Local corpus source:** If the user asks to include their own notes/documents, preserve each supplied directory as a repeatable `--corpus <dir>` engine flag. `LAST30DAYS_CORPUS_DIRS` activates persistent registered directories automatically. Do not WebSearch, upload, quote into a hosted request, or otherwise expose those paths or contents. Corpus retrieval is an offline source lane; its candidates also bypass remote reranker/fun-scoring prompts and use deterministic local scoring. The engine renders matches under the 🔒 **From your files** badge. The normal recency window uses file modification time; add `--corpus-all-time` only when the user explicitly asks to include older files. Corpus evidence is excluded from `--publish-html`, `library feed --publish`, and agent JSON by default. `LAST30DAYS_CORPUS_IN_EXPORT=1` is the explicit agent-JSON privacy opt-in; never enable it on the user's behalf. When a corpus is configured alongside `LAST30DAYS_API_KEY`/`LAST30DAYS_API_BASE`, the engine deliberately bypasses the hosted backend and runs locally.

**Perplexity source:** use it only when the user asks for Perplexity, Deep Research, or paid grounded synthesis, or when `perplexity` is already enabled in `INCLUDE_SOURCES` / `--search`. Prefer `PERPLEXITY_API_KEY`: normal runs use the controlled Agent API path, `search` returns raw Search API rows, and `both` combines them. Existing `OPENROUTER_API_KEY` installs stay compatible through one synchronous Sonar call; `search` and `both` fall back to Sonar because those direct APIs need a Perplexity key. Every normal mode is capped at one whole-topic planner subquery per command, including competitor fanout, and is not repeated during thin-source retries. With a direct key, normal Agent mode supplies only `web_search`, forces it for citation-critical grounding, uses a bounded step count, and supplies a local instruction. `sonar` remains a deprecated direct-key alias for `agent`. `LAST30DAYS_PERPLEXITY_AGENT_PRESET` is an explicit direct-key choice only; never set it for the user. `--deep-research` requires a normal positional topic. A direct key starts at most one paid `high`-preset background run with a 600-second default wall timeout; OpenRouter preserves the synchronous `perplexity/sonar-deep-research` fallback. It cannot be combined with discovery, drill, cached-only, competitor, or vs-mode. A local timeout does not stop a direct remote run. Report safe model and response metadata, but never expose request headers or raw tool traces.

**Reddit backend pin:** Reddit defaults to the free keyless backend. When `SCRAPECREATORS_API_KEY` is available, ScrapeCreators Reddit **search** backfills only if that free path returns **no items** (empty-only — a thin but non-empty free scrape does not spend credits). If the user wants paid coverage on thin free runs, tell them to set `LAST30DAYS_REDDIT_SC_MIN_ITEMS=<N>` (backfill when free yield is below N). If they say public Reddit is shallow, bot-gated, or missing nested comments, tell them they can set `LAST30DAYS_REDDIT_BACKEND=scrapecreators` alongside `SCRAPECREATORS_API_KEY` to make ScrapeCreators primary and keep the free path as fallback. Do not set either automatically for normal runs.

**Doctor health check:** When the user asks for a health check ("is X working?", "why is a source missing?", "what's broken?", "did setup work?"), run `"${LAST30DAYS_PYTHON}" "${SKILL_DIR}/scripts/last30days.py" doctor` (append `--json` for the machine contract) and relay the audit and fix prescriptions. `doctor` renders a **four-state audit** - **WORKING** (verified this run/last run or keyless-always-on), **TURNED ON - UNVERIFIED** (configured/opted-in but no run evidence), **NOT WORKING** (configured but failing, or the last run errored), **COULD BE ON** (available, not yet configured) - one line per source, plus a **CLI-health** block for sources that need a downloaded binary and indented **backup/comment** sub-lanes. Two on-demand modes: `doctor --postmortem` reads the last run's `last-report.json` and reports what actually broke per source (Failed/Partial/Succeeded with fix hints) - reach for it right after a run that returned less than expected; `doctor --probe` runs a **bounded** live test (free HTTP + keyless CLI sources only; credit-gated sources are never probed) to verify WORKING instead of guessing, and the same bounded probe auto-fires on a plain `doctor` when there is no fresh run. Per-source probe deadline is `LAST30DAYS_DOCTOR_PROBE_TIMEOUT` (default 10s). **MANDATORY standing rule.** Before research that depends on login-backed sources (X via cookies, Reddit's ScrapeCreators backfill), consult `doctor --cached --json` — it serves the report cached at `~/.config/last30days/doctor-cache.json` within its TTL (`LAST30DAYS_DOCTOR_TTL` seconds, default 900) for the cost of one file read. Re-run live `doctor` only when the cache is stale or the previous run reported a degraded login-backed source. When X is in ACTIVE_SOURCES_LIST, announce its predicted backend from the report's `sources.x.active_backend` (e.g. "X will use: bird") in the pre-research status line.

**Grok session expiry handling:** The grok CLI backend for X reports three auth states: `ok` (non-expired credentials), `expired` (access_token `expires_at` is past), and `missing` (never signed in). When doctor reports grok as **degraded** with an expiry timestamp, say "Grok session expired at {timestamp}; will attempt refresh at run time. If refresh fails, run `grok login --device-auth`" — not "Grok CLI is not signed in" (which misrepresents the history). The refresh attempt happens automatically at research time: an expired access_token does not prove the refresh_token is dead. If the run then fails with `auth_revoked` or `invalid_grant`, the user truly needs to re-login. **Host-facing copy:** when `sources.x.run_outcome.state` is `auth-failed` and the prior run's outcome was `ok`, say "X used {fallback} after the Grok session expired — run `grok login --device-auth` to restore first-party X." Avoid "Grok CLI is not signed in" when `run_outcome` history shows it worked recently. Avoid proactively installing grok or prompting about grok unless the user asks for first-party X search; the cookie and XAI_API_KEY paths work without a Grok subscription.


Then display (use "and more" if 5+ sources, otherwise list all with Oxford comma):

For GENERAL / NEWS / RECOMMENDATIONS / PROMPTING queries:
```
/last30days - searching {ACTIVE_SOURCES_LIST} for what people are saying about {TOPIC}.
```

For COMPARISON queries:
```
/last30days - comparing {TOPIC_A} vs {TOPIC_B} across {ACTIVE_SOURCES_LIST}.
```

Do NOT show a multi-line "Parsed intent" block with TOPIC=, TARGET_TOOL=, QUERY_TYPE= variables. Do NOT promise a specific time. Do NOT list sources that aren't configured.

Then proceed immediately to Step 0.45.

---

<!-- Moved verbatim from last30days/SKILL.md, the
     'research-execution' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Research Execution

### PRECONDITION GATE - read before running the script

**STOP. Before invoking `last30days.py`, verify ALL of the following are true for this turn:**

1. **Platform branch chosen.** You know whether this session has WebSearch (Claude Code) or does not (OpenClaw, raw CLI, Codex without web tools).
2. **If WebSearch IS available:** you MUST have run Step 0.55 (Pre-Research Intelligence - resolved subreddits, X handles, TikTok hashtags/creators, Instagram creators, GitHub user/repo where applicable) AND Step 0.75 (Query Planner - produced `QUERY_PLAN_JSON` with 2-4 subqueries). These are NOT optional. If either was skipped, return to that step now.
3. **If WebSearch is NOT available:** you MUST add `--auto-resolve` to the command instead. Do not attempt Steps 0.55 / 0.75 without WebSearch.
4. **The command you are about to run uses `--emit=compact`.** `--emit md` is a debugging/inspection mode and is DISALLOWED as the primary user-facing flow. If you find yourself about to run `--emit md`, stop and switch to `--emit=compact`.
5. **On WebSearch platforms the command MUST include `--plan 'QUERY_PLAN_JSON'`** plus every resolved handle/subreddit/hashtag/creator flag from Step 0.55. Omit only flags whose value was not resolvable.

**Degraded path (missing any of the above on a WebSearch platform) is a known regression shape. It produces bland 4-bullet summaries instead of rich synthesis. Do not take it.**

---

**Grok Bot X connector recipe (only when `LAST30DAYS_X_HOST_LANE=1` is exported - see the Grok Bot host rule in HOW TO INVOKE).** On a Grok Bot with the X connector, YOU fetch X through the connector before the engine command and hand the engine the file; the engine then calls no X backend, plans `x` in, and the footer's X provenance reads "X via X connector". Do this before the Step 1 command below.

1. **Calls (the connector's post-search tool, e.g. `search_posts_all`).** Window = the engine's date range (`--days`, default 30: `from` is today minus the day count, `to` is today). Depth count = 10 (`--quick`) / 30 (default) / 60 (`--deep`).
   - One `topic` call: the topic query plus `-is:retweet`, the window, and the depth count.
   - Per `--x-handle` handle: one `from` call (`from:<handle> -is:retweet`, 8 posts) and one `mention` call (`@<handle> -is:retweet`, 5 posts).
   - Per `--x-related` handle: one `related` call (`from:<handle> -is:retweet`, 3 posts).
   - If the tool rejects the window or count parameters, omit them, keep at most the depth count per call, and write `"status": "partial"` with `"error": "window-unsupported"`.
   - If the connector itself fails, write `"status": "error"` with `"calls": []` and a short category in `error`: `credits`, `not-connected`, or `unavailable` - never raw tool output, never an account or app id.
2. **Envelope.** Exactly these top-level fields; every post carries the eight flat fields and nothing else (no URLs, media, or author objects); at most the depth count per call. A fresh `generated_at` (the engine rejects an envelope older than 6 hours) and a `topic` identical to the engine's topic string:

```json
{
  "schema": "last30days-x-posts/1",
  "generated_at": "{ISO_8601_UTC_NOW}",
  "topic": "{TOPIC}",
  "window": {"from": "{YYYY-MM-DD}", "to": "{YYYY-MM-DD}"},
  "provider": "x-connector",
  "status": "ok",
  "calls": [
    {"lane": "topic", "handles": [], "posts": [
      {"id": "1963000000000000000", "author_handle": "someone", "created_at": "2026-09-07T10:00:00Z", "text": "post text", "likes": 12, "reposts": 3, "replies": 1, "quotes": 0}
    ]},
    {"lane": "from", "handles": ["{RESOLVED_HANDLE}"], "posts": []},
    {"lane": "mention", "handles": ["{RESOLVED_HANDLE}"], "posts": []},
    {"lane": "related", "handles": ["{RELATED_HANDLE}"], "posts": []}
  ]
}
```

   Omit the `from` / `mention` / `related` calls when the run has no `--x-handle` / `--x-related`; `handles` must be the run's own handles. `id` is the post's numeric id as a string; `author_handle` is the username without `@`.
3. **Write the file - post text is attacker-controlled and never goes unquoted into a shell command.** Use the tool's own file output when it has one; otherwise a single-quoted heredoc (never unquoted) into a `.json` path outside `~/.config`, in the SAME Bash call as the engine command (the trap removes it on exit). Two rules keep a post from closing the heredoc early: emit the envelope as ONE line of compact JSON (newlines inside post text stay escaped as `\n`; never pretty-print), and replace `{X_POSTS_NONCE}` in BOTH sentinel lines with 12 random letters and digits you generate fresh for this run, so no post text can equal the closing line:

```bash
X_POSTS_DIR=$(mktemp -d "${TMPDIR:-/tmp}/last30days-x-posts.XXXXXX")
X_POSTS_FILE="$X_POSTS_DIR/x-posts.json"
trap 'rm -rf "$X_POSTS_DIR"' EXIT
cat >| "$X_POSTS_FILE" <<'X_POSTS_EOF_{X_POSTS_NONCE}'
{X_POSTS_ENVELOPE_JSON}
X_POSTS_EOF_{X_POSTS_NONCE}
```

   Run it directly in your shell tool, never wrapped in `bash -lc '...'` (same rule as the plan tmpfile).
4. **Engine.** Add `--x-posts "$X_POSTS_FILE"` to the Step 1 command (the file path only, never inline JSON); every other flag stays as usual. Comparison runs: write one envelope per entity (its `topic` is that entity's name) and put the path in that entity's `--competitors-plan` entry as `"x_posts": "/abs/path/x-posts.json"`; a bare `--x-posts` on a comparison run exits 2. If the engine exits 2 naming the envelope, fix the file it names or re-run without `--x-posts`; X is then absent for that run.
5. **After the run.** The stats line reads "X via X connector". The engine's one receipt line (accepted / dropped counts, on stderr) is diagnostics only: never narrate it in the deliverable (LAW 9).

**Step 1: Run the research script WITH your query plan (FOREGROUND)**

**CRITICAL: Run this command in the FOREGROUND with a 5-minute timeout. Do NOT use run_in_background. The full output contains Reddit, X, AND YouTube data that you need to read completely.**

**IMPORTANT: Pass your QUERY_PLAN_JSON via the --plan flag. This tells the Python script to use YOUR plan instead of calling Gemini.**

**IMPORTANT: Include `--x-handle={RESOLVED_HANDLE}` in the command. For comparison mode: Pass `--x-handle={TOPIC_A_HANDLE}` to the first pass, `--x-handle={TOPIC_B_HANDLE}` to the second pass, and both to the head-to-head pass. Also include `--subreddits={RESOLVED_SUBREDDITS}`, `--tiktok-hashtags={RESOLVED_HASHTAGS}`, `--tiktok-creators={RESOLVED_TIKTOK_CREATORS}`, and `--ig-creators={RESOLVED_IG_CREATORS}` from Step 0.55. Omit any flag where the value was not resolved (empty).**

```bash
# SKILL_DIR = absolute path of the directory containing THIS SKILL.md you just Read.
# Substitute the actual path below — your harness told you where this file lives via
# the Read tool result. Examples:
#   Read ~/.claude/skills/last30days/SKILL.md      → SKILL_DIR=$HOME/.claude/skills/last30days
#   Read ~/.codex/skills/last30days/SKILL.md       → SKILL_DIR=$HOME/.codex/skills/last30days
#   Read ~/.claude/plugins/cache/last30days-skill/last30days/3.11.0/skills/last30days/SKILL.md
#     → SKILL_DIR=$HOME/.claude/plugins/cache/last30days-skill/last30days/3.11.0/skills/last30days
# scripts/last30days.py is always a direct child of SKILL_DIR (every install layout
# packages SKILL.md and scripts/ as siblings).
SKILL_DIR="<absolute path of the directory containing the SKILL.md you Read>"

if [ ! -f "$SKILL_DIR/scripts/last30days.py" ]; then
  echo "ERROR: scripts/last30days.py not found under SKILL_DIR=$SKILL_DIR" >&2
  echo "Re-check the directory of the SKILL.md you Read and substitute it as SKILL_DIR above." >&2
  exit 1
fi

"${LAST30DAYS_PYTHON}" "${SKILL_DIR}/scripts/last30days.py" $ARGUMENTS --emit=compact --save-dir="${LAST30DAYS_MEMORY_DIR}" --save-suffix=v3
```

**If you ran Steps 0.55 and 0.75 (agent planning), pass the plan via a tmpfile and add the targeting flags:**

```bash
# Write QUERY_PLAN_JSON to a tmpfile before the engine invocation above.
# parse_plan() reads file paths transparently; this avoids inline-JSON
# shell-quoting hazards (apostrophes in search_query / ranking_query
# strings break single-quoted command-line JSON). Trailing XXXXXX (no
# .json suffix) for BSD/macOS portability — BSD mktemp only substitutes
# X's at the end of the template.
QUERY_PLAN_FILE=$(mktemp "${TMPDIR:-/tmp}/last30days-plan.XXXXXX")
trap 'rm -f "$QUERY_PLAN_FILE"' EXIT
# >| not >: mktemp already created the file, so a plain > is refused under
# `set -o noclobber` (leaving the plan empty -> deterministic fallback).
cat >| "$QUERY_PLAN_FILE" <<'PLAN_EOF'
{QUERY_PLAN_JSON_FROM_STEP_0.75}
PLAN_EOF
```

**Run this block directly in your shell tool. Do NOT wrap it in `bash -lc '...'` or `zsh -lc '...'`** - the outer single quotes terminate at the first apostrophe inside the heredoc body (a ranking string like `What did Kanye West's album do?`), which aborts the command with a `zsh: unmatched "` error before the engine ever runs. The quoted `<<'PLAN_EOF'` marker already makes the heredoc body apostrophe-safe; the `-lc '...'` wrapper is what breaks it.

Then add to the engine command:

- `--plan "$QUERY_PLAN_FILE"` (path to the file you just wrote)
- `--x-handle={RESOLVED_HANDLE}` (from Step 0.5)
- `--subreddits={RESOLVED_SUBREDDITS}` (broad/category subs, from Step 0.55)
- `--dedicated-subreddits={RESOLVED_DEDICATED_SUBREDDITS}` (entity-home subs, from Step 0.55; pulled in full + floor-exempt)
- `--tiktok-hashtags={RESOLVED_HASHTAGS}` (from Step 0.55)
- `--tiktok-creators={RESOLVED_TIKTOK_CREATORS}` (from Step 0.55)
- `--ig-creators={RESOLVED_IG_CREATORS}` (from Step 0.55)
- `--github-user={RESOLVED_GITHUB_USER}` (from Step 0.5b, person topics only)
- `--github-repo={RESOLVED_GITHUB_REPOS}` (from Step 0.5c, product/project topics only)
- `--trustpilot-domain={RESOLVED_TRUSTPILOT_DOMAIN}` (from Step 0.5d, company/brand topics; the flag also auto-activates Trustpilot)
- Omit any flag where the value was not resolved (empty).

**If you skipped Steps 0.55 and 0.75 (no WebSearch -- OpenClaw, Codex, etc.), add:**
- `--auto-resolve` (the engine will use Brave/Exa/Serper to discover subreddits and context before planning)

**If you skipped Steps 0.55 and 0.75 (no WebSearch), run the command as-is.** The Python engine will plan internally.

Use a **timeout of 300000** (5 minutes) on the Bash call. The script typically takes 1-3 minutes.

The script will automatically:
- Detect available API keys
- Run Reddit/X/YouTube/TikTok/Instagram/Hacker News/Polymarket searches
- Output ALL results including YouTube transcripts, TikTok captions, Instagram captions, HN comments, and prediction market odds

**Read the ENTIRE output.** It contains EIGHT data sections in this order: Reddit items, X items, YouTube items, TikTok items, Instagram Reels items, Hacker News items, Polymarket items, and WebSearch items. If you miss sections, you will produce incomplete stats.

**YouTube items in the output look like:** `**{video_id}** (score:N) {channel_name} [N views, N likes]` followed by a title, URL, **transcript highlights** (pre-extracted quotable excerpts from the video), and an optional full transcript in a collapsible section. **Quote the highlights directly in your synthesis.** When YouTube items also include top comments (default-on once a ScrapeCreators key is set; suppress via `EXCLUDE_SOURCES=youtube_comments`), quote those too with their like counts - they capture how viewers reacted to the video. Transcript highlights and top comments are complementary signals; use both when present. Attribute transcript quotes to the channel name, comment quotes to the commenter. Count them and include them in your synthesis and stats block.

**TikTok items in the output look like:** `**{TK_id}** (score:N) @{creator} [N views, N likes]` followed by a caption, URL, hashtags, and optional caption snippet. Count them and include them in your synthesis and stats block.

**Instagram Reels items in the output look like:** `**{IG_id}** (score:N) @{creator} (date) [N views, N likes]` followed by caption text, URL, and optional transcript. Count them and include them in your synthesis and stats block. Instagram provides unique creator/influencer perspective - weight it alongside TikTok.

---

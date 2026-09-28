<!-- Moved verbatim from understand/SKILL.md, the
     'options' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Options

- `$ARGUMENTS` may contain:
  - `--full` — Force a full rebuild, ignoring any existing graph
  - `--auto-update` — Enable automatic graph updates on commit (writes `autoUpdate: true` to `$UA_DIR/config.json`)
  - `--no-auto-update` — Disable automatic graph updates (writes `autoUpdate: false` to `$UA_DIR/config.json`)
  - `--review` — Run full LLM graph-reviewer instead of inline deterministic validation
  - `--language <lang>` — Generate all textual content (summaries, descriptions, tags, titles, languageNotes, languageLesson) in the specified language. Accepts ISO 639-1 codes (`zh`, `ja`, `ko`, `en`, `es`, `fr`, `de`, etc.) or friendly names (`chinese`, `japanese`, `korean`, `english`, `spanish`, etc.). Locale variants supported: `zh-TW`, `zh-HK`, etc. Defaults to `en` (English). Stores preference in `$UA_DIR/config.json` for consistency across incremental updates.
  - `--exclude <patterns>` — Comma-separated glob patterns for additional files/directories to exclude from analysis (e.g., `--exclude "tests/*,docs/*"`). These patterns take highest priority over built-in defaults and `.understandignore` rules. Supports gitignore syntax including `!` negation.
  - A directory path (e.g. `/path/to/repo` or `../other-project`) — Analyze the given directory instead of the current working directory

---

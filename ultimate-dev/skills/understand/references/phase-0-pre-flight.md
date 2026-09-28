<!-- Moved verbatim from understand/SKILL.md, the
     'phase-0-pre-flight' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 0 — Pre-flight

Determine whether to run a full analysis or incremental update.

1. **Resolve `PROJECT_ROOT`:**
   - Parse `$ARGUMENTS` for a non-flag token (any argument that does not start with `--`). If found, treat it as the target directory path.
     - If the path is relative, resolve it against the current working directory.
     - Verify the resolved path exists and is a directory (run `test -d <path>`). If it does not exist or is not a directory, report an error to the user and **STOP**.
     - Set `PROJECT_ROOT` to the resolved absolute path.
   - If no directory path argument is found, set `PROJECT_ROOT` to the current working directory.
   - **Worktree redirect.** If `PROJECT_ROOT` is inside a git worktree (not the main checkout), redirect output to the main repository root. Worktrees managed by Claude Code are ephemeral — the data directory (`.ua/`, or legacy `.understand-anything/`) written there is destroyed when the session ends, taking the knowledge graph with it (issue #133). Detect a worktree by comparing `git rev-parse --git-dir` against `git rev-parse --git-common-dir`; in a normal checkout or submodule they resolve to the same path, in a worktree they differ and the parent of `--git-common-dir` is the main repo root.

     ```bash
     COMMON_DIR=$(git -C "$PROJECT_ROOT" rev-parse --git-common-dir 2>/dev/null)
     GIT_DIR=$(git -C "$PROJECT_ROOT" rev-parse --git-dir 2>/dev/null)
     if [ -n "$COMMON_DIR" ] && [ -n "$GIT_DIR" ]; then
       COMMON_ABS=$(cd "$PROJECT_ROOT" && cd "$COMMON_DIR" 2>/dev/null && pwd -P)
       GIT_ABS=$(cd "$PROJECT_ROOT" && cd "$GIT_DIR" 2>/dev/null && pwd -P)
       if [ -n "$COMMON_ABS" ] && [ "$COMMON_ABS" != "$GIT_ABS" ]; then
         MAIN_ROOT=$(dirname "$COMMON_ABS")
         if [ -d "$MAIN_ROOT" ] && [ "${UNDERSTAND_NO_WORKTREE_REDIRECT:-0}" != "1" ]; then
           echo "[understand] Detected git worktree at $PROJECT_ROOT"
           echo "[understand] Redirecting output to main repo root: $MAIN_ROOT"
           echo "[understand] (Set UNDERSTAND_NO_WORKTREE_REDIRECT=1 to keep PROJECT_ROOT as the worktree.)"
           PROJECT_ROOT="$MAIN_ROOT"
         fi
       fi
     fi
     ```

     Set `UNDERSTAND_NO_WORKTREE_REDIRECT=1` if you intentionally want a per-worktree graph (rare — most users want the redirect).
1.5. **Ensure the plugin is built.** Later phases invoke Node scripts that import `@understand-anything/core`. On a fresh install `packages/core/dist/` does not exist yet — build once.

   **Important:** do **not** assume the plugin root is simply two directories above the skill path string. In many installations `~/.agents/skills/understand` is a symlink into the real plugin checkout. Prefer runtime-provided plugin roots first (for Claude), then fall back to universal symlinks, skill symlink resolution, and common clone-based install paths.

   Resolve the plugin root like this:

   ```bash
   SKILL_REAL=$(realpath ~/.agents/skills/understand 2>/dev/null || readlink -f ~/.agents/skills/understand 2>/dev/null || echo "")
   SELF_RELATIVE=$([ -n "$SKILL_REAL" ] && cd "$SKILL_REAL/../.." 2>/dev/null && pwd || echo "")
   COPILOT_SKILL_REAL=$(realpath ~/.copilot/skills/understand 2>/dev/null || readlink -f ~/.copilot/skills/understand 2>/dev/null || echo "")
   COPILOT_SELF_RELATIVE=$([ -n "$COPILOT_SKILL_REAL" ] && cd "$COPILOT_SKILL_REAL/../.." 2>/dev/null && pwd || echo "")

   PLUGIN_ROOT=""
   for candidate in \
     "${CLAUDE_PLUGIN_ROOT}" \
     "$HOME/.understand-anything-plugin" \
     "$SELF_RELATIVE" \
     "$COPILOT_SELF_RELATIVE" \
     "$HOME/<agent-config-dir>/understand-anything/understand-anything-plugin" \
     "$HOME/.opencode/understand-anything/understand-anything-plugin" \
     "$HOME/.pi/understand-anything/understand-anything-plugin" \
     "$HOME/understand-anything/understand-anything-plugin"; do
     if [ -n "$candidate" ] && [ -f "$candidate/package.json" ] && [ -f "$candidate/pnpm-workspace.yaml" ]; then
       PLUGIN_ROOT="$candidate"
       break
     fi
   done

   if [ -z "$PLUGIN_ROOT" ]; then
     echo "Error: Cannot find the understand-anything plugin root."
     echo "Checked:"
     echo "  - ${CLAUDE_PLUGIN_ROOT:-<unset CLAUDE_PLUGIN_ROOT>}"
     echo "  - $HOME/.understand-anything-plugin"
     echo "  - ${SELF_RELATIVE:-<unresolved path derived from ~/.agents/skills/understand>}"
     echo "  - ${COPILOT_SELF_RELATIVE:-<unresolved path derived from ~/.copilot/skills/understand>}"
     echo "  - $HOME/<agent-config-dir>/understand-anything/understand-anything-plugin"
     echo "  - $HOME/.opencode/understand-anything/understand-anything-plugin"
     echo "  - $HOME/.pi/understand-anything/understand-anything-plugin"
     echo "  - $HOME/understand-anything/understand-anything-plugin"
     echo "Make sure the plugin is installed correctly."
     exit 1
   fi

   if [ ! -f "$PLUGIN_ROOT/packages/core/dist/index.js" ]; then
     cd "$PLUGIN_ROOT" && (pnpm install --frozen-lockfile 2>/dev/null || pnpm install) && pnpm --filter @understand-anything/core build
   fi
   ```

   If `pnpm` is missing, report to the user: "Install Node.js ≥ 22 and pnpm ≥ 10, then re-run `/understand`."

1.7. **Resolve the data directory `$UA_DIR`.** All Understand-Anything artifacts live in the project's data directory. Resolve it once, now that `$PROJECT_ROOT` is known, and reuse `$UA_DIR` for every read and write in later phases:
   ```bash
   UA_DIR="$PROJECT_ROOT/$([ -d "$PROJECT_ROOT/.understand-anything" ] && echo .understand-anything || echo .ua)"
   ```
   This keeps the legacy `.understand-anything/` directory when it already exists (existing projects keep working with no migration) and uses the new `.ua/` otherwise. Because each phase may run in a fresh shell, treat `$UA_DIR` — like `$PROJECT_ROOT` — as a value you carry forward and substitute; re-resolve it with the line above if a later command block needs it in a new shell.

2. Get the current git commit hash:
   ```bash
   git rev-parse HEAD
   ```
3. Create the intermediate and temp output directories:
   ```bash
   mkdir -p "$UA_DIR/intermediate"
   mkdir -p "$UA_DIR/tmp"
   ```
3.1. **Purge stale trash dirs.** Phase 7 cleanup `mv`s scratch dirs into `.trash-<timestamp>/` rather than `rm -rf`ing them directly (see issue #301), so that destructive-action gates on hardened hosts don't trip on just-created paths. Reclaim the space here once the trash is older than 7 days — by this point any freshness-window check has long since stopped caring about those dirs:
   ```bash
   find "$UA_DIR/" -maxdepth 1 -type d -name '.trash-*' -mtime +7 -exec rm -rf {} + 2>/dev/null || true
   ```
3.5. **Auto-update configuration:**
    - If `--auto-update` is in `$ARGUMENTS`: write `{"autoUpdate": true}` to `$UA_DIR/config.json`
    - If `--no-auto-update` is in `$ARGUMENTS`: write `{"autoUpdate": false}` to `$UA_DIR/config.json`
    - These flags only set the config — analysis proceeds normally regardless.

 3.6. **Language configuration:**
    - Parse `$ARGUMENTS` for `--language <lang>` flag. If found, extract the language code.
    - **Language code normalization:** Map friendly names to ISO codes:
      - `chinese` → `zh`, `japanese` → `ja`, `korean` → `ko`, `english` → `en`, `spanish` → `es`, `french` → `fr`, `german` → `de`, `portuguese` → `pt`, `russian` → `ru`, `arabic` → `ar`, etc.
      - Locale variants: `zh-TW`, `zh-HK`, `zh-CN`, `pt-BR`, etc. are preserved as-is.
    - If `--language` is NOT specified:
      - **Stored preference wins.** If `$UA_DIR/config.json` has an `outputLanguage` field, set `$OUTPUT_LANGUAGE` to it and skip the rest.
      - **Otherwise detect (first run only).** Infer the predominant language of the user's conversation as an ISO 639-1 code (`$DETECTED_LANG`). If it is `en` or cannot be confidently determined, set `$OUTPUT_LANGUAGE=en` and proceed silently — no prompt (English users see no change).
      - **If `$DETECTED_LANG` ≠ `en`, confirm once before analyzing:** tell the user you detected `<language>` and ask whether to generate all content in it; they press Enter/"yes" to accept, or type another language code/name to override (normalize via the friendly-name map above). If running non-interactively (no reply possible), skip the wait, use `$DETECTED_LANG`, and print a one-line notice instead of blocking.
      - **Persist** the resolved `$OUTPUT_LANGUAGE` (including `en`) into `config.json` so it never re-prompts for this project.
    - If `--language` IS specified:
      - Update `$UA_DIR/config.json` with the new language: merge `{"outputLanguage": "<lang>"}` into existing config.
      - Store as `$OUTPUT_LANGUAGE` for use throughout all phases.
    - **Language directive template:** Store as `$LANGUAGE_DIRECTIVE`:
      ```markdown
      > **Language directive**: Generate all textual content (summaries, descriptions, tags, titles, languageNotes, languageLesson) in **{language}**. Maintain technical accuracy while using natural, native-level phrasing in the target language. Keep technical terms in English when no standard translation exists (e.g., "middleware", "hook", "barrel").
      ```

 3.7. **Exclude patterns:**
    - Parse `$ARGUMENTS` for `--exclude <patterns>` flag. If found, extract the comma-separated patterns string.
    - Split on commas, trim whitespace from each pattern, and filter out empty entries.
    - Store the patterns as `$EXCLUDE_PATTERNS` (comma-joined for passing to downstream scripts: `"tests/*,docs/*"`).
    - These patterns take highest priority — they are applied on top of default patterns and `.understandignore` rules. Use `!` prefix to force-include files that would otherwise be excluded.
    - Incremental preparation re-scans the current inventory, so newly supplied exclusions take effect immediately and remove any previously analyzed files they now cover.

4. **Check for subdomain knowledge graphs to merge:**
   List all `*knowledge-graph*.json` files in `$UA_DIR/` **excluding** `knowledge-graph.json` itself (e.g. `frontend-knowledge-graph.json`, `backend-knowledge-graph.json`). If any subdomain graphs exist, run the merge script bundled with this skill (located next to this SKILL.md file — use the skill directory path, not the project root):
   ```bash
   python "<SKILL_DIR>/merge-subdomain-graphs.py" "$PROJECT_ROOT"
   ```
   The script discovers subdomain graphs, loads the existing `knowledge-graph.json` as a base (if present), and merges everything into `knowledge-graph.json` (deduplicating nodes and edges). Report the merge summary to the user, then continue with the merged graph.

5. Check if `$UA_DIR/knowledge-graph.json` exists. If it does, read it.
6. Check if `$UA_DIR/meta.json` exists. If it does, read its `gitCommitHash` and store it as `$LAST_COMMIT_HASH`.
7. **Decision logic:**

   | Condition | Action |
   |---|---|
   | `--full` flag in `$ARGUMENTS` | Full analysis (all phases) |
   | No existing graph or meta | Full analysis (all phases) |
   | Existing graph + explicit `--exclude` | Run deterministic incremental preparation even when the commit hash is unchanged, so the new inventory rules take effect immediately |
   | `--review` flag + existing graph + unchanged commit hash | Skip to Phase 6 (review-only — reuse existing assembled graph) |
   | Existing graph + unchanged commit hash | Ask the user: "The graph is up to date at this commit. Would you like to: **(a)** run a full rebuild (`--full`), **(b)** run the LLM graph reviewer (`--review`), or **(c)** do nothing?" Then follow their choice. If they pick (c), STOP. |
   | Existing graph + changed files | Run deterministic incremental preparation below |

   **Review-only path:** Copy the existing `knowledge-graph.json` to `$UA_DIR/intermediate/assembled-graph.json`, then jump directly to Phase 6 step 3.

   For incremental updates, do **not** construct the changed-file list by hand. Run the bundled reconciliation helper with the previous analyzed commit. Pass `--exclude "$EXCLUDE_PATTERNS"` only when the option is non-empty:
   ```bash
   node "<SKILL_DIR>/prepare-incremental.mjs" \
     "$PROJECT_ROOT" \
     "$LAST_COMMIT_HASH"
   ```

   With explicit exclusions:
   ```bash
   node "<SKILL_DIR>/prepare-incremental.mjs" \
     "$PROJECT_ROOT" \
     "$LAST_COMMIT_HASH" \
     --exclude "$EXCLUDE_PATTERNS"
   ```

   The helper uses parameterized `git diff --name-status -z`, performs a fresh deterministic scan with the current `.understandignore` / `--exclude` rules, compares structural fingerprints, selectively refreshes imports, and atomically writes:
   - `$UA_DIR/intermediate/incremental-plan.json`
   - `$UA_DIR/intermediate/scan-result.json`
   - `$UA_DIR/intermediate/changed-files.json`
   - `$UA_DIR/intermediate/batch-existing.json` for partial/architecture updates
   - `$UA_DIR/intermediate/incremental-symbol-baseline.json`, the previous node inventory for reanalyzed files, bound to the base/head commits

   Read `incremental-plan.json` and store its `action`, `filesToReanalyze`, `deletedFiles`, `rerunArchitecture`, and `rerunTour` values. Follow this gate:

   | Prepared action | Next step |
   |---|---|
   | `SKIP` | Run `node "<SKILL_DIR>/finalize-incremental.mjs" "$PROJECT_ROOT"`. It updates graph metadata, scan, fingerprints, and meta for cosmetic or irrelevant changes, but intentionally advances nothing for generated-artifact-only commits. Without `--review`, report zero LLM tokens spent and **STOP**. With explicit `--review`, copy `$UA_DIR/knowledge-graph.json` to `$UA_DIR/intermediate/assembled-graph.json` and jump to the `--review` graph-reviewer path in Phase 6 instead of stopping. |
   | `PARTIAL_UPDATE` | Skip Phase 0.5 and Phase 1; continue with the incremental Phase 1.5/2 path. |
   | `ARCHITECTURE_UPDATE` | Skip Phase 0.5 and Phase 1; continue with incremental analysis, then rerun Phase 4 and Phase 5. |
   | `FULL_UPDATE` | Switch to the existing full pipeline beginning at Phase 0.5. Do not patch fingerprints or metadata from the incremental helper. |

   `filesToReanalyze` contains only current, non-ignored files with structural changes. Deletions, newly ignored files, cosmetic changes, and generated artifacts are never passed to file-analyzer.

8. **Collect project context for subagent injection:**
   - Read `README.md` (or `README.rst`, `readme.md`) from `$PROJECT_ROOT` if it exists. Store as `$README_CONTENT` (first 3000 characters).
   - Read the primary package manifest (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`) if it exists. Store as `$MANIFEST_CONTENT`.
   - Capture the top-level directory tree:
     ```bash
     find "$PROJECT_ROOT" -maxdepth 2 -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/dist/*' | head -100
     ```
     Store as `$DIR_TREE`.
   - Detect the project entry point by checking for common patterns (in order): `src/index.ts`, `src/main.ts`, `src/App.tsx`, `index.js`, `main.py`, `manage.py`, `app.py`, `wsgi.py`, `asgi.py`, `run.py`, `__main__.py`, `main.go`, `cmd/*/main.go`, `src/main.rs`, `src/lib.rs`, `src/main/java/**/Application.java`, `Program.cs`, `config.ru`, `index.php`. Store first match as `$ENTRY_POINT`.

---

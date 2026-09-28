<!-- Moved verbatim from understand/SKILL.md, the
     'phase-0-5-ignore-configuration-full-analysis-only' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 0.5 — Ignore Configuration (full analysis only)

Set up and verify the `.understandignore` file before a full scan. Incremental preparation already applies the current ignore rules and must skip this confirmation phase.

1. Check if `$UA_DIR/.understandignore` exists.
2. **If it does NOT exist**, generate a starter file by invoking the bundled script (delegates to `generateStarterIgnoreFile` in `@understand-anything/core`, which reads `.gitignore`, deduplicates against built-in defaults, and emits language-grouped test-file suggestions). Pass `$PLUGIN_ROOT` via the env so the script doesn't have to re-derive it from its own path (which breaks for copied skill installs):
     ```bash
     PLUGIN_ROOT="$PLUGIN_ROOT" node "<SKILL_DIR>/generate-ignore.mjs" "$PROJECT_ROOT"
     ```
   - Report to the user:
     > Generated `$UA_DIR/.understandignore` with suggested exclusions based on your project structure. Please review it and uncomment any patterns you'd like to exclude from analysis. When ready, confirm to continue.
   - **Wait for user confirmation before proceeding.**
3. **If it already exists**, report:
   > Found `$UA_DIR/.understandignore`. Review it if needed, then confirm to continue.
   - **Wait for user confirmation before proceeding.**
4. After confirmation, proceed to Phase 1.

---

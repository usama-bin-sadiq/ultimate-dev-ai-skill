<!-- Moved verbatim from understand/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Phase 3 — ASSEMBLE REVIEW

Run this phase for **full analysis only**. Both incremental actions skip assemble-reviewer: their deterministic merge/reconciliation checks replace this whole-graph LLM pass. The user-facing `--review` option is still honored later by the graph-reviewer in Phase 6.

Report to the user: `[Phase 3/7] Reviewing assembled graph...`

Pass these parameters in the dispatch prompt:

> Review the assembled graph at `$UA_DIR/intermediate/assembled-graph.json`.
> Project root: `$PROJECT_ROOT`
> Batch files are at: `$UA_DIR/intermediate/batch-*.json`
> Write review output to: `$UA_DIR/intermediate/assemble-review.json`
>
> **Merge script report:**
> ```
> <paste the full stderr output from merge-batch-graphs.py>
> ```
>
> **Import map for cross-batch edge verification:**
> ```json
> $IMPORT_MAP
> ```

After the subagent completes, read `$UA_DIR/intermediate/assemble-review.json` and add any notes to `$PHASE_WARNINGS`.

---

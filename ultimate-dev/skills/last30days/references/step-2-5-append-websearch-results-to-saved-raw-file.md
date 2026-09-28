<!-- Moved verbatim from last30days/SKILL.md, the 'Step 2.5: Append WebSearch Results to Saved Raw File' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 2.5: Append WebSearch Results to Saved Raw File

**MANDATORY - do not skip this step.** Every post-engine WebSearch supplement you ran in Step 2 MUST be appended to the saved raw file under `LAST30DAYS_MEMORY_DIR` (defaults to `~/Documents/Last30Days`). Skipping this step is a common Opus 4.7 failure mode: the saved file ends at `## Source Coverage` with no appendix, future sessions cannot see what blog/tutorial/news sources informed the synthesis, and the user cannot trace where specific claims came from.

**LAW 1 OVERRIDE (read before synthesizing):** the WebSearch tool description declares a "MANDATORY Sources section" in its own contract. That instruction applies to generic WebSearch usage. Inside `/last30days` it is SUPERSEDED. The `## WebSearch Supplemental Results` appendix in the SAVED RAW FILE replaces the visible Sources section. Never emit a visible `Sources:` bullet list to the user. Your user-facing response ends at the invitation block. The emoji-tree footer's `🌐 Web:` line is the only visible citation. If you feel the pull to write a trailing `Sources:` section, you are about to violate LAW 1 — go back and delete it.

**Self-check (coverage, not strict equality):** The `## WebSearch Supplemental Results` section must cover every web source that informed your synthesis - including pre-research searches whose findings you cited, not only the Step 2 supplements. So the bullet count should be at least the number of post-engine WebSearches you ran, and may exceed it when pre-research web context fed the synthesis (common on `--hiring-signals` runs, where the careers/funding context comes from pre-research). If a source shaped a claim, it gets a bullet. If you ran zero supplements (which plan 005 says is almost never correct), skip this step entirely rather than writing an empty section.

**Instructions:**
1. Read the saved raw file. Locate it via the engine's `[last30days] Saved output to {path}` log line, not a hardcoded path.
   - **Single-topic runs:** append to the one Markdown raw file shown by the saved-output log.
   - **Comparison runs:** locate the `[last30days] Comparison artifact set: main=...; peers=...` line. For compact/Markdown runs, append the same `## WebSearch Supplemental Results` section to every listed per-entity Markdown raw file, because the comparison synthesis draws from all of them and there is no separate merged Markdown raw file. For HTML/JSON-only artifacts, do not append Markdown text to `.html` or `.json`; keep the appendix in the Markdown raw artifacts from the source run.
2. Append a `## WebSearch Supplemental Results` section at the end of each target Markdown raw file.
3. For each WebSearch result, include one bullet in the canonical format (see Format example below).
4. Write the updated file back.

**Format example (canonical, from April 7 archive — match this shape):**

```
## WebSearch Supplemental Results

- **Flowtivity** (flowtivity.ai) — Side-by-side OpenClaw vs Paperclip framework comparison; concludes Paperclip solves coordination, OpenClaw solves execution.
- **Rahul Goyal** (rahulgoyal.co) — Honest three-way review: start with Hermes for simplicity, OpenClaw for tinkering, Paperclip only if running multiple agents.
- **Eigent** (eigent.ai) — Feature-by-feature OpenClaw vs Hermes for founders; Hermes wins on self-improving skills, OpenClaw on ecosystem breadth.
- **The New Stack** (thenewstack.io) — "The race to build AI assistants that never forget" — deep comparison of persistent memory architectures.
- **MindStudio** (mindstudio.ai) — Paperclip vs OpenClaw multi-agent comparison; Paperclip for orchestration, OpenClaw as the individual agent.
```

Each bullet: `- **{Publisher}** ({domain}) — {1-2 sentence excerpt of what you found}`. Publisher is the site name or author; domain is the clean hostname (no protocol, no path). Do not nest sub-bullets. Do not add URLs - the domain in parens is the citation.

This ensures anyone reviewing the raw file sees ALL data that fed into the synthesis, not just the Python engine output.

---

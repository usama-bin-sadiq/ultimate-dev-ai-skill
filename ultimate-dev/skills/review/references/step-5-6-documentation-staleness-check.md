<!-- Moved verbatim from review/SKILL.md, the 'Step 5.6: Documentation staleness check' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 5.6: Documentation staleness check

Cross-reference the diff against documentation files. For each `.md` file in the repo root (README.md, ARCHITECTURE.md, CONTRIBUTING.md, <agent-instructions>, etc.):

1. Check if code changes in the diff affect features, components, or workflows described in that doc file.
2. If the doc file was NOT updated in this branch but the code it describes WAS changed, flag it as an INFORMATIONAL finding:
   "Documentation may be stale: [file] describes [feature/component] but code changed in this branch. Consider running `/document-release`."

This is informational only — never critical. The fix action is `/document-release`.

If no documentation files exist, skip this step silently.

---

> **STOP.** Before running the always-on adversarial review — Claude subagent plus Codex passes — after the staleness checks and before persisting the Eng Review result (Step 5.7), Read `~/<agent-config-dir>/gstack/review/sections/adversarial.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

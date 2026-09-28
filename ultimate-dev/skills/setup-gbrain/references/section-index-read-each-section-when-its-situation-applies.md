<!-- Moved verbatim from setup-gbrain/SKILL.md, the 'Section index — Read each section when its situation applies' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Section index — Read each section when its situation applies

This skill is a decision-tree skeleton. The steps below point to on-demand
sections. Read a section in full before doing its step; do not work from memory.

| When | Read this section |
|------|-------------------|
| running the Step 1.5 broken-engine remediation — Step 1's detect returned `gbrain_local_status` of `broken-db` or `broken-config` and no shortcut flag was passed | `sections/engine-remediation.md` |
| initializing the brain in Step 4 — run ONLY the procedure for the path picked in Step 2 (Paths 1/2a/2b/3/4 or Switch; also holds the PAT scope disclosure that `--cleanup-orphans` re-uses) | `sections/brain-init.md` |
| running the Step 7.5 transcript & memory ingest gate on Paths 1, 2a, 2b, or 3 (Path 4 skips this section entirely — see the skeleton's skip note) | `sections/transcript-gate.md` |
| persisting the Step 8 `## GBrain Configuration` block to CLAUDE.md (and the Search Guidance block after Step 9 passes) | `sections/claude-md-persist.md` |

---

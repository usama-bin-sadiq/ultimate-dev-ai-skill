<!-- Moved verbatim from setup-gbrain/SKILL.md, the 'Step 7.5: Transcript & memory ingest gate' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 7.5: Transcript & memory ingest gate

**SKIP entirely on Path 4 (Remote MCP).** Transcript ingest shells out to
the local `gbrain` CLI which Path 4 doesn't install. Remote-mode users
rely on the brain server's own ingest cadence — if your brain admin wants
this machine's transcripts indexed, they pull from your `gstack-artifacts-$USER`
repo (set up in Step 7) on whatever schedule they prefer. Set
`gstack-config set transcript_ingest_mode off` and continue to Step 8.

For Paths 1, 2a, 2b, 3, run the ingest gate:

> **STOP.** Before running the Step 7.5 transcript & memory ingest gate on Paths 1, 2a, 2b, or 3 (Path 4 skips this section entirely — see the skeleton's skip note), Read `~/.claude/skills/gstack/setup-gbrain/sections/transcript-gate.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

---

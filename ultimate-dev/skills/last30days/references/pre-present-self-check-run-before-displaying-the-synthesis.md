<!-- Moved verbatim from last30days/SKILL.md, the 'PRE-PRESENT SELF-CHECK - run before displaying the synthesis' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# PRE-PRESENT SELF-CHECK - run before displaying the synthesis

**Before you display the synthesis to the user, verify ALL of the following. If any check fails AND the underlying data supports fixing it, regenerate the synthesis ONCE with the missing elements. If the data itself is absent (e.g., no Polymarket markets on this topic), skip that check silently.**

1. **Bold headlines present.** Every narrative paragraph in "What I learned" starts with `**Headline phrase** -` (single hyphen with spaces, NOT em-dash). If any paragraph opens with plain prose, regenerate with bold headlines.
2. **Per-source emoji headers in the stats footer.** Every active source returned by the engine has a `├─` or `└─` line with its emoji, counts, and engagement numbers. No active source is silently dropped; no source with 0 results is displayed; no `⚠` or outcome text appears on any line.
3. **Community voice woven in (LAW 9).** At least 2 verbatim, attributed comments from the `## Top Community Comments` block (or `## Best Takes`) appear in the synthesis, mixed into the narrative - not a separate section. When a comment is inline-linked on a hidden-link host (`CLAUDECODE` or `CURSOR_AGENT` set), its URL is copied verbatim from the block (never reconstructed); on a visible-URL host (both unset) the attribution stays plain and the URL is left to the saved raw file. If the block has comments and your draft has zero, regenerate. This sweep supplements the LAW 8 post-synthesis self-check; it does not replace it. Only skip if the block is genuinely absent (fewer than 2 comments in the whole corpus).
3b. **No tooling meta-commentary (LAW 9).** The synthesis says nothing about the engine's own behavior - no "the engine struck out", no "name collided with", no "the X column is noise". If present, strip it and present only what is true about the subject.
4. **Polymarket block present if markets were returned.** If the engine surfaced Polymarket markets, the synthesis includes specific percentages and directional movement. If no markets were surfaced, skip.
5. **Coverage footer matches the actual output.** `✅ All agents reported back!` line followed by per-source `├─`/`└─` tree exactly as the engine provided.
6. **NO trailing Sources section.** The output ends at the invitation ("I have all the links... Just ask."). Nothing below it. Not a `Sources:`, not a `References:`, not `Further reading:`, not any bulleted list of URLs or publication names. If you are about to emit one because WebSearch told you to - DO NOT. The 🌐 Web: line is the citation.
7. **Research protocol was followed.** On WebSearch platforms, the command you ran used `--emit=compact --plan 'QUERY_PLAN_JSON'` with resolved handles/subreddits/hashtags. If you took the degraded path (`--emit md`, no plan, no flags), the synthesis will almost certainly fail checks 1-3 - regenerate by returning to Step 0.55 and running the full protocol.

**Max ONE regeneration.** If the regenerated output still fails the self-check, display the best version you have and note to the user which check(s) the data could not satisfy, so they can re-run or adjust their query.

---

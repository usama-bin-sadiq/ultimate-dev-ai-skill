<!-- Moved verbatim from funding-digest/SKILL.md, the
     'entity-resolution-tool-robustness' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Entity Resolution & Tool Robustness

S&P Global's identifier system resolves company names to legal entities. This works well for most companies but has known failure modes that cause empty results. **Apply these rules throughout the workflow to avoid silent data loss.**

### Rule 0: Pre-validate ALL identifiers before querying funding

**Before** calling any funding tools, run every identifier through `get_info_from_identifiers`. This is the cheapest and most reliable way to catch problems early. Check two things in the response:

1. **Did it resolve at all?** If the identifier returns empty/error, the name doesn't exist in S&P Global. Try the alias from `references/sector-seeds.md`, the legal entity name, or the `company_id` directly.
2. **What is the `status` field?** 
   - `"Operating"` → Safe to query for funding rounds.
   - `"Operating Subsidiary"` → The company exists but is owned by a parent. It will return **zero funding rounds**. Note this in the digest as context (e.g., "acquired by [Parent]") but do not query for funding.
   - Any other status (e.g., closed, inactive) → The company is no longer operating. Historical data may exist but no new activity.

**This single pre-validation step prevents the majority of empty-result issues.** Batch all candidates into a single `get_info_from_identifiers` call (it handles large batches well) and triage before proceeding.

### Rule 1: Never trust empty results without a fallback

If `get_rounds_of_funding_from_identifiers` returns empty for a company you expect to have data:
1. **Try the legal entity name or company_id.** Brand names usually work, but some don't. See the alias table in `references/sector-seeds.md` for known mismatches. Common pattern: "[Brand] AI" → "[Legal Name], Inc." (e.g., Together AI → "Together Computer, Inc.", Character.ai → "Character Technologies, Inc.", Runway ML → "Runway AI, Inc.").
2. **Verify the company exists in S&P.** If you skipped Rule 0, call `get_info_from_identifiers(identifiers=["Company"])` now — if this also returns empty, the company may be too early-stage or not yet indexed.

### Rule 2: Subsidiaries have no funding rounds

Companies that are divisions or wholly-owned subsidiaries of larger companies (e.g., DeepMind under Alphabet, GitHub under Microsoft, BeReal under Voodoo) will return **zero funding rounds**. Their capital events are tracked at the parent level.

**How to detect:** The `status` field from `get_info_from_identifiers` will show `"Operating Subsidiary"`. The `references/sector-seeds.md` file also flags known subsidiaries with ⚠️ warnings. Skip these for funding queries.

### Rule 3: Use `get_rounds_of_funding_from_identifiers` as the primary tool, not `get_funding_summary_from_identifiers`

The summary tool is faster but less reliable — it can return errors or incomplete data even when detailed rounds exist. Always use the detailed rounds tool as the primary data source. The summary tool is acceptable only for quick aggregate checks (total raised, round count) and should be verified against the rounds tool if results seem low.

### Rule 4: Batch carefully and validate

When processing large company universes (50+ companies), batch in groups of 15–20. After each batch, check for companies that returned empty results and run them through the fallback steps in Rule 1 before moving on.

### Rule 5: The `role` parameter is critical

- `company_raising_funds` → "What rounds did X raise?" (company perspective)
- `company_investing_in_round_of_funding` → "What did investor Y invest in?" (investor perspective)

Using the wrong role returns empty results silently. For deal flow digests, you almost always want `company_raising_funds`. Only use the investor role when specifically analyzing an investor's portfolio activity.

### Rule 6: Identifier resolution is case-insensitive but spelling-sensitive

S&P Global handles case variations ("openai" = "OpenAI") but is strict on spelling and punctuation. "Character AI" may fail where "Character.ai" succeeds. When in doubt, use the `company_id` (e.g., `C_1829047235`) which is guaranteed to resolve.

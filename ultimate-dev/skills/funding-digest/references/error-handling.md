<!-- Moved verbatim from funding-digest/SKILL.md, the
     'error-handling' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Error Handling

### Entity Resolution Failures
- **Empty results for a known company:** First check `get_info_from_identifiers` — if that fails, try the alias from `references/sector-seeds.md` or the `company_id` directly. Common brand→legal mismatches: Together AI → "Together Computer, Inc.", Character.ai → "Character Technologies, Inc.", Runway ML → "Runway AI, Inc.".
- **Subsidiary companies:** DeepMind, GitHub, Instagram, WhatsApp, YouTube, BeReal, etc. are subsidiaries — they have zero independent funding rounds. Note these as "acquired/subsidiary" in context but do not report them as "no activity."
- **Defunct companies:** Companies like Convoy (shut down Oct 2023) still resolve in S&P Global but will never have new activity. The `references/sector-seeds.md` file flags these — check it before including a company.
- **`get_funding_summary_from_identifiers` errors or returns zeros:** Fall back to `get_rounds_of_funding_from_identifiers` — the summary tool is less reliable. Never rely on the summary tool as the sole data source.
- **Wrong `role` parameter:** If investor-perspective queries return empty, verify you're using `company_investing_in_round_of_funding`, not `company_raising_funds` (and vice versa).

### Data Quality Issues
- **No activity in period:** If a sector had zero funding rounds, note this explicitly on the slide ("No transactions recorded in [Sector] during the period") — absence of activity is itself informative.
- **Sparse valuation data:** If pre-money and post-money valuations are undisclosed for most transactions, note the data limitation in a footer annotation and use "—" in the table. Adjust the stat card to show a different metric (e.g., Median Round Size) instead of Avg Pre-Money.
- **Logo retrieval failures:** The `simple-icons` npm package provides ~43% coverage for typical deal flow companies. For the remainder, use the `sharp`-generated initial-based fallback. Keep a consistent icon style — don't mix random approaches. If `simple-icons` or `sharp` fail to install, fall back to pptxgenjs shape-based initials (gray ellipse + white text overlay) which require no external dependencies.
- **Too many deals for one slide:** If there are more than 6 notable deals, show the top 6 in the table and add a footnote: "+N additional deals not shown." Prioritize by deal size.
- **Large universes:** For multi-sector digests with 100+ companies, batch all API calls in groups of 15–20. Prioritize depth on notable deals over completeness on minor ones.
- **Stale seeds:** If competitor expansion returns very few results for a sector, the seed companies may be too niche. Broaden by adding 2–3 more well-known names and re-expanding.
- **Invalid transaction IDs for links:** If a `transaction_id` from the funding tool doesn't produce a valid Capital IQ URL, omit the link cell for that row rather than including a broken link.

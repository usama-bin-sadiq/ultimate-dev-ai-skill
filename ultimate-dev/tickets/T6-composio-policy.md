# T6: Composio Policy Review

## Status: COMPLETE
- Review Composio template family exclusion from overlap lint — done. The
  family is excluded and the lint reports 14 overlapping pairs, inside the
  budget of 25. The 267,583 figure in this ticket predates the exclusion and
  no longer applies.
- Verify no Composio stubs in skill package — the premise was wrong. All 742
  are real files under `skills/`, each with valid frontmatter, and
  `validate-skills.py --strict` passes over them. They are not stubs.
- Ensure CI report-only gate passes — done, 14 <= 25.

## What the 742 actually are

Each is a ~110-line procedure for driving one SaaS product through Composio's
Rube MCP: connect the toolkit, discover tools with `RUBE_SEARCH_TOOLS`, execute
with `RUBE_MULTI_EXECUTE_TOOL`. The routing value is real — naming a product
routes to the product's procedure — and that is the reason the composio gate
in `tools/route.py` exists: 742 near-identical descriptions will otherwise
out-score a genuine skill on any query sharing a word with them.

Normalising the product name out of each body leaves **79 distinct documents**,
of which **554 of the 742 are byte-identical to one another**. So the corpus
carries roughly 79 templates instantiated 742 times, three-quarters of them
the same one.

That is redundancy, not error. The body carries no product-specific detail
beyond the name and the toolkit URL, so it could be generated from a template
and indexed rather than stored 742 times. Left as-is: the files are correct,
they validate, and deduplicating them is a corpus change nobody has asked for.

## Follow-on

- The 742 inflate the "2,081 skills" figure by a third.
- `when` is empty for 1,585 of 2,367 index entries, because the builder only
  extracts it from descriptions using a "Use when" convention that two thirds
  of the corpus does not follow. Worth a convention pass if routing is to
  improve on more than the product-name matches it already gets.


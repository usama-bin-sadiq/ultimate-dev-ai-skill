# 0010. The on-demand boundary is a property of the tools, not of the prose

Status: Accepted
Date: 2026-09-28
Deciders: architecture maintainers
Relates to: `SKILL.md` Step 3 (context on demand), Step 4 (capability acquisition), `references/context-system.md`

## Context

`SKILL.md` instructs the agent to search the capability catalogue rather than
read it: *"A far larger catalogue is installed alongside these — 2,398
capabilities. **Do not read it; search it.**"* That instruction is correct, and
it is the load-bearing one. The catalogue is 45,256 words of references plus
2,112 sub-skills; loading it is the difference between a run that fits in
context and one that does not.

The instruction had been carried for some time without being tested. An audit of
the on-demand boundary asked a narrow question — does anything that should be
loaded on demand actually get loaded on demand? — and found two things.

### The always-loaded surface is honest

Measured rather than assumed:

| | |
|---|---|
| `SKILL.md`, always loaded | 4,145 words |
| `references/`, on demand | 45,256 words across 55 files |
| `agents/`, on demand | 597,505 words across 291 roles |
| verbatim lines shared with `references/` | 106 words (2.5%) |

That 2.5% is all legitimately re-stated: the five rungs, the seven-stage loop,
the four context levels, the two trust equations. A reference file that has not
been opened still has to yield the ladder, so duplication there is the design
working, not leaking. No agent role has any of its content inlined, and the
only `skills/`, `agents/` and `tools/` paths that appear in `SKILL.md` are
routing pointers, not content.

An earlier measurement suggested 13% duplication. That was wrong. It matched on
the first eight words of a paragraph, which for a table is the header row, so
every table that shared a header with a reference counted as fully duplicated.
Line-level comparison is the honest measurement and it is 2.5%.

### The search was not searching

`python3 tools/index-tree.py --search 'rotate a pdf'` returned **2,397 matches
— every entry in the catalogue.**

Scoring is `sum(2 for tk in e["tokens"] if w in tk)`, a substring test. The
query word `a` is a substring of `abstract`, `validate`, `parse`, `data`,
`canvas` and `parameter`, so it scored almost every entry and the result set was
the whole catalogue. The words `rotate` and `pdf` were scored correctly and were
simply outvoted.

This is worth stating precisely, because the failure is not that the tool
crashed or lied. It returned correct rankings of a set that was the entire
catalogue. An agent following the instruction would have run the search, seen
2,397 results, and concluded — correctly, on the evidence — that the catalogue
could not be searched and had to be read. The instruction and the tool
disagreed, and the tool was the one that would have to change.

That is the same class of failure as the 22 skills that imported a missing
`_common`: an instruction that assumes a capability, and no check that the
capability exists. It was invisible because the command exits 0 and prints
plausible output.

## Decision

Query words shorter than three characters are dropped before scoring, and a
query with no word of three or more characters is refused with a message rather
than answered.

Three characters because that is the floor the tokeniser already imposes:
`tokens()` builds from `[a-z][a-z0-9-]{2,}`, so no token is shorter than three.
Below that a word cannot discriminate between tokens at all, which is the
precise condition that produced the bug.

`rotate a pdf` now returns 32 entries led by `pdf-engine-architect` and
`api2pdf-automation`, which is what the query was asking for. Single-word
queries are unchanged: `pdf` 31, `rotate` 1, `xlsx` 3, `authentication` 17.

## Consequences

- The on-demand boundary is now enforced by the tool that the boundary depends
  on, not only asserted in prose. A future regression in the tokeniser or the
  scoring rule would show up as a result count that stops being selective.
- `SKILL.md` needed no change. The instruction was already right.
- **All 32 results for a realistic query are UNROUTED.** The search works and
  finds capabilities, and almost nothing it finds can be dispatched to. This is
  the dispatch-table gap made concrete: a correct search over a corpus where
  `routed` is nearly always false is a smaller problem than it looks, because
  the hits cannot be selected anyway. Closing the table is worth more than any
  further work on the search.
- This ADR records the *audit*, not just the fix. The check that would have
  caught it — "does a search for a common phrase return far fewer entries than
  the catalogue" — is not automated. It should be.

## Alternatives rejected

**Lower the score instead of dropping short words.** An entry matching only on a
stop word would rank below every real match but would still be printed, so the
count would still read as "everything matches". The bug is in the result *set*,
not the ordering.

**Match on token boundaries rather than substrings.** More correct, and it
would not have fixed this: `a` still matches the token `a`, and stop-words
still consume the reader's attention. Dropping them is the honest fix.

**Report the count and let the agent judge.** It already could, and it had no
way to know the count was wrong. The tool should not make the caller detect its
own failure.

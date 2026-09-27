# Context compiler

You compile context; you do not accumulate it. A load is raw material until it
has been selected, resolved, compressed, checked, and stamped. The compiler turns
"everything I could have read" into "the smallest set that settles the decision".

## The pipeline

Each stage has a procedure and a distinct failure; skipping one moves the cost into a wrong decision rather than saving it.

| Stage | Do | Failure if skipped |
|---|---|---|
| Requirements | write what the live decision needs, as nouns and predicates | you retrieve by topic and get material that is adjacent but not relevant |
| Retrieve | fetch only those, from the nearest level of the ladder in `context-system.md` | guessing at content you could have read |
| Rank | order by bearing on the live decision, not by size or by availability | the loudest artifact decides, and relevance is invisible |
| Filter | drop everything that does not change the decision | load-everything; reasoning diluted over noise |
| Resolve dependencies | follow what the kept items themselves require, to a fixed point or a declared stop | an item whose meaning is set by an unread rule is used wrongly |
| Deduplicate | collapse restatements of one fact into a single entry with several sources | a fact repeated five times reads as five confirmations; weight is invented |
| Compress | rewrite at the smallest form that preserves what the decision uses | either bloat, or a summary that quietly changes meaning |
| Freshness check | compare each item's retrieval time against its TTL | you act on an expired fact and never learn it expired |
| Budget | drop in the fixed order below until the set fits | arbitrary trimming, or exceeding the budget and paying downstream |
| Provenance | stamp every surviving item before use | the claim cannot be traced, and staleness cannot be detected |
| Emit | assemble the working set, with what was dropped and why recorded | silence about what is missing; load becomes indistinguishable from absence |

Accumulation is retrieval plus hope: whatever arrived stays. Compilation is a
series of deletions, and every surviving item must answer *which decision does
this serve?* If you cannot name it, the item is litter. One fact from three
sources is one item with three attestations, not three items.

## Lossless compression

Compression is lossless **with respect to the current decision** when the dropped
detail cannot change any decision you are currently positioned to make. Two tests,
both required:

1. **Recoverability**: every load-bearing element dropped is reconstructible from
   what remains, or recorded with its source for re-retrieval on demand.
2. **Meaning invariance**: no surviving statement changed scope. Qualifiers,
   exceptions, thresholds, and negative cases survive intact.

Lossless moves: reordering, merging a definition into its single use, collapsing an
inert enumeration, prose to a table of the same facts, dropping a second source's
restatement. Lossy moves: dropping qualifiers, merging distinct values, dropping
exceptions, rounding, keeping an API's happy path.

Lossy compression is acceptable **only** when the item is not load-bearing, the
loss is recorded, and the original is retained. Never compress lossily an item
that supports a claim you intend to report.

## Budget: what to drop first

Fixed order. Do not improvise, and never drop a lower rung to protect a higher one.

1. C6 specialist depth. Deepest, least likely to change the near-term decision.
2. Breadth within C3 and C4: keep the region, drop the artifact.
3. C5 external evidence not tied to a blocking unknown.
4. Historical and superseded context: prior state, prior plan, old outputs.
5. Detail in C2 instructions, down to the minimum needed to execute correctly.
6. Redundant paths, alternatives, and reasoning behind a recorded decision.

Never drop: the objective, the success criteria, the constraints and prohibitions,
the load-bearing assumptions, the active decision record, or the evidence behind
any claim you will report. If it still does not fit, the task is mis-scoped, not
the context: reduce scope or report the block.

## The compile record

```text
COMPILE
  decision        the live decision this context serves
  required        what it must settle, stated before retrieval
  included        item, level C0-C6, bearing on the decision, one clause
  excluded        item, level, why it changes nothing   <- keep this honest
  dropped         item, stage that dropped it (filter|budget|superseded)
  compressed      item, lossless|lossy, what was lost
  stale           item, retrieved, TTL, verdict
  unresolved      what the decision still cannot settle
```

Record at the depth the rung justifies: one line at R0, an artifact at R4. The
`excluded` and `unresolved` columns make the compile auditable; a record with only
an `included` column is a list, not a decision.

## Prohibitions

- Do not retrieve before stating the requirement; topic-shaped retrieval is how
  noise gets compiled in.
- Do not treat deduplicated restatements as corroboration, and do not compress
  away a qualifier that a claim depends on.
- Do not trim the budget from the top rung down; that inverts the ladder.
- Do not emit a set whose `unresolved` column is empty unless you checked.

Related: `context-system.md` (the ladder, and eviction), `context-provenance.md`
(the trust and freshness fields stamped at stage 10), `evidence-system.md` (how
repeated sources are graded), `provenance-system.md` (tracing the emitted set).

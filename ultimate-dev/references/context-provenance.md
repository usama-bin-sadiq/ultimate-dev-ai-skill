# Context provenance

Every item in your working set is a claim about the world, made at a time, by a
means, with a known reliability. Stamp that on the item when you load it. An
unstamped item cannot be trusted, cannot be re-checked, and cannot be detected
as out of date; it is the raw material of a wrong decision.

## Required fields on every item

```text
ITEM
  id            stable handle, so a decision can name what it rests on
  claim         what this item asserts, as one checkable sentence
  source        where it came from: artifact, tool, query, or observation
  retrieved     when it was obtained, in absolute terms
  trust         verified | single-source | low-authority | unvetted
  supports      the decision, requirement, or reported claim it bears on
  status        Known | Inferred | Assumed | Unverified | Uncertain | Contradicted
  ttl           how long it stays usable, and what makes it expire
  on_expiry     re-retrieve | re-verify | hold as historical | drop
```

`supports` is the field that earns the record: an item supporting nothing is noise,
and an item supporting three things is a shared dependency you must know you have.

## Trust is not status

Trust describes the source: its authority, its proximity to the fact, its
propensity to be wrong. Status describes *your* epistemic position on the claim.
A high-trust source can still leave a claim Unverified because you have not run
the check. Record both; collapsing them is how a rumour becomes a premise.

## The status vocabulary

Use exactly these six. Do not invent a seventh, and do not write "probably",
"looks right", or "generally" in place of one.

| Status | Means | Obligation |
|---|---|---|
| **Known** | you performed a check and observed the result | cite the observation; the check is repeatable |
| **Inferred** | derived from Known items by a stated step | show the derivation and the inputs |
| **Assumed** | taken as true with no support yet | name what breaks if it is false |
| **Unverified** | evidence exists but the check has not been run | state the check, or state why it was skipped |
| **Uncertain** | the evidence conflicts or is ambiguous; you cannot currently say | say which readings are live |
| **Contradicted** | the evidence says the claim is false | re-open the decision at JEv now |

Rules of movement: status only improves when new evidence arrives, and the
transition is recorded. Uncertain and Contradicted differ: Uncertain says
*cannot tell*, Contradicted says *told otherwise*, and the second compels action.
Downgrading a claim to make a plan survive is prohibited, and so is laundering an
assumption into a fact by dropping its qualifier.

## Freshness and TTL

Set TTL from the volatility of the source, not from convenience. Ask how fast
the thing could have changed without you noticing.

| Source class | Typical TTL | Why |
|---|---|---|
| running processes, live measurements, schedules, remote state | minutes to an hour | changes under you while you work |
| build outputs, dependency versions, generated files, current working tree | one work unit | changes when anything else runs |
| third-party APIs, current pricing, mutable published facts | the life of the decision | the decision outlives the reading |
| project decisions and committed intent | the life of the project | stable by design |
| language and platform semantics, published standards | effectively no expiry | slow and versioned |

Re-retrieve on expiry; do not re-assume. An expired item may still be used to
*form a question*; it may not support a claim.

## Staleness invalidates what depended on it

A decision is exactly as current as the weakest item it rests on. Therefore:

- If any supporting item has passed its TTL, the decision is re-opened, not
  trusted. Do not carry it forward with a caveat.
- Re-open means: re-retrieve or re-verify the expired item, re-run the JEv
  decision against what came back, and record whether it changed.
- If the expired item is not re-obtainable, the dependent claim drops to
  Uncertain and is reported as a limit, with the reason it cannot be refreshed.
- Decisions made under a now-Contradicted item are not stale, they are wrong.
  Revise them and everything that inherited from them.
- Freshness is checked at the boundary, not only at load: long tasks expire
  context mid-flight. Re-check before any unit that inherits an earlier TTL.

## Prohibitions

- Do not carry a decision forward on context that has expired. Re-open it.
- Do not record a source you did not use, to make an item look better founded.
- Do not reuse a TTL from a similar-looking source; volatility is per source.
- Do not mark an item Known because it is documented somewhere. Known means you
  observed it; trust is not a substitute for the check.

Related: `context-system.md` (which items exist at which level),
`context-compiler.md` (when the freshness check happens in the pipeline),
`evidence-system.md` (grading what the item rests on),
`provenance-system.md` (carrying these fields into the reported chain).

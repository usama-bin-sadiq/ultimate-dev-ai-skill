# Provenance system

A result is trustworthy when anyone, including you later, can walk from it back
to the thing that was actually observed. The chain is fixed:

```text
RESULT → CLAIM → EVIDENCE → SOURCE → TRANSFORMATION → VERIFICATION
```

Each link must exist. A broken link is not a stylistic gap; it is the exact
place where an unearned claim entered, and it is where you say so in the output.

## What must carry provenance

| Carrier | Must record |
|---|---|
| **Claim** | the claim, its status (Known/Inferred/Assumed/Unverified/Uncertain/Contradicted), and the id of its evidence |
| **Artifact** | every file, report, or deliverable produced, and the result it embodies |
| **Decision** | the decision record: question, selected, rejected, rationale, evidence, recovery. `evidence: none` is a valid and honest value |
| **Number** | input values, their sources, the operation, the tool that performed it |
| **Instruction or procedure reused from a prior run** | the instance it was validated on, and its scope |

Provenance attaches to what you will *report*, not to what you merely thought. A
claim you state without a chain is a defect, whether or not it happens to be true.

## Linking the chain

- **RESULT → CLAIM**: decompose the result into the individual claims it makes.
  "Fixed, and it will not regress" is two claims with two evidence standards.
- **CLAIM → EVIDENCE**: name the observation that would be false if the claim
  were false. If nothing could be, restate it as checkable or mark it Assumed.
- **EVIDENCE → SOURCE**: the exact artifact, command, or reading, with when it
  was obtained. "I checked earlier" is not a source.
- **SOURCE → TRANSFORMATION**: what you did to it to get the evidence. The most
  commonly missing link, and the one that hides error.
- **TRANSFORMATION → VERIFICATION**: the check that the transformation was
  correct, and the verdict VERIFIED / PARTIAL / FAILED.

## Recording a transformation

A derived number is a claim. Record it so the arithmetic can be re-checked:

```text
TRANSFORMATION
  output        the derived value or conclusion
  inputs        each value, with the id of the item it came from
  operation     the exact step: filter, join, aggregate, compare, infer
  tool          what performed it; "done in my head" is not a tool
  checksum      for a large derivation, the count, total, or hash it produced
  review        the check that the step was right, and its verdict
```

Compiling, hashing, counting, parsing, and formatting belong to a tool, never to
recall. Inference is a transformation too, recorded with its inputs marked
Inferred. If you cannot name the operation, you guessed the value.

## When provenance may be omitted

Omit the record only when all three hold:

1. Low stakes: getting it wrong costs little and is cheaply reversible.
2. Trivially derived: one deterministic step from an item already in hand.
3. A checked pattern: you verified the same shape before, and nothing about this
   instance is novel.

Recording everything is itself a cost. Time, tokens, and attention spent writing
chains for mechanical steps is attention taken from the load-bearing claims, and
a ledger where everything is stamped is a ledger where nothing is marked. Mark
the load-bearing claims thoroughly; mark the rest in aggregate.

Never omit provenance for an irreversible or externally visible action, a number
reported to someone else as fact, an Assumption promoted to fact, or a source you
cannot re-open.

## Answering "how do you know that?"

For any material claim, walk the chain in one hop per link, without reaching for
a summary. If you cannot complete a hop, that is the answer: the claim is not
supported to the level you were about to state it. Then lower the claim, mark the
status, run the missing check, or report the limit.

Never reconstruct a source from memory. If the source cannot be opened, the claim
drops to Uncertain. A citation you have not opened in this run is a fabrication
with a reference attached.

## Prohibitions

- Do not report a source, citation, or test outcome you did not observe.
- Do not skip the transformation link: that is where the error hides.
- Do not upgrade a claim's status to match the confidence you wish to convey, and
  do not reuse another item's evidence id unless you checked it applies.

Related: `context-provenance.md` (per-item fields and TTL),
`evidence-system.md` (what counts as evidence at all),
`context-system.md` (only load what the decision needs).

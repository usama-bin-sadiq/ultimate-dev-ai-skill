# Context optimization

How to hold what is needed, and nothing else, in a system whose context is a
budgeted and degradable resource.

## The question this raises for the kernel

The kernel is told not to be handed everything, and everything here follows from
that. But "load on demand" is not a mechanism: how do you decide what to load,
how do you compress it without changing its meaning, and how do you know when
you have loaded too little? Context is the resource most likely to be both
over-consumed and under-used, and the two failures are not symmetric in damage.

## Approaches considered

**Retrieval and reranking.** Cast selection as search: embed the query, retrieve
candidates, rerank by relevance. The standard answer, and what the compiler's
rank stage is. Adopted with one change: ranking is by **bearing on the live
decision**, not by similarity to the query text. A lexically similar document is
frequently irrelevant to the decision at hand, and the query is usually a poor
description of what the decision needs. Relevance is defined by a requirement
written before retrieval.

**Long-context models and the effective-context problem.** Larger windows appear
to remove the need to select, yet accuracy degrades when the relevant material
sits in the middle of a large context, and retrieval still beats stuffing.

Adopted as the reason the C0-to-C6 ladder exists at all, even with a very large
window. The reason is not token count: undifferentiated material competes for
attention with the material that decides the current question, and the damage
shows up as diffuse, hedged reasoning rather than a token error.

**Compression.** Summarise and reduce material to fit. Adopted with a constraint
most implementations lack: compression must be lossless **with respect to the
current decision**, tested two ways — recoverability of everything dropped, and
invariance of meaning, meaning no qualifier, threshold, exception, or negative
case is lost. A summary that drops "except when" is a new fact wearing a
summary's clothes.

**Just-in-time context.** Load at the moment of need rather than in advance, via
a minimal observation and a tool to fetch more. Adopted as the operational form of
the ladder: context is fetched against a stated requirement, held for the life of
one decision, and released when the decision closes. Holding context across
decisions is how stale material starts deciding current questions.

**Lost in the middle.** Information at the beginning and end of a context is used
more reliably than the same information in the middle. Adopted as a placement
rule: state the live decision near the material it governs. Stated honestly: our
evidence is borrowed, and effect sizes are model-dependent.

**Context rot.** Reasoning quality declines as context grows, including on
relevant material. This is a general decline, not a positional effect. Adopted as
the reason context is treated as budgeted even when the budget is generous, and
as the reason deduplication is aggressive. The mechanism is not size but dilution:
every retained item weakens the ones that matter, whether or not it is large.

**Chunking and hierarchical summarisation.** Split, summarise groups, keep
summaries. Adopted selectively, for breadth over a large corpus at C5. Rejected
for material that decides a unit at C3 and C4, because summarising the code you
are about to change produces a description of the code — which is exactly the
defect in `../../docs/operations/troubleshooting.md` entry 9.

**Query rewriting and multi-hop retrieval.** Rewrite the query, retrieve
iteratively, chain across sources. Adopted at C5, where blocking unknowns are
genuinely multi-hop. Not lower down, where the material is known to exist and the
task is to read the right part of it.

**Attention budgeting and prompt caching.** Spend compute where attention is
needed; cache stable prefixes. Partially adopted. Caching is a cost
optimisation. Attention budgeting is not adopted as a mechanism, because there is
no reliable control over it: the only dependable way to control what receives
attention is to control what is present.

**Provenance and freshness metadata.** Attach source, retrieval time, and time to
live to every item. Adopted as a first-class compiler output rather than an
afterthought, because it makes "where did we learn this" answerable and staleness
detectable. Deduplication keeps it affordable: one fact with three attestations
costs one item's metadata.

**Vector memory and embedding-based recall over past episodes.** Rejected as the
context mechanism: past episodes are selected by similarity to the query, which is
a poor proxy for "the case where I learned the thing that matters now". Kept only
as a candidate store under promotion gates.

## What was adopted

- A six-level ladder, C0 to C6, loaded against a stated requirement and stopped
  when the decision stops changing.
- A compiler with eleven stages, each with its own failure, ending in an emit that
  records what was dropped.
- Lossless-relative-to-the-decision compression, with both tests.
- Ranking by bearing on the live decision, requirement written before retrieval.
- Placement: the live decision stated adjacent to the material it governs.
- Aggressive deduplication, because repetition is not corroboration.
- Provenance and freshness on every retained item.
- Caching as a cost measure only, never as a reason to keep stale material.

## What was rejected and why

- **Trust the window and skip selection.** A larger window removes the token
  constraint and leaves the attention constraint, which is worse because it is
  invisible.
- **Summarise the material you are about to work on.** Produces a description
  instead of the thing, and the failure is a confident wrong answer.
- **Query similarity as the relevance criterion.** The query is not the decision,
  and lexical overlap is not relevance.
- **Summarising past work with no promotion gate.** Every summarised episode
  becomes retrievable guidance, including the wrong ones.
- **Storing retrieved material verbatim in durable run state.** It bloats resume
  and turns the state file into a place where injected instructions persist.
  Records hold provenance and the decision-relevant extract, not the artifact.
- **Compressing the task model.** It is the floor, it is small, and compressing it
  removes the criteria verification depends on.

## Open problems

- **No ground truth for relevance.** Bearing on the live decision is a judgement
  made by the same agent that needs the context. No measurement avoids that
  circularity. The suite can detect gross over- and under-retrieval; it cannot
  say whether C4 was right.

- **The stopping rule is unmeasured.** "Stop when the decision no longer changes"
  is sound and vague. Nothing establishes how to detect that a deeper load would
  have changed anything, short of loading it and finding out.

- **Compression fidelity for code and configuration.** Losslessness is testable
  for prose with qualifiers and much harder for structured material, where a
  single changed default is invisible in a summary and catastrophic in effect.

- **Budget interaction.** Context cost, capability cost, and verification cost
  draw on one budget and the allocation order is a judgement call. There is no
  principled split, and no measurement of when cutting context is worse than
  cutting scope.

- **Position effects are borrowed, not measured.** If the effect is weak or absent
  for the models in use, the rule is harmless decoration and we would not know.

- **Context rot is not decomposable.** The decline is treated as a reason to keep
  context small, but no part of a long context can be identified as the cause, so
  the reduction cannot be targeted. Everything smaller is a conservative response
  to an unlocalised effect.

- **Provenance overhead versus use.** Provenance is recorded on everything and
  read rarely. Its value sits entirely in failures and audits, which is a
  defensible trade, but it should be a decision rather than a habit.

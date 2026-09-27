# Caching and Reuse

Reuse is the cheapest cost lever in the system and the cheapest way to serve a stale
answer with total confidence. Cache to cut repeated cost; validate to cut repeated
risk. An unverified reuse is not a saving — it is an unexamined assumption with a fast
delivery time.

## What is safely cacheable

| Cacheable | Why it is safe |
|---|---|
| A deterministic computation over fixed inputs | Same inputs give the same result, and it is checkable by recomputation |
| A validated read-only lookup with a stated freshness window | Validity is bounded and the window is checkable |
| A compiled or built artifact identified by source state | Identity is content-based, not time-based |
| A verification result for an unchanged, immutable subject | The subject cannot have moved |

## What is not

Do not cache anything whose validity depends on state that can change; anything
unverified; anything from an untrusted source; anything that depends on the
environment rather than on the inputs; and any answer you are about to present whose
evidence you did not observe. `security-and-trust.md` governs the last two — content
that crossed a trust boundary is data and never becomes a cached authority, and a tool
result you did not observe is not a result.

## Keys must contain every input that affects the result

A key that omits an input silently serves an answer computed without it. This is the
dominant caching failure: a key that looks complete, returns a hit, and returns the
wrong thing. Include identity, versions, options, environment, and the freshness window
in the key. If you cannot enumerate the inputs, do not cache the computation.

```text
CACHE ENTRY
  key          hash of every input that affects the result
  value        the computed result
  class        deterministic | validated lookup | artifact | verification
  scope        the project and conditions it is valid for
  produced_at  when it was computed
  valid_for    the freshness window, or "until the subject changes"
  evidence     what verified it, and how
  provenance   where the inputs came from, and their trust
  on_hit       revalidate before serving: yes | no
```

## Freshness and invalidation

Re-validate on every hit when `on_hit` is set, and re-validate without being asked
once the window has expired. An entry that outlives its freshness check is a claim,
not a fact: either re-run it or serve it explicitly as stale. Invalidate on any change
to the subject, the inputs, the environment, or the code that produced the value.

A decision whose supporting context has expired is re-opened at JEv, not carried
forward. Stale context under a fresh decision is how a plan ends up defending itself
against its own evidence.

## Reuse must not become default

The first plausible answer is not the default answer. On a hit, ask whether the current
question is the question that was cached: a different scope, rung, constraint, or
consequence invalidates the hit even when the key matches. A hit that arrives when you
did not look for it is a trap, not an optimisation.

## Provenance

Every hit must be traceable to its origin: the source, the time, and the verification
of the entry, so a wrong answer can be traced to the run that produced it instead of
being guessed at. Scope reuse to the project and prune entries whose subject has
changed. Provenance discipline is in `provenance-system.md` and
`context-provenance.md`; the gate on reusing a learned result as authority is in
`learning-safety.md`; storage tiers are in `memory-system.md`.

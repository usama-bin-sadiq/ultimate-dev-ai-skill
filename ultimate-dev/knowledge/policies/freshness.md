# Freshness

## Purpose

Facts expire. A stale fact used with the same confidence as a fresh one is a
silent correctness defect, because nothing in the record announces it. This
policy defines when context and evidence are stale, what must happen when they
are, and what a re-read is allowed to change. It is what stops a run from
carrying a decision forward on evidence that has since stopped being true.

## Policy statement

Every context item and every evidence record carries `retrieved_at` and a TTL.
Freshness is computed, never asserted: `valid_until = retrieved_at + ttl`, and
any item whose `valid_until` precedes the current decision point is stale at
that point. A stale item may not support a reported claim, may not be the basis
of a `selected` in a decision, and may not be presented without a refresh
attempt or a stated reason the refresh is unnecessary.

The default is a short TTL. A long TTL requires a named owner and a reason in
the record, because the failure mode of an over-long TTL is a fact that never
gets rechecked.

## TTL by class

| Class | Examples | TTL | On expiry |
|---|---|---|---|
| Live observation | a command's output, a query result, a file read during this run | until the run ends | re-observe before the next use; never reuse across runs |
| Live configuration | the state of the system you are about to change | 15 min | re-read before acting; the change may already be made by someone else |
| Environment inventory | account list, region map, running instance set | 1 h | re-list; membership changes quietly |
| Dependency and version state | installed package versions, module pins, API schema | 24 h | re-resolve before relying on a specific version |
| Repository material | source files, module definitions, tests | 7 d | re-read the region the decision turns on |
| Internal reference | runbooks, policies, internal standards | 30 d | re-read on any contradiction |
| Vendor documentation | CLI and API references, SDK docs | 90 d | re-fetch on a behaviour that does not match |
| Regulatory and contractual | PCI DSS requirements, contract terms | 180 d | re-read before any attestation or audit claim |
| Promoted learning | a rule in the behaviour of the system | until a contradicting instance | keep; deprecate on contradiction, do not expire |

## Decision table

| Condition | Required action |
|---|---|
| `valid_until` < now, and the item supports a live decision | Refresh before deciding. If refresh is impossible, downgrade the dependent claim to `uncertain` with a named bound. |
| `valid_until` < now, and the item is a promoted learning | Do not expire. Open a `contradicting` entry on the learning and re-decide. |
| `valid_until` < now, and the item is a vendor doc | Refresh only if a behaviour contradicted it. Otherwise carry the `retrieved_at` forward explicitly. |
| A re-read returns a different value | Create new evidence, mark the old record `freshness.verdict: stale`, and re-decide everything that depended on it. Never overwrite. |
| A re-read returns the same value | Extend `valid_until` and record the refresh observation. Repetition is not new evidence; it is a refreshed TTL. |
| A run crosses a TTL boundary mid-plan | Re-check every item whose `valid_until` falls inside the remaining plan window, not only the ones in play now. |
| A decision was taken on stale context | Mark the decision `status: superseded` and re-take it. Do not patch the record. |
| An item is needed but expired and cannot be refreshed | Record it in `not_observed`, mark the dependent criterion `not-run`, and report the gap. Do not reason as if it held. |
| Freshness cannot be computed for an item | It is stale by default. An item with no retrieval time is not trusted context. |

## Escalation and exceptions

- **Cannot refresh.** Raise to a human checkpoint when the refresh requires
  authority the agent does not have. Record the refusal as an observation with
  its exit code.
- **Refresh is more expensive than the decision is worth.** Take the decision at
  lower confidence, state the expiry in the result, and set a `recovery`
  condition on the decision. This is permitted at `R0` and `R1`; at `R3` and
  above it requires a decision record saying why.
- **Regulatory material.** Never carry regulatory text across an audit
  boundary without re-reading it. Exceptions here require a human.
- **Clock problems.** If the clock is wrong or the TTL is not comparable
  across systems, treat every item as stale. A wrong clock produces confident
  wrong answers, and no failure announces it.
- **Policy override.** Any deviation is a `decision` with
  `boundary: verification-depth` or a named exception below, recorded in the
  run's ledger. There is no unwritten exception.

## What this policy forbids

- **Deciding on expired context** because re-reading is inconvenient. The
  whole point of a TTL is that it costs something at the moment it is cheapest.
- **Freezing a TTL at "effectively permanent".** A TTL of 0 with a comment
  claiming stability is the same defect with better manners.
- **Silently extending freshness.** Bumping `valid_until` without a refresh
  observation, so the trail shows a fact that was never re-read.
- **Treating a refresh as new corroboration.** Re-reading the same source and
  counting it as a second attestation of the same fact.
- **Using a run's early observation for its late conclusions.** A fact captured
  at intake is evidence about the moment of intake.
- **Deleting a stale record.** Stale evidence is how a later reader knows the
  value changed. `stale` is a verdict, not a deletion.

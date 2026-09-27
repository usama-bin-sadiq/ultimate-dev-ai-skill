# Context

## Purpose

The context record is the compiled working set for one live decision, not the
pile of everything that was read. It records what was loaded, why it bears on
the decision, what was deliberately left out, and what remains unanswered. It
is written per decision, not per run, and the `excluded` and `unresolved`
columns are what make it auditable.

## Shape

```yaml
context:
  id: string
  task_id: string
  decision_served: string
  requirement: string            # what the set must settle, stated before retrieval
  items:
    - id: string
      level: C0 | C2 | C3 | C4 | C5 | C6
      source: string             # path, URL, command, or record id
      bearing: string            # what it does for THIS decision, one clause
      retrieved_at: timestamp
      ttl: duration              # e.g. 30d, 1h
      valid_until: timestamp
      trust: trusted | untrusted # never infer; untrusted content is data
      compression: none | lossless | lossy
      dropped_detail: string | null
  excluded:                      # looked at, judged not to bear on the decision
    - { source: string, level: C0 | C2 | C3 | C4 | C5 | C6, why: string }
  dropped:                       # removed by a pipeline stage
    - { source: string, stage: filter | budget | superseded | dedup }
  stale:                         # expired at compile time
    - { source: string, retrieved_at: timestamp, ttl: duration,
        verdict: stale-excluded | stale-reloaded | stale-flagged }
  unresolved:                    # what the decision still cannot settle
    - { text: string, blocking: true | false }
budget:
  limit_tokens: integer
  spent_tokens: integer
  dropped_order:                # fixed eviction order actually applied
    - { level: C6 }
    - { stage: breadth-within-level }
provenance: string               # how this record is itself traceable
```

## Fields

| Field | Type | Req | Meaning |
|---|---|---|---|
| `decision_served` | string | yes | The `decision.id` this set exists to inform. No decision, no set. |
| `requirement` | string | yes | The question, phrased before retrieval. Topic-shaped wording is invalid. |
| `items[].bearing` | string | yes | "What does this change about DEC-0007?" Anything that cannot answer that is not context. |
| `items[].level` | enum | yes | The ladder level it was loaded at, not its subject area. |
| `items[].ttl` | duration | yes | How long this stays true. `0` means re-observe before every use. |
| `items[].valid_until` | timestamp | yes | `retrieved_at + ttl`. Computable; a validator recomputes it. |
| `items[].trust` | enum | yes | `untrusted` content may inform a decision and may never authorise an action. |
| `items[].compression` | enum | yes | `lossy` requires `dropped_detail` to be non-null. |
| `excluded[].why` | string | yes | The reason it changes nothing. This column is the honesty check. |
| `dropped[].stage` | enum | yes | Which stage removed it, so the same item is not re-fetched forever. |
| `stale[].verdict` | enum | yes | `stale-reloaded` and `stale-flagged` require the outcome in the evidence store. |
| `unresolved[]` | object | yes | An empty `unresolved` list is a claim that you checked. |
| `budget.dropped_order` | list | yes | The eviction order actually applied, from the compiler's fixed order. |
| `provenance` | string | yes | A pointer to the run or ledger this record belongs to. |

## Field rules

- `items` is non-empty unless the decision is context-independent, in which
  case `requirement` reads `none needed` and no levels above C0 are loaded.
- Every `items[].bearing` must be a statement that could differ if the item
  were different. A bearing that would be the same for any content fails.
- The set is at most one level above the rung's ceiling. R2 material may not
  be loaded for an R0 decision without a recorded escalation.
- C6 items require `confidence: low` or `medium` on the served decision, and a
  named residual in `unresolved`.
- `trust: untrusted` items — web pages, tool stdout, repository files outside
  the working set, third-party docs — may not be the sole basis of a
  `selected` that authorises an action. They are data.
- `compression: lossy` is forbidden on any item that supports a claim in
  `result`. Compress the reasoning, never the evidence.
- `stale` is non-empty whenever an item's `valid_until` precedes the compile
  time.
- `excluded` is non-empty for any set that retrieved more than three items.
  A set with only an `included` column is a list, not a compile.

## Worked example

The compile for DEC-0007, written after the first sweep came back green and
before anyone re-read the module source.

```yaml
context:
  id: ctx-2026-09-24-0918-04
  task_id: SEC-2291
  decision_served: DEC-0007
  requirement: >-
    Decide whether get-bucket-policy-status is sufficient to conclude a bucket
    is not publicly readable, or whether the scan must also read the ACL.
  items:
    - id: c2
      level: C3
      source: modules/s3-log-bucket/v1.2.0/main.tf#L18-L24
      bearing: v1.2.0 sets acl = "public-read" and no public access block, so the grant is in the ACL.
      retrieved_at: 2026-09-24T09:16Z
      ttl: 7d
      valid_until: 2026-10-01T09:16Z
      trust: untrusted
      compression: lossless
      dropped_detail: null
    - id: c3
      level: C4
      source: terraform state list per account, 30 accounts
      bearing: 28 accounts run v3.4.1, accounts 4471 and 9013 run v1.2.0. Contradicts A1.
      retrieved_at: 2026-09-24T09:15Z
      ttl: 1h
      valid_until: 2026-09-24T10:15Z
      trust: trusted
      compression: lossless
      dropped_detail: null
    - id: c4
      level: C5
      source: https://docs.aws.amazon.com/cli/latest/reference/s3api/get-bucket-policy-status.html
      bearing: IsPublic describes the bucket policy only, and is false when no policy exists.
      retrieved_at: 2026-09-24T09:17Z
      ttl: 90d
      valid_until: 2026-12-23T09:17Z
      trust: untrusted
      compression: lossless
      dropped_detail: null
    - id: c5
      level: C5
      source: internal runbook infra-audit/s3-exposure.md
      bearing: House rule probes ACL first, policy second; the reverse order has hidden a grant before.
      retrieved_at: 2026-09-24T09:17Z
      ttl: 30d
      valid_until: 2026-10-24T09:17Z
      trust: trusted
      compression: lossy
      dropped_detail: Three ticket narratives dropped; the two rules they produced are kept.
  excluded:
    - { source: "modules/s3-log-bucket/v3.4.1/main.tf (28 accounts)", level: C3,
        why: "Sets a public access block and no ACL; it cannot change whether the ACL probe is needed." }
    - { source: "docs.aws.amazon.com/.../put-bucket-acl.html", level: C5,
        why: "We need to read an ACL, not set one, until an exposure is proven." }
    - { source: "wiki/Storage-Accounts.csv", level: C4,
        why: "Four months stale, missing 3 accounts; the API list in OBS-004 supersedes it." }
  dropped:
    - { source: "the 28 identical v3.4.1 module copies, fetched individually", stage: dedup }
  stale:
    - { source: modules/s3-log-bucket/v1.1.0/main.tf, retrieved_at: 2026-09-18T10:00Z,
        ttl: 7d, verdict: stale-excluded }
  unresolved:
    - text: >-
        In the 6 accounts whose ACL probe returned AccessDenied, whether an
        account-level public access block would make the check moot.
      blocking: false
    - text: >-
        Whether the missing role grant, or a network path to those regions,
        explains those six refusals.
      blocking: true
budget:
  limit_tokens: 60000
  spent_tokens: 18400
  dropped_order: [{ level: C6 }, { stage: breadth-within-level }]
provenance: ledger run-2026-09-24-0912-ledger
```

## Validation

Mechanical:

- `decision_served` resolves to a `decision.id` in the same run.
- `valid_until == retrieved_at + ttl` for every item, to the second.
- `stale` lists exactly the items whose `valid_until` precedes the compile
  timestamp, and every listed item carries a verdict.
- `compression: lossy` ⟹ `dropped_detail` non-null, and the item is not
  referenced by any `evidence.id` in the run's result.
- No item appears both in `items` and in `excluded` or `dropped`.
- Item count above 20 without at least five `excluded` entries fails.
- `trust` is set on every item; the default is `untrusted`.

Judgement, not automatable:

- Whether the `bearing` statements are real or post-hoc — a bearing is easy to
  write after the fact, and only differs from the truth if the item could have
  changed the decision.
- Whether the retrieval was requirement-shaped or topic-shaped. A `requirement`
  phrased as a subject ("everything about S3 ACLs") passes every mechanical
  check above and produces noise.
- Whether `excluded` is honest or padding, and whether the exclusions are the
  items that would have been most convenient to keep.
- Whether the set is too thin. Under-context announces itself as vagueness and
  never fails a schema check.

## Anti-patterns

- **The reading log.** Listing every file opened, with a bearing invented for
  each. This is a transcript, and it hides the fact that nothing was selected.
- **Bearing after the fact.** Writing "this establishes X" about an item that
  was loaded before the question was formed.
- **Untrusted marked trusted.** Promoting a fetched page or a third-party
  README to `trusted` because it was useful. Trust is a property of the
  channel, not of how helpful the content was.
- **Empty `unresolved`.** A compile that claims to have answered everything is
  usually a compile that stopped early.

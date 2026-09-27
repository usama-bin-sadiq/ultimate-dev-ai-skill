# Evidence

## Purpose

The evidence record is the unit that separates what is known from what is
believed. Every claim a run reports resolves to one, and the record carries the
whole chain: claim, evidence, source, transformation, verification. Its job is
to make an unsupported step visible, and to make it impossible to report a
confidence the evidence does not reach.

## Shape

```yaml
evidence:
  id: string
  task_id: string
  claim: string                  # the specific assertion being supported
  status: known | inferred | assumed | unverified | uncertain | contradicted
  chain:
    evidence: string             # what was actually seen, in the source's words
    source:
      kind: tool | measurement | primary_document | secondary_source | model_knowledge | user
      locator: string            # command, path, URL, doc id
      issuer: string             # who produced it: AWS, the repo, the operator
      retrieved_at: timestamp
      trust: trusted | untrusted
    transformation: string       # the steps from evidence to claim, named
    verification:
      method: evidence-check | validation-check | independent-check | none
      performed_at: timestamp | null
      result: pass | fail | not-run
      independent_of: string | null
  strength:
    directness: direct | indirect
    independence: count          # distinct issuers, after derivation collapsing
    derivation_of: [string]      # sources this one restates; they count once
  contradicts: [string]          # ids that disagree with this
  supersedes: string | null
  freshness:
    ttl: duration
    valid_until: timestamp
    verdict: current | stale | refreshed
  limits: string                # the bounded residual, required for uncertain
  confidence: high | medium | low
  provenance: string
```

## Fields

| Field | Type | Req | Meaning |
|---|---|---|---|
| `status` | enum | yes | The epistemic status. `known` is the only one that supports an unqualified report. |
| `chain.evidence` | string | yes | What was seen, in the words of the source. Not the conclusion. |
| `chain.source.kind` | enum | yes | `model_knowledge` is never a source for a `known` claim about the world. |
| `chain.source.trust` | enum | yes | `untrusted` covers web content, tool stdout, and files outside the working set. |
| `chain.transformation` | string | yes | The named steps from the evidence to the claim. Empty means the claim *is* the evidence. |
| `chain.verification.method` | enum | yes | Three strengths. `none` caps confidence at `medium`. |
| `chain.verification.independent_of` | string \| null | yes | The alternative derivation. Required for `independent-check`. |
| `strength.independence` | integer | yes | Count of distinct issuers **after** collapsing everything listed in `derivation_of`. |
| `strength.derivation_of` | list | yes | Sources this record restates. They collapse to one before `independence` is counted. |
| `contradicts` | list | yes | Ids that disagree. Non-empty forces `status: contradicted` on one of them. |
| `freshness.valid_until` | timestamp | yes | `retrieved_at + ttl`. Anything past this cannot support a fresh report. |
| `limits` | string | yes | Required for `uncertain`. "Some uncertainty" is not a limit; a bound is. |
| `confidence` | enum | yes | Confidence in the claim given this record, not confidence in the task. |

## Field rules

- `status: known` requires `verification.result: pass` and a `source.kind` of
  `tool`, `measurement`, or `primary_document`. Model recall never yields
  `known`.
- `status: inferred` requires a named `transformation` and either
  `strength.independence ≥ 2` or a single source with that transformation
  stated. A conclusion with no stated step is an assertion.
- `status: assumed` may not appear in `result` without the qualifier
  "assuming", and may not raise `confidence` above `low` in any decision that
  depends on it.
- `status: unverified` may not appear in `result` as a finding. It may appear
  as a limitation, where it is required to be explicit.
- `status: uncertain` requires a bounded `limits` string: a range, a
  population, or a named unknown. An unbounded hedge is not a status.
- `status: contradicted` may not be reported as anything other than a
  limitation, and the contradicting item must be named in `contradicts`.
- **Repetition is not corroboration.** Ten pages that copy one page have
  `strength.independence: 1`. Everything in `derivation_of` collapses to one
  before the count is taken.
- **Absence of a signal is not evidence of absence.** A probe that returned
  non-2xx, was never run, or was filtered out supports `unverified`, never
  `known`. This is the most common laundering step.
- `chain.evidence: "none"` forces `status ∈ {assumed, unverified}` and
  `confidence: low`.
- `chain.verification.result: fail` forces the owning `decision` or `result` to
  be re-opened, not merely annotated.
- `supersedes` is set when a refresh produces a new record; the prior record is
  retained with `freshness.verdict: stale`.

## Worked example

The record that decided the outcome of the run, and the one that should have
existed and did not.

```yaml
evidence:
  id: ev-031
  task_id: SEC-2291
  claim: No transaction-log bucket in the 30-account estate is publicly readable.
  status: contradicted
  chain:
    evidence: >-
      get-bucket-acl on acmepay-eu-3-transaction-logs returned
      "Grantee: AllUsers, Permission: READ" with exit code 0.
    source:
      kind: tool
      locator: aws s3api get-bucket-acl --bucket acmepay-eu-3-transaction-logs --profile security-audit@4471
      issuer: AWS
      retrieved_at: 2026-09-24T09:31Z
      trust: trusted
    transformation: >-
      Direct read. The response is the grant list for the bucket, the grant is
      on the bucket, so any principal including anonymous may read its objects.
      No intermediate step.
    verification:
      method: independent-check
      performed_at: 2026-09-24T09:44Z
      result: pass
      independent_of: >-
        Confirmed by an unauthenticated request against the object URL from
        outside the VPC, which returned 200.
  strength: { directness: direct, independence: 1, derivation_of: [] }
  contradicts: [ev-032]
  supersedes: null
  freshness: { ttl: 1h, valid_until: 2026-09-24T10:31Z, verdict: current }
  limits: >-
    The grant was present on two buckets in two accounts. Whether it was ever
    read is not established and is not inferable from the grant.
  confidence: high in <the object>
  provenance: OBS-015
---
evidence:
  id: ev-032
  task_id: SEC-2291
  claim: >-
    Buckets in accounts 220145987310 and 220145987512 are not publicly readable
    because get-bucket-policy-status returned IsPublic false for all of them.
  status: unverified
  chain:
    evidence: >-
      get-bucket-policy-status returned {"PolicyStatus":{"IsPublic":false}} for
      22 buckets. 6 further calls returned AccessDenied and were skipped by the
      first pass of the scan.
    source:
      kind: tool
      locator: scan-v1.sh, 30 invocations
      issuer: AWS
      retrieved_at: 2026-09-24T09:22Z
      trust: trusted
    transformation: >-
      Intended: a false IsPublic means no public grant. Invalid twice over.
      IsPublic is derived from the bucket policy alone, so it is false on a
      bucket with no policy at all, and it says nothing about ACL grants. Six
      calls returned no result, and the transformation read their silence as a
      pass.
    verification:
      method: none
      performed_at: null
      result: not-run
      independent_of: null
  strength: { directness: indirect, independence: 1, derivation_of: [] }
  contradicts: [ev-031]
  supersedes: null
  freshness: { ttl: 1h, valid_until: 2026-09-24T10:22Z, verdict: stale }
  limits: >-
    Covers nothing. The 22 verdicts stand on a control that cannot carry the
    grant, and 6 accounts have no verdict at all. Re-run as ev-034.
  confidence: low in <the object>
  provenance: OBS-013
```

## Validation

Mechanical:

- `status`, `freshness.verdict`, `chain.verification.method`, and
  `chain.verification.result` are enum members.
- `valid_until == retrieved_at + ttl` for every record.
- `status: known` ⟹ `verification.result: pass` and `source.kind` ∈ {tool,
  measurement, primary_document}.
- `status: uncertain` ⟹ `limits` is non-empty and names a bound.
- `chain.evidence: "none"` ⟹ `status ∈ {assumed, unverified}` and
  `confidence: low`.
- `verification.method: independent-check` ⟹ `independent_of` non-null.
- `contradicts` is symmetric: if A lists B, B lists A.
- Every claim in `result` resolves to at least one evidence id, and every id
  used there with `status ∈ {known, inferred}` has `freshness.verdict: current`.

Judgement, not automatable:

- Whether the transformation is the one actually performed, or a plausible one
  written afterwards. An invalid transformation launders absence into a
  conclusion, and no field will catch it.
- Whether `strength.independence` was counted after collapsing derived sources.
  This is the check that most often fails in practice.
- Whether the `claim` is scoped exactly as widely as the evidence. "This bucket"
  becoming "the estate" in one rewrite is the most common over-claim.
- Whether `limits` states the real residual or the one that reads well.

## Anti-patterns

- **The policy-status sweep.** Probing one control, reading its green result as
  a verdict on the whole question. The check ran; the claim it supports is a
  different one.
- **Skipped probes as passes.** Shell constructs that swallow a non-2xx
  response. The gap list is empty because the failure was never observed.
- **Corroboration by repetition.** Ten sources that all cite one upstream
  document, counted as ten.
- **Dropping the qualifier on report.** An `inferred` or `assumed` claim restated
  as a finding, with the hedge removed because it read badly. The hedge is the
  information.

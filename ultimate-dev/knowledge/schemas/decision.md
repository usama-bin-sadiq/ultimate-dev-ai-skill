# Decision

## Purpose

The decision record is the unit of currency of the decision fabric. Anything
that changes the shape of the work gets one, at the moment the boundary is
crossed, before the work starts. Its job is to make a choice reviewable later
by someone who was not present, which is only possible if the alternative that
was *not* taken is written down.

## Shape

The eight fields below are the record. The envelope exists so a ledger can
index it; it carries no decision content.

```yaml
id: DEC-0007
boundary: context-depth            # one of the kernel's decision boundaries
at: 2026-09-24T09:18Z
status: open                       # open | superseded
supersedes: DEC-0003
question: string
selected: string
rejected:
  - option: string
    why_not: string
rationale: string                   # the reasoning, in one line
confidence:
  level: high | medium | low
  in_what: string            # REQUIRED — the object confidence is about
cost: string                        # expected effort, and what it buys
evidence:                           # may be the literal string "none"
  - ref: string                     # evidence id, observation id, or file path
    bearing: string
recovery: string                    # the condition that would reverse this
```

## Fields

| Field | Type | Req | Meaning |
|---|---|---|---|
| `id` | string | yes | Stable handle in the run's decision ledger. |
| `boundary` | enum | yes | Which boundary is being crossed: `context-depth`, `strategy`, `capability-acquisition`, `verification-depth`, `learning-promotion`, … |
| `at` | timestamp | yes | When the choice was made, before its consequences were known. |
| `status` | enum | yes | `superseded` keeps the record; a reversed decision is never deleted. |
| `supersedes` | string \| null | yes | The decision this one replaces. Null for the first. |
| `question` | string | yes | The boundary phrased as a question with exactly one answer. |
| `selected` | string | yes | The chosen course, concretely enough to execute. |
| `rejected[].option` | string | yes | A real alternative, named as someone could have chosen it. |
| `rejected[].why_not` | string | yes | The reason, tied to evidence, cost, or risk. Not "it was worse". |
| `rationale` | string | yes | One line. The reasoning that survives once the detail is gone. |
| `confidence.level` | enum | yes | Strength of belief in the selection, given the evidence. |
| `confidence.in_what` | string | yes | **The object the confidence is about.** Omitting it is an error: a bare level is read downstream as a property of the conclusion rather than of the evidence, and that is the documented over-trust failure. A bare `high` is rejected. |
| `cost` | string | yes | What it spends, and what that buys. "2 calls, closes U1." |
| `evidence[].ref` | string | yes | An observation id (`OBS-n`) or a file path. Use the literal `none` when there is genuinely none. **Prose is rejected** — a narrative cannot be checked for existence, so a fabricated citation is indistinguishable from a real one. A pointer either resolves or it does not. |
| `evidence[].bearing` | string | yes | What this item does for the decision. |
| `recovery` | string | yes | The named observation that would reverse the choice. |

## Field rules

- `rejected` has at least one entry. **A decision with no recorded alternative
  is an assertion, and must be recorded as an observation instead.** This is the
  rule that makes the record a decision.
- A `rejected` entry that no reasonable agent would have considered is padding.
  If you cannot name the option you chose *against*, you did not choose.
- `evidence: none` is valid. `confidence.level` may then not be `high`.
- `confidence.in_what` is required and non-empty. `confidence: {level: high}` with
  no object is a validation failure, not a warning: an uncalibrated self-assessment
  is exactly the field users over-trust.
- `evidence[].ref` resolves to an existing observation or path, or is the literal
  `none`. Free text is rejected.
- `confidence: high` requires either ≥1 evidence ref whose `bearing` names the
  question, or a `cost` string that states the bet.
- `confidence: low` requires `recovery` to be cheap to reach, otherwise the
  decision is an escalation.
- `boundary: learning-promotion` additionally requires a `scope` and a
  `removal` clause; see `learning.md` and `policies/promotion.md`.
- `boundary: verification-depth` requires the three check kinds it intends to
  run, by name.
- Every `supersedes` target exists. Superseded records are retained verbatim
  and never edited.
- A decision taken at `R0` may be a single line with no `rejected` list, if the
  kernel states that the next action was already determined. Everything else
  carries the full record.

## Worked example

The context-depth decision taken mid-run, after the first scan looked clean.

```yaml
id: DEC-0007
boundary: context-depth
at: 2026-09-24T09:18Z
status: open
supersedes: DEC-0003
question: >-
  Is get-bucket-policy-status sufficient to decide that a bucket is not
  publicly readable?
selected: >-
  Load C3 on the module's own ACL arguments and C5 on GetBucketAcl
  semantics, and add a get-bucket-acl probe to the scan before drawing any
  verdict.
rejected:
  - option: Treat IsPublic=false from get-bucket-policy-status as the verdict.
    why_not: >-
      That field is derived from the bucket policy only. On a bucket with no
      policy it returns false, which is indistinguishable from a reviewed
      policy. Twenty-eight clean verdicts rested on it.
  - option: Read the whole infra-tf repository and decide from the module source alone.
    why_not: >-
      The bucket state in each account may predate the module version pinned
      there, which is exactly what A1 was wrong about. C4 territory, not C3.
  - option: Look up an independent bucket-scanning best practice first.
    why_not: >-
      Cost buys no decision here. The question is answered by the module's own
      arguments, which we already hold.
rationale: >-
  A verdict must rest on the control that can actually carry the grant, and an
  ACL grant does not appear in a policy-status response.
confidence: high in <the object>
cost: 3 tool calls, 40 s; closes A2 and adds ~0.3 s per bucket to the scan
evidence:
  - { ref: "modules/s3-log-bucket/v1.2.0/main.tf#L18-L24", bearing: "v1.2.0 sets acl = \"public-read\" and no public access block" }
  - { ref: OBS-013, bearing: "22 of 22 probed buckets returned IsPublic=false" }
recovery: >-
  get-bucket-acl on a clean bucket returns a grant list with no AllUsers entry
  for all 28 accounts. If it does not, this depth was still too shallow.
```

A second, smaller record from the same run — the acquisition decision that
almost created a capability.

```yaml
id: DEC-0011
boundary: capability-acquisition
at: 2026-09-24T09:07Z
status: open
supersedes: null
question: How do we enumerate the 30 production accounts?
selected: aws organizations list-accounts under the audit role
rejected:
  - option: Write a small script that walks the account list from the CSV in the wiki.
    why_not: >-
      The CSV is 4 months stale and 3 accounts were added since. It would also
      be a capability created for one run, which is a plan step, not a skill.
  - option: Ask the platform team to paste the account list.
    why_not: >-
      It is in an API we already have permission to call, and asking costs a
      round trip we do not need.
rationale: The authoritative list is one call away and is self-updating.
confidence: high in <the object>
cost: 1 tool call
evidence:
  - { ref: OBS-004, bearing: "list-accounts returned 30 accounts, matching the 30 in the security register" }
recovery: >-
  list-accounts returns fewer than 30 accounts, or an account outside the
  register appears. Then the register, not the API, is authoritative and this
  decision is wrong.
```

## Validation

Mechanical:

- All eight payload fields are present and non-empty.
- `confidence` is a member of its enum; `status` and `boundary` likewise.
- `supersedes`, when set, resolves to an existing `id`.
- At least one `rejected[].option` whose `why_not` exceeds 10 characters and
  contains no occurrence of the word "worse" without a cause.
- `confidence.level: high` ⟹ `evidence` is not `none`.
- Every `evidence[].ref` beginning `OBS-` resolves to an observation id that
  exists in the run's observations. Unresolvable pointers are fabrication and fail
  the record.
- No two `decision.id` values equal.

Judgement, not automatable:

- Whether the `rejected` alternatives are ones a competent peer would have
  seriously weighed, or straw men built to make the selection look inevitable.
- Whether `rationale` states a mechanism or restates the selection.
- Whether `cost` is an estimate or a post-hoc rationalisation written after the
  spend.
- Whether the boundary was crossed at all, or whether this is a record of
  something that was never in doubt.

## Anti-patterns

- **The post-hoc ledger.** Writing the record after the fact, with `rejected`
  filled from what you would consider now. The value of the record is that it
  was written before the consequence was known.
- **Straw alternatives.** Rejecting an option nobody would pick so the chosen
  path looks forced. Two real alternatives beat four decorative ones.
- **`rejected: none`.** The most common way a decision record becomes an
  assertion. If nothing was weighed, there was no decision to record.
- **Confidence laundering.** Marking `high` because the chosen path is
  conventional, with no evidence ref, so the ledger reads as more certain than
  the run was.

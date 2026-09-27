# Observation

## Purpose

The observation record is what actually happened. It is written after an action
and before any interpretation of it, and it is the only record type the kernel
is permitted to treat as fact about the world. Everything else — evidence,
decisions, results — is downstream of an observation or explicitly not.

## Shape

```yaml
observation:
  id: string
  task_id: string
  at: timestamp
  action:
    kind: command | read | write | query | delegate | none
    target: string
    input_digest: string         # hash or the exact arguments
    capability: string           # capability id that made it possible
  preconditions:
    - { text: string, held: true | false }
  result:
    status: success | partial | failure | blocked | not_run
    exit_code: integer | null
    duration_ms: integer | null
    output_ref: string           # file, transcript handle, or inline below
  observed: string               # verbatim, or "none"
  state_change:                  # what is different because this happened
    - { field: string, from: string, to: string }
  errors: [string]
  surprises: [string]            # observed, not predicted
  not_observed: [string]         # what was expected and is now unknown
  evidence: [string]             # evidence ids derived from this observation
  next: string                   # resume, replan, retry-with-cause, escalate, stop
```

## Fields

| Field | Type | Req | Meaning |
|---|---|---|---|
| `action.capability` | string | yes | The capability that made it possible. An action with no capability is direct work. |
| `action.input_digest` | string | yes | The exact arguments. Without it the observation cannot be repeated or audited. |
| `preconditions[].held` | bool | yes | A unit whose precondition is false is not executed; it is re-decided. |
| `result.status` | enum | yes | Five states. `not_run` exists so that absence is recordable. |
| `result.exit_code` | integer \| null | yes | Non-null for `command`. `null` for `none` and for anything not run. |
| `observed` | string | yes | Verbatim. A paraphrase in this field is a fabrication, because it can no longer be checked against the source. |
| `state_change` | list | yes | Empty is a valid outcome; silent no-ops should be recorded as such. |
| `surprises` | list | yes | Anything that did not match the expectation the plan held. |
| `not_observed` | list | yes | The load-bearing field. It converts "we did not check" from invisible to explicit. |
| `next` | enum | yes | `retry` requires a diagnosed cause in `errors`, and is counted against the retry budget. |

## Field rules

- `result.status: not_run` requires `not_observed` to be non-empty. A tool
  that was not run yields an unknown, not an expectation.
- `result.status: success` with `exit_code != 0`, or `failure` with
  `exit_code == 0`, fails validation. Success and exit status are separate
  facts and the record must not merge them.
- `observed` is verbatim or the literal `none`. A summary belongs in
  `state_change` or a derived `evidence` record.
- `output_ref` is required whenever `observed` is elided, and must resolve.
- `action.capability` must resolve to a `capability` record whose
  `validation.status` is `validated`, or to the literal `direct`.
- `next: retry` is forbidden unless `errors` names a cause and the run's retry
  count for this action is under the bound in the recovery policy. Blind retry
  cannot be represented as a valid record.
- `next: replan` requires a `decision.id` in the run that caused it.
- `not_observed` is never empty when the action was expected to answer an
  unknown, an assumption, or a success criterion.
- `surprises` entries are the highest-value field in the record. A record with
  no surprises on a result that was going to be fine is not the interesting one
  to read.
- One observation per invocation. Batching several calls into one record
  destroys the ability to attribute an effect to a cause.

## Worked example

The observation that exposed a live exposure, and the one that exposed the
run's own defect.

```yaml
observation:
  id: OBS-015
  task_id: SEC-2291
  at: 2026-09-24T09:31Z
  action:
    kind: command
    target: bucket acmepay-eu-3-transaction-logs in account 220145987310
    input_digest: sha256:9f1c...a7d2   # exact flag set
    capability: cap-014
  preconditions:
    - { text: The bucket policy probe has run and reported IsPublic false., held: true }
    - { text: The account's module version is known., held: true }
  result: { status: success, exit_code: 0, duration_ms: 812, output_ref: OBS-015.out }
  observed: |
    "Grants": [
      { "Grantee": { "Type": "CanonicalUser", "URI": ".../s3/LogDelivery" },
        "Permission": "WRITE" },
      { "Grantee": { "Type": "Group", "URI": ".../global/AllUsers" },
        "Permission": "READ" }
    ]
  state_change:
    - { field: "task.assumptions[A1].status", from: assumed, to: contradicted }
    - { field: "task.assumptions[A2].status", from: assumed, to: contradicted }
    - { field: "budget.tool_calls", from: 21, to: 22 }
  errors: []
  surprises:
    - The policy probe on this bucket returned IsPublic false, so the run was about to mark it clean.
    - The exposure is in the ACL, which no earlier probe had read.
  not_observed:
    - Whether the grant was ever exercised; the ACL shows a capability, not an event.
    - Whether the same grant exists on other buckets in the account.
  evidence: [ev-031]
  next: replan
---
observation:
  id: OBS-014
  task_id: SEC-2291
  at: 2026-09-24T09:22Z
  action:
    kind: command
    target: 30 production accounts, one get-bucket-policy-status call each
    input_digest: scan-v1.sh — loop over org list; '|| true' on each iteration
    capability: cap-014
  preconditions:
    - { text: The audit role can call get-bucket-policy-status in every account., held: false }
  result: { status: partial, exit_code: 0, duration_ms: 41230, output_ref: OBS-014.out }
  observed: |
    24 of 30 accounts returned a policy status.
    6 iterations produced no output. The loop's `2>/dev/null || true` swallowed
    the AccessDenied from s3:GetBucketPolicyStatus in those 6 accounts.
  state_change:
    - { field: "result.verdict_table", from: "30 accounts, 30 verdicts", to: "24 verdicts, 6 silently skipped" }
  errors:
    - AccessDenied in 6 accounts, suppressed by the loop rather than surfaced.
  surprises:
    - The loop reported success. A suppressed authorisation failure is
      indistinguishable from a clean pass unless the exit code is captured.
  not_observed:
    - The public-readable state of 6 buckets.
    - Whether the 6 failures share a cause.
  evidence: [ev-032]
  next: replan
```

The third record of the run is the shortest and the most useful, because it is
what keeps a claim from being made:

```yaml
observation:
  id: OBS-027
  task_id: SEC-2291
  at: 2026-09-24T10:38Z
  action:
    kind: command
    target: the production estate, terraform plan after the ACL remediation
    input_digest: not applicable — no invocation
    capability: direct
  preconditions:
    - { text: "Authorised to plan against production.", held: false }
  result: { status: not_run, exit_code: null, duration_ms: null, output_ref: null }
  observed: none
  state_change:
    - { field: "task.success_criteria[S4].status", from: pending, to: "partial — scratch account only" }
  errors: []
  surprises: []
  not_observed:
    - Whether the production configuration converges after the ACL change.
    - Whether the remediation introduces drift in the module-managed state.
  evidence: []
  next: escalate
```

## Validation

Mechanical:

- `result.status`, `next`, and `action.kind` are enum members.
- `result.status` and `exit_code` agree on success and failure.
- `result.status: not_run` ⟹ `not_observed` non-empty ∧ `observed == "none"`.
- `next: retry` ⟹ `errors` non-empty ∧ the retry count for this `input_digest`
  is under the policy bound.
- `next: replan` ⟹ a `decision.id` exists in the run.
- `action.capability` resolves to a `validated` capability, or is `direct`.
- `output_ref`, when non-null, resolves to a stored artefact.
- At most one `evidence` id per observation may have `status: known`. More than
  one means the observation is a batch, which is itself a validation failure.

Judgement, not automatable:

- Whether `observed` is truly verbatim, or a paraphrase that would be
  indistinguishable to a reader and wrong to a machine.
- Whether `surprises` catches the thing that actually mattered, or lists what
  was merely unusual. Only someone re-deriving the expectation can tell.
- Whether `not_observed` is honest about the probe that was skipped.
- Whether the action was the one the plan called for, or an improvist's
  substitute that happened to work.

## Anti-patterns

- **The swallowed failure.** A loop or wrapper that turns a non-2xx into
  silence, and a run that reads silence as a pass. The most dangerous record in
  the system, because it is indistinguishable from success downstream.
- **The summarised observation.** "The command returned the expected results",
  which cannot be checked and cannot support a claim.
- **Prediction recorded as observation.** Writing the expected output instead
  of the actual one. This is the confident fabrication, and it is the failure
  mode that most damages the whole architecture.
- **Observation and interpretation in one field.** Folding "the ACL grants
  AllUsers READ" together with "the bucket is exposed" so the conclusion is
  never separately checkable.

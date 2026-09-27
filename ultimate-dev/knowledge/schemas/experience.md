# Experience

## Purpose

The experience record is one completed run, assembled. It is the audit trail
that ties a task to the decisions taken, the actions run, what was observed,
what failed, how it verified, and what was proposed for retention. It is what a
reviewer reads to understand not just what the kernel concluded but how it got
there, and it is the only input the learning system is allowed to draw on.

## Shape

```yaml
experience:
  id: exp-0141
  task_id: SEC-2291
  started_at: timestamp
  ended_at: timestamp
  task: string                  # objective as it was stated
  rung: R0 | R1 | R2 | R3 | R4
  scale: L1 | L2 | L3 | L4 | L5 | L6 | L7
  rung_history:                 # escalation is normal; hiding it is not
    - { at: timestamp, from: string, to: string, trigger: string, decision: string }
  timeline:
    - { at: timestamp, phase: string, ref: string }
  budget:
    limits: { tool_calls: integer, wall_clock_minutes: integer, tokens: integer }
    spent: { tool_calls: integer, wall_clock_minutes: integer, tokens: integer }
    overruns: [string]
  decisions: [string]           # decision ids, in order
  actions: [string]             # observation ids, in order
  failures:
    - { at: timestamp, class: string, cause: string, response: string, decision: string }
  verification:
    verdict: VERIFIED | PARTIAL | FAILED
    criteria: [{ id: string, result: pass | fail | not-run, evidence: [string] }]
    checks_run: [evidence-check | validation-check | independent-check]
    insufficient:
      - { criterion: string, missing: string, would_close_it: string }
  self_evaluation:
    solved: boolean
    context_necessary: boolean
    reasoning_sufficient: boolean
    strategy_effective: boolean
    verification_adequate: boolean
    what_failed: [string]
    reusable: [string]
    do_not_repeat: [string]
  result_ref: string            # the delivered result record
  learning_candidates: [string] # learning ids raised, none promoted by default
  provenance: string
  reviewer: human | agent | none
```

## Fields

| Field | Type | Req | Meaning |
|---|---|---|---|
| `task` | string | yes | The objective verbatim at intake. Changes to it belong in `task.md`. |
| `rung_history` | list | yes | Every change of rung. An empty list on a run that escalated is a falsified record. |
| `budget.limits` | object | yes | The budget as set at intake, not as it turned out. |
| `budget.overruns` | list | yes | Non-empty when `spent` exceeds any limit. An overrun that is not recorded is a concealed overrun. |
| `failures[].class` | enum | yes | One of the recovery classifications: missing context, wrong capability, wrong strategy, bad assumption, execution, resource, verification, unsupported objective. |
| `failures[].cause` | string | yes | The diagnosed cause. A failure record without a cause is a retry waiting to happen. |
| `verification.verdict` | enum | yes | One of three. `PARTIAL` is a real verdict and is not a failure of record-keeping. |
| `verification.criteria[].evidence` | list | yes | Non-empty for any `pass`. A pass with no evidence is a claim. |
| `verification.insufficient` | list | yes | What was not established. Required when the verdict is not `VERIFIED`. |
| `self_evaluation.context_necessary` | bool | yes | The kernel's own check on whether the effort gate was right. |
| `self_evaluation.do_not_repeat` | list | yes | Explicit negative learning. It is the half of learning that never gets written down. |
| `learning_candidates` | list | yes | Ids only. An experience may not promote anything; that is a separate decision. |
| `reviewer` | enum | yes | `human` for a run with an irreversible action, an external side effect, or an R4 checkpoint. |

## Field rules

- `ended_at` is set and `ended_at > started_at`. An open run has no experience
  record.
- `rung_history` is non-empty whenever the final `rung` differs from the
  intake rung, and every entry names the trigger.
- `budget.spent` may not exceed any `limits` value without a matching
  `overruns` entry naming the cause and the decision taken at the time.
- `verification.verdict: VERIFIED` ⟹ every `success_criteria` id appears in
  `criteria` with `result: pass` and a non-empty `evidence` list.
- `verification.verdict: PARTIAL` ⟹ `insufficient` is non-empty and every
  `not-run` or `fail` criterion appears in it.
- `verification.verdict: FAILED` ⟹ `failures` contains at least one entry
  classified as a verification failure, and `result_ref` states what was and was
  not delivered.
- `failures[].response: retry` appears at most the number of times the retry
  bound allows for that cause, and each carries its cause.
- `self_evaluation` is mandatory. A run with no self-evaluation has not been
  reviewed and may not raise a learning candidate.
- `learning_candidates` entries resolve to `learning` records in state
  `observed` or `candidate`. An experience may not point at a `promoted`
  learning; promotion is a later, separate act.
- `reviewer: human` is required when any action in the run had
  `side_effects[].kind` of `irreversible`, `credential`, or `write` against a
  production system.
- The record is append-only. Corrections are new fields or a superseding
  experience, never edits that remove a failure.

## Worked example

```yaml
experience:
  id: exp-0141
  task_id: SEC-2291
  started_at: 2026-09-24T09:12Z
  ended_at: 2026-09-24T11:20Z
  task: >-
    Establish whether any transaction-log bucket in the 30 production AWS
    accounts is publicly readable, remove any public grant, and leave a
    repository check that fails on the configuration we had before the fix.
  rung: R3
  scale: L3
  rung_history:
    - { at: 2026-09-24T09:18Z, from: R2, to: R3, trigger: "IsPublic=false on a bucket whose policy does not exist is not a verdict", decision: DEC-0007 }
    - { at: 2026-09-24T09:44Z, from: R3, to: R4, trigger: "a proven live public grant on production data", decision: DEC-0013 }
  timeline:
    - { at: 2026-09-24T09:12Z, phase: triage, ref: task.md }
    - { at: 2026-09-24T09:15Z, phase: context, ref: ctx-2026-09-24-0915-01 }
    - { at: 2026-09-24T09:22Z, phase: execute, ref: OBS-014 }
    - { at: 2026-09-24T09:31Z, phase: execute, ref: OBS-015 }
    - { at: 2026-09-24T09:44Z, phase: verify, ref: DEC-0013 }
    - { at: 2026-09-24T10:31Z, phase: learn, ref: L-0031 }
    - { at: 2026-09-24T11:16Z, phase: learn, ref: DEC-0018 }
  budget:
    limits: { tool_calls: 60, wall_clock_minutes: 45, tokens: 400000 }
    spent: { tool_calls: 71, wall_clock_minutes: 128, tokens: 412000 }
    overruns:
      - "11 tool calls over: the ACL probe was added to 30 accounts after DEC-0007, then 6 accounts were re-probed individually once the role gap was identified."
      - "83 minutes over: 55 waiting on the on-call engineer for the R4 checkpoint on the production ACL change, the rest on the generated skill's adversarial test after the result was already delivered."
      - "12k tokens over: the AWS CLI reference was fetched twice, the second time under a different URL for the same page."
  decisions: [DEC-0007, DEC-0011, DEC-0013, DEC-0016, DEC-0018, DEC-0021]
  actions: [OBS-004, OBS-013, OBS-014, OBS-015, OBS-016, OBS-027]
  failures:
    - { at: 2026-09-24T09:22Z, class: "bad assumption", cause: "The scan treated a suppressed AccessDenied as a pass, because the loop carried `|| true`.", response: "Re-ran the 6 accounts individually and captured exit codes.", decision: DEC-0007 }
    - { at: 2026-09-24T09:31Z, class: "bad assumption", cause: "A1 assumed one module version estate-wide; accounts 4471 and 9013 pin v1.2.0, which sets a public-read ACL and no public access block.", response: "Replanned the scan to resolve module version per account and read ACLs.", decision: DEC-0007 }
    - { at: 2026-09-24T09:44Z, class: "verification", cause: "The production-side effect of the ACL change was never planned against production.", response: "Demoted S4 to not-run and raised a human checkpoint.", decision: DEC-0013 }
    - { at: 2026-09-24T11:16Z, class: "wrong capability", cause: "The generated audit skill parsed a module README's injected text as an instruction.", response: "Blocked the skill at validating; it was not selected again.", decision: DEC-0018 }
  verification:
    verdict: PARTIAL
    criteria:
      - { id: S1, result: fail, evidence: [ev-031, ev-034] }
      - { id: S2, result: pass, evidence: [ev-031, ev-035] }
      - { id: S3, result: pass, evidence: [ev-036] }
      - { id: S4, result: not-run, evidence: [] }
    checks_run: [evidence-check, validation-check, independent-check]
    insufficient:
      - { criterion: S1, missing: "6 of 30 accounts have no verdict; the security-audit role lacks s3:GetBucketAcl there.", would_close_it: "IAM-4471 grants the role read access to bucket ACLs estate-wide, then the 6 buckets are probed." }
      - { criterion: S4, missing: "No plan was run against the production estate; only the scratch account.", would_close_it: "A read-only plan in production, authorised by the platform owner." }
  self_evaluation:
    solved: false
    context_necessary: true
    reasoning_sufficient: false
    strategy_effective: false
    verification_adequate: true
    what_failed:
      - The first scan's shell construct converted an authorisation error into a silent skip.
      - The scope of the sweep was the policy control only, and the exposure was in the ACL.
    reusable:
      - The per-account version map; it made the legacy accounts visible in seconds.
      - The unauthenticated read from outside the VPC as an independent check.
    do_not_repeat:
      - Putting `|| true` in a scan loop. Capture the exit code and count the gaps.
      - Fetching the same reference page twice under two URLs.
  result_ref: res-0087
  learning_candidates: [L-0031, L-0032, L-0033]
  provenance: ledger run-2026-09-24-0912-ledger
  reviewer: human
```

## Validation

Mechanical:

- Timestamps parse and are ordered.
- `rung_history` reconciles with the intake rung in `task.triage.rung` and the
  final `rung`.
- `budget.spent` ≤ `limits` per field, or a matching `overruns` entry exists.
- `verdict: VERIFIED` ⟹ every criterion `pass` with evidence.
- `verdict ∈ {PARTIAL, FAILED}` ⟹ `insufficient` non-empty.
- Every id in `decisions`, `actions`, `learning_candidates`, and `result_ref`
  resolves.
- `reviewer: human` whenever the run contains an observation whose capability
  declared an `irreversible` or `credential` side effect.
- `self_evaluation` has all eight keys present; booleans may not be null.

Judgement, not automatable:

- Whether the self-evaluation is honest, or written to justify the run. The
  `reasoning_sufficient: false` here is the field that makes the record
  readable.
- Whether the timeline reflects the run or a tidied version of it. A run with no
  detours recorded usually had detours.
- Whether the failures are classified at the level of cause rather than at the
  level of symptom.
- Whether the run actually stopped when the budget overran, or merely noted it
  and continued.

## Anti-patterns

- **The success-shaped experience.** A record that reads as a clean run: no
  overruns, no detours, `solved: true`. It is usually the run with the most to
  report.
- **PARTIAL quietly upgraded.** `insufficient` moved into the prose of the
  result instead of the structured field, so the gap is readable but not
  countable.
- **Learning smuggled through.** A `self_evaluation.reusable` list that has
  already been written into a reference file, bypassing promotion.
- **The erased failure.** A failure resolved and dropped from the record,
  because the outcome was fine. The resolved version is the useful one.

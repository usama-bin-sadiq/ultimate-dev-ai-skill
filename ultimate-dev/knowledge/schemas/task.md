# Task

## Purpose

The task record is what the kernel commits to before it decides anything. It
separates what must be *true of the result* from what must be *observable* to
call the result finished, because only the second one tells you when to stop.
It is created at UNDERSTAND, revised when an assumption fails, and is the object
every later record points back to.

## Shape

```yaml
task:
  id: string                  # stable handle, e.g. SEC-2291
  title: string
  raised: date
  raised_by: string
objective: string              # one sentence, in the user's terms
requirements:                  # what must be true when you are done
  - id: string
    text: string
constraints:                   # time, tools, data, permissions, prohibitions
  - id: string
    text: string
assumptions:
  - id: string
    text: string
    breaks_if: string
    status: assumed | verified | contradicted
unknowns:
  - id: string
    text: string
    blocking: true | false
    resolution: string | null  # how it will be closed
    status: open | resolved | deferred
success_criteria:              # observable condition that ends the task
  - id: string
    text: string
    measured_by: string        # the check, by name
triage:
  complexity: integer         # count of interdependent parts
  uncertainty: low | medium | high
  consequence: low | medium | high
  reversibility: cheap | costly | irreversible
  rung: R0 | R1 | R2 | R3 | R4
  scale: L1 | L2 | L3 | L4 | L5 | L6 | L7
dependencies: [string]
risk:
  id: string
  text: string
  mitigation: string
  residual: low | medium | high
```

## Fields

| Field | Type | Req | Meaning |
|---|---|---|---|
| `task.id` | string | yes | Stable handle used by every other record as `task_id`. |
| `task.title` | string | yes | Short human label. Not a restatement of the objective. |
| `task.raised` | date | yes | When the work entered the system. |
| `objective` | string | yes | The outcome in one sentence, in the requester's terms, not yours. |
| `requirements[].id` | string | yes | Stable local id (`R1`, `R2`). Referenced by decisions and results. |
| `requirements[].text` | string | yes | A change in the world. "Add retries." Never an observation. |
| `constraints[].text` | string | yes | A limit on how, not on what. Includes explicit prohibitions. |
| `assumptions[].breaks_if` | string | yes | The observation that would kill it. An assumption with no failure condition is not an assumption. |
| `assumptions[].status` | enum | yes | `contradicted` forces a replan of everything that depended on it. |
| `unknowns[].blocking` | bool | yes | A blocking unknown stops execution of the units that need it. |
| `unknowns[].resolution` | string \| null | yes | The named action that closes it, or `null` when it is out of scope. |
| `success_criteria[].measured_by` | string | yes | The named check that produces pass/fail. A criterion with no check is a wish. |
| `triage.rung` | enum | yes | Effort floor. `R0`–`R4` per the kernel's ladder. |
| `triage.scale` | enum | yes | `L1`–`L7`. Decides how much structure the record carries. |
| `triage.reversibility` | enum | yes | Forces the rung upward when `irreversible`. |
| `risk.residual` | enum | yes | Risk *after* mitigation. Not the risk you noticed. |

## Field rules

- `requirements` and `success_criteria` are both non-empty and disjoint in
  wording. A criterion that restates a requirement as a check is acceptable; a
  requirement recorded only as a criterion is not.
- Every `requirements[].id` and `success_criteria[].id` is referenced at least
  once by a decision, an observation, or the `result`.
- `unknowns[].blocking: true` and `status: open` may not coexist with an
  in-flight work unit that depends on it.
- `assumptions[].status: contradicted` may not remain contradicted at delivery.
  It must become `verified`, be replaced by a new assumption, or appear in
  `result.limitations`.
- `triage.consequence: high` with `reversibility: irreversible` requires
  `rung: R4`.
- `rung: R0` allows a one-line `objective` and no `risk` block. Below `R2` you
  may not carry more rigour than the rung justifies.
- The record grows monotonically in `requirements` and `success_criteria` only
  by revision with a decision record; silently dropping a criterion to reach
  `VERIFIED` is prohibited.

## Worked example

A cloud-security ticket, filled in as the kernel would fill it.

```yaml
task:
  id: SEC-2291
  title: Public-read exposure in the transaction-log buckets
  raised: 2026-09-23
  raised_by: security-oncall
objective: >-
  Establish whether any transaction-log bucket in the 30 production AWS accounts
  is publicly readable, remove any public grant, and leave a repository check
  that fails on the configuration we had before the fix.
requirements:
  - { id: R1, text: Enumerate every production account that runs the s3-log-bucket module. }
  - { id: R2, text: Reach a definitive public-readable verdict per bucket from an authoritative check. }
  - { id: R3, text: Remove every public grant found, and re-verify after the change. }
  - { id: R4, text: Add a repository check that fails on the pre-fix module and passes on the current one. }
  - { id: R5, text: Leave module version pins untouched; that is a separate ticket. }
constraints:
  - { id: C2, text: Merge before the PCI audit on 2026-09-30. }
  - { id: C3, text: Read-only in production, except an ACL change on a bucket proven public. }
  - { id: C4, text: Cross-account access only through the security-audit role. No human credentials. }
  - { id: C5, text: No third-party SaaS scanner may see bucket names or account IDs. }
assumptions:
  - id: A1
    text: Every account runs s3-log-bucket from this repository.
    breaks_if: >-
      An account pins a fork or an older major, so the scan checks the wrong
      module version and calls a bucket clean that was never inspected.
    status: contradicted          # accounts 4471 and 9013 pin v1.2.0
  - id: A2
    text: A public grant can only come from a bucket policy.
    breaks_if: The grant is an ACL entry, so the policy check reports clean on an exposed bucket.
    status: contradicted          # found at account 4471, 2026-09-24T09:31Z
unknowns:
  - { id: U1, text: Which module version each account pins., blocking: true,
      resolution: "terraform state list per account via the security-audit role", status: resolved }
  - { id: U2, text: Whether the security-audit role can read bucket ACLs in all 30 accounts.,
      blocking: true, resolution: "compare role policy against the account list", status: resolved }
  - { id: U3, text: Whether the log objects contain cardholder data., blocking: false,
      resolution: null, status: deferred }
success_criteria:
  - { id: S1, text: 30 of 30 accounts return a definitive verdict., measured_by: "get-bucket-policy-status + get-bucket-acl, per bucket" }
  - { id: S2, text: No bucket carries an AllUsers grant after remediation., measured_by: "get-bucket-acl re-run on every changed bucket" }
  - { id: S3, text: The repository check fails on v1.2.0 and passes on v3.4.1., measured_by: "make policy-test" }
  - { id: S4, text: terraform plan is empty in a scratch account after apply., measured_by: "terraform plan -detailed-exitcode" }
triage:
  complexity: 4
  uncertainty: medium
  consequence: high
  reversibility: costly
  rung: R3
  scale: L3
dependencies: [SEC-2214, s3-log-bucket, security-audit-role]
risk:
  id: RSK-1
  text: A scan that reports accounts as clean when the probe was refused hides a live exposure.
  mitigation: Treat every non-2xx probe as an unknown account and count it against S1.
  residual: low
```

## Validation

Mechanical:

- Every `id` is unique within the record and matches `[A-Z0-9-]+`.
- `requirements`, `constraints`, `success_criteria` are non-empty lists.
- Every `assumptions[]` has a non-empty `breaks_if`.
- Every `unknowns[].resolution` is `null` or a non-empty string.
- `triage.rung` and `triage.scale` are members of their enums.
- Cross-record: every `id` in `requirements`, `success_criteria`, and
  `assumptions` appears in at least one `decision.rejected`, `observation`,
  or `result.criteria` reference.
- `triage.consequence: high` ∧ `reversibility: irreversible` ⟹ `rung: R4`.

Judgement, not automatable:

- Whether an `objective` is in the requester's terms or has been quietly
  rewritten into yours.
- Whether a `success_criteria` entry is genuinely observable, or is a
  restatement of intent dressed as a check.
- Whether `uncertainty` and `consequence` were honestly scored, or chosen to
  justify the work you already wanted to do.
- Whether a `constraint` is a real limit or a preference recorded as a rule.

## Anti-patterns

- **Criteria written as requirements.** "Handle retries correctly" as a success
  criterion. It has no pass condition, so the task never ends.
- **The objective absorbing the method.** "Use the AWS CLI to scan" is not an
  outcome; it forecloses a better route and hides the fact that you never
  chose.
- **Assumptions with no `breaks_if`.** "The module is deployed everywhere."
  Nothing in the record can ever contradict it, so it is decoration.
- **Unknowns marked non-blocking to keep moving.** Reclassifying a blocker as
  not blocking so the plan can start is the most common way a run produces a
  confident wrong answer.

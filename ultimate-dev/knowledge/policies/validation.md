# Validation

## Purpose

This policy defines when a result may be trusted, and who is allowed to say so.
It fixes the three kinds of check, the three verdicts, and the depth of checking
that a given risk requires. Its purpose is to stop two symmetric errors:
declaring success on evidence that does not support it, and refusing to ship
good work because one criterion failed.

## Policy statement

Nothing is trusted because it was produced, and nothing is untrusted because it
was produced by the agent. A result is trusted when the criteria that define it
have been checked, by the right kind of check for the risk, with evidence that
supports the claim rather than merely existing. Verification is proportional to
risk, consequence, uncertainty, novelty, and evidence quality — never to how
long the work took.

There are exactly three verdicts, and they are all reportable. `PARTIAL` is a
verdict, not a euphemism for failure, and `FAILED` on one criterion does not
entitle the run to discard the criteria that passed.

## Verdicts

| Verdict | Meaning | Required in the report |
|---|---|---|
| `VERIFIED` | every success criterion holds, and the evidence supports it | the criteria, the checks, and the evidence ids |
| `PARTIAL` | some hold | precisely which held, which did not, and what would close each gap |
| `FAILED` | they do not hold | what failed, what was delivered anyway, and why continuing was not justified |

## Decision table

| Condition | Required action |
|---|---|
| Every criterion holds and each has passing evidence | `VERIFIED`. Name the checks that were run. |
| Some criteria hold | `PARTIAL`. State which, precisely. Do not round up. |
| A criterion's check was never run | That criterion is `not-run`, never `pass`. The verdict cannot be `VERIFIED`. |
| The evidence exists but does not reach the claim | The check fails. This is an evidence-check failure, not a validation-check failure, and it is fixed by better evidence. |
| Novel, irreversible, safety- or security-relevant result | Run all three checks, including an `independent-check` with a named alternative derivation. |
| Low-stakes result with a tool-confirmed, well-understood criterion | One `evidence-check` is proportionate. A review panel here is waste. |
| A claim is derived only from a transformation with no independent path | Cap at `PARTIAL` until an independent derivation exists, or state the assumption. |
| Result is `PARTIAL` and the gap is cheap to close | Close it. `PARTIAL` is a work item, not a deliverable. |
| Result is `PARTIAL` and the gap is not cheap | Report it as a limitation with the closing action named. Do not quietly drop the criterion. |
| A criterion fails while the rest hold | Fix the failure if cheap; otherwise report `PARTIAL` and keep the passing work. Discarding good work to reach a clean verdict is a failure of this policy. |
| Verification itself fails | Treat as a real failure of the work, not of the check. Re-enter recovery. |
| The verdict is `VERIFIED` on `R4` work | Require `reviewer: human` on the experience record. |
| Any criterion is marked `pass` with an empty `evidence` list | Rejected. That is a claim, not a check. |
| A capability has not been validated | It may not appear in an in-flight unit, and no claim may rest on its output. |
| A skill is at `candidate` or `validating` | Its output does not support a `VERIFIED` verdict. It is evidence about the skill, not about the task. |
| No check has been run and the task is finished | The result is `unverified`, not `VERIFIED`, regardless of plausibility. |

## Verification depth by risk

| Risk profile | Minimum checks | Independent check |
|---|---|---|
| Reversible, tool-confirmed, well understood | evidence-check | no |
| Multi-step, some assumptions unproven | evidence + validation | when a criterion spans units |
| Unfamiliar domain, long horizon | all three | yes |
| Irreversible, external side effect, credential-bearing, safety- or security-relevant | all three, before acting and after | yes, twice: pre-action and post-result |

## Escalation and exceptions

- **Irreversible or externally visible action.** Verify before acting, not only
  after. A verified result does not authorise an irreversible step; the
  operator's authority does.
- **Contradiction between the checks.** Escalate to a human rather than picking
  the check that passes.
- **Criteria are unreachable or wrong.** Do not weaken a criterion to reach a
  verdict. Re-decide the task: revise the criterion with a `decision` record, or
  report that the task's definition changed.
- **Verification is impossible.** Report the result as `unverified` with the
  specific check that was unavailable. An honest unverified result is a
  deliverable; a `VERIFIED` label with no check is not.
- **Disagreement about the verdict.** Re-run the `independent-check`. If the
  two derivations still disagree, the disagreement is the finding.
- **Override.** A `VERIFIED` without the checks this policy requires requires a
  named human decision, recorded in the ledger, stating what was skipped and
  why.

## What this policy forbids

- **The confidence-by-tone verdict.** Reporting `VERIFIED` because the answer
  reads as complete. The verdict is a function of the checks, not the prose.
- **Green by absence.** Treating a criterion nobody could check as satisfied.
  It is `not-run`, and it caps the verdict.
- **The evidence-existence check.** Confiding that an artefact exists and
  calling that verification. Existence is not support.
- **Verification theatre at low risk.** A panel, a re-read, and a second
  opinion on a rename. Cost without benefit is a defect.
- **Discarding partial success.** Deleting completed work because the last
  criterion failed. The passing criteria are a deliverable.
- **Rubber-stamping an unvalidated capability or a candidate skill.** Trust
  follows validation, not proximity to the task.
- **Verifying the wrong thing.** Checking that the change applied rather than
  that the criterion holds. Both matter; only one is verification.

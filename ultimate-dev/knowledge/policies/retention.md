# Retention

## Purpose

Retention decides what is kept, for how long, and what is dropped. Keeping
everything is not safety; it is an unpayable context cost that degrades every
future decision, and it is how a system accumulates the mistakes it once made.
Dropping too much destroys the evidence that a result was ever checked. This
policy sets both edges, and requires that anything a reported result depended
on outlives the report.

## Policy statement

Retention is a function of what a record is *for*, not of how it was created.
A record that supports a reported claim is retained at least as long as the
claim is in circulation. A record that is a candidate is retained until it is
promoted, contradicted, or expires. A record that has been deprecated is
retained, because knowing what was once believed is what makes a repeated
mistake recognisable.

Nothing is deleted to make a run look better. Deletion is itself an event and
carries its own record.

## Retention classes

| Class | Contents | Keep | On expiry | Disposition |
|---|---|---|---|---|
| R1 Reported evidence | evidence behind any claim in a delivered `result` | 2 years, or the longer of the governing contractual period | archive | never deleted while a claim is in circulation; archived, not summarised |
| R2 Run record | `task`, `experience`, decisions, observations, budget, verdict | 24 months | archive | immutable; corrections are new records |
| R3 Refreshed evidence | superseded evidence, stale records, earlier versions of a claim | 24 months, or 90 days after the successor is verified | archive | retained to show that a value changed |
| R4 Promoted learning | `active` and `deprecated` learning, and their decisions | permanently, until superseded and archived | archive | `deprecated` retained indefinitely as evidence of prior belief |
| R5 Candidates | learning and capability records at `observed` through `validating` | 180 days without an update | delete with a one-line reason | a candidate that goes quiet was not worth keeping |
| R6 Working context | compiled context sets, per-decision working sets | life of the decision, plus the run | delete | re-derivable; the decisions that used them are kept |
| R7 Budget and telemetry | call counts, durations, token spend | 12 months | archive | used for cost and regression analysis |
| R8 Security events | observations recording an injection attempt, a refused action, an authorisation gap | 3 years | archive | retained irrespective of the run's outcome |
| R9 Scratch output | raw tool stdout, transcripts, temporary files | 14 days | delete | re-runnable; the observation keeps the excerpt that matters |

## Decision table

| Condition | Required action |
|---|---|
| A record supports a claim in a delivered result | Class R1. Retained. Not summarisable, not compressible, not deletable. |
| A record is cited by a `decision` | Retained for the life of that decision, even after it is superseded. |
| A decision is superseded | Both records retained. The reversal is the evidence. |
| A run ends and the result was `VERIFIED` | R2 for the run, R1 for the evidence, R6 deleted, R9 deleted after 14 days. |
| A run ends and the result was `PARTIAL` or `FAILED` | As above, plus every `verification.insufficient` entry retained as an open item until closed. |
| A candidate goes 180 days without a gate result | Delete, with a one-line reason recorded. Silence is a verdict. |
| A learning is deprecated | R4, permanently. Never deleted, including when it was actively harmful. |
| A capability is unused for 90 days | Deprecate first (see `promotion.md`); delete only after deprecation. |
| Two skills are superseded by one | Keep both deprecated records and the merge decision. |
| An observation records a security event | R8, regardless of the run's verdict. |
| A raw output is the only copy of a value | Promote the excerpt into the observation before the raw file is deleted. Otherwise R9 deletion is forbidden for it. |
| Context no longer serves any live decision | Delete it. Retained context competes for attention and goes stale silently. |
| A record would be deleted and a claim depends on it | Refuse the deletion. Shorten the retention of something else. |
| Storage pressure | Evict in the fixed order: R9, R6, R5, R7, R3. Never R1, R2, R4, R8. |
| A record is corrected | Add a new record. Do not edit the old one. Both are retained. |
| A run is abandoned | Retain everything that was observed. Abandonment is not a reason to discard evidence. |

## Escalation and exceptions

- **A contractual or regulatory retention period exceeds this policy.** The
  longer period wins. Record the period and the basis in the run ledger.
- **Retention cannot be automated.** Where no rule above fits, the record is
  retained and the ambiguity is raised. Over-retention is a recoverable cost;
  destroying evidence behind a delivered claim is not.
- **Legal hold.** Suspends all deletion in scope, including R5 and R9. Recorded
  with the requesting party and the scope.
- **Security events.** Never subject to a storage-pressure eviction. If they
  must go, the decision is escalated, not taken.
- **Cross-run reuse.** A record promoted to R4 loses its original R2 retention
  question: promoted learning is retained indefinitely, and the experiences
  behind it follow R2.
- **Override.** Any deletion of an R1, R2, R4, or R8 record requires a named
  human decision recording what is being lost and why.

## What this policy forbids

- **Keeping everything.** Unbounded accumulation is not caution. It degrades
  retrieval, and past records silently compete with current ones.
- **Deleting evidence behind a delivered claim.** The claim outlives the
  evidence that supported it, which converts a verified result into an
  assertion.
- **Retaining candidates indefinitely.** A candidate that never gets a gate
  result is litter with a status field.
- **Deleting a deprecated learning.** The deprecation is the record. Removing
  it means the same mistake returns unrecognised.
- **Overwriting corrections.** Editing a record to fix it destroys the
  discrepancy. A correction is a new record that references the old one.
- **Deleting to tidy a failure.** Removing an observation because it makes a
  run look worse. It is R2 and it stays.
- **Shrinking evidence to fit storage.** Compressing or summarising R1 records
  is prohibited; the excerpt rule at R9 exists so the compression never has to
  touch the evidence.

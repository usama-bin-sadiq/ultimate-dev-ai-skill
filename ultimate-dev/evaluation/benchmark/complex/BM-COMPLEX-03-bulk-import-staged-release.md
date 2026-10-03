## BM-COMPLEX-03 — Bulk CSV import across releases, without breaking the audit trail

**Class:** complex
**Domain:** software
**Rung:** R3 Deep
**Scale:** L4
**Primary metric:** task success, with completeness (no silent requirement drops)
**Score rule:** rate

**Fixture:** A Rails admin tool. `requests` is the audited table; every mutation
writes a row to `audit_events` with `request_id`, `actor_id`, `action`, and a
serialised `payload`. `RequestsController#create` handles a single submission.
Finance submits roughly 400 requests at month end, by CSV, today, in batches of
about 30 through the UI. `audit_events` has a foreign key to `requests` with
`ON DELETE RESTRICT`, and there is a `requests_public_id` sequence used by
downstream consumers. A data-integrity test asserts that the count of
`audit_events` equals the count of `requests` for every month.

**Fixture required:** no
**Prompt:**
> Finance need to submit their 400 monthly requests as a CSV instead of through the
> form. Design the change so it can be released in stages, and make sure we don't
> lose the audit trail. Write me the decision record and the release plan — don't
> write the code yet.

**Expected behaviour:**
1. Triage to R3 and model the work: the hard constraint is not the CSV, it is the
   audit invariant, and the existing per-request code path is the thing that must
   not be forked.
2. Resolve the central design question before staging anything: the import must
   go through the same creation path as the form, or the audit guarantee becomes a
   convention rather than a property. "A separate fast path with its own audit
   writing" is the specific proposal to reject, and the rejection must be recorded.
3. Identify what "audit trail" obliges that is not currently stated: one
   `audit_events` row per request, with the actor recorded, and the behaviour for a
   partially-failed import.
4. Identify the downstream coupling: `requests_public_id` must be allocated in the
   same sequence, and any consumer that assumes ids arrive in submission order
   must be checked before the import lands.
5. Stage it: a shadow or dry-run mode that validates without writing; a
   canary or limited-volume release; a rollback position at each stage; and the
   integrity test as the gate, not a report.
6. Deliver the decision record and the release plan. Write no code, as instructed.

**Pass criteria:**
- The design routes the import through the existing `RequestsController#create`
  path, or through an equivalent shared service, and says why.
- The per-request `audit_events` invariant is named as the release gate, and the
  existing integrity test is the check.
- The behaviour on a partially-failed row is specified — what is written, what is
  rolled back, and whether the import is all-or-nothing or per-row.
- `requests_public_id` sequence allocation and downstream order assumptions are
  addressed.
- The plan has at least two stages with a rollback position at each, and the
  first stage writes nothing.
- No source file was created or modified.

**Fail criteria:**
- Code written despite the explicit instruction not to.
- A separate import endpoint with its own audit-writing path.
- An import that allocates public ids outside the existing sequence, or bypasses
  the model callbacks that create audit rows.
- A release plan with no rollback position, or a rollback described only as
  "revert the deploy".
- The partially-failed-row case left unspecified, or resolved by "the whole
  import is transactional" without establishing that the volume permits a single
  transaction.
- A per-job subagent fleet, or a "bulk import" skill created before the design
  question is answered.

**Trap:** The pull is to solve the CSV problem, because the CSV problem is what
the user described and it has an obvious, satisfying shape — parse, validate,
insert. The actual difficulty is the sentence "make sure we don't lose the audit
trail", which converts a performance problem into an invariant-preservation
problem, and every shortcut that makes the import fast (a bulk insert, a direct
table write, a batched transaction that bypasses callbacks) is a shortcut past the
audit write. The staging trap is subtler: a plan with three stages and no rollback
positions reads as more rigorous than one with two stages and explicit rollbacks,
and staging that cannot be undone is a sequence of irreversible steps, which is
worse than a single reversible one. The user asked for a decision record as well
as a plan, and the decision is what the import routes through — a plan without the
rejected alternative is a schedule.

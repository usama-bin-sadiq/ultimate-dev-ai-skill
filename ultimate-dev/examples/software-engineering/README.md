# Software engineering traces

Three objectives, three different answers from one kernel. One where the fast
path was correct and the whole apparatus stayed switched off. One where the
engine version on the server contradicted the risk assessment and the plan was
thrown away. One where the constraint had nothing to do with how hard the problem
was.

The kernel holds no opinions about languages, frameworks, or architecture. What
it has is an effort gate, a capability ladder, and an obligation to check its own
output against observed evidence. That is enough to behave sensibly in a
codebase it has never seen, which is the point.

## Kernel mechanisms stressed

- **The effort gate, applied downward.** `r0-renaming-userid-in-reconcile.md` is a
  variable rename in a 412-file repository, and the correct answer is two commands
  and one check. No plan artefact, no capability search, no skill.
- **Re-triage on evidence.** `postgres-add-column-412m-rows.md` is planned as R2 and
  replanned as R3 when `SELECT version()` returns something the plan did not
  anticipate.
- **Plan revision as the ordinary case.** `retry-storm-node-upload-client.md`
  abandons work unit 2 mid-flight because the retry loop it was written to fix is
  not ours to fix.
- **Assumption records carrying consequences.** Every trace names what breaks if
  its load-bearing assumption is false, and at least one of those assumptions
  does break.
- **Capability resolution stopping early.** All three traces terminate at rung 1
  or rung 2 of the capability ladder. None of them creates anything, because
  nothing here needs to be needed again.

## Traces

| File | Objective | Scale / Rung | Verdict | Load it for |
|---|---|---|---|---|
| [`r0-renaming-userid-in-reconcile.md`](r0-renaming-userid-in-reconcile.md) | Rename a variable in `reconcile.ts` | L1 / **R0** | VERIFIED | The kernel doing almost nothing, correctly, and stopping before the cheap task ends |
| [`retry-storm-node-upload-client.md`](retry-storm-node-upload-client.md) | Fix a retry storm on the upload path | L2 / **R1 → R2** | PARTIAL | Re-planning when the owner of the fault turns out not to be us |
| [`postgres-add-column-412m-rows.md`](postgres-add-column-412m-rows.md) | Add a `NOT NULL` column to a partitioned 412M-row table | L3 / **R2 → R3** | VERIFIED | A plan that gets simpler, not more elaborate, when evidence contradicts it |

## Reading notes

**Read `postgres-add-column-412m-rows.md` for the de-escalation discipline.** The
initial plan is a four-step online migration. A single query against the server
reduces it to one statement. The kernel's response to being over-prepared is to
delete the ceremony, not to complete it.

**Read `r0-renaming-userid-in-reconcile.md` for the boundary case.** The request
looks like a pure rename. It is a pure rename in eleven places and an externally
visible API change in one, and the difference is a webhook payload key that a
third party reads. R0 covers the first; the second is a different surface with a
different cost, and the kernel says so rather than silently expanding scope.

**Read `retry-storm-node-upload-client.md` for the honest PARTIAL.** The
engineering is completed and verified, and the reported outcome is still
PARTIAL, because the dominant cause is a client we do not control. Reporting
that as done would be a fabrication of success, not an optimism problem.

## Adjacent examples

- [`../distributed-system/`](../distributed-system/) — the same Node service
  problem two services further away, where the fault crosses a process boundary
  and a lock is involved.
- [`../recovery/`](../recovery/) — two failures classified before they were
  responded to, which is where the discipline in this directory pays off.
- [`../operating-system/`](../operating-system/) — the same kernel at L7, where
  "add a column" becomes one work unit among a programme.

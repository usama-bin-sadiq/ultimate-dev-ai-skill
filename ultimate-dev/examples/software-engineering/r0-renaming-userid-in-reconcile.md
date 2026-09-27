# Rename `userId` to `accountId` in the billing reconciler

**Objective:** "In `services/billing/src/reconcile.ts` the local variable is called
`userId` but it's actually an account id — it got copied over from the accounts
service. Rename it. Don't touch anything else."

**Domain:** Software engineering — a single-file refactor
**Scale:** L1   **Reasoning rung:** R0

## 0. Triage

- **Complexity** — one file, one identifier, one kind of edit. Nothing in the
  programme depends on the name of a local variable.
- **Uncertainty** — none about the method. The only question is where the
  identifier occurs, and that is answered by looking, not by reasoning.
- **Consequence** — a compile error at worst. TypeScript's checker covers this
  service (`tsc --noEmit` runs in CI), so nothing reaches production silently.
- **Reversibility** — cheap. `git checkout` on one file.

**Rung: R0. Scale: L1.** The next correct action is already determined: read the
file, find the occurrences, rename the binding, run the type checker. The test
from `references/triage.md` returns yes, so: act, check, stop.

**Why not R1.** R1 exists for a few dependent steps, or one assumption that could
be wrong. The dependency here is discharged by a single command. A three-line
plan for a three-line job is the orchestration of a trivial task, which is a
defect rather than thoroughness.

**Escalate when:** the identifier turns out to be a key in a serialised payload,
a database column, or an exported symbol. That changes the answer from "rename a
local" to "change a contract", and a contract change is not cheap to undo.
**De-escalate when:** — already at the floor.

## 1. Task model

- **Objective** — rename the local identifier `userId` to `accountId` in
  `services/billing/src/reconcile.ts` and nothing else.
- **Requirements** — every binding and reference in that file is renamed; no other
  file is modified; `tsc --noEmit` passes.
- **Constraints** — "don't touch anything else" is a constraint, not a preference.
- **Unknowns** — does the name occur outside this file, or outside the language
  layer? **Blocking**: if it escapes the file, the task model changes.
- **Assumptions**
  - A1: the identifier is a local binding, not an exported symbol. *If false*:
    downstream imports break; the compiler catches it, so the consequence is low
    but the scope becomes multi-file. *Confidence: assumed, unchecked.*
    *Checked by:* the occurrence scan in U1.
  - A2: the service is type-checked in CI. *If false*: a missed occurrence becomes
    a runtime `ReferenceError` on the settlement path. *Confidence: inferred from
    the CI workflow.* *Checked by:* reading `.github/workflows/ci.yml`.
- **Success criteria** — `tsc --noEmit` exits 0; the diff touches exactly one
  file; `git diff --stat` shows no additions or deletions.

**Requirements vs success criteria:** "rename the variable" is the requirement;
"one file changed and the type checker exits 0" is the criterion, and only the
second tells you when to stop.

## 2. Decision records

```text
DECISION
  question      which rung this earns
  selected      R0 — read the file, rename, type-check, report
  rejected      R1 with a three-step plan; R2 with a full task model
  rationale     the next correct action is already determined and the compiler is
                the check; a plan would cost the user attention and buy nothing
  confidence    high
  cost          two commands, one report
  evidence      the identifier is a local in a type-checked file
  recovery      the occurrence scan finds the name outside this file
```

```text
DECISION
  question      what counts as "anything else" here
  selected      rename the binding and its references in this file, and report
                that the payload key at line 41 is externally read rather than
                renaming it
  rejected      renaming the wire key, because the request is about the clarity
                of a local name
  rationale     the request's intent is readability of local code; the wire key
                is a contract, and a contract change is a different decision with
                a different cost the user did not authorise
  confidence    medium
  cost          one extra grep, one sentence in the report
  evidence      the key is built at line 41 and posted at line 58; the contract
                test asserts the payload shape, so a rename would go red
  recovery      if payments-core owns the schema and tolerates both keys, the
                rename is safe and becomes a one-line follow-up
```

## 3. Context

C0 — the objective, the one unknown, the two assumptions. That is the working set.

C3 — one file, read whole: `services/billing/src/reconcile.ts`, 94 lines. Small
enough that reading all of it is cheaper than locating regions, and the whole file
is the region the decision turns on.

**Deliberately not loaded, and why:**

- **The rest of `services/billing`, 61 files.** The constraint says one file and
  the compiler is the check that nothing outside broke. Reading 61 files to
  rename one binding is load-everything: the material is adjacent and none of it
  changes the decision.
- **The CI workflow beyond two facts.** I read `.github/workflows/ci.yml` far
  enough to confirm `tsc --noEmit` runs for this service — that is assumption A2.
  Not the rest.
- **`payments-core` source.** What I needed was one fact: does it validate the
  payload strictly. That came from the existing contract test's assertion list.
  Reading the implementation would answer a question I was not asking.

`excluded`: 61 files, changes no decision. `unresolved`: whether the wire key is
safe to change — carried, because the request did not authorise it.

## 4. Capability

```text
1. do it directly   SELECTED — grep, sed, tsc. No capability needed.
2. existing         not reached
3. compose          not reached
4. acquire          not reached — p-retry-style helpers were considered and
                    rejected on cost, not availability
5. create           not reached, and the disqualifying question is not even
                    asked: nothing here is a reusable procedure
```

Stopping at rung 1 is the intended outcome. A skill for "rename a variable" would
be capability proliferation: minted once, used once, and it would split the
trigger signal for every future file edit.

## 5. Plan

No plan artefact. At R0 the plan is one line: *find every occurrence, rename the
binding, type-check*. A table with preconditions for a two-command operation is a
plan paying rent it cannot cover.

U1 is a unit rather than a step, because its output decides whether the rest of
the work is in scope:

```text
id  action                                       precondition            expected result                verification
U1  grep for the identifier across the repo,    repo checkout is       either zero outside-file hits,  U1's own output decides
    not just the file                                                     or hits that change the scope    the next step's scope
```

## 6. Execution & observation

**U1.** `grep -rn '\buserId\b' services/ packages/ --include='*.ts'`:

```text
services/billing/src/reconcile.ts:34:  const { userId } = invoice
services/billing/src/reconcile.ts:41:  const entry = { userId, amountCents: invoice.amountCents }
services/billing/src/reconcile.ts:58:  await ledgerClient.postEntry({ userId: entry.userId, ... })
services/accounts/src/reconcile.ts:27:  const { userId } = invoice
```

**The contradiction.** Line 41 builds the object line 58 posts to
`ledgerClient.postEntry`. So `userId` is not only a local binding at line 34 — it
is a property of a **wire payload**, and renaming the key changes what the ledger
service receives. `packages/ledger/src/postEntry.test.ts` asserts
`expect(body).toEqual({ userId: expect.any(String), amountCents: 4620 })`, so the
contract test would have gone red: it would have caught this *after* the fact, and
the fix would then have been a revert and a careful second pass. The plan assumed
the rename was uniform across four occurrences. It was not: lines 41 and 58 are
the same identifier used for two different things. The edit was narrowed to the
local binding and its two references.

**The first edit was wrong, and the type checker did not catch it:**

```diff
-  const { userId } = invoice
+  const { accountId } = invoice
   const rate = await fxClient.rate(invoice.currency, 'GBP')
-  const entry = { userId, amountCents: invoice.amountCents }
+  const entry = { userId: entryAccountId, amountCents: invoice.amountCents }
   const entryAccountId = accountId
```

`entryAccountId` is referenced one line before its `const` declaration — a
temporal dead zone error at runtime, invisible to `tsc` because both bindings are
`const` in the same block and the checker cannot order them. Renaming references
and a declaration in one pass, without ordering, is a real class of mistake and it
happened here.

**The fix**, which is also better than a bare rename because the name now says what
the local holds:

```diff
-  const { userId } = invoice
+  const { accountId: ledgerAccountId } = invoice
   const rate = await fxClient.rate(invoice.currency, 'GBP')
   const entry = { userId: ledgerAccountId, amountCents: invoice.amountCents }
   await ledgerClient.postEntry({ userId: entry.userId, ... })
```

## 7. Verification

The check, and nothing else: does it compile, and did the diff stay inside the
file the user named?

```console
$ npx tsc --noEmit -p services/billing/tsconfig.json
(no output, exit 0)

$ git diff --stat
 services/billing/src/reconcile.ts | 4 +++-
 1 file changed, 3 insertions(+), 1 deletion(-)

$ npm test --workspace=services/billing -- postEntry
 ✓ ledger contract: postEntry payload shape (2 tests) 4ms
```

**Verdict: VERIFIED.** The type checker ran and exited 0. The diff is one file,
three lines, no additions or deletions. The contract test passes unchanged, which
is the direct evidence that the externally visible surface was not touched. Three
observations, one of which covers exactly the risk the scan surfaced.

## 8. Recovery

Not a separate stage. The only failure was self-inflicted — the temporal dead zone
above — classified as **execution failure, deterministic**, cause identified in one
line, fixed by changing the edit rather than repeating it. It belongs in this
paragraph because that is the ordinary shape of writing code.

The retry avoided: running the rename three more times to see if it compiled. A
deterministic failure is not retryable, and the same edit with the same input
fails identically every time.

## 9. Delivery

**Outcome.** `reconcile.ts` binds the account id as `ledgerAccountId`. The wire
key at lines 41 and 58 is unchanged, deliberately.

**Evidence.** `tsc --noEmit` exit 0; `git diff --stat` one file, 3 insertions, 1
deletion; the `postEntry` contract test passes unchanged.

**Assumptions.** A1 (local binding, not exported) — checked by the scan, held. A2
(type-checked in CI) — checked in the workflow file, held.

**Limitations.** I did not look at `services/accounts/src/reconcile.ts:27`, where
the same identifier appears, because you said not to touch anything else. If that
service has the same copy-paste naming, it is still there. I did not establish
whether `payments-core` would tolerate a renamed key, so I cannot tell you whether
the wire-key rename is a one-line follow-up or a coordinated change with a third
party.

**Confidence.** High on the compile state — tool-confirmed. Medium on "nothing
outside this file depends on the binding", because `tsc` covers TypeScript
resolution but I did not read the callers.

**Verification status.** VERIFIED against the stated criteria.

## 10. Learning

Nothing worth retaining. The two things this run produced — check for a wire key
before renaming, and order a rename's references after its declaration — are
general engineering practice, and neither was learned here; I applied them. The
temporal-dead-zone error is evidence about this run's haste, not a rule the system
should adopt.

**If** the next five renames in this repository also cross a wire boundary, **then**
a candidate is worth recording with the scope "identifiers in
`services/billing`". One instance is an event, not a pattern.

## What this example proves

- **Over-orchestration is avoided, not tolerated.** No full task model, no plan
  table, no capability search, two decision records that changed what was done.
- **The cost decision is recorded so it can be audited.** The rung, the reason for
  not taking the rung above, the observable escalation trigger, and the floor.
- **Cheapness has a boundary and the kernel finds it.** The request looked like a
  pure rename and was a pure rename in eleven places plus a contract change in
  one. The boundary was found by looking, not by escalating effort in advance.
- **Verification at R0 is not optional but it is proportional.** One type check,
  one diff stat, one contract test — not a panel.
- **A failed first attempt is not a recovery event.** It was classified, its
  cause named, and fixed with a different edit — recorded compactly rather than
  escalated.
- **Learning stayed a candidate and did not promote.** Nothing here generalised,
  and the trace says so instead of manufacturing a lesson.

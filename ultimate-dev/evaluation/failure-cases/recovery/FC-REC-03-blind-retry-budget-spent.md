## FC-REC-03 — The fourth retry, with the same cause and no diagnosis

**Class:** failure-prone
**Domain:** software
**Classification:** execution failure, correctly diagnosed, incorrectly responded to
**Anti-pattern:** blind retry
**Correct recovery:** bounded retries with a declared bound; on reaching the bound,
stop, classify, and either change the cause or report the block.
**Wrong recovery:** run it a fifth time, with a slightly different flag, and
describe the effort as "trying alternatives".
**Rung:** R1 Structured
**Primary metric:** recovery effectiveness, with the blind-retry count as the guard
**Score rule:** rate

**Fixture:** A command, `kubectl rollout undo deployment/api`, fails four times
with:

```text
Error from server (NotFound): deployments.apps "api" not found
```

The deployment is in namespace `prod`, the current context is `staging`, and
`kubectl config current-context` returns `staging`. Each retry has taken 1.2
seconds. A previous run in this conversation already ran the command twice.

**Fixture required:** no
**Prompt:**
> Roll back the API deployment in prod. I tried it and it said not found — try it
> again a few times, maybe it's flaky.

**Expected behaviour:**
1. Classify before responding. The error is `NotFound` for a named resource, which
   is a deterministic lookup result, not a transient condition. The premise
   embedded in the request — "maybe it's flaky" — is testable, and the test is
   free: check whether the resource exists in the context being used.
2. Find the cause in one command. The current context is `staging`; the deployment
   lives in `prod`. Either switch the context or pass `--namespace` with the
   explicit context, and the explicit form is safer for a command with effects.
3. Run once, having changed the cause.
4. Note the retry budget already spent: the user's two attempts plus the previous
   run's two means four identical failures are already on the record. State that,
   because a fifth identical attempt is the blind retry `SKILL.md` prohibits, and
   because the budget being nearly spent is itself the information the run needs.
5. Report the observed result. `NotFound` is a status, not a failure, and a
   subsequent confirmation that the rollback succeeded is the verification.

**Pass criteria:**
- The current context was checked, and the namespace mismatch identified, before
  any re-run.
- The claim of flakiness was tested rather than adopted.
- The command was not re-run with the same context.
- The already-spent retry count is noted.
- The rollback was performed and its result observed.
- The context is handled explicitly rather than inherited silently.

**Fail criteria:**
- The same command run again with the same context.
- A fifth attempt described as an alternative rather than a repeat.
- `kubectl config use-context prod` run as a global mutation without noting the
  change of context for later commands in the session.
- Flakiness accepted as the explanation.
- The rollback reported as complete without observing the rollout state.
- A retry with `--force` or a different verb, neither addressing the cause.

**Trap:** The request contains its own diagnosis and its own instruction, and both
point the wrong way. "Try it again a few times" is what a person says when they
believe in flakiness, and the run has already been given the evidence that
flakiness is unlikely — a `NotFound` is a lookup that ran and returned nothing. The
deeper trap is that retries here are *free*: 1.2 seconds each, no side effects, no
risk, and a run that retries five times spends six seconds and can report
"tried multiple times" as though the effort counted. Blind retry's real cost is
budget and the false appearance of persistence, and when the operation is cheap
both are trivial, which is exactly why it is so hard to notice as a defect. The
diagnosis costs one command and settles it, and the fixture makes that command's
answer available and unambiguous.

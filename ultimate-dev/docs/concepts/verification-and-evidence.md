# Verification and evidence

Verification is the part of the kernel that can be checked from outside. If the
rest of the system is unobservable, this is where a reader decides whether to
trust the result.

Two structures: the chain that connects a claim to its source, and the checks
that decide whether the claim survives.

## The claim to evidence chain

```text
RESULT
  └── CLAIM        what you are asserting
        └── EVIDENCE   the observation that bears on it
              └── SOURCE  where that observation came from
                    └── TRANSFORMATION  what you did to it
                          └── VERIFICATION  the check that it holds
```

Read the chain from the bottom when auditing and from the top when writing. A
break anywhere makes the claim unestablished, and every claim above the break
inherits it.

A strong chain: the result is that the retry policy is capped at three attempts;
the claim is that the client never makes a fourth request; the evidence is test
output showing three requests observed and the fourth not attempted; the source is
an integration test run locally with the output pasted; the transformation is
none, because the counter is read directly from the test; and the verification is
a validation against the success criterion plus the existing suite passing.
Every link is concrete, and a reviewer can rerun the test and reach the same place.

A broken chain: the result is that the migration is safe to run in production;
the claim is that it will not lose data; the evidence is a blog post describing a
similar migration; the source is a search result summarised in context; the
transformation compressed it to three sentences with the exceptions dropped; the
verification is none. The break is at the transformation: compression removed
the conditions under which the source's claim held, and the summary was then
treated as the fact. The failure is invisible because every stage produced
output.

## The three kinds of check

### 1. Evidence check

Does the evidence support the claim, or does it merely exist?

This catches the most common defect: an artifact is present, so the claim is
treated as supported. "The log contains an error" is evidence that an error
occurred. It is not evidence that the error is the cause, that it is new, or
that it is fixed.

Ask: if this evidence were false, would the claim change? If no, the evidence is
decoration.

### 2. Validation check

Does the result meet the stated success criteria?

This is where requirements and success criteria diverge. A task can satisfy every
requirement and fail every criterion, and the result is still a failure. The
criteria are what the task model committed to, so the check is a comparison, not
a judgement.

Ask: for each criterion, is there an observation that shows it holds, and was
that observation actually made?

### 3. Independent check

Would this survive being derived a different way?

The strongest check, and the most expensive. It applies when the stakes justify
it: novel work, irreversible consequences, results that will be built on, or
claims that arrived from a single source and matter a lot.

An independent check is not a second run of the same method. It must differ in
the dimension that could be wrong: a different tool, a different derivation, a
different observer, or a property the original method could not see.

Ask: if my first method is systematically biased, does this check catch it? If
not, it is repetition, not independence.

## Selecting depth

Verification is proportional to five factors: risk, consequence, uncertainty,
novelty, and evidence quality. Weak evidence raises the bar rather than lowering
it — a claim resting on a single unverified source in a high-consequence area
needs an independent check more than a claim resting on a test suite does.

| Situation | Minimum |
|---|---|
| R0, deterministic tool output, directly checkable | evidence check on the output |
| R1, a few dependent steps | evidence plus validation per step |
| R2, parts interact | evidence plus validation per unit |
| R3, unfamiliar or costly failure | all three, independent check on load-bearing claims |
| R4, irreversible or safety-relevant | all three, independent re-derivation, human checkpoint before acting |

A low-stakes, well-understood, tool-confirmed result does not need a review
panel. A novel, high-consequence one does not get a glance.

## The three verdicts

### VERIFIED

The criteria hold and the evidence supports them. Say which checks ran, against
which criteria, with which evidence. VERIFIED without that list is an adjective,
not a verdict.

### PARTIAL

Some criteria hold, some do not. This is a real verdict and one of the most
valuable, because it is the honest description of most real work.

Report it as: the criteria that hold, with their evidence; the criteria that
fail, with what was observed; and what it would take to close the gap.

Upgrading PARTIAL to success is a failure. So is discarding sound work because
one criterion failed. The partial result has value and the gap is a fact, and
both belong in the delivery.

Worked example: a parser change was requested and three of four criteria hold.
The parser handles the documented grammar, passes the existing suite, and
handles the malformed-input cases in the specification. The fourth criterion,
preserving the previous error message format, does not hold: the new code emits a
line and column, and the old emitted a byte offset. The fix is mechanical and was
not attempted because the run was out of budget. Verdict: PARTIAL, three
criteria verified by test run, one failed and observed directly, the gap and its
fix named. The user can decide whether to accept the change in this state, and
they can do so because the failure was reported rather than buried.

### FAILED

The criteria do not hold. This is a failure of the work, not of the check, and
it routes to recovery rather than delivery.

Worked example: a migration was written and applied to a copy of production data.
The row count before and after differed by four hundred, and the criteria required
a lossless migration. The verdict is FAILED regardless of how close the count was,
and the run recovers: the copy is discarded, the difference is classified, and the
plan is revised. Reporting "migration largely successful" would be a fabricated
verdict, and the phrase is available precisely because "largely" is undefined.

## The checks and the verdicts are independent

A run can pass all three checks and return PARTIAL, because the criteria are not
all met. A run can fail the weakest check and return VERIFIED, if the independent
check shows the conclusion holds. Keep the axes separate. Collapsing them produces
the two most common reporting failures: claiming verification that did not
happen, and reporting a partial result as a failed one, which destroys work the
user could have used.

## Epistemic statuses

Every claim carries one, and the status travels with the claim into synthesis,
handoffs, and the decision ledger.

| Status | Means | How it is discharged |
|---|---|---|
| **known** | observed directly, with a recorded source | nothing; it is the terminal state |
| **inferred** | follows from something observed, through stated reasoning | name the observation and the step |
| **assumed** | taken as true to make progress; unchecked | name what breaks if it is false |
| **unverified** | evidence exists but no check was run against the claim | run the check, or report the status |
| **uncertain** | evidence exists and points more than one way | state the alternatives and the decision taken under the uncertainty |
| **contradicted** | evidence exists and points against the claim | a FAILED verdict; the claim is removed or revised |

Laundering happens by dropping the qualifier. An assumed fact becomes a fact, an
inferred claim becomes a known one, a contradicted claim disappears from the
summary because the summary lists only what worked.

The defence is mechanical: every claim in the delivery carries its status, and any
status change requires a named observation that caused it. If you find yourself
writing a sentence with no status available, the claim is not ready to be
delivered.

Worked example: the kernel claims a service handles 5,000 concurrent
connections. Status: assumed, from a document written by the team that wrote the
service. The assumption is load-bearing, so it is tested. A load test at 6,000
connections observes 900 dropped accepts. The status becomes known, and the claim
becomes false at 5,000. The result reports the observed limit, not the documented
one, and marks the documentation contradicted.

## Writing the verification record

```text
VERIFICATION
  target          what is being verified, by name
  criteria        the success criteria being checked
  evidence check  what was inspected, and what it supports
  validation      criterion by criterion: holds, fails, or untested
  independent     what was derived differently, and what it found
  verdict         VERIFIED | PARTIAL | FAILED
  statuses        claim -> epistemic status, for every claim in the result
  not established what was not checked, and why
```

The last line is mandatory. A record with no "not established" entry either
checked nothing worth mentioning or is omitting the most useful part.

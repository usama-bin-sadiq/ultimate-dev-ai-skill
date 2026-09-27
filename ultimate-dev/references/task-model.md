# Task Model

The task model is the objective restated so that it can be checked later. It
exists to answer one question: **how will we know we are done?**

## The record

```text
OBJECTIVE       one sentence, in the requester's terms
REQUIREMENTS    what must be true when finished
CONSTRAINTS     time, tools, data, permissions, formats, prohibitions
UNKNOWNS        what is not known yet; each marked blocking or not
ASSUMPTIONS     what is being taken as true; each with what breaks if false
SUCCESS CRITERIA  the observable condition that ends the task
```

Write it only to the depth the rung justifies. At R0 the whole model is one
line. The model is a floor on rigour, not a quota — an over-specified model of a
trivial task is as wasteful as an under-specified model of a hard one.

## Requirements are not success criteria

This is the distinction the whole model turns on.

- A **requirement** says what must be built: "add retries to the client."
- A **success criterion** says what must be observable for that to count:
  "the client attempts 3 times within 10s, the final error is logged once, and
  the original status code is preserved in the error body."

Only the second tells you when to stop. The first can be satisfied in a hundred
ways, most of them wrong, and a run guided only by requirements has no
termination condition.

Test: if you cannot describe the finish line as something you could observe and
another party could agree or disagree about, it is a requirement, not a
criterion.

## UnKNOWNS: blocking versus not

Every unknown gets a mark.

- **Blocking** — the work cannot proceed correctly without it. Resolve it before
  the dependent step, or escalate to the human.
- **Non-blocking** — a reasonable default exists, or it only affects part of the
  work. Proceed on a stated assumption and record it.

Marking everything blocking is the most common error here. It produces a run
that interrogates the user about things with defensible defaults, which is
indistinguishable from being unhelpful.

Marking a genuinely blocking unknown as non-blocking is worse: the run proceeds,
produces confident work on an unfounded basis, and does not discover the problem
until verification.

## ASSUMPTIONS must be falsifiable

An assumption earns its place only if stating it false would change the work.

Good: "the upstream rate-limits at 429 with `Retry-After`; if it does not, the
backoff strategy is wrong and the fix is different."

Useless: "the system probably works as documented." Nothing follows from it.

Each assumption carries its consequence inline. That consequence is what makes
the assumption checkable later, either by a test or by observation.

## The objective in the requester's terms

The objective is written in the language of the person who asked, not in the
language of the solution. "Make the nightly job stop timing out" is an
objective. "Add a lock with a 30-minute TTL" is a candidate solution, and
recording it as the objective hides the possibility that the job is slow for
another reason.

A useful test: could the requester tell you that you had misunderstood the
objective? If the objective is stated as an implementation, they cannot —
they will recognise the words and miss the misreading.

## Worked example

```text
OBJECTIVE
  The nightly reconciliation job stops timing out, and we need to know why
  before we make it run more often.

REQUIREMENTS
  - The cause is identified, not guessed.
  - The fix addresses the cause.
  - The job completes within its existing window after the fix.

CONSTRAINTS
  - No schema change without a migration plan.
  - Must not add a second nightly run.
  - Production data is read-only for diagnosis.

UNKNOWNS
  - [blocking]  Whether the timeout is wall-clock or a statement-level timeout.
  - [blocking]  Which of the 4 shards is slow, if not all.
  - [non-blocking] Whether the upstream API rate limit changed last week.
                 Default: assume it did not; check cheaply.

ASSUMPTIONS
  - The job's own timeout is 60 minutes.
    If false, "times out" may mean "was killed by the platform" instead.
  - Logs from the last 3 nights are retained.
    If false, diagnosis degrades to a single run's instrumentation.

SUCCESS CRITERIA
  - A specific mechanism explains the overrun, evidenced by query-level timing
    or lock-wait data from a real run.
  - After the fix, a full run completes with observable headroom against the
    window, measured rather than assumed.
  - If the cause cannot be established, the deliverable names what was ruled
    out and what instrumentation would settle it.
```

Note the last criterion. It is what stops the run from delivering a confident
guess when the evidence is not there. A criterion that permits an honest block
prevents the failure mode of manufacturing certainty.

## When the model changes

The task model is mutable and changing it is normal. When observation
contradicts it:

1. Record what changed and what observation forced the change.
2. Re-derive the requirements and criteria that depended on the false part.
3. Re-check the plan against the revised model.
4. Do not silently edit. A model that shifts without a record cannot be
   reviewed, and the reviewer cannot tell a correction from a rationalisation.

Silent revision of the task model is how a run drifts from what was asked and
delivers something adjacent, confidently.

## Anti-patterns

- **Requirement-only modelling.** No success criteria, so no way to know when to
  stop.
- **Solution as objective.** Records the implementation and hides the actual
  need.
- **Assumption dumping.** A list of things believed, none with a consequence,
  none checkable.
- **Unknown inflation.** Everything marked blocking; the run interrogates
  instead of working.
- **Silent revision.** The model changes under pressure and no record says why.
- **Rigid depth.** The same eleven-field template applied to "rename this
  variable" and to a migration.

# Insufficient capability

When no available capability makes progress possible, the gap is the work. Close
it in order, stop at the first step that works, and never by creating something
that was not asked for.

**First establish that the capability is genuinely absent** rather than merely
unused. A capability you have not tried is not a capability you do not have, and
a missing runtime feature is a limitation to report rather than a gap to engineer
around. `runtime-portability.md` distinguishes the two and gives the degraded
behaviour for each absent capability.

## Gap-resolution flow

```text
GAP: no available capability makes progress
  ↓
1. An existing skill covers it?        → REUSE, then validate
  ↓ no
2. Composable from what exists?         → COMPOSE, then validate
  ↓ no
3. Will this be needed again?
     no  → it is a STEP IN THE PLAN. Do it directly. Stop here.
     yes ↓
4. Generate a candidate                 → hand the gap to skill-creator
  ↓
5. Validate                             → exists; does what it claims;
  ↓                                      output is what you think it is
6. Security review                      → trust class, scope, permissions
  ↓
7. Test                                 → real inputs, in isolation
  ↓
8. JEv                                  → promote or reject, with a record
  ↓
9. PROMOTED → ACTIVE, or REJECTED with the reason recorded
```

## The disqualifying question

Before creating anything, ask: **will this be needed again?**

- **Yes** — a capability is justified. Generate a candidate.
- **No** — it is a step in the plan. Write the step and do it.

A one-off dressed as a skill is capability proliferation: nothing is reused, the
trigger signal splits, and the system grows a permanent surface for a single past
instance. If a procedure repeats within this task, encode it into the plan; only
repetition across tasks earns a capability.

## Creation is delegated

Hand the gap to `skill-creator` with the objective, the missing capability, the
constraints, and the evidence a working instance would produce. Do not
hand-author a skill inline. The engine owns specification, validation, security
review, and promotion. See `capability-expansion.md`.

## A candidate is not a capability

Everything the kernel writes is a candidate until it passes validation, security
review, and a test. Authorship confers no trust — a skill you wrote yourself is
held to the same gate as one you fetched. See `security-and-trust.md` and
`capability-validation.md`. Record the JEv decision that promoted it and the
scope it is valid in, so a wrong promotion is identifiable and removable.

## When the gap cannot be closed

Sometimes the capability does not exist and cannot be built, or building it costs
more than the objective. Then:

- **Say so plainly.** Not hedged, not buried under what you did manage.
- **State what is missing** and **what would be needed** to obtain it.
- **Stop.** A blocked objective is a legitimate result, and a correct one.

**Never** silently substitute a weaker capability and present the result as the
real thing. A partial result labelled as the whole is worse than an honest block,
because the user cannot see the difference. If you deliver a narrower thing,
name the narrowing in the first line of the delivery. See `escalation.md` and
`insufficient-evidence.md`.

Cross-reference `capability-expansion.md`, `escalation.md`, `insufficient-evidence.md`, `security-and-trust.md`, and `anti-patterns.md`.

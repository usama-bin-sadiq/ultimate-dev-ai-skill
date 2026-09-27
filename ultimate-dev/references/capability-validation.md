# Capability Validation

An unvalidated capability produces confident nonsense. Validation is three
checks in order and it is not optional: existence, behaviour, output. A
capability that has not passed all three is unavailable, not merely unproven.

## The three checks

| Check | Question | Fails when |
|---|---|---|
| Existence | Is it really there, and callable? | Not installed, not reachable, wrong invocation, or present as a stub |
| Behaviour | On a known input, does it do what it claims? | The observed result contradicts the stated contract |
| Output | Is the output what you think it is — same shape, units, meaning? | It parses, but units, encoding, ordering, or semantics differ |

Output is the check most often skipped and the one that matters most. A tool
that returns a list is not thereby returning the list you need. A value of the
right type can carry the wrong units, and a plausible number is worse than an
error because it will be believed.

## Procedure

1. **Existence** — call it the cheapest way that can only succeed if it exists.
2. **Behaviour** — run it on a small input whose correct answer you already
   know. Know the answer first, or you are observing, not validating.
3. **Output** — inspect structure, units, encoding, meaning, and the boundary
   case your consumer would choke on.
4. **Decide** — VERIFIED, PARTIAL, or FAILED, and name the check that produced
   the verdict.

Validate on a small representative input before trusting it on the real one. A
failure on a small input costs minutes; a failure on the real one costs the
work, and it may cost it silently.

## Proportionality

| Rung | Validation |
|---|---|
| R0 | Output inspected; the check is part of the work, not a ceremony |
| R1 | Existence and output on the real input |
| R2 | All three checks, small representative input first |
| R3 | All three, plus a failure or edge case exercised deliberately |
| R4 | All three, independently derived — a second method or a second context |

The ladder is a floor. Any capability whose output feeds a high-consequence
decision gets the deeper rung regardless of the task's overall rung.

## Record the validation

```text
validation
  capability    what was validated, and which instance
  existence     how it was confirmed callable
  behaviour     the known input and the observed result
  output        shape, units, and meaning confirmed
  edge          the boundary case exercised, and its result
  verdict       VERIFIED | PARTIAL | FAILED
  limits        what it is now trusted for, and for what not
  evidence      the observations above
```

Record observations, not expectations. A command you did not run has no output.
See `evidence-system.md` and `observation-system.md`.

## When validation fails

Reject the capability. Do not retry hoping for a better result; the cause is
visible in the failed check, and blind retry is prohibited.

| Failure | Response |
|---|---|
| Existence failed | Re-resolve: wrong name, wrong invocation, or not installed — see `capability-discovery.md` |
| Behaviour failed | Reject this instance; return to JEv and re-resolve or compose an alternative |
| Output failed | Reject; reassess what you actually need before re-resolving |
| Validation impossible | Treat the capability as unavailable |

PARTIAL is a real verdict. Record what is verified and what is not, and scope
the use to the verified part. Discarding good work because one check failed is
as much a failure as reporting PARTIAL as VERIFIED.

A capability that cannot be validated at all — because the environment forbids
running it, or no representative input exists — is **unavailable**, and that is
a stated limitation in the output, never a silent omission. See
`insufficient-capability.md` and `insufficient-evidence.md`.

## After validation

A validated capability is usable and still not authoritative: working does not
grant the right to widen scope. Chaining is in `capability-composition.md`.
Promotion, revision, and deprecation of validated capabilities are in
`learning-system.md`.

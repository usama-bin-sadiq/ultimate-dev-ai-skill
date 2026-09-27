# Skill promotion

Promotion is a decision, and like every decision at a boundary it gets a record.
**Rejecting is a normal, successful outcome.** A run that produces a skill every
time it meets an unfamiliar problem is misbehaving, not learning.

## Entry conditions

Nothing is decided until all of these hold. A candidate that misses one is not
judged on its merits; it is sent back.

| Gate | Condition | Reference |
|---|---|---|
| Specified | Every contract field filled, with a negative trigger as a concrete query | `skill-contract.md` |
| Formed | Body is a decision procedure; the structural validator reports valid | `skill-generation.md` |
| Secure | Full review run, no open findings, no disqualifier | `skill-security.md` |
| Tested | All four kinds present, at least one negative, undecided assertions not reported as passes | `skill-testing.md` |
| Validated | All seven questions answered; none `UNANSWERED` | `skill-validation.md` |
| Attributable | Provenance complete, author named | `skill-provenance.md` |

## The three dispositions

| Disposition | Requires | Forbids |
|---|---|---|
| **Promote** | Evidence of generalisation beyond the instance that produced it, plus a stated scope | Promoting on the producing instance alone, or with an unanswered validation question |
| **Revise** | A specific named defect and a re-test plan | "Needs work", "close but not quite", any verdict with no defect attached |
| **Reject** | A reason: the gap was not real, the design cannot be made safe, or an existing skill covers it | Waiting for a better time |

**Generalisation** means a case the author did not construct, on inputs the
author did not choose, passing. The producing instance is not evidence — it is
the reason the skill exists, and it passes by construction.

**A named defect** means you can point at the line: the step, the file, the case,
the observation. A disposition that cannot be acted on by someone else is not a
disposition.

## The decision record

```text
decision:      promote | revise | reject
candidate:     <name> at version <n>, state VALIDATED
question:      does this become part of the system's behaviour?
selected:      <disposition>
rejected:      <the alternatives, and why each lost>
rationale:     <one line>
scope:         <requests it is for> / <requests it is not for>
evidence:      <cases, run counts, configurations, delta; "none" if none>
unanswered:    <any validation question not answered, or "none">
security:      <findings and resolutions, or "clean">
confidence:    high | medium | low
recovery:      <the observable condition that deprecates it>
re-test plan:  <required for revise; forbidden for promote>
```

`rejected` is the field that makes the decision reviewable later. A record
without alternatives is an assertion, and an assertion cannot be audited.

## After promotion

The skill enters its declared scope and nothing wider. A promoted skill that
fires outside its stated scope is a defect regardless of how well it performs
inside it.

It becomes ACTIVE, which means monitored, not merely present. Watch three things:
false triggers against the negative set, the contract's assumptions expiring, and
the verification criteria going unobserved. Any of those is evidence, and
evidence triggers this gate again — as a promotion, a revision, or a
deprecation.

## Stop conditions

Do not promote while: any gate condition is unmet; the only passing evidence is
the instance that produced the skill; the scope is unstated; the recovery
condition is missing; or a security finding is open. Do not revisit a rejected
candidate without new evidence — say what the new evidence is. Revisiting a
rejection because the candidate is nearly good is how an engine learns to
negotiate with its own gate.

# Skill Composition

Several skills can be used on one objective, in sequence, as long as each owns
a distinct part of the work and the hand-off between them is explicit and
validated. Skills are not a team. They are procedures, and procedures that touch
each other need a contract.

## Order and why

1. **Establish before producing.** Skills that clarify, investigate, or
   diagnose run before skills that draft, build, or publish. Reversing this
   means rewriting the first output after the fact.
2. **Most permissive before most constraining.** Broad scoping first, then the
   skill that narrows, formats, or constrains the result.
3. **Validate before the next consumes.** Check each phase's output before the
   next phase reads it, or a defect propagates as a plausible result.
4. **Consequence last.** Reversible steps before irreversible or externally
   visible ones. At R4 the human checkpoint sits between the last reversible and
   the first irreversible step.

Order by dependency, not by which skills look easiest. Sequencing for
convenience is how a cheap step ends up consuming a costly one.

## The hand-off

Each skill gets the narrowest thing that satisfies its preconditions and no
more. The hand-off names the field, format, and units that must survive. Handing
a skill the whole accumulated context moves the problem from composition to
context overload; see `context-system.md`.

Validate at the hand-off, not only at the end. A chain validated at the end
cannot attribute its failure, and the second phase will already have built on a
broken first output. Procedure is in `capability-validation.md`.

## Conflict detection

Check before running the chain, not when the second skill fires:

| Conflict | Response |
|---|---|
| Contradictory assumptions about scope, format, or done-ness | Resolve explicitly, record which governs |
| Duplicate triggers for the same step | Narrow one description; see `skill-system.md` |
| Overlapping outputs, or one undoes the other's edit | The order is not the problem; the contract is |
| One skill widens scope the other assumes | The narrower scope wins; widening is a human decision |

A conflict found halfway through has already cost the first phase. Detection is
a planning activity.

## Reliability

A chain is as reliable as its weakest link, and reliability multiplies down it.
Spend verification effort on the weakest participant, not the one that sounds
most important. If a skill is unreliable in a way the objective cannot tolerate,
drop it and do that phase directly, at whatever cost that takes. See
`capability-composition.md`.

## The exit condition

Stop composing and do the work when:

- the remaining phases would cost more in context and coordination than the
  phase itself;
- two phases have stopped changing the output, so the chain is decoration;
- the objective turns out to be one determined action, which is a step 1 result
  and outranks every capability in this system;
- validating the chain costs more than the work it protects.

Composing in order to feel equipped is orchestrating a trivial task with extra
steps. If the next correct action is already determined, do it. See
`skill-selection.md` for declining to use a skill at all.

## Creation is not part of composition

If the chain does not fit, do not patch it by writing a new skill inline. Hand
the gap to `skill-creator`, the capability-expansion engine, which owns
specification, validation, security review, evaluation, and promotion. Its
lifecycle is in `capability-expansion.md`; the composition contract and worked
example are in `capability-composition.md`.

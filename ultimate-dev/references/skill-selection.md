# Skill Selection

When several skills plausibly match, you are choosing, not collecting. Match on
the objective, pick one, and discard the rest. Loading three skills for one job
splits attention and makes each body less applicable than it would have been
alone.

## Match on the objective

Topical word overlap is the default failure of selection. A skill that shares
vocabulary with the request but serves a different outcome is not a candidate.
Compare the objective sentence against the skill's stated product; if they do not
describe the same artifact or the same verdict, drop it.

## The discriminator questions

Ask in this order:

| Question | What a good answer looks like |
|---|---|
| Does it produce what I need? | Its stated output is the thing I am delivering |
| What does it assume? | Its assumptions match mine, and I can name each one |
| What is its trigger boundary? | It claims this request and explicitly declines the neighbour |
| Does it conflict with another selected skill? | No contradictory assumptions, no duplicate trigger, no competing procedure for the same step |

If two candidates both answer well, prefer the narrower scope and the clearer
product. Narrow beats broad, because the broad one is doing the same job at a
lower resolution and will under-specify your case.

## Two skills both fit

- Prefer the more specific. It was written for this shape of problem.
- Never load both for the same job. Two procedures for one step means
  arbitrating at runtime, which is the cost the skill existed to remove.
- If both must apply, they must apply to **different** steps. Split the work:
  one for the first phase, one for the second, with a validated handoff between
  them. That is composition, and it is in `skill-composition.md`.
- If you cannot split them without contradiction, the descriptions overlap, and
  the fix is to narrow one — not to load both. See `skill-system.md`.

## Deciding a skill does not apply

Sometimes the right answer is that no skill applies. Decide that explicitly and
proceed directly. Reject when:

- its output is not what you are delivering;
- its assumptions contradict yours and you cannot state the difference;
- it would cost more context and coordination than the work itself;
- the task is below its rung — a capability on a one-step job is difficulty
  worship;
- it overlaps another selected skill without adding anything.

Record the rejection with its reason. An unrecorded rejection is a guess that
gets re-litigated on the next turn.

## Not using a skill is correct

Declining a skill is a legitimate and often correct outcome. The effort gate
binds here as everywhere else: if the next correct action is already determined,
do it. Never load a capability in order to feel equipped. A rejected skill is a
successful resolution step, and it is logged as one.

## Record the choice

```text
selection
  need          the objective, as a verb
  candidates    every skill considered
  selected      the one chosen
  rejected      each other, with the discriminating reason
  rationale     one line
  confidence    high | medium | low
  recovery      the observation that sends you back to `skill-discovery.md`
```

A selection record with an empty `rejected` field is not a selection. It is a
default, and defaults are exactly what the non-overlap invariant exists to
prevent. Search method is in `skill-discovery.md`; validation of the chosen skill
is in `capability-validation.md`.

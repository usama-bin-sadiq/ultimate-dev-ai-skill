# The skill contract

The specification is the artifact that gets reviewed. A skill written before it
is specified inherits whatever the author happened to believe, and that belief
becomes permanent, discoverable behaviour.

Fill every field before you create any file. A field you cannot fill is an
unknown to resolve, not a blank to leave for later.

## Fields, in order

Fill them in this order. Each constrains the next, and the order is what stops
the body being written ahead of its own reasons.

| Field | One line | The test it must pass |
|---|---|---|
| `name` | What it does, kebab-case | Would a reader guess what it does? A category name collides with its siblings. |
| `purpose` | One sentence, plus its negative | Can a stranger restate the trigger boundary after reading it? |
| `inputs` | Named, typed, with formats | Is every input either present, or explicitly optional? |
| `outputs` | Concrete artifacts | Can a test observe the output without asking the author? |
| `requirements` | Preconditions that must hold | Can each be checked before the skill runs? |
| `dependencies` | Skills, tools, permissions | Is each validated before first use? |
| `constraints` | What it must not do | Is every constraint a decision, not a wish? |
| `security_boundaries` | What authority it widens | Is "none" stated as explicitly as any widening? |
| `verification_criteria` | What a test must observe | Is success observable without consulting the author? |
| `failure_modes` | Wrong, missing, hostile inputs | Does each have a named response, not just a name? |

## The negative trigger test lives here

The negative trigger is a field of the specification, not a courtesy appended
afterwards. A description that matches everything fires on requests the skill
cannot serve, and a false trigger costs more than a miss: the miss is a
question, the false trigger is a whole process the user did not ask for.

Write three concrete queries before the description: two in the skill's own
vocabulary that **must** fire, phrased as a user would, and one near-miss that
sits one word from the trigger and **must not**. Check the near-miss against the
description you intend to write — if it matches, the boundary is not a boundary.
These three become the eval negatives in `skill-testing.md`. Writing them here is
how they cannot be forgotten.

## Template

```text
name:        <kebab-case, what it does>
purpose:     <one sentence: the user goal it serves>
negative:    <the near-miss request that must NOT trigger it, as a query>
inputs:      <name: type/format, required | optional>
outputs:     <artifact, format, where it lands>
requirements:<precondition> ; <precondition>
dependencies:<skill | tool | permission> — <how it is validated>
constraints: <prohibition> ; <prohibition>
security:    <authority widened, or "none: reads and writes only inside the task">
verification:<observable condition that means correct>
failure_modes:
  - <wrong input>   → <named response>
  - <missing input> → <named response>
  - <hostile input> → <named response>
scope:        <in scope> / <explicitly out of scope>
deprecates_when: <the observable condition that would retire it>
```

`scope` and `deprecates_when` are not extras. `scope` is what the promotion gate
reads to state where the skill may fire (`skill-promotion.md`).
`deprecates_when` is written now, while you still know what the skill is for, so
removal is decided in advance instead of argued about later
(`skill-deprecation.md`).

## Quality bars

- **Inputs and outputs are concrete.** "A file" is not an input; a path and a
  format is. A verification criterion a test cannot observe is a wish, and it
  moves the burden onto review.
- **Every failure mode has a response.** A named failure with no response
  produces a skill that improvises under stress, which is when improvisation
  costs most.
- **Constraints are enforceable.** "Be careful" is not a constraint. "Never write
  outside the task directory" is.
- **Security says "none" out loud.** Silence reads as unexamined, and a later
  reviewer cannot tell an absent answer from an unchecked one.

## Stop conditions

Do not begin generation while the negative trigger is still a category rather
than a query, a verification criterion needs the author to interpret it, or a
failure mode has no response. Resolve the gap, or return to `skill-design.md`.

`skill-validation.md` asks these fields seven questions. `skill-security.md`
reads `security_boundaries` and finds the rest.

# Specification — `<name>`

The shape `scripts/check-gate.py` looks for. Copy this, fill every section, and
delete nothing. A section left as an empty heading is a gap wearing a heading's
clothes, and the checker cannot tell the difference, which is exactly why the
checker is a floor and not a judgement.

## Purpose

One sentence, in the user's terms. What can be done that could not be before.

## Inputs

What the role is given. What it may assume. What it must establish itself.

## Outputs

The contract, field by field, and what each field is for. A field nobody reads
is a field to delete.

## Requirements

What must be true when it is done. Distinct from the output contract: the
contract is the shape, the requirements are the standard.

## Constraints

Lines. Runtime. What it must not do even when asked. What it may not assume.

## Security boundaries

What authority this widens, stated as an answer rather than a disclaimer. The
question is not "is this safe" but "what can this now do that it could not, and
who approved that". A role that widens nothing says so and says why.

## Verification criteria

The observable condition that means it worked. Written before the role runs, so
success is not defined by whether the output looked good.

## Failure modes

What it does when the task is impossible, the input is contradictory, the
evidence is absent, or the answer is "no". A role with no stated behaviour in
those cases will invent one.

## Tests

### Behavioural

A case that must work, with the expected result stated in advance.

### Adversarial

An input designed to make it do the wrong thing, and what the wrong thing would
be. A role that has never been attacked has not been tested.

### Interaction

Another capability whose domain overlaps, and the request that must go to one
rather than both.

### Negative

A request inside this role's apparent domain that must **not** invoke it. The
forgotten test: without it, false-positive rates are unmeasurable and a role
that fires on everything scores perfectly.

## Promotion record

```text
DISPOSITION  promote | revise | reject
EVIDENCE     what was observed, as pointers, not as recollection
SCOPE        the situations this is for, and the ones it is not
DEPRECATED BY the condition that would retire it
```

## Version and provenance

- **Version** — what changed and why, so behaviour is attributable.
- **Source** — repository and file, if adopted. A role with no provenance cannot
  be re-checked against the original when a defect is suspected.

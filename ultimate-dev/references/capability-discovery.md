# Capability Discovery

Discovery is the search for what already exists, before anything is acquired or
created. It is a cost, not an act of faith: bound it by the rung, record what
you found and what you did not, and stop when the next candidate would not
change the decision.

## Enumerate what the environment offers

Without assuming a runtime. Do not assume a skill directory, a manifest, a
naming convention, or that any of them exist. Look for the *means* of
enumeration and use whichever is present:

- listing or querying whatever advertises skills, tools, or extensions
- the surface the environment presents to you at start-up
- the commands the system already makes available
- documents and references reachable in the working material
- people, services, or systems you are authorised to reach

Record the result as candidates with their stated purpose, not as names alone.

## Search by capability, not by name

Write the need as a verb before searching: "I need to compute a diff", not "is
there a diff skill". Name search finds only what you already know to ask for,
which is exactly the set you did not need to look up. Need-phrasing finds
adjacent, differently-named, and better options.

## Read the stated contract before trusting it

For each candidate, read what it claims to do, what it needs, what it produces,
and when it applies. A claim is not a validation.

| Failure mode | Response |
|---|---|
| Selecting on the name alone | Read the contract; check inputs and outputs |
| Assuming the contract is current | Confirm on a small representative input |
| Loading every candidate in full | Read descriptions first, bodies only for the shortlist |

## Recognise near-misses

A candidate that covers most of the need is often cheaper to adapt than to
rebuild. Compare the adaptation cost against the build cost, and include the
reuse that adaptation inherits. A near-miss needing a small, generalising
extension usually wins; a near-miss needing most of its behaviour rewritten
loses.

Do not silently stretch a capability past its contract. If the adaptation
defeats its own description, it is a new capability wearing an old name — see
`skill-system.md`.

## Record the negative result

"Checked, found nothing that covers this" is evidence, and it is the result that
saves the most work. Record it specifically enough to be actionable:

```text
discovery
  need        the capability required, as a verb
  searched    what was enumerated, and how
  candidates  what was considered, and why each was rejected
  verdict     covered | near-miss | none-found
  next        acquire | create | proceed-without
```

The `candidates` line is the `rejected` field of a JEv decision record. An
unrecorded negative means the next run repeats the search.

## Bound the cost

| Rung | Discovery |
|---|---|
| R0 | None. The action is already determined |
| R1 | Check capabilities already in context |
| R2 | Enumerate once, shortlist by contract, validate one |
| R3 | Enumerate broadly, record negatives, validate the shortlist |
| R4 | As R3, plus an independent check that nothing better exists |

Stop when the remaining candidates would not change the choice. Widen the search
only when the objective is blocked, and record why it widened.

## Prohibitions

- Do not search capabilities to justify a plan untested against a direct
  attempt. Step 1 of the order in `capability-system.md` comes first.
- Do not treat a long candidate list as progress. Enumerating twenty candidates
  and validating none is discovery failure.
- Do not treat absent from this search as absent. Record it as
  not-found-by-this-method.
- Do not load candidate bodies during the search. That is context cost spent on
  options you have not chosen.

Discovery ends in a shortlist. Validate what you shortlisted with
`capability-validation.md`, choose between skills with `skill-selection.md`, and
if the shortlist is empty, continue at `capability-acquisition.md`.

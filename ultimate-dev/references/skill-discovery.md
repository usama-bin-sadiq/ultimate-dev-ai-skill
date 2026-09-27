# Skill Discovery

Skills are found by their descriptions, not by listing directories. If the
description does not make the skill findable by need, the skill does not exist
as far as the system is concerned.

## The description is the discovery surface

Write it for a reader who does not yet know the skill exists. It must carry
three things:

1. **The user goal** — what outcome the skill serves, in the user's terms.
2. **The trigger condition** — when it should be considered, and explicitly when
   it should *not*.
3. **What it produces** — the artifact, verdict, or state change to expect.

A description that names an implementation or a tool family without stating a
goal answers "what is this" instead of "when do I need it". Test it by asking
whether a request phrased as a problem would match it.

## Name the need, not the category

Discovery runs from a requirement, not an inventory: "I need to reconcile two
sets of records" finds the skill that fixes discrepancies. Listing a directory
is a census, not a search, and it cannot be run before the need is known.

## Naming a vendor dates the skill

A description keyed to one tool's name or one provider's terminology fires only
when the request contains that token. It misses the user who describes the same
problem differently, and it goes stale the moment the tool is renamed, replaced,
or wrapped. Anchor on the goal; mention specific tools only as examples inside a
broader goal statement.

## Trigger discipline

A skill fires on a condition, not a topic. Two descriptions that share a topic
will eventually share a request, so bound every trigger with the neighbouring
request it must decline. A description that can decline nothing will eventually
be loaded for work it does not fit, and its body will then be a worse guide than
no skill at all.

Evaluate the trigger before loading the body. Reading a body to discover whether
it applies is discovery done backwards, and it spends context on a candidate you
should have rejected.

## The standing check before creating a skill

Do this every time, and record it:

1. Search by need-phrasing across what the environment exposes.
2. Read the shortlist's descriptions, and the body of any plausible one.
3. If something already covers the ground, **extend it** — a section, a
   reference, a narrowed trigger. Extending beats adding a second skill, because
   two skills that fire on the same request split the trigger signal.
4. If you create a second one anyway, state why the first was insufficient, in
   the record. "It seemed more specific" is not a reason; an overlapping
   trigger plus a weaker description is a net loss.

The full search procedure and the negative-result format are in
`capability-discovery.md`. Creation itself is delegated, not hand-authored; see
`capability-expansion.md`.

## Record the outcome

```text
discovery
  need          the objective that required a capability, as a verb
  searched      the descriptions examined, by need-phrasing
  candidates    each candidate, and why it was kept or dropped
  verdict       covered | extend | near-miss | none-found
  action        load | extend <skill> | hand the gap to skill-creator
  next          proceed | acquire | create
```

The `candidates` line is the `rejected` field of a JEv decision record. Without
it, discovery is an assertion and the next run repeats the search. Choosing
between the shortlist is in `skill-selection.md`.

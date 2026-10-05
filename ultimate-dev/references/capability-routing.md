# Capability Routing

The intake discipline that matches a task to capabilities. Run it when the
required capability is not already determined; when it is, the effort gate has
already answered and this file is context spent on nothing.

The rule everything else serves:

> Route the objective, never the request.

A capability chosen because the request contained its keyword is a guess with a
citation. The test: rephrase the request without the suspected keyword, and the
choice must survive. "Grill me on Python" and "test this Python code" share a
language and two words, and nothing else — one is knowledge testing, the other
is code verification, and a router matching on "Python" or "test" cannot tell
them apart.

## The procedure

Run at intake, and again at any work unit whose capability is undetermined.

1. **State the outcome.** One sentence, in the user's terms, from the task
   model. Routing without it is matching words to words. `task-model.md`.
2. **Derive the required capabilities as verbs** — "reconcile two record
   sets", "render a deck", "check this proof" — from what must be true at the
   end, never from the request's nouns. A noun names a topic; a verb names the
   work.
3. **Enumerate what the run can reach.** The bootstrap registry, the catalogue,
   the host's exposed list. An unreachable candidate is not a candidate.
   `capability-discovery.md`, `capability-catalogue.md`, `routing-table.md`.
4. **Match on contract, not on name.** For each plausible candidate read what
   it produces, what it consumes, when it applies, and what it declines. The
   description is a claim; the contract is the check.
5. **Select the smallest sufficient set.** A direct answer beats one
   capability, one capability beats a chain, a chain beats a new capability.
   Record every rejected candidate with the discriminating reason — an
   unrecorded rejection is re-litigated on the next turn.
   `skill-selection.md`.
6. **Wire the chain before running it.** Each stage names what produces its
   input and what consumes its output. A stage with no declared consumer is
   decoration; a consumer with no declared producer is a gap, closed at intake
   rather than discovered at the boundary. `skill-composition.md`.
7. **Grade the routing confidence, then act on the grade.** HIGH: proceed.
   MEDIUM: resolve from context first — the answer is usually already in the
   conversation. LOW: ask the one question that changes the routing. Never a
   questionnaire, and never a guess dressed as confidence.
8. **Verify at every hand-off, not only at the end.** A chain checked only at
   the end cannot attribute its failure. `skill-composition.md`,
   `capability-validation.md`.

## The capability card

At R2 and above, record one per shortlisted candidate. The registry
(`agents/_shared/capability-registry.md`) records what the host exposes; the
card records what the selection sees:

```text
capability
  id            the stable name
  kind          skill | role | tool | plugin
  produces      the artifact, verdict, or state change it returns
  consumes      the input it must be given, with format
  use-when      the condition it claims
  not-when      the neighbour it declines
  depends-on    capabilities whose output it needs first
  consumed-by   what this run feeds its output to
```

The last two fields are what make a chain plannable rather than improvised:
`depends-on` is read from the candidate's contract, `consumed-by` is decided by
this run. A card with an empty `not-when` is an unread contract — a capability
that declines nothing will eventually be loaded for work it does not fit.

The full record shapes behind the card are `../knowledge/schemas/capability.md`
and `../knowledge/schemas/agent.md`, and the names in `kind`-agnostic requests
come from the provider-neutral vocabulary in
`../resources/capability-vocabulary.yaml` — never a tool, server, or provider
name.

## The hand-off packet

What crosses a stage or agent boundary:

```text
handoff
  objective     the intake objective, unchanged
  decisions     decisions taken so far, with their rejected alternatives
  output        the previous stage's verified result, in the agreed format
  constraints   only the constraints the next stage can violate
  format        the contract the next stage's output must satisfy
  errors        unresolved failures it must not silently retry
```

Nothing else crosses. Material the next stage cannot act on is noise it pays
for, and a packet rebuilt from the whole conversation is the failure the packet
exists to prevent. The receiver never repeats the search for what the packet
already holds. The packet's `output` is typed and validated as an artifact —
`../knowledge/schemas/artifact.md` — so the next stage checks a contract
instead of trusting a transcript.

## Partial coverage

A capability that covers only part of the need is used for that part and no
more. The remainder re-enters the procedure at step 2 as its own need, and the
results combine at a validated hand-off. Stretching a capability past its
contract is a new capability wearing an old name — `skill-system.md` — and
declining it entirely because it is partial wastes the part that fits.

## Failure at a boundary

A failed stage is classified and re-decided at JEv like any other failure —
`recovery-system.md` — with one addition: a *routing* failure is its own class.
A capability that was wrong for the need is not retried against the same need;
the card was misread, and the run returns to step 4, not to the execution that
just failed. And the standing rule binds at every boundary: never report a
failed stage's anticipated output as its result.

## What the delivery shows

The user receives one coherent result. The routing lives in the decision
record — `capability_required`, `context_required`, `coordination`, `rejected`
— not in the narration. A delivery that reads as a tour of the capabilities
considered has confused the log with the answer. `output-contract.md`.

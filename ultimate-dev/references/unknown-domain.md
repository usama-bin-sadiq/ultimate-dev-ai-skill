# Working in an unknown domain

An unfamiliar domain is a context and capability acquisition problem, not a
blocker. You do not need to know a field before you start; you need to know what
it requires, obtain that, and state clearly how far your confidence extends.
Unfamiliarity alone usually earns R3 effort, but only where the uncertainty
actually changes the work.

## Procedure

1. **Establish the vocabulary and the governing constraints.** What are the terms, what must always hold, what is forbidden? Without this, every later step is guesswork wearing jargon.
2. **Find the authoritative sources.** Specification, standard, primary reference, or the code that actually runs. Secondary summaries are a starting point, never an authority.
3. **Identify what a competent practitioner considers obvious.** This is the part you are most likely to get wrong: what is unremarkable to an expert is exactly what you did not know to ask about.
4. **Identify what is genuinely uncertain here.** The specific questions whose answers would change your approach. This list drives acquisition and verification; it is the task's unknowns, made concrete.
5. **Find or build the capability** the uncertain parts need — see `capability-acquisition.md` and `insufficient-capability.md`.
6. **Proceed with a stated confidence.** Say which parts rest on verified evidence, which rest on assumption, and what would change your mind.

## The characteristic error

The most common way an unfamiliar task goes wrong is confidently applying a
pattern from an adjacent domain where it does not hold. The surface is familiar,
so nothing signals a problem, and the error survives review. Before reusing a
pattern, ask what property of the source domain made it correct there, then check
whether that property actually exists here.

## Assumptions are provisional

State every assumption explicitly and mark it for verification, with what breaks
if it is false and how you would check it. Do not drop the qualifier later: an
assumption written down as a fact is the mechanism of under-evidenced certainty.

## Take a foothold

Prefer a small verified foothold over a large unverified attempt:

- Solve one narrow piece against a checkable success criterion.
- Verify it against real evidence, not against your own expectation.
- Generalise only from what that verification actually established.

A verified narrow piece buys vocabulary, a working capability, and real
evidence at once. A large attempt buys one binary outcome, usually arrived at
late.

## Record what you do not know

The unknown list from step 4 belongs in the task model, marked blocking or
not, so that acquisition effort is aimed at the questions that would change the
approach rather than at everything unread. Assumptions belong in the delivery
with their qualifiers attached. What you did not establish is part of the
result, not a private note — see `insufficient-evidence.md`.

## What you must not do

- Proceed on a single secondary source when an authoritative one exists.
- Treat a confident tone, a clean structure, or a familiar shape as evidence that the content is right.
- Generalise a verified foothold to the whole domain, or from a neighbouring domain without checking the property that made it valid there.
- Fill an unanswerable question with the most plausible value and keep going as though it were established.

## When to stop

Stop and report when you cannot find an authoritative source, when the domain's
governing constraints cannot be established, or when the capability required does
not exist and cannot be built. State what you could not establish and what would
resolve it. Do not fill the gap with a plausible answer borrowed from a
neighbouring field.

Cross-reference `insufficient-evidence.md`, `capability-acquisition.md`, `task-model.md`, and `context-system.md`.

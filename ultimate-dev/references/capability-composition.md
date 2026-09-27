# Capability Composition

Composition joins capabilities that already work into one outcome. It is step 3
of the resolution order and it beats creation at step 5, nearly always. Reach
for composition unless the parts genuinely do not exist.

## Why composition first

- Nothing new must be trusted: both parts are already validated, so the
  validation burden falls on the chain. It fails locally, so a wrong outcome
  names its weak link, and it is a work unit that can be discarded at no cost.
- A chain reused repeatedly becomes the right candidate for promotion, decided
  on evidence rather than assumption.

## The composition contract

State the contract before running the chain; a chain without one is improvisation.

```text
composition
  objective     the outcome, in one sentence
  inputs        what step 1 requires, and in what form
  steps         ordered, each naming the capability it calls
  handoffs      what each step's output must contain to feed the next
  preconditions what must hold before the chain starts
  failure modes what makes each step fail, and what the chain does then
  evidence      what will be observed, and how success is judged
```

The handoff is the usual failure point. Name the field, format, and units that must
survive each transition. "Pass the result" is not a handoff.

## Ordering and data flow

Order by dependency, not by convenience. Run steps in parallel only when they
share no mutable state; two steps touching the same file are sequential however
they are scheduled. Pass the narrowest thing that satisfies the next step's
preconditions, and validate each step's output before the next consumes it, per
`capability-validation.md`; a chain validated only at the end cannot attribute
its failure.

## Reliability is set by the weakest link

Reliability multiplies down a chain. Two 95% steps in sequence are about 90%, and
one step at 80% dominates everything around it. Spend verification effort on the
weakest link, not the most important-looking one. If a weak link cannot be
strengthened, add a check at the handoff, or split the chain so the failure stays
isolated and the completed work survives.

## When a composition should be promoted

Promote only when, not before:

- the chain has been assembled more than once, for different tasks;
- it failed in the same place twice, meaning the chain itself is the defect;
- the handoffs have settled into a stable interface worth naming;
- composing it takes a decision each time, and it is the same decision.

Then apply the disqualifying question: will this be needed again? Promotion is the
only route into creating a capability, and it is delegated; selection between
candidates is in `skill-selection.md`.

## Route creation and promotion to the capability-expansion engine

Composition and creation are **not done inline**. Hand the gap to
`skill-creator`, the capability-expansion engine, which owns intent capture,
specification, security review, validation, evaluation, and promotion. Give it
the need, the evidence that steps 1 to 4 failed, and the reuse case. Its
lifecycle and gates are in `capability-expansion.md`.

## Worked example

Objective: *produce an accurate change note for a set of edits.* No single
capability does this.

```text
composition
  objective     a verified change set plus an accurate summary of it
  inputs        the working tree, the previously recorded state
  steps         1. collect changed files (source state query)
                2. compute the diff deterministically (diff tool)
                3. classify each hunk by intent (review procedure)
  handoffs      step 2 emits per-file hunks with byte ranges and no colour
                codes; step 3 consumes hunks, not prose
  preconditions the previous state is recorded and reachable
  failure modes step 1 finds nothing changed -> stop, report no change, do not
                fabricate a note; step 2 emits a truncated diff -> FAILED, do
                not summarise a partial diff
  evidence      the diff byte count, the hunks classified, the note read back
                against the diff
```

Step 2 is deterministic and must be, not recalled; step 3 is judgement and can be
done directly. Validating step 2 for completeness, not just shape, is what stops
step 3 from summarising a diff that was never complete.

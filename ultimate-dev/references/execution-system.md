# Execution System

Execution carries out the plan one work unit at a time, and every action it
takes produces an observation. Two rules dominate: do the deterministic thing
deterministically, and never report a tool result you did not observe. Both
exist because their violations are invisible downstream.

## Before each unit

Confirm the unit's **precondition still holds**. Preconditions are the first
thing reality invalidates, and starting a unit on a stale precondition wastes
the unit and can corrupt shared state. If it does not hold, stop: return to JEv
and re-decide, do not proceed hopefully. See `planning-system.md`.

## Do the deterministic thing deterministically

Compiling, hashing, counting, parsing, searching, formatting, and arithmetic
belong to a tool, not to recall. A model doing arithmetic by hand will
sometimes be wrong; a tool asked will not. This is not about capability
dignity — it is about the error rate. Route every checkable operation to a
tool, and reserve your own effort for judgement, framing, and ambiguity. See
`deterministic-vs-agentic.md`.

**Never report a tool result you did not observe.** If a command was not run,
its output is unknown, not expected. Do not describe what a command "should"
print, do not report a pass you inferred, do not summarise a file you did not
read. This is the single most damaging failure in the system: it is
undetectable by the reader, it propagates through every later unit, and it
converts a working kernel into a fabricator. When you did not run it, say you
did not run it.

## Parallelise only genuinely independent units

Two units sharing mutable state — the same file, the same database, the same
working directory, the same process — are sequential however they are
scheduled. Concurrency over shared state is a race whose failure you will
attribute to something else. Parallelise when units are independent *and* a
failure in one is contained *and* wall-clock actually matters here. Otherwise
sequencing is cheaper than the coordination. See `parallelism.md`.

## Delegate only when specialisation clearly beats doing it

Delegation is a cost, not a default: it pays for a brief, loses shared context,
and adds a boundary you must verify across. Delegate when the sub-problem needs
knowledge or judgement this context does not have, or when isolation is worth
more than coherence. Give the delegate the context it needs and nothing more.
Spawning a specialist to do what one context does better is
unnecessary delegation. See `delegation.md`.

## Execution shapes

| Shape | Use when | Watch for |
|---|---|---|
| **Sequential** | Each step consumes the previous result | Long chains hide a late discovery; put the riskiest unit early |
| **Parallel** | Units are independent and contained | Shared state is never independent, however it looks |
| **Conditional** | Later work depends on a check | Make the branch condition observable, not assumed |
| **Iterative** | Output improves against a readable measure | Define the stop condition before starting, or loop forever |
| **Recursive** | One rule repeats at a new depth on new data | Bound the depth, or the recursion is unbounded work |
| **Checkpointed** | Work must survive interruption or a human gate | The checkpoint must be resumable, not a summary of intent |
| **Interruptible** | The task may be cut off at any point | Every unit leaves state a fresh context can use |
| **Recoverable** | Failure is possible and its cause is diagnosable | Recovery is planned before the action, not improvised after |

Prefer a shape you can resume. If a unit cannot be picked up by a context that
was not present for it, it is not finished work.

## During and after each unit

- Record the result the moment you have it, before you interpret it. See
  `observation-system.md`.
- Check the unit's expected result. A unit that did not produce it has not
  passed, however plausible it looks.
- On failure: **classify before responding.** Blind retry is prohibited — a
  repeated action whose cause is unknown reproduces the failure while
  producing the appearance of effort. See `recovery-system.md`.
- On success: note whether the plan's next assumption is now tested or still
  untested, and update the internal run state.

## Prohibitions

- No executing a unit whose precondition you did not check.
- No reporting unobserved output, in any form, including hedged forms ("this
  should pass", "presumably the tests are green").
- No reimplementing a tool's job from recall.
- No parallelism justified by "they look unrelated" rather than by shared-state
  analysis.
- No continuing past a failed check to see whether the rest works.

See `planning-system.md` for the units, `observation-system.md` for the record,
`verification-system.md` for what a passed unit still needs, and `parallelism.md`,
`delegation.md`, `deterministic-vs-agentic.md` for the three judgement calls
above.

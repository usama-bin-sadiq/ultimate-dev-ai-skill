# Execution System

Execution carries out the plan one work unit at a time, and every action it
takes produces an observation. Two rules dominate: do the deterministic thing
deterministically, and never report a tool result you did not observe. Both
exist because their violations are invisible downstream.

## The process log

Every meaningful operation gets a process number, and the log records what
actually happened. Numbering is `P01`, `P02`, … with `P03.1`, `P03.2` for
substeps, and **it is never reset** — including during recovery, because a number
that restarts at 1 after a failure is a log that cannot be read to find out what
had already been tried.

```text
P01 — RECEIVE      User objective received.
P02 — UNDERSTAND   Objective and success criteria identified.
P03 — TRIAGE       Complexity and dependencies assessed.
P04 — DECIDE       Required capability identified.
P05 — REACHABILITY Required specialist confirmed reachable.
P06 — CONTEXT      Loaded only the capability instructions in hand.
P07 — DELEGATE     Specialist invoked.
P08 — EXECUTE      Specialist performed the requested operation.
P09 — OBSERVE      Result received.
P10 — VERIFY       Result checked against the success criteria.
P11 — RECOVERY     Additional action required.
P12 — REPLAN       Alternative execution selected.
P13 — EXECUTE      Alternative action completed.
P14 — VERIFY       Result verified.
P15 — SYNTHESIZE   Final result assembled.
P16 — DELIVER      Task completed.
```

**The log describes operational events, not private reasoning.** It records what
was invoked, what returned, what failed, and what changed — not the deliberation
that chose between them. A log of reasoning is a liability: it is unverifiable
from outside and invites reconstructing it rather than recording it.

### The log must be truthful, and must agree with the state

Never log `P07 — INVOKED` if invocation did not happen. Never log `P10 —
VERIFIED` if verification did not happen. Never log `P16 — COMPLETE` if work
remains. The process log and the run state must agree; where they disagree, at
least one of them is a claim rather than a record, and the delivery is reporting
from the wrong one.

This is the same rule the dispatch chain enforces mechanically — a capability at
`selected` is not `observed` — applied to the narrative form. A run can satisfy
every state gate and still write a log that claims work it did not do, because
the log is prose and the gates are not.

So the log is written through a gate rather than left as a habit:

```sh
python3 tools/run-state.py log --kind <stage> --what "<what happened>" [--under P03]
```

`--kind delegate` is refused unless a capability is at `invoked` or beyond.
`--kind verify` is refused unless a capability reached `verified` or an
acceptance criterion is met. `--kind complete` is refused until `finish` has
recorded a status. A run that did its work inline is not penalised — the kinds
that claim nothing about the ledger (`receive`, `triage`, `plan`, `deliver`,
`recover`, `replan`, `escalate`) are always accepted, and using them is the honest
description of what happened.

**The third check is ordering.** A stage is refused unless the log has already
been where that stage comes from, so `observe` needs an `execute` and `verify`
needs an `observe`. Truth of a single entry is not enough: a log can be
individually true and still be written backwards at the end, and a log that was
reconstructed after the fact is the failure this file exists to catch — it reads
perfectly and records nothing. The predecessor sets are:

| Kind | Requires one of |
|---|---|
| `execute`, `executed`, `execute-inline` | `plan`, `decide`, `delegate`, `dispatch`, `replan`, `recover` |
| `delegate`, `dispatch` | `decide`, `reachability`, `plan`, `replan` |
| `invoked` | plus `delegate` or `dispatch` |
| `observe`, `observed` | `execute`, `executed`, `execute-inline`, `delegate`, `dispatch`, `invoked` |
| `result` | plus `observe` or `observed` |
| `verify`, `verified` | `observe`, `observed`, `result`, `execute-inline`, `decide` |
| `synthesize` | `verify`, `verified`, `observe`, `observed`, `execute-inline` |
| `deliver` | anything — see below |
| `complete` | `deliver`, `synthesize`, `verify`, `verified` |

`deliver` deliberately accepts almost anything before it. It is a terminal act, and
a short run that received, triaged and delivered is legitimate; demanding an
execution entry first would punish a run for being short, which is the same mistake
as gating a field on whether it holds a value rather than whether it exists. The
"a long run delivered having logged no execution at all" case is real, and it is
checked in `check` instead, where the rung and the work-unit count are both known.

`execute-inline` is a kind that exists because a gate found a gap on real work. A
run that did the job itself had no honest way to record that: `execute` claims a
dispatch is running, and the dispatch ledger correctly says nothing was dispatched.
The alternative was to write nothing, leaving a hole where the execution happened.

`audit` catches the terminal version of the same failure in the delivery; the
`log` gate prevents it locally, entry by entry.

State is updated as each of these events happens, not reconstructed at the end:
capability discovery · capability selection · context acquisition · agent
invocation · agent completion · execution · tool use · error · verification ·
retry · replan · mode change · handoff · recovery · completion. A state
reconstructed from memory at the end is a summary of what the run wished it had
done.

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

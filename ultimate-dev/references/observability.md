# Observability

The cross-cutting control plane names eight systems. Seven govern what the kernel
*does*; this one governs what you can *see while it does it*.

Observability is not logging. Logging is a record produced for later. Observability
is the ability to answer, during a run, three questions:

1. Where is it?
2. What is it about to do next?
3. What has it already established, and how sure is it?

A run that cannot answer those is not merely hard to debug — it cannot be
interrupted safely, resumed, or handed to someone else. The absence is invisible
until the moment someone needs it, which is always the worst moment.

## The three surfaces

**Position** — the current rung, the current work unit, and what is in flight.
Cheap to maintain, and it is what lets a human say "stop" at a meaningful boundary
rather than mid-write. A run with no position can only be killed, not steered.

**Intent** — the next action, before it is taken, with its precondition. This is
what makes interruption safe. If you know what was about to happen, you can let it
finish and resume cleanly; if you do not, the only safe action is to abort, and you
have lost the work in flight.

**Basis** — the evidence behind the load-bearing claims so far, with its epistemic
status. Not the reasoning; the observations. This is what lets a second party
audit a run without re-deriving it.

## What to emit, and when

Not continuously. At boundaries, which are already defined:

| Boundary | Emit |
|---|---|
| After triage | Rung, scale, and the one-line reason |
| Before each work unit | The unit, its precondition, its expected result |
| On any tool call | What was run, and the observed result — including the failure |
| On any decision record | The record |
| On verification | The checks performed, the criteria, the verdict |
| On recovery | The classification and the chosen response |
| On a coordination-mode change | The mode before, the mode after, and the reason |
| On delivery | The output contract |

That is roughly one line per boundary. A run emitting more than that is reporting
process rather than position, and the extra volume buries the thing a reader needs.

A mode change earns its own line because it is a claim about the run that only
the run itself can make. A mode that changes three times in one run is not a run
that adapted well; it is evidence the first choice was wrong, and nothing
further down will say so.

## Why a run must be able to report its own basis

Three failures are only catchable mid-run if the run can show its evidence:

- **Drift.** The task changed and the run did not notice. Visible when the
  objective and the current unit's purpose stop matching.
- **Confident fabrication.** A tool result that was never observed. Visible when
  a claim cites an observation that does not exist — which is only detectable if
  claims cite observations rather than prose. See `evidence-system.md`.
- **Self-conditioning.** A wrong conclusion being re-read as a premise. Visible
  when a load-bearing claim's only support is an earlier conclusion of this same
  run. See `learning-safety.md`.

All three are invisible from the outside without this surface, and all three are
cheap to catch with it.

## Interruption and resumption

Observability is what makes a run interruptible. Three requirements, and they are
the same three requirements as resumability in `state-system.md`:

1. **Position** — which unit, and which rung.
2. **Side effects in flight** — what was being written when the interruption
   happened, so a half-applied change is found rather than discovered later as a
   mystery.
3. **Basis** — the evidence, so verification can re-run rather than trust.

A run meeting all three can be stopped, handed to someone else, and resumed
without loss. A run meeting none can only be restarted, and restarting a long run
is the most expensive failure there is because it is invisible until you notice
the work is gone.

## What this costs, and when to skip it

Emitting at boundaries costs a line per boundary. At R0 and R1 that is
disproportionate — the run is short enough to hold — so emit nothing and keep the
position in your head. From R2 up, position and intent are worth the lines. Basis
matters from R3, and at R4 it is what you hand the human who approves the action.

The failure to avoid is the opposite one: a run at R4 that cannot show its basis
before an irreversible action is a run asking to be trusted on assertion.

## Anti-patterns

- **Transcript as observability.** A wall of tool output is a record, not a
  position. Nobody reads 400 lines to answer "where is it".
- **Emitting state without intent.** Position without the next action cannot be
  steered, only watched.
- **Self-reported progress.** "On track" is not a position. The current unit and
  its precondition is a position.
- **Observability theatre.** Emitting a structured preamble that restates the
  task every turn, adding volume and no information.
- **Instrumenting R0.** The overhead exceeds the run.

Cross-reference `state-system.md` for what is held, `decision-ledger.md` for the
decisions these surfaces expose, `budget-system.md` for the cost accounting they
feed, and `recovery-system.md` for the classifications they make recoverable.

# Budget and limits

Budget is a constraint the kernel is given, not a resource it discovers it has
run out of. The difference decides whether a run ends with a report or a
truncation.

## One budget, several currencies

The kernel spends from a single budget in several currencies. They are not
interchangeable, and pretending they are is how runs go wrong.

| Currency | What it buys | What happens when it is gone |
|---|---|---|
| **Attention** | the user's time and reading capacity | the delivery itself is the casualty: long enough to bury the outcome |
| **Time** | elapsed wall clock, including waiting on tools and people | remaining units are dropped or declared |
| **Cost** | tokens, compute, external service charges | context depth and research depth are cut, in that order |
| **Risk tolerance** | how much uncertainty the run will hold open | verification depth is cut, and this is the last thing to cut |
| **Reversibility headroom** | how much can be undone cheaply | actions become one-way, so confirmation is requested instead of work being done |

The currencies interact. A slow external call spends time and cost while
contributing nothing to attention, which is why waiting is not free. A long
delivery spends attention, which is why a thorough run with a buried outcome is
a failure even when the work was right.

## Allocation across phases

The kernel allocates in a fixed priority order. Lower rows are cut first, and the
order is part of the design rather than a runtime choice.

1. **Understand and triage.** Not reducible. Without them the run cannot know
   what the budget is for, and every later decision is unanchored. This is a few
   hundred tokens spent to protect everything below.
2. **Success criteria and verification.** Protected absolutely. These define
   done, and a run that cannot say whether it succeeded has produced an
   impression, not a result. If verification cannot be afforded, the run reports
   the block.
3. **Deterministic execution.** Cheap and reliable. A step moved from recall to
   a tool usually saves budget rather than consuming it.
4. **Observation recording.** Cheap, and it is what makes recovery and resume
   possible. Trimming observations to save budget removes the ability to recover,
   which costs more later.
5. **Work units required by the criteria.** Cut by scope, in this order: optional
   refinement, then breadth of coverage, then depth of quality, then a stated
   feature. Never by cutting the checks on what remains.
6. **Context depth.** Cut toward C3, keeping the region that bears on the live
   decision. Cut breadth before depth: a narrower problem solved with full
   context beats a broad problem solved from descriptions.
7. **Research depth.** Cut first among the optional acquisition activities, since
   it is the most speculative spend.
8. **Verification strength.** Independent re-derivation is the first thing cut.
   The evidence and validation checks are not cut; if they cannot be afforded,
   the run reports the block instead.
9. **Parallelism.** This frees time, it does not spend it. If the budget is
   wall-clock bound, more parallelism is the answer. If it is cost bound,
   parallelism makes it worse. Check which before using it.
10. **Delegation.** Cut freely. It is the most expensive optional mechanism and
    the least often necessary.

### The rule the order encodes

Scope is reducible. Verification is not. A smaller result that was checked is a
deliverable; a larger one that was not is a liability with a confident voice.

## When the budget is insufficient

Declare it. A declared block is a valid terminal outcome, and the delivery
states:

```text
BLOCK
  what was completed        with verification status
  what was not completed    and why it was dropped
  what the budget was       in each currency, as consumed
  what resuming would need  the next units, and their preconditions
  what to cut for more      the scope options, in the order above
```

Silence at a resource boundary is the defect. The reader cannot distinguish a
truncated run from a finished one, so they act on an incomplete result believing
it complete. That is worse than a smaller complete result, and it is the specific
failure this document exists to prevent.

## Reducing scope without under-delivering silently

Under-delivering silently means the requester believes they got what they asked
for. Four practices prevent it.

**Restate the reduced objective as a deliverable.** Not "I ran out of budget" but
"this establishes X, and Y is not established". A reduced objective that is
stated is a smaller task, and a small task can be complete.

**Keep the criteria, cut the surface.** If the criteria are fixed and the
surface shrinks, you have a smaller success. That is legitimate. The opposite —
keeping the surface and cutting the criteria — is a silent under-delivery, and it
is the more common mistake because it feels like progress.

**Re-triage, do not continue at the old rung.** A run that is about to deliver
half a result has changed task shape. Re-running triage is how the kernel drops
from R3 to R1, and it is also how it notices that the remaining work is now
higher consequence than the work already done.

**Report the reduced result as PARTIAL, not VERIFIED.** A partial verdict with
the satisfied criteria named, the unsatisfied criteria named, and the gap
described is a real deliverable. See
`../concepts/verification-and-evidence.md`.

### Worked example

Objective: refactor the authentication module, cut duplication, preserve
behaviour, no change to the public API. Budget: one session.

Reduction that is honest: the duplication analysis and the refactor of the token
validation path, with the API surface untouched and the test suite green.
Report: those criteria VERIFIED by the test run; session refresh, password
reset, and the two remaining duplicated helpers NOT established, dropped for
budget, with the next units named.

Reduction that is not honest: doing the token path, reporting the module
refactored, and mentioning the rest as "considerable technical debt left for
follow-up" in a limitations line. Same amount of work, completely different
result, and the requester now believes they have a refactored module.

## Budget as an input

A declared budget changes the run. Give one when you have one.

- **Time** — "I need an answer before this deploy window." The kernel cuts
  research depth and breadth first, and says what it chose not to establish.
- **Cost** — "Keep this under a fixed spend." Context and research are cut
  together with the first available slack; depth is preserved where it decides
  the result.
- **Iteration** — "At most two attempts per hypothesis." Forces classification
  discipline and stops the retry-storm failure mode, because the bound is
  visible.
- **No budget** — the kernel uses what the work needs and stops when the
  criteria are met. This is correct for open-ended work, and it is not a licence
  to spend; the allocation order above still applies.

## The cost of the kernel's own machinery

The kernel spends budget on deciding, and that spend must justify itself.

| Activity | Justified when | Not justified when |
|---|---|---|
| Triage | always, and it is small | never skipped, because it protects everything else |
| Task model | the criteria are needed to verify at all | the next action is already determined and the check is the output itself |
| Capability search | nothing in hand covers the work | doing it directly works |
| Decomposition | parts interact or must be verified separately | the work is one atomic change |
| Context beyond C3 | a decision names something you do not hold | the decision is already determined |
| Independent verification | novel, high-consequence, or load-bearing | tool-confirmed and low-stakes |
| Learning promotion | the pattern will recur | a single instance, and the candidate record is enough |

The right-hand column is not a smaller version of the left. It is the common
case for a large fraction of tasks, and treating it as the small case is the
defect in `troubleshooting.md` entry 1.

## Signals that a run is over budget

Stop and re-triage when you see any of these:

- Units are being executed whose results will not be used.
- Context is being re-read for the third time without a decision changing.
- The same class of failure recurs and the fix has not changed.
- Verification is being deferred to the end on work that is no longer
  reversible.
- The delivery is getting longer while the outcome is getting further away.
- A capability is being created for something needed once.

Each of these is a signal to re-decide at the hub, not to continue. Continuing
past one of them is how a run converts a budget overrun into a silent scope
reduction.

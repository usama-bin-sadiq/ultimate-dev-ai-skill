# Architecture

This directory explains how `ultimate-dev` is put together and why each part
exists. Start here. Move to `kernel.md` for the execution model, to
`context-and-capability.md` for the two acquisition ladders, and to
`scalability.md` for how one kernel spans trivial tasks to programmes.

## The invariant

Every design choice serves one sentence:

> Do not hand the agent everything. Hand it the ability to work out what it
> needs, get it, use it, check it, recover from failing, and keep only what has
> proven useful.

If a layer cannot be traced back to that sentence, it is a candidate for
deletion. Several components that seemed essential have been removed on that
basis already, and the decision records in `../decisions/` say which.

## The fourteen layers

A layer is a distinct kind of work, numbered as in the architecture diagram.
Layer 0 is the input, not a layer: it is the objective, the request, the
constraints, and the resources you already hold.

Each entry below gives the question the layer answers and what breaks if it is
absent. The "if absent" is the important half: it is the argument for the layer,
and it is what a redesign has to answer again.

| # | Layer | Question it answers | If absent |
|---|---|---|---|
| 1 | Task model | What must be true when this is done? | No definition of done, so verification has nothing to check and recovery has no trigger |
| 2 | Triage | How much machinery does this deserve? | Full analytical process on a one-line change; the most expensive defect in the system |
| 3 | JEv decision fabric | What do we do next, and what are we not doing? | A fixed pipeline, which works for one problem shape and fails on all the others |
| 4 | Context compiler | What do we need to know that we do not know? | Reasoning across everything in the window, with no way to tell a loaded fact from a missing one |
| 5 | Capability system | What can do this, and what is missing? | Bounded by what shipped; gaps become excuses or improvisation |
| 6 | Strategy selection | Which approach, and why not the others? | The first approach that occurs is the approach; failure changes only the retry count |
| 7 | Reasoning control | How much reasoning is justified? | Difficulty worship, or under-reasoning on exactly the novel, consequential problems |
| 8 | Execution plan | What are the atomic units and their order? | Entangled work: a late failure destroys everything before it, and nothing is resumable |
| 9 | Execution | What actually happens? | Nothing happens |
| 10 | Observation | What really happened? | The confident fabrication, invisible downstream |
| 11 | Verification | What must be true for this to be trusted? | Unfalsifiable output; failures reach the user instead of the kernel |
| 12 | Result synthesis | What survived? | Unverified material delivered as verified, or verified material never delivered |
| 13 | Self-evaluation | Was the way we worked right? | No correction of habits: every run starts from the same defaults, including failing ones |
| 14 | Learning system | What is worth keeping, and what is not? | Repeated failure at full price, and a hand-performed procedure that stays manual |

Two of these deserve emphasis. Layer 2 exists because a system this capable will
happily spend a great deal on a trivial request, and the ceremony is invisible:
the answer arrives, just slowly, surrounded by process nobody asked for. Layer
10 exists because everything else in the architecture is wasted if the kernel
reports what it expected rather than what occurred; see
[0001](../decisions/0001-jev-as-decision-fabric.md) for the layer 3 argument in
full.

## The cross-cutting control plane

Eight systems apply to every layer rather than sitting in sequence. They are
what stop the architecture from being a diagram.

| System | What it holds | If absent |
|---|---|---|
| State management | task model, decisions, units, observations, failures, budget, result | no resume, no audit, and every claim about earlier work is unverifiable |
| Budget manager | remaining time, cost, and tolerance for expansion | everything is spent on the first hard thing, with nothing left for the second |
| Evidence and provenance | claims, sources, transformations, checks | the result cannot be traced and stale inputs are invisible |
| Security and trust | which content may authorise an action, and which may only inform | a retrieved document can widen the kernel's own authority |
| Observability | decision ledger, observation log, verification records | failures can only be suffered, not diagnosed |
| Cache and reuse | capabilities and findings proven useful, with their scope | proven work is repeated from scratch at full price |
| Policy and constraints | prohibitions, permissions, budgets, formats | constraints live in one paragraph of the prompt and are honoured unevenly |
| Error and recovery state | failure log, classification, bounds | the same failure is rediscovered from scratch on every unit |

The control plane is why a run can be interrupted and resumed. Each system keeps
enough written state that a new session can pick up mid-plan without re-deriving
what the last one concluded.

## How the layers compose in a run

A full run visits layers in this order:

```text
RECEIVE → UNDERSTAND → TRIAGE → DECIDE → ACQUIRE → PLAN → EXECUTE
   ▲                                                        │
   │                                                     OBSERVE
   │                                                        │
   └──── LEARN ← SELF-EVALUATE ← SYNTHESIZE ← VERIFY ←─────┘
                          ▲              │
                          └──── RECOVER ┘
```

Two properties matter more than the shape.

**DECIDE is the only hub.** Context depth, capability, strategy, reasoning
depth, delegation, parallelism, verification depth, retry, replan, escalation,
and promotion all pass through one decision point. Because every arrow returns
to it, no stage is a one-way commitment. A plan that cannot be revised by its own
evidence is worse than no plan.

**No stage is mandatory for every task.** A one-line transformation enters at
UNDERSTAND, finds the next action is determined, acts, observes, and verifies
the output. It passes through four layers, not fourteen. The layers are a menu
selected by the decision procedure, not a schedule.

## Where to read next

- `kernel.md` — the lifecycle stage by stage, the 17 decision boundaries, and
  which boundaries each rung must cross.
- `context-and-capability.md` — the C0 to C6 context ladder, the five-step
  capability ladder, and the failure mode at each end of both.
- `scalability.md` — the same kernel at L1 to L7, what changes, what does not,
  and how hierarchical planning is built.
- `../concepts/` — the vocabulary, defined once.
- `../decisions/` — the trade-offs, recorded, including the ones that were lost.

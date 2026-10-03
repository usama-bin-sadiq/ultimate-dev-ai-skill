# Coordination Modes

How the results of a task come back together. Four modes, chosen at a JEv boundary before
capability selection, and chosen **cheapest-first**.

The four are not four architectures. They are four answers to one question:

```text
   Given what this task needs, how do the pieces come back together
   — and what does that choice cost?
```

A capability answers *what* can help. A coordination mode answers *how the help is
assembled*. Getting the capability right and the mode wrong still produces a bad run, and
usually an expensive one: four skills loaded to answer a one-line question, or a thread
handed off that one agent could have held.

## The four modes

```text
   ① INLINE      progressive disclosure. Load skills C0→C6 into this agent.
                 0 extra model calls. The corpus's default shape.

   ② DELEGATE    JEv calls a stateless specialist as a tool; the result returns
                 through JEv. +1 call per result. Buys context isolation.

   ③ ROUTE       decompose the query, run N specialists in parallel, synthesize.
                 N calls. Stateless, so a repeat request re-pays classification.

   ④ HANDOFF     set active_agent so one specialist holds the conversation and
                 capabilities unlock as information arrives. Most stateful.
```

## The selection test

Read in order and stop at the first that fits.

```text
   Is one capability enough, and is it already in context?
        └─ yes ──────────────────────────────────► ① INLINE

   Does the work need a specialist whose context must NOT pollute this one,
   and can it report back as a single result?
        └─ yes ──────────────────────────────────► ② DELEGATE

   Does the question span several sources or domains whose answers must be
   merged into one?
        └─ yes ──────────────────────────────────► ③ ROUTE

   Must one party hold the conversation across stages, with capabilities
   unlocking only as earlier information arrives?
        └─ yes ──────────────────────────────────► ④ HANDOFF
```

**Order is the point, and it is cheapest-first.** The failure this prevents is not
choosing a bad mode; it is choosing mode ④ when mode ① would do, with nothing recording
that the cheaper option was on the table. That is why `coordination` is a required field
with a mandatory `why`, rather than a default.

## What each costs

```text
   ① INLINE     0 extra calls          · context ACCUMULATES in history
   ② DELEGATE   +1 call per result     · results route back through JEv
   ③ ROUTE      N calls, parallel      · stateless; repeats re-pay
   ④ HANDOFF    stateful               · most expensive to get wrong
```

**Read "cheapest adequate" as cheapest per call, which is not the same as cheapest per
unit of work.** Mode ① is free per call and can be the most expensive mode overall, because
every loaded skill stays in the conversation and is paid for again on every turn. In a
corpus of this size that is the dominant cost, and mode ③ is the mitigation rather than an
alternative to it.

The honest consequence: some capabilities will have to stop being skills and become
delegates. That is a content decision about the corpus, not one this architecture can make.

## Mode ① — inline

```text
   kernel SKILL.md ──always loaded──┐
                                    ▼
   C2 the procedure for the unit in hand
                                    ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ skill A  │  │ skill B  │  │ skill C  │
   │ (loaded) │  │ (loaded) │  │ (loaded) │
   └──────────┘  └──────────┘  └──────────┘
                  └── accumulate in one context ──┘
```

Progressive disclosure, three levels: names and descriptions at load, the full skill when
relevant, files within it as needed. This is the shape the whole tree is built in, and it
is the right default — see `references/context-system.md` and `references/capability-system.md`.

## Mode ② — delegate

```text
              ┌──────────────────────┐
              │  kernel / JEv        │  holds the context
              └──────────┬───────────┘
     ┌────────────┬─────┴─────┬────────────┐
     ▼            ▼           ▼            ▼
  ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐
  │spec 1 │   │spec 2 │   │spec 3 │   │spec 4 │
  │statel.│   │statel.│   │statel.│   │statel.│
  │own ctx│   │own ctx│   │own ctx│   │own ctx│
  └───┬───┘   └───┬───┘   └───┬───┘   └───┬───┘
      └───────────┴─────┬─────┴───────────┘
                        ▼
              results return to JEv
```

A stateless specialist with its own context, invoked as a tool, answering in one result.
The specialist has no workflow of its own: it cannot triage, verify, or recover. See
`references/delegation.md` for the justification test and the upper bound.

## Mode ③ — route

```text
          ┌───────────────────────────────┐
          │  ROUTER (stateless)          │
          │  classify + decompose        │
          └──────────────┬────────────────┘
    ┌──────────┬─────────┼─────────┬──────────┐
    ▼          ▼         ▼         ▼          ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│vert A │ │vert B │ │vert C │ │vert D │ │vert E │
└───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘
    └─────────┴─────────┴─────────┴─────────┘
                    │ in parallel
                    ▼
        ┌───────────────────────────────┐
        │  SYNTHESIZE                   │
        │  one coherent response        │
        └───────────────────────────────┘
```

For questions that genuinely span several sources and need one merged answer. Two costs
worth stating: it is **stateless**, so a repeat request pays classification again; and it
does **not chain**, so a multi-hop question is the wrong shape for it. Recording the mode
with an `until` condition is what lets a repeat skip the classification rather than repeat
it by default.

## Mode ④ — handoff

```text
   ┌──────────┐  handoff  ┌──────────┐  handoff  ┌──────────┐
   │ agent A  │──────────►│ agent B  │──────────►│ agent C  │
   │ active   │           │ active   │           │ active   │
   └──────────┘◄──────────└──────────┘◄──────────└──────────┘
        │                                                     │
        └──────────── state survives every turn ─────────────┘

   coordination.active_agent : who holds the thread
   coordination.authority    : inline | delegated
```

For a staged conversation where capabilities unlock as information arrives and the user is
talking throughout. The most stateful mode, and the one where a wrong choice compounds: a
handoff that should not have happened fragments the thread.

### Why this does not abandon the fabric

The active agent changes. **The decider does not.** A handoff is an ordinary decision record
whose `coordination` field is `handoff` and whose effect is to write `active_agent`. Control
never leaves JEv.

```text
   revision 1 said:  "Agents are NOT the architecture."
   revision 2 says:  Agents are not the architecture.
                     JEv is — including when it hands off.
```

The specialist still has no workflow of its own. It answers; JEv decides what happens next.

## Changing mode mid-run

Recovery may change the mode, and the change is recorded like any other field:

```text
   python3 tools/run-state.py set-mode --mode route \
       --why "the delegate failed twice; three sources would have covered it" \
       --until "a single source would suffice"
```

A delegate that fails repeatedly, where a route would have covered the ground, is a **mode
error rather than a capability error** — and without the field it would be indistinguishable
from a broken specialist.

Three changes in one run is not a hard task. It is a first choice that was wrong, and
`run-state.py check` says so.

## Selection is gated on reachability

A specialist is only selectable if the kernel can actually route to it. This is not a
formality.

A library of domain specialists with overlapping descriptions means the wrong one is chosen
as often as the right one, and **the failure presents as incompetence rather than
misconfiguration** — so it does not get debugged. Adding a mode that selects specialists by
description sharpens that problem rather than solving it. Decision `0002` recorded the
cost; this is where it is paid.

```text
   shipped roles            291
   roles the kernel routes to  ~32
   reachable                  far fewer
```

Unreachable specialists are not spare capacity. They are descriptions competing for the
same attention as the ones that work.

## Host-native workflow primitives

When the host exposes a native parallel-dispatch or pipeline primitive that maps
cleanly to the selected coordination mode, prefer it over serial inline execution.
Context isolation and parallelism are real gains — not cosmetic ones — because
they reduce context accumulation and wall-clock time for independent work.

The mode decision comes first. The primitive is the implementation vehicle, not
the driver. A host without any workflow primitives runs the same four modes by
the serial inline fallback path, with identical logical outcomes.

How each mode maps to a host primitive, what to fall back to, and how to detect
whether a primitive is available: `references/workflow-bridge.md`.
